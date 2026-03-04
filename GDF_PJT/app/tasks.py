from __future__ import annotations

from pathlib import Path
import xml.etree.ElementTree as ET
from typing import Dict, Iterable, List, Tuple
import shutil
import time
import zipfile

from celery import shared_task
from django.db import transaction
from django.utils import timezone

from app.classes.CargaXml import Carga_xml, EmpresaNaoCadastradaError
from app.db_GDF.Public.models import CargaXmlJob, CargaXmlParam


MODEL_FOLDER_MAP: Dict[str, Tuple[str, str]] = {
    '55': ('modelo55', 'NFe'),
    '57': ('modelo57', 'CTe'),
    '67': ('modelo67', 'CTe'),
    '13': ('modelo13', 'NFSe'),
    'SPC': ('modeloSPC', 'NFe'),
    'SPF': ('modeloSPF', 'NFe'),
}

# Previously the parameters included an optional "modelos" field that
# allowed restricting processing to certain document types.  That column
# was removed in migration 0013, so the filtering logic is now obsolete.
# We continue to scan every known folder by default.


def _extract_zips_in_folder(base_dir: Path) -> None:
    """Encontra todos os .zip na pasta (e subpastas), extrai o conteúdo na mesma
    pasta onde está cada zip e segue. Não altera pastas 'processados' e 'pendentes'.
    """
    if not base_dir.exists() or not base_dir.is_dir():
        return

    excluded_names = {'processados', 'pendentes'}
    zip_paths: List[Path] = []
    for p in base_dir.rglob('*.zip'):
        parts = {part.lower() for part in p.parts}
        if parts & excluded_names:
            continue
        if p.is_file():
            zip_paths.append(p)

    for zip_path in zip_paths:
        extract_dir = zip_path.parent
        extract_resolved = extract_dir.resolve()
        try:
            with zipfile.ZipFile(zip_path, 'r') as zf:
                for member in zf.namelist():
                    if member.endswith('/'):
                        continue
                    # path traversal: extrair só se o path final estiver dentro de extract_dir
                    dest = (extract_dir / member).resolve()
                    if not str(dest).startswith(str(extract_resolved)):
                        continue
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    with zf.open(member, 'r') as src:
                        dest.write_bytes(src.read())
        except (zipfile.BadZipFile, OSError, ValueError):
            pass


def _collect_xml_files(base_dir: Path) -> List[Path]:
    """Return all XML files found under *base_dir* (recursively).

    Historically we only looked inside a fixed set of subfolders derived
    from :data:`MODEL_FOLDER_MAP`.  The user story now is that the company
    directory may contain *any* number of model-specific subdirectories
    (``MODELO55``, ``Modelo67`` etc) and we should blindly traverse them
    rather than relying on their names.  This helper therefore performs a
    recursive glob and returns all ``*.xml`` paths.
    """

    if not base_dir.exists() or not base_dir.is_dir():
        return []

    # exclude any files already inside the archive folders
    excluded_names = {'processados', 'pendentes'}

    files = []
    for p in sorted(base_dir.rglob('*.xml')):
        # skip files under excluded directories (case-insensitive)
        parts = {part.lower() for part in p.parts}
        if parts & excluded_names:
            continue
        files.append(p)

    return files


def _detect_doc_type(xml_bytes: bytes) -> str | None:
    """Infer document type by inspecting every element's local name.

    The old implementation relied on :meth:`ElementTree.find` with explicit
    namespace prefixes, which raised ``ValueError: prefix 'nfse' not found in
    prefix map`` when parsing XML that did not declare the namespace.  In
    practice the job may receive files from arbitrary sources, some of which
    omit prefixes entirely, so we take a more robust approach: iterate through
    every element in the tree and check the *localname* portion of the tag
    (i.e. strip any namespace URI).  This removes any dependency on the
    document's namespace mapping and avoids accidental exceptions during
    detection.
    """

    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError:
        return None

    for elem in root.iter():
        # ``elem.tag`` could be '{namespace}localname' or simply 'localname'
        local = elem.tag.split('}')[-1]
        if local == 'infNFe':
            return 'NFe'
        if local in ('infCte', 'infCTe'):
            return 'CTe'
        # NFSe is very inconsistent; look for obvious markers
        if local in ('NFSe', 'NotaFiscal', 'InfNfse', 'InfRps'):
            return 'NFSe'

    return None


def _safe_move(src: Path, dest_dir: Path) -> Path:
    """Move `src` into `dest_dir`, creating `dest_dir` if needed.

    If a file with the same name exists in the destination, append a
    timestamp suffix to avoid overwriting. Returns the final destination
    path.
    """
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / src.name
    if dest.exists():
        ts = int(time.time())
        dest = dest_dir / f"{src.stem}_{ts}{src.suffix}"
    try:
        shutil.move(str(src), str(dest))
    except Exception:
        src.rename(dest)
    return dest


@shared_task
def scan_cargaxml_params() -> int:
    now = timezone.localtime()
    params = CargaXmlParam.objects.filter(ativo=True)
    enqueued = 0

    for param in params:
        if param.horario.hour != now.hour or param.horario.minute != now.minute:
            continue

        if param.ultima_execucao:
            last = timezone.localtime(param.ultima_execucao)
            if last.date() == now.date() and last.hour == now.hour and last.minute == now.minute:
                continue

        process_cargaxml_param.delay(param.id)
        enqueued += 1

    return enqueued


@shared_task
def process_cargaxml_param(param_id: int) -> Dict[str, int]:
    param = CargaXmlParam.objects.select_related('cliente', 'usuario_criacao').get(id=param_id)
    now = timezone.localtime()

    # build list of files to process; walk company directory recursively and
    # ignore non-XML entries.  We no longer constrain by subfolder names,
    # because customers may create arbitrary directories under the base
    # path.
    base_dir = Path(param.diretorio)
    # Se houver arquivos .zip na pasta, extrair tudo na mesma pasta e continuar
    _extract_zips_in_folder(base_dir)
    xml_files: List[Path] = _collect_xml_files(base_dir)

    job = CargaXmlJob.objects.create(
        cliente=param.cliente,
        parametro=param,
        status='RUNNING',
        total_arquivos=len(xml_files),
        started_at=now,
        usuario_execucao=param.usuario_criacao,
    )

    success = 0
    errors = 0
    log_lines: List[str] = []

    processor = Carga_xml()

    if not base_dir.exists() or not base_dir.is_dir():
        errors = 1
        log_lines.append(f'Diretorio nao encontrado: {base_dir}')

    for xml_path in xml_files:
        try:
            with xml_path.open('rb') as handle:
                xml_bytes = handle.read()

            # detect document type from the XML itself; this is the ultimate
            # source of truth.  If the file is mis‑placed the detection will
            # catch it and log an error.
            tipo = _detect_doc_type(xml_bytes)
            if not tipo:
                errors += 1
                log_lines.append(f'ERRO: {xml_path.name} - tipo de documento nao identificado')
                # move to pendentes/unknown
                try:
                    _safe_move(xml_path, base_dir / 'pendentes' / 'unknown')
                except Exception:
                    pass
                continue

            # optional: warn if the folder name doesn't match the inferred
            # type (helps users keep the directory tree tidy)
            folder_name = xml_path.parent.name.lower()
            expected_folder = None
            for _, (folder, tipo_doc) in MODEL_FOLDER_MAP.items():
                if tipo_doc == tipo:
                    expected_folder = folder.lower()
                    break
            if expected_folder and expected_folder != folder_name:
                log_lines.append(
                    f'AVISO: {xml_path.name} - documento {tipo} em pasta "{folder_name}"'
                )

            if tipo == 'NFe':
                try:
                    processor.set_nfe(xml_bytes, param.origem_dados, 'SYSTEM',
                                      param.cliente.cod_cliente if param.cliente else None)
                except EmpresaNaoCadastradaError as exc:
                    errors += 1
                    log_lines.append(f'PENDENTES (empresa nao cadastrada): {xml_path.name} - {exc}')
                    try:
                        _safe_move(xml_path, base_dir / 'pendentes' / 'sem_empresa')
                    except Exception:
                        pass
                    continue
            elif tipo == 'CTe':
                processor.set_cte(xml_bytes, param.origem_dados, 'SYSTEM',
                                  param.cliente.cod_cliente if param.cliente else None)
            elif tipo == 'NFSe':
                processor.set_nfse(xml_bytes, param.origem_dados, 'SYSTEM',
                                   param.cliente.cod_cliente if param.cliente else None)
            else:
                # should never happen because _detect_doc_type returns only
                # known values, but protect against future regressions
                raise ValueError(f'Tipo nao suportado: {tipo}')
            success += 1
            log_lines.append(f'OK: {xml_path.name}')
            # move processed file to processados/<tipo>
            try:
                _safe_move(xml_path, base_dir / 'processados' / tipo.lower())
            except Exception:
                # moving shouldn't break job; just warn
                log_lines.append(f'AVISO: nao foi possivel mover {xml_path.name} para processados')
        except Exception as exc:
            errors += 1
            log_lines.append(f'ERRO: {xml_path.name} - {exc}')
            # move problematic file to pendentes/<tipo_or_unknown>
            try:
                target = (base_dir / 'pendentes' / (tipo.lower() if tipo else 'unknown'))
                _safe_move(xml_path, target)
            except Exception:
                log_lines.append(f'AVISO: nao foi possivel mover {xml_path.name} para pendentes')

    status = 'SUCCESS' if errors == 0 else 'ERROR'
    finished_at = timezone.localtime()

    # Ordenar: erros e pendentes primeiro para não serem cortados pelo truncamento (5000 chars)
    def _prioridade_log(line):
        t = (line or '').strip()
        if t.startswith('ERRO:'):
            return 0
        if t.startswith('PENDENTES'):
            return 1
        if t.startswith('OK:'):
            return 2
        return 3
    log_lines = sorted(log_lines, key=_prioridade_log)

    with transaction.atomic():
        job.status = status
        job.total_sucesso = success
        job.total_erro = errors
        job.mensagem = '\n'.join(log_lines)[:5000]
        job.finished_at = finished_at
        job.save(update_fields=['status', 'total_sucesso', 'total_erro', 'mensagem', 'finished_at'])

        param.ultima_execucao = finished_at
        param.save(update_fields=['ultima_execucao'])

    return {
        'success': success,
        'errors': errors,
        'total': len(xml_files),
    }
