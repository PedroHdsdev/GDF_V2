import base64
import json
import socket
from dataclasses import dataclass
from typing import Any, Dict, List
from urllib import error as url_error
from urllib import parse as url_parse
from urllib import request as url_request

from django.conf import settings


class SapFiscalMaterialError(Exception):
    """Erro base para consumo do servico SAP de consulta fiscal de material."""


class SapFiscalMaterialNotConfiguredError(SapFiscalMaterialError):
    """Configuracao de integracao ainda nao informada."""


class SapFiscalMaterialTimeoutError(SapFiscalMaterialError):
    """Timeout ao consumir o servico SAP."""


class SapFiscalMaterialHttpError(SapFiscalMaterialError):
    """Erro HTTP no servico SAP."""

    def __init__(self, status_code: int, body: str = ""):
        self.status_code = int(status_code)
        self.body = body or ""
        super().__init__(f"HTTP {self.status_code}")


class SapFiscalMaterialInvalidResponseError(SapFiscalMaterialError):
    """Resposta invalida/inesperada do SAP."""


@dataclass
class SapFiscalMaterialResult:
    items: List[Dict[str, Any]]
    mensagem: str = ""


def _str_cfg(name: str, default: str = "") -> str:
    return str(getattr(settings, name, default) or "").strip()


def _float_cfg(name: str, default: float) -> float:
    try:
        return float(getattr(settings, name, default))
    except (TypeError, ValueError):
        return float(default)


def _header_auth() -> Dict[str, str]:
    mode = _str_cfg("SAP_CONSULTA_FISCAL_MATERIAL_AUTH_MODE", "none").lower()
    if mode in ("", "none"):
        return {}

    if mode == "basic":
        username = _str_cfg("SAP_CONSULTA_FISCAL_MATERIAL_BASIC_USER")
        password = _str_cfg("SAP_CONSULTA_FISCAL_MATERIAL_BASIC_PASS")
        if not username or not password:
            raise SapFiscalMaterialNotConfiguredError(
                "Autenticacao BASIC configurada sem usuario/senha."
            )
        token = base64.b64encode(f"{username}:{password}".encode("utf-8")).decode("ascii")
        return {"Authorization": f"Basic {token}"}

    if mode == "bearer":
        token = _str_cfg("SAP_CONSULTA_FISCAL_MATERIAL_BEARER_TOKEN")
        if not token:
            raise SapFiscalMaterialNotConfiguredError(
                "Autenticacao BEARER configurada sem token."
            )
        return {"Authorization": f"Bearer {token}"}

    if mode == "api_key":
        key_value = _str_cfg("SAP_CONSULTA_FISCAL_MATERIAL_API_KEY")
        key_header = _str_cfg("SAP_CONSULTA_FISCAL_MATERIAL_API_KEY_HEADER", "X-API-Key")
        if not key_value:
            raise SapFiscalMaterialNotConfiguredError(
                "Autenticacao por API Key configurada sem chave."
            )
        return {key_header: key_value}

    raise SapFiscalMaterialNotConfiguredError(
        f"Modo de autenticacao nao suportado: {mode!r}"
    )


def _pick_first(src: Dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in src and src.get(key) is not None:
            return src.get(key)
    return None


def _normalize_row(raw: Dict[str, Any]) -> Dict[str, Any]:
    row = raw if isinstance(raw, dict) else {}
    return {
        "chave_acesso": _pick_first(row, "chave_acesso", "chaveAcesso", "CHAVE_ACESSO", "ACCESS_KEY", "chave"),
        "cod_material": _pick_first(row, "cod_material", "codigo_material", "material", "MATNR", "codMaterial"),
        "desc_material": _pick_first(row, "desc_material", "descricao_material", "material_desc", "MAKTX", "descMaterial"),
        "cod_fornecedor": _pick_first(row, "cod_fornecedor", "codigo_fornecedor", "fornecedor", "LIFNR", "codFornecedor"),
        "aliquota_icms": _pick_first(row, "aliquota_icms", "icms", "ALIQ_ICMS", "aliqIcms"),
        "aliquota_st": _pick_first(row, "aliquota_st", "st", "ALIQ_ST", "aliqSt"),
        "aliquota_cofins": _pick_first(row, "aliquota_cofins", "cofins", "ALIQ_COFINS", "aliqCofins"),
        "aliquota_ipi": _pick_first(row, "aliquota_ipi", "ipi", "ALIQ_IPI", "aliqIpi"),
        "aliquota_pis": _pick_first(row, "aliquota_pis", "pis", "ALIQ_PIS", "aliqPis"),
        "fcp": _pick_first(row, "fcp", "fundo_combate_pobreza", "FUNDO_COMBATE_POBREZA", "aliqFcp"),
    }


def normalizar_item_para_tabela(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Converte um item vindo do SAP para o formato usado pela tabela da tela."""
    row = _normalize_row(raw or {})
    return {
        "material": row.get("cod_material") or "",
        "descricao_material": row.get("desc_material") or "",
        "fornecedor": row.get("cod_fornecedor") or "",
        "aliquota_icms": row.get("aliquota_icms"),
        "aliquota_st": row.get("aliquota_st"),
        "aliquota_cofins": row.get("aliquota_cofins"),
        "aliquota_ipi": row.get("aliquota_ipi"),
        "aliquota_pis": row.get("aliquota_pis"),
        "reducao_base": row.get("fcp"),
    }


def _extract_items(parsed: Any) -> List[Dict[str, Any]]:
    payload = parsed
    if isinstance(parsed, dict):
        payload = (
            parsed.get("items")
            or parsed.get("data")
            or parsed.get("results")
            or parsed.get("resultado")
            or parsed.get("registros")
            or parsed.get("value")
        )

    if payload is None:
        return []

    if not isinstance(payload, list):
        raise SapFiscalMaterialInvalidResponseError(
            "Resposta do Web Service nao possui lista de registros."
        )

    return [_normalize_row(row) for row in payload]


def consultar_fiscal_material(filtros: Dict[str, Any]) -> SapFiscalMaterialResult:
    """
    Consome o Web Service SAP (SICF) para consulta fiscal de material.
    Envia somente filtros preenchidos.
    """
    base_url = _str_cfg("SAP_CONSULTA_FISCAL_MATERIAL_URL")
    if not base_url:
        raise SapFiscalMaterialNotConfiguredError(
            "Integracao SAP da Consulta Fiscal Material ainda nao configurada."
        )

    method = _str_cfg("SAP_CONSULTA_FISCAL_MATERIAL_HTTP_METHOD", "POST").upper()
    timeout = _float_cfg("SAP_CONSULTA_FISCAL_MATERIAL_TIMEOUT", 25.0)

    body_data = {k: v for k, v in (filtros or {}).items() if v not in (None, "")}
    headers: Dict[str, str] = {
        "Accept": "application/json",
    }
    headers.update(_header_auth())

    request_url = base_url
    payload_bytes = None
    if method == "GET":
        qs = url_parse.urlencode(body_data)
        sep = "&" if "?" in base_url else "?"
        request_url = f"{base_url}{sep}{qs}" if qs else base_url
    else:
        payload_bytes = json.dumps(body_data, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = url_request.Request(
        url=request_url,
        data=payload_bytes,
        headers=headers,
        method=method,
    )

    try:
        with url_request.urlopen(req, timeout=timeout) as resp:
            status = getattr(resp, "status", resp.getcode())
            raw_body = resp.read().decode("utf-8", errors="replace")
    except url_error.HTTPError as exc:
        body = ""
        try:
            body = exc.read().decode("utf-8", errors="replace")
        except Exception:
            body = ""
        raise SapFiscalMaterialHttpError(status_code=exc.code, body=body) from exc
    except (url_error.URLError, ConnectionError, socket.gaierror) as exc:
        reason = getattr(exc, "reason", exc)
        if isinstance(reason, socket.timeout) or isinstance(exc, socket.timeout):
            raise SapFiscalMaterialTimeoutError("Timeout ao conectar no SAP.") from exc
        raise SapFiscalMaterialError(f"Erro de comunicacao com SAP: {exc}") from exc
    except socket.timeout as exc:
        raise SapFiscalMaterialTimeoutError("Timeout ao conectar no SAP.") from exc

    if int(status) < 200 or int(status) >= 300:
        raise SapFiscalMaterialHttpError(status_code=int(status), body=raw_body)

    try:
        parsed = json.loads(raw_body) if raw_body else {}
    except json.JSONDecodeError as exc:
        raise SapFiscalMaterialInvalidResponseError(
            "Resposta do Web Service nao esta em JSON valido."
        ) from exc

    items = _extract_items(parsed)
    mensagem = ""
    if isinstance(parsed, dict):
        mensagem = str(
            parsed.get("mensagem")
            or parsed.get("message")
            or parsed.get("detail")
            or ""
        ).strip()
    return SapFiscalMaterialResult(items=items, mensagem=mensagem)
