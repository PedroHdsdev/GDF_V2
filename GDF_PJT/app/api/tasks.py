"""
Tarefas Celery para Carga XML agendada.
- scan_cargaxml_params: dispara a cada minuto, enfileira process_cargaxml_param para
  parâmetros cujo horário coincide com o atual.
- process_cargaxml_param: processa XMLs do diretório do parâmetro (extrai ZIPs, detecta
  tipo NFe/CTe/NFSe, usa app.classes.CargaXml e move para processados/pendentes).
"""
from __future__ import annotations

import shutil
import time
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from typing import Dict, List, Tuple

from celery import shared_task
from django.db import transaction
from django.utils import timezone

from app.classes.CargaXml import CargaXml, EmpresaNaoCadastradaError
from app.db_GDF.Public.models import JobCargaXml, ParametroCargaXml


MODEL_FOLDER_MAP: Dict[str, Tuple[str, str]] = {
    "55": ("modelo55", "NFe"),
    "57": ("modelo57", "CTe"),
    "67": ("modelo67", "CTe"),
    "13": ("modelo13", "NFSe"),
    "SPC": ("modeloSPC", "NFe"),
    "SPF": ("modeloSPF", "NFe"),
}


def _extract_zips_in_folder(base_dir: Path) -> None:
    """Encontra todos os .zip na pasta (e subpastas), extrai o conteúdo na mesma
    pasta onde está cada zip. Não altera pastas 'processados' e 'pendentes'.
    """
    if not base_dir.exists() or not base_dir.is_dir():
        return
    excluded_names = {"processados", "pendentes"}
    zip_paths: List[Path] = []
    for p in base_dir.rglob("*.zip"):
        parts = {part.lower() for part in p.parts}
        if parts & excluded_names:
            continue
        if p.is_file():
            zip_paths.append(p)
    for zip_path in zip_paths:
        extract_dir = zip_path.parent
        extract_resolved = extract_dir.resolve()
        try:
            with zipfile.ZipFile(zip_path, "r") as zf:
                for member in zf.namelist():
                    if member.endswith("/"):
                        continue
                    dest = (extract_dir / member).resolve()
                    if not str(dest).startswith(str(extract_resolved)):
                        continue
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    with zf.open(member, "r") as src:
                        dest.write_bytes(src.read())
        except (zipfile.BadZipFile, OSError, ValueError):
            pass


def _collect_xml_files(base_dir: Path) -> List[Path]:
    """Retorna todos os .xml sob base_dir (recursivo), exceto em processados/pendentes."""
    if not base_dir.exists() or not base_dir.is_dir():
        return []
    excluded_names = {"processados", "pendentes"}
    files = []
    for p in sorted(base_dir.rglob("*.xml")):
        parts = {part.lower() for part in p.parts}
        if parts & excluded_names:
            continue
        files.append(p)
    return files


def _detect_doc_type(xml_bytes: bytes) -> str | None:
    """Infere tipo (NFe, CTe, NFSe) pelo nome local dos elementos."""
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError:
        return None
    for elem in root.iter():
        local = elem.tag.split("}")[-1]
        if local == "infNFe":
            return "NFe"
        if local in ("infCte", "infCTe"):
            return "CTe"
        if local in ("NFSe", "NotaFiscal", "InfNfse", "InfRps"):
            return "NFSe"
    return None


def _safe_move(src: Path, dest_dir: Path) -> Path:
    """Move src para dest_dir; se já existir arquivo com mesmo nome, usa sufixo com timestamp."""
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
    """Enfileira process_cargaxml_param para parâmetros ativos cujo horário é o atual (minuto a minuto)."""
    now = timezone.localtime()
    params = ParametroCargaXml.objects.filter(ativo=True)
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
    """Processa XMLs do diretório do parâmetro: extrai ZIPs, detecta tipo, grava via CargaXml e move arquivos."""
    param = ParametroCargaXml.objects.select_related("gdfcliente", "usuario_criacao").get(id=param_id)
    now = timezone.localtime()
    base_dir = Path(param.diretorio)
    _extract_zips_in_folder(base_dir)
    xml_files: List[Path] = _collect_xml_files(base_dir)

    job = JobCargaXml.objects.create(
        gdfcliente=param.gdfcliente,
        parametro=param,
        status="RUNNING",
        total_arquivos=len(xml_files),
        started_at=now,
        usuario_execucao=param.usuario_criacao,
    )

    success = 0
    errors = 0
    log_lines: List[str] = []
    processor = CargaXml()
    tipo: str | None = None

    if not base_dir.exists() or not base_dir.is_dir():
        errors = 1
        log_lines.append(f"Diretorio nao encontrado: {base_dir}")

    for xml_path in xml_files:
        processor._avisos = []
        try:
            with xml_path.open("rb") as handle:
                xml_bytes = handle.read()
            tipo = _detect_doc_type(xml_bytes)
            if not tipo:
                errors += 1
                log_lines.append(f"ERRO: {xml_path.name} - tipo de documento nao identificado")
                try:
                    _safe_move(xml_path, base_dir / "pendentes" / "unknown")
                except Exception:
                    pass
                continue
            folder_name = xml_path.parent.name.lower()
            expected_folder = None
            for _, (folder, tipo_doc) in MODEL_FOLDER_MAP.items():
                if tipo_doc == tipo:
                    expected_folder = folder.lower()
                    break
            if expected_folder and expected_folder != folder_name:
                log_lines.append(f'AVISO: {xml_path.name} - documento {tipo} em pasta "{folder_name}"')
            if tipo == "NFe":
                try:
                    processor.set_nfe(
                        xml_bytes,
                        param.origem_dados,
                        "SYSTEM",
                        param.gdfcliente.cod_cliente if param.gdfcliente else None,
                        nome_arquivo=xml_path.name,
                    )
                except EmpresaNaoCadastradaError as exc:
                    errors += 1
                    log_lines.append(f"PENDENTES (empresa nao cadastrada): {xml_path.name} - {exc}")
                    try:
                        _safe_move(xml_path, base_dir / "pendentes" / "sem_empresa")
                    except Exception:
                        pass
                    continue
            elif tipo == "CTe":
                processor.set_cte(
                    xml_bytes,
                    param.origem_dados,
                    "SYSTEM",
                    param.gdfcliente.cod_cliente if param.gdfcliente else None,
                )
            elif tipo == "NFSe":
                processor.set_nfse(
                    xml_bytes,
                    param.origem_dados,
                    "SYSTEM",
                    param.gdfcliente.cod_cliente if param.gdfcliente else None,
                )
            else:
                raise ValueError(f"Tipo nao suportado: {tipo}")
            for a in getattr(processor, "_avisos", []):
                log_lines.append(f"AVISO: {a.get('file', '')} - {a.get('message', '')}")
            success += 1
            log_lines.append(f"OK: {xml_path.name}")
            try:
                _safe_move(xml_path, base_dir / "processados" / tipo.lower())
            except Exception:
                log_lines.append(f"AVISO: nao foi possivel mover {xml_path.name} para processados")
        except Exception as exc:
            errors += 1
            log_lines.append(f"ERRO: {xml_path.name} - {exc}")
            try:
                target = base_dir / "pendentes" / (tipo.lower() if tipo else "unknown")
                _safe_move(xml_path, target)
            except Exception:
                log_lines.append(f"AVISO: nao foi possivel mover {xml_path.name} para pendentes")

    status = "SUCCESS" if errors == 0 else "ERROR"
    finished_at = timezone.localtime()

    def _prioridade_log(line: str) -> int:
        t = (line or "").strip()
        if t.startswith("ERRO:"):
            return 0
        if t.startswith("PENDENTES"):
            return 1
        if t.startswith("OK:"):
            return 2
        return 3

    log_lines.sort(key=_prioridade_log)

    with transaction.atomic():
        job.status = status
        job.total_sucesso = success
        job.total_erro = errors
        job.mensagem = "\n".join(log_lines)[:5000]
        job.finished_at = finished_at
        job.save(update_fields=["status", "total_sucesso", "total_erro", "mensagem", "finished_at"])
        param.ultima_execucao = finished_at
        param.save(update_fields=["ultima_execucao"])

    return {"success": success, "errors": errors, "total": len(xml_files)}
