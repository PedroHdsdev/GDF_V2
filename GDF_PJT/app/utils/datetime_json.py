"""Serialização de datetime para JSON no fuso de settings.TIME_ZONE (America/Sao_Paulo)."""
from __future__ import annotations

from datetime import date, datetime
from typing import Any, Optional, Union

from django.utils import timezone


def isoformat_brasilia(value: Union[datetime, date, Any, None]) -> Optional[str]:
    """
    Retorna ISO 8601 em horário local do Django (TIME_ZONE), não UTC bruto.
    Campos somente data permanecem como date.isoformat().
    """
    if value is None:
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value.isoformat()
    if not isinstance(value, datetime):
        return None
    if timezone.is_naive(value):
        value = timezone.make_aware(value, timezone.get_current_timezone())
    return timezone.localtime(value).isoformat()
