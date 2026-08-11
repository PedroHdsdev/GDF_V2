from dataclasses import dataclass
from typing import Any, Dict, List

from django.db.models import CharField, F, Q, Value
from django.db.models.functions import Coalesce, NullIf, Trim
from app.db_GDF.NFe.models import NFe_Produto


@dataclass
class ConsultaFiscalMaterialDbResult:
    items: List[Dict[str, Any]]
    total: int
    page: int
    total_pages: int
    mensagem: str = ""


_ORDER_MAP = {
    "material": "material",
    "descricao_material": "descricao_material",
    "fornecedor": "fornecedor",
    "aliquota_icms": "aliquota_icms",
    "aliquota_st": "aliquota_st",
    "aliquota_cofins": "aliquota_cofins",
    "aliquota_ipi": "aliquota_ipi",
    "aliquota_pis": "aliquota_pis",
    "reducao_base": "reducao_base",
}


def _normalizar_texto(valor: Any) -> str:
    return str(valor or "").strip()


def consultar_fiscal_material_db(
    cod_cliente: str,
    filtros: Dict[str, Any],
    page: int = 1,
    page_size: int = 30,
    order: str = "material",
    direction: str = "asc",
) -> ConsultaFiscalMaterialDbResult:
    order_field = _ORDER_MAP.get((order or "").strip(), "material")
    descending = str(direction or "").strip().lower() == "desc"
    page = max(1, int(page))
    page_size = max(1, int(page_size))

    filtros = filtros or {}
    data_inicio = _normalizar_texto(filtros.get("data_inicio"))
    data_fim = _normalizar_texto(filtros.get("data_fim"))
    chave_acesso = _normalizar_texto(filtros.get("chave_acesso"))
    cod_material = _normalizar_texto(filtros.get("cod_material"))
    filtro_fornecedor = _normalizar_texto(filtros.get("fornecedor") or filtros.get("cod_fornecedor"))

    qs = (
        NFe_Produto.objects
        .filter(
            nfe_serie__nfe__gdfcliente_id=cod_cliente,
            nfe_serie__emissao__date__gte=data_inicio,
            nfe_serie__emissao__date__lte=data_fim,
        )
        .annotate(
            material=Coalesce(
                NullIf(Trim(F("codigo_interno")), Value("")),
                Value(""),
                output_field=CharField(),
            ),
            descricao_material=Coalesce(
                NullIf(Trim(F("descricao")), Value("")),
                Value(""),
                output_field=CharField(),
            ),
            fornecedor=Coalesce(
                NullIf(Trim(F("nfe_serie__nfe__emitente__razao_social")), Value("")),
                NullIf(Trim(F("nfe_serie__nfe__emitente__cnpj")), Value("")),
                Value(""),
                output_field=CharField(),
            ),
            aliquota_icms=F("icms__aliquota"),
            aliquota_st=F("icms__aliquota_st"),
            aliquota_cofins=F("cofins__aliquota"),
            aliquota_ipi=F("ipi__aliquota"),
            aliquota_pis=F("pis__aliquota"),
            reducao_base=F("icms__percentual_reducao"),
        )
    )

    if chave_acesso:
        qs = qs.filter(nfe_serie__chave_acesso__icontains=chave_acesso)

    if cod_material:
        qs = qs.filter(codigo_interno__icontains=cod_material)

    if filtro_fornecedor:
        qs = qs.filter(
            Q(nfe_serie__nfe__emitente__razao_social__icontains=filtro_fornecedor)
            | Q(nfe_serie__nfe__emitente__cnpj__icontains=filtro_fornecedor)
        )

    order_expr = F(order_field)
    qs = qs.order_by(
        order_expr.desc(nulls_last=True) if descending else order_expr.asc(nulls_last=True)
    )

    total = qs.count()
    if total == 0:
        return ConsultaFiscalMaterialDbResult(items=[], total=0, page=1, total_pages=1)

    total_pages = max(1, (total + page_size - 1) // page_size)
    page = min(page, total_pages)
    offset = (page - 1) * page_size

    items = list(
        qs.values(
            #"material",
            "descricao_material",
            #"fornecedor",
            "aliquota_icms",
            "aliquota_st",
            "aliquota_cofins",
            "aliquota_ipi",
            "aliquota_pis",
            "reducao_base",
        )[offset: offset + page_size]
    )

    return ConsultaFiscalMaterialDbResult(items=items, total=total, page=page, total_pages=total_pages)