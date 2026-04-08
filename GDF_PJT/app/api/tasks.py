"""
Tarefas Celery — Carga XML/SPED (manual e automática).

- scan_carga_automatica: tarefa única agendada pelo beat; avalia XML + SPED.
- scan_cargaxml_params / scan_cargasped_params: mantidas para compatibilidade (chamam o mesmo núcleo).
- process_cargaxml_param / process_cargasped_param: processam o diretório do parâmetro.

Regras de agendamento: app.api.carga_automatica.parametro_deve_executar_carga_automatica
"""
from __future__ import annotations

import logging
import shutil
import time
import xml.etree.ElementTree as ET
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

from celery import shared_task
from django.db import transaction
from django.utils import timezone

from app.api.carga_automatica import parametro_deve_executar_carga_automatica
from app.classes.CargaXml import CargaXml, EmpresaNaoCadastradaError
from app.db_GDF.Public.models import JobCargaXml, ParametroCargaXml

logger = logging.getLogger("gdf")


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


def _enqueue_or_run_cargaxml(param_id: int) -> None:
    """Tenta Celery; se broker/worker indisponível, executa na hora (evita carga automática silenciosa)."""
    try:
        process_cargaxml_param.delay(param_id)
    except Exception as exc:
        logger.warning(
            "Carga XML automática: fila Celery indisponível (param_id=%s). Executando em processo: %s",
            param_id,
            exc,
        )
        process_cargaxml_param.apply(args=(param_id,))


def _dispatch_cargaxml_params_due() -> int:
    enqueued = 0
    qs = ParametroCargaXml.objects.filter(ativo=True).only("id", "horario", "ultima_execucao")
    for row in qs.iterator(chunk_size=50):
        if not parametro_deve_executar_carga_automatica(row.horario, row.ultima_execucao):
            continue
        _enqueue_or_run_cargaxml(row.id)
        enqueued += 1
    return enqueued


@shared_task
def scan_cargaxml_params() -> int:
    """Enfileira process_cargaxml_param para parâmetros ativos no horário (ver carga_automatica)."""
    n = _dispatch_cargaxml_params_due()
    if n:
        logger.info("scan_cargaxml_params: enfileirados=%s", n)
    return n


@shared_task
def process_cargaxml_param(param_id: int) -> Dict[str, int]:
    """Processa XMLs do diretório do parâmetro: extrai ZIPs, detecta tipo, grava via CargaXml e move arquivos."""
    today = timezone.localdate()
    with transaction.atomic():
        param = (
            ParametroCargaXml.objects.select_for_update()
            .select_related("gdfcliente", "usuario_criacao")
            .get(id=param_id)
        )
        if not parametro_deve_executar_carga_automatica(param.horario, param.ultima_execucao):
            logger.info("process_cargaxml_param ignorado param_id=%s (agenda ou ja executou hoje)", param_id)
            return {"skipped": 1}
        if JobCargaXml.objects.filter(parametro=param, started_at__date=today).exists():
            logger.info("process_cargaxml_param ignorado param_id=%s (job automatico ja existe hoje)", param_id)
            return {"skipped": 1}
        now = timezone.localtime()
        job = JobCargaXml.objects.create(
            gdfcliente=param.gdfcliente,
            parametro=param,
            status="RUNNING",
            total_arquivos=0,
            started_at=now,
            usuario_execucao=param.usuario_criacao,
        )
    base_dir = Path(param.diretorio)

    success = 0
    errors = 0
    log_lines: List[str] = []
    xml_files: List[Path] = []
    tipo: str | None = None

    def _prioridade_log(line: str) -> int:
        t = (line or "").strip()
        if t.startswith("ERRO:"):
            return 0
        if t.startswith("PENDENTES"):
            return 1
        if t.startswith("OK:"):
            return 2
        return 3

    try:
        _extract_zips_in_folder(base_dir)
        xml_files = _collect_xml_files(base_dir)
        job.total_arquivos = len(xml_files)
        job.save(update_fields=["total_arquivos"])

        processor = CargaXml()

        if not base_dir.exists() or not base_dir.is_dir():
            errors = 1
            log_lines.append(f"ERRO: Diretorio invalido ou inexistente: {base_dir}")
        elif len(xml_files) == 0:
            errors = 1
            log_lines.append(
                "ERRO: Nenhum arquivo XML no diretorio configurado (pastas processados/pendentes ignoradas)."
            )
        else:
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
    except Exception as exc:
        logger.exception("process_cargaxml_param param_id=%s", param_id)
        success = 0
        errors = 1
        log_lines = [f"ERRO: Falha na execucao da carga automatica XML: {exc}"]
        status = "ERROR"

    finished_at = timezone.localtime()
    log_lines.sort(key=_prioridade_log)
    if status == "ERROR" and not log_lines:
        log_lines.append("ERRO: Carga automatica finalizada com erro (sem detalhe adicional).")

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


def _enqueue_or_run_cargasped(param_id: int) -> None:
    try:
        process_cargasped_param.delay(param_id)
    except Exception as exc:
        logger.warning(
            "Carga SPED automática: fila Celery indisponível (param_id=%s). Executando em processo: %s",
            param_id,
            exc,
        )
        process_cargasped_param.apply(args=(param_id,))


def _dispatch_cargasped_params_due() -> int:
    from app.db_GDF.Public.models import ParametroCargaSped

    enqueued = 0
    qs = ParametroCargaSped.objects.filter(ativo=True).only("id", "horario", "ultima_execucao")
    for row in qs.iterator(chunk_size=50):
        if not parametro_deve_executar_carga_automatica(row.horario, row.ultima_execucao):
            continue
        _enqueue_or_run_cargasped(row.id)
        enqueued += 1
    return enqueued


@shared_task
def scan_cargasped_params() -> int:
    """Dispara process_cargasped_param quando o horário do dia já passou (ver carga_automatica)."""
    n = _dispatch_cargasped_params_due()
    if n:
        logger.info("scan_cargasped_params: enfileirados=%s", n)
    return n


@shared_task
def scan_carga_automatica() -> Dict[str, int]:
    """
    Uma única batida periódica: XML + SPED.
    Configure apenas esta tarefa no Celery Beat em produção.
    """
    nx = _dispatch_cargaxml_params_due()
    ns = _dispatch_cargasped_params_due()
    if nx or ns:
        logger.info("scan_carga_automatica: xml=%s sped=%s", nx, ns)
    return {"xml": nx, "sped": ns}


@shared_task
def process_cargasped_param(param_id: int) -> Dict[str, int]:
    """Processa .txt do diretório do parâmetro SPED (pasta raiz do param.diretorio)."""
    from app.classes.CargaSped import CargaSped
    from app.db_GDF.Public.models import JobCargaSped, ParametroCargaSped

    today = timezone.localdate()
    with transaction.atomic():
        param = (
            ParametroCargaSped.objects.select_for_update()
            .select_related("gdfcliente", "usuario_criacao", "empresa")
            .get(id=param_id)
        )
        if not parametro_deve_executar_carga_automatica(param.horario, param.ultima_execucao):
            logger.info("process_cargasped_param ignorado param_id=%s (agenda ou ja executou hoje)", param_id)
            return {"skipped": 1}
        if JobCargaSped.objects.filter(parametro=param, started_at__date=today).exists():
            logger.info("process_cargasped_param ignorado param_id=%s (job automatico ja existe hoje)", param_id)
            return {"skipped": 1}
        now = timezone.localtime()
        job = JobCargaSped.objects.create(
            gdfcliente=param.gdfcliente,
            parametro=param,
            status="RUNNING",
            total_arquivos=0,
            started_at=now,
            usuario_execucao=param.usuario_criacao,
        )
    base_dir = Path(param.diretorio)
    cod_cliente = param.gdfcliente.cod_cliente if param.gdfcliente else ""

    log_lines: List[str] = []
    n_ok = 0
    n_err = 0
    txt_count = 0
    status = "ERROR"

    def _prioridade_sped(line: str) -> int:
        t = (line or "").strip()
        if t.startswith("ERRO:"):
            return 0
        if t.startswith("AVISO:"):
            return 1
        if t.startswith("OK:"):
            return 2
        return 3

    try:
        if base_dir.is_dir():
            txt_count = sum(1 for p in base_dir.glob("*.txt") if p.is_file())
        job.total_arquivos = txt_count
        job.save(update_fields=["total_arquivos"])

        if not base_dir.exists() or not base_dir.is_dir():
            n_err = 1
            log_lines.append(f"ERRO: Diretorio invalido ou inexistente: {base_dir}")
        elif txt_count == 0:
            n_err = 1
            log_lines.append("ERRO: Nenhum arquivo .txt na pasta do parametro (carga automatica).")
        else:
            cl = CargaSped()
            try:
                result = cl.processar_pasta_temp(str(base_dir), cod_cliente, empresa=param.empresa)
            except Exception as exc:
                logger.exception("process_cargasped_param processar_pasta_temp param_id=%s", param_id)
                n_err = 1
                log_lines.append(f"ERRO: Falha ao processar pasta SPED: {exc}")
            else:
                success_list = result.get("success") or []
                err_list = result.get("errors") or []
                for name in success_list:
                    log_lines.append(f"OK: {name}")
                for err in err_list:
                    fn = err.get("file", "") if isinstance(err, dict) else ""
                    msg = err.get("error", "") if isinstance(err, dict) else str(err)
                    log_lines.append(f"ERRO: {fn} - {msg}")
                n_ok = len(success_list)
                n_err = len(err_list)
                status = "SUCCESS" if n_err == 0 else "ERROR"

        if not base_dir.exists() or not base_dir.is_dir() or txt_count == 0:
            status = "ERROR"
    except Exception as exc:
        logger.exception("process_cargasped_param param_id=%s", param_id)
        n_ok = 0
        n_err = 1
        log_lines = [f"ERRO: Falha na execucao da carga automatica SPED: {exc}"]
        status = "ERROR"

    finished_at = timezone.localtime()
    log_lines.sort(key=_prioridade_sped)
    if status == "ERROR" and not log_lines:
        log_lines.append("ERRO: Carga automatica SPED finalizada com erro (sem detalhe adicional).")

    with transaction.atomic():
        job.status = status
        job.total_sucesso = n_ok
        job.total_erro = n_err
        job.mensagem = "\n".join(log_lines)[:5000]
        job.finished_at = finished_at
        job.save(update_fields=["status", "total_sucesso", "total_erro", "mensagem", "finished_at"])
        param.ultima_execucao = finished_at
        param.save(update_fields=["ultima_execucao"])

    return {"success": n_ok, "errors": n_err, "total": txt_count}


@shared_task
def processar_job_xml_manual(
    job_id: int,
    temp_dir: str,
    type_xml: str,
    origem_dados: str,
    user_id: int,
    cod_cliente: str,
    empresa_id: str | None = None,
) -> None:
    """
    Processa em worker Celery a carga manual de XML (job criado pela API).
    Evita que o job fique eternamente 'em andamento' quando o processo web é reciclado.
    """
    from app.api.jobs import processar_job_xml_background
    empresa_id = (empresa_id or "").strip() or None
    cod_cliente = (cod_cliente or "").strip() or None
    processar_job_xml_background(
        job_id, temp_dir, type_xml, origem_dados, user_id, cod_cliente, empresa_id
    )


