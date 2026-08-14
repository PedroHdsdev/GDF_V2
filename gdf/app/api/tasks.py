"""
Tarefas Celery — Carga XML manual em worker (fora do processo web).
"""
from __future__ import annotations

from celery import shared_task


@shared_task
def processar_job_xml_manual(
    job_id: int,
    temp_dir: str,
    type_xml: str,
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
    processar_job_xml_background(job_id, temp_dir, type_xml, user_id, cod_cliente, empresa_id)
