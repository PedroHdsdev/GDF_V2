from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, List, Tuple

from celery import shared_task
from django.db import transaction
from django.utils import timezone

from app.classes.CargaXml import Carga_xml
from app.db_GDF.Public.models import CargaXmlJob, CargaXmlParam


MODEL_FOLDER_MAP: Dict[str, Tuple[str, str]] = {
    '55': ('modelo55', 'NFe'),
    '57': ('modelo57', 'CTe'),
    '67': ('modelo67', 'CTe'),
    '13': ('modelo13', 'NFSe'),
    'SPC': ('modeloSPC', 'NFe'),
    'SPF': ('modeloSPF', 'NFe'),
}


def _parse_modelos(modelos: str | None) -> List[str]:
    if not modelos:
        return []
    return [item.strip().upper() for item in modelos.split(',') if item.strip()]


def _collect_xml_files(base_dir: Path, folders: Iterable[str]) -> List[Path]:
    files: List[Path] = []
    for folder in folders:
        folder_path = base_dir / folder
        if not folder_path.exists() or not folder_path.is_dir():
            continue
        files.extend(sorted(folder_path.glob('*.xml')))
    return files


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
    modelos = _parse_modelos(param.modelos)

    if modelos:
        folders = [MODEL_FOLDER_MAP[m][0] for m in modelos if m in MODEL_FOLDER_MAP]
    else:
        folders = [value[0] for value in MODEL_FOLDER_MAP.values()]

    base_dir = Path(param.diretorio)
    xml_files = []
    if base_dir.exists() and base_dir.is_dir():
        xml_files = _collect_xml_files(base_dir, folders)

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
    error_messages: List[str] = []

    processor = Carga_xml()

    if not base_dir.exists() or not base_dir.is_dir():
        errors = 1
        error_messages.append(f'Diretorio nao encontrado: {base_dir}')

    for xml_path in xml_files:
        try:
            folder_name = xml_path.parent.name
            tipo = None
            for model_key, (folder, tipo_doc) in MODEL_FOLDER_MAP.items():
                if folder == folder_name:
                    tipo = tipo_doc
                    break

            if not tipo:
                errors += 1
                error_messages.append(f'Pasta desconhecida: {folder_name}')
                continue

            with xml_path.open('rb') as handle:
                xml_bytes = handle.read()

            if tipo == 'NFe':
                processor.set_nfe(xml_bytes, param.origem_dados, 'SYSTEM')
            elif tipo == 'CTe':
                processor.set_cte(xml_bytes, param.origem_dados, 'SYSTEM')
            elif tipo == 'NFSe':
                processor.set_nfse(xml_bytes, param.origem_dados, 'SYSTEM')
            else:
                raise ValueError(f'Tipo nao suportado: {tipo}')

            success += 1
        except Exception as exc:
            errors += 1
            error_messages.append(f'{xml_path.name}: {exc}')

    status = 'SUCCESS' if errors == 0 else 'ERROR'
    finished_at = timezone.localtime()

    with transaction.atomic():
        job.status = status
        job.total_sucesso = success
        job.total_erro = errors
        job.mensagem = '\n'.join(error_messages)[:5000]
        job.finished_at = finished_at
        job.save(update_fields=['status', 'total_sucesso', 'total_erro', 'mensagem', 'finished_at'])

        param.ultima_execucao = finished_at
        param.save(update_fields=['ultima_execucao'])

    return {
        'success': success,
        'errors': errors,
        'total': len(xml_files),
    }
