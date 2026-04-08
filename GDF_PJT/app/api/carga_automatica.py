"""
Regras da carga automática (XML e SPED).

Objetivo: disparo confiável sem depender de “coincidir” com um intervalo curto do Celery.
- Depois do horário configurado no dia corrente (fuso TIME_ZONE).
- No máximo uma execução por parâmetro por dia civil (via ultima_execucao ou job já criado).
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from django.utils import timezone


def parametro_deve_executar_carga_automatica(
    horario,
    ultima_execucao: Optional[datetime],
) -> bool:
    """
    True se já passou o horário agendado hoje e este parâmetro ainda não “rodou” hoje
    (ultima_execucao em data local < hoje ou nula).

    Diferente de janela fixa de minutos: se o worker/beat atrasar horas, ainda dispara
    no mesmo dia (catch-up), desde que não tenha havido execução registrada hoje.
    """
    if horario is None:
        return False
    now = timezone.localtime()
    if now.time() < horario:
        return False
    if ultima_execucao is not None:
        ult_dia = timezone.localtime(ultima_execucao).date()
        if ult_dia >= now.date():
            return False
    return True


# Alias legado (run_carga_scheduler, testes)
deve_disparar_carga_automatica_agora = parametro_deve_executar_carga_automatica
