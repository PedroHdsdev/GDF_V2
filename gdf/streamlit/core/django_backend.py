"""Chamadas HTTP ao Django: RFC e integrações SAP rodam só no backend."""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any, Dict


def demonstrativos_contabeis_api_url() -> str:
    """
    URL absoluta da API de demonstrativos contábeis.

    Por padrão **não** inclui FORCE_SCRIPT_NAME (/gdf): chamadas diretas ao Gunicorn usam
    ``/api/sap/demonstrativos-contabeis/``. Com ``STREAMLIT_DJANGO_API_USE_FORCE_SCRIPT_NAME=True``
    monta ``{base}{FORCE_SCRIPT_NAME}/api/...`` para deploys em que o PATH interno mantém o prefixo.
    """
    from django.conf import settings

    base = getattr(settings, "STREAMLIT_DJANGO_API_BASE_URL", None) or "http://127.0.0.1:8500"
    base = str(base).strip().rstrip("/")
    if getattr(settings, "STREAMLIT_DJANGO_API_USE_FORCE_SCRIPT_NAME", False):
        prefix = (getattr(settings, "FORCE_SCRIPT_NAME", None) or "").strip().rstrip("/")
        if prefix:
            return f"{base}{prefix}/api/sap/demonstrativos-contabeis/"
    return f"{base}/api/sap/demonstrativos-contabeis/"


def post_json_bearer(
    url: str,
    bearer_token: str,
    payload: Dict[str, Any],
    timeout: int = 180,
) -> Dict[str, Any]:
    """POST JSON com Authorization Bearer (mesmo JWT do iframe do dashboard)."""
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {bearer_token}",
            "X-Forwarded-Proto": "https",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        try:
            err_body = e.read().decode("utf-8")
            data = json.loads(err_body) if err_body.strip() else {}
        except Exception:
            data = {"sucesso": False, "mensagem": e.reason or str(e)}
        if not isinstance(data, dict):
            return {"sucesso": False, "mensagem": str(data)}
        data.setdefault("sucesso", False)
        return data
    except urllib.error.URLError as e:
        reason = getattr(e, "reason", e)
        return {
            "sucesso": False,
            "mensagem": (
                f"Não foi possível contatar o Django em {url}. "
                f"O Gunicorn deste projeto usa por padrão a porta 8500 (veja GUNICORN_BIND em etc/gunicorn_config.py). "
                f"No .env defina STREAMLIT_DJANGO_API_BASE_URL=http://127.0.0.1:PORTA (a mesma do bind) ou o host interno "
                f"(Docker: nome do serviço). Confirme que o processo Django/Gunicorn está em execução. Detalhe: {reason}"
            ),
        }
