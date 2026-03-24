"""
Recebe dados de Relatório de Custo enviados pelo SAP via POST e persiste em sap.relatorio_custo.

Formato esperado do JSON (POST):
  {
    "cod_empresa": "1000",           // obrigatório (código empresa GDF = bukrs SAP)
    "cod_filial": "001",             // opcional
    "registros": [
      { "DOCNUM": "...", "MJAHR": "...", "MBLNR": "...", "PSTDAT": "2025-01-15", ... },
      ...
    ]
  }

Ou formato alternativo com chaves em minúsculo:
  { "cod_empresa": "1000", "registros": [ { "docnum": "...", "pstdat": "2025-01-15", ... } ] }

Cada registro usa update_or_create por (empresa, docnum, mjahr, mblnr).
"""
from decimal import Decimal, InvalidOperation
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from app.db_GDF.Public.models import Empresa, Filial
from app.db_GDF.Sap.models import RelatorioCusto


MAPEAMENTO_SAP = {
    'DOCNUM': 'docnum', 'MJAHR': 'mjahr', 'MBLNR': 'mblnr', 'MATNR': 'matnr', 'NFENUM': 'nfenum',
    'SERIES': 'series', 'DOCSTA': 'docsta', 'KUNNR': 'kunnr', 'NAME1': 'name1', 'ORT01': 'ort01',
    'CHAVE_ACESSO': 'chave_acesso', 'ITMNUM': 'itmnum', 'PSTDAT': 'pstdat', 'WERKS': 'werks',
    'NAME': 'name', 'STCD1': 'stcd1', 'UF_ORIGEM': 'uf_origem', 'UF_DESTINO': 'uf_destino',
    'CANCEL': 'cancel', 'MAKTX': 'maktx', 'MTART': 'mtart', 'MATKL': 'matkl', 'WGBEZ': 'wgbez',
    'CFOP': 'cfop', 'QTD_PROD': 'qtd_prod', 'UNID_MEDIDA': 'unid_medida', 'MEINS': 'meins',
    'UMREZ': 'umrez', 'MENGE_UMB': 'menge_umb', 'PRC_UNITARIO': 'prc_unitario',
    'PRC_UNIT_CST_LIQ': 'prc_unit_cst_liq', 'PRC_UNIT_CST_ADM': 'prc_unit_cst_adm',
    'BC_ICMS': 'bc_icms', 'PCT_ICMS': 'pct_icms', 'VLR_ICMS': 'vlr_icms',
    'BC_ICMS_ST': 'bc_icms_st', 'ALQ_ST': 'alq_st', 'VLR_ST': 'vlr_st',
    'BC_IPI': 'bc_ipi', 'PCT_IPI': 'pct_ipi', 'VLR_IPI': 'vlr_ipi',
    'BC_PIS': 'bc_pis', 'PCT_PIS': 'pct_pis', 'VLR_PIS': 'vlr_pis',
    'BC_COF': 'bc_cof', 'PCT_COF': 'pct_cof', 'VLR_COF': 'vlr_cof',
    'TP_DOC': 'tp_doc', 'TOTAL_IMPOSTOS': 'total_impostos', 'VLR_DESCONTO': 'vlr_desconto',
    'VLR_FRETE': 'vlr_frete', 'VLR_LIQUIDO': 'vlr_liquido', 'VLR_TOT_DOC': 'vlr_tot_doc',
    'CMV': 'cmv', 'LUCRO_0': 'lucro_0', 'MARGEM_0': 'margem_0', 'MARGEM_CONTRIB': 'margem_contrib',
    'CMV_GERENCIAL': 'cmv_gerencial', 'LUCRO_0_GERENCIAL': 'lucro_0_gerencial',
    'MARGEM_REAL': 'margem_real', 'LUCRO_REAL': 'lucro_real', 'MARGEM_CONTRIB_GER': 'margem_contrib_ger',
    'CMV_MEDIA': 'cmv_media', 'PER_TAXA_ADM': 'per_taxa_adm', 'VLR_TAXA_ADM': 'vlr_taxa_adm',
    'PER_TAXA_FRT': 'per_taxa_frt', 'VLR_TAXA_FRT': 'vlr_taxa_frt', 'CMV_UE': 'cmv_ue',
}

CAMPOS_DECIMAL = frozenset((
    'qtd_prod', 'umrez', 'menge_umb', 'prc_unitario', 'prc_unit_cst_liq', 'prc_unit_cst_adm',
    'bc_icms', 'pct_icms', 'vlr_icms', 'bc_icms_st', 'alq_st', 'vlr_st',
    'bc_ipi', 'pct_ipi', 'vlr_ipi', 'bc_pis', 'pct_pis', 'vlr_pis', 'bc_cof', 'pct_cof', 'vlr_cof',
    'total_impostos', 'vlr_desconto', 'vlr_frete', 'vlr_liquido', 'vlr_tot_doc',
    'cmv', 'lucro_0', 'margem_0', 'margem_contrib', 'cmv_gerencial', 'lucro_0_gerencial',
    'margem_real', 'lucro_real', 'margem_contrib_ger', 'cmv_media',
    'per_taxa_adm', 'vlr_taxa_adm', 'per_taxa_frt', 'vlr_taxa_frt', 'cmv_ue',
))


def _to_decimal(val: Any) -> Optional[Decimal]:
    if val is None or val == '':
        return None
    if isinstance(val, Decimal):
        return val
    try:
        return Decimal(str(val).replace(',', '.'))
    except (InvalidOperation, TypeError):
        return None


def _to_date(val: Any):
    """Retorna date ou None."""
    if val is None or val == '':
        return None
    if hasattr(val, 'date') and callable(val.date):
        return val.date()
    if hasattr(val, 'year') and hasattr(val, 'month') and hasattr(val, 'day'):
        return val
    if isinstance(val, str):
        for fmt in ('%Y-%m-%d', '%d.%m.%Y', '%d/%m/%Y'):
            try:
                return datetime.strptime(val[:10], fmt).date()
            except (ValueError, TypeError):
                continue
    return None


def _row_to_kwargs(row: Dict[str, Any], empresa, filial) -> Tuple[Optional[str], Optional[str], Optional[str], Dict]:
    """Converte uma linha do payload para kwargs do RelatorioCusto. Retorna (docnum, mjahr, mblnr, defaults)."""
    if not isinstance(row, dict):
        row = dict(row) if hasattr(row, 'keys') else {}
    row_upper = {str(k).strip().upper(): v for k, v in row.items()}
    kwargs = {'empresa': empresa, 'filial': filial}
    for sap_key, model_field in MAPEAMENTO_SAP.items():
        val = row_upper.get(sap_key) or row_upper.get(model_field.upper())
        if val is None:
            continue
        if model_field == 'pstdat':
            kwargs[model_field] = _to_date(val)
        elif model_field in CAMPOS_DECIMAL:
            kwargs[model_field] = _to_decimal(val)
        else:
            kwargs[model_field] = str(val).strip()

    docnum = (kwargs.get('docnum') or '').strip()
    mjahr = (kwargs.get('mjahr') or '').strip() or None
    mblnr = (kwargs.get('mblnr') or '').strip() or None
    if not docnum:
        return None, None, None, {}

    kwargs.setdefault('docsta', ' ')
    key_fields = ('empresa', 'docnum', 'mjahr', 'mblnr')
    defaults = {}
    for k, v in kwargs.items():
        if k in key_fields or v is None:
            continue
        try:
            f = RelatorioCusto._meta.get_field(k)
            if hasattr(f, 'max_length') and f.max_length and isinstance(v, str) and len(v) > f.max_length:
                v = v[: f.max_length]
        except Exception:
            pass
        defaults[k] = v
    return docnum, mjahr, mblnr, defaults


def persistir_relatorio_custo(
    cod_empresa: str,
    registros: List[Dict[str, Any]],
    cod_filial: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Persiste registros de relatório de custo em sap.relatorio_custo.

    Args:
        cod_empresa: Código da empresa (GDF = bukrs SAP).
        registros: Lista de dicts com os campos (chaves em maiúsculo ou minúsculo).
        cod_filial: Opcional. Código da filial.

    Returns:
        dict: {'sucesso': bool, 'mensagem': str, 'total_recebidos': int, 'total_gravados': int, 'erros': [str]}
    """
    cod_empresa = (cod_empresa or '').strip()
    if not cod_empresa:
        return {
            'sucesso': False,
            'mensagem': 'cod_empresa é obrigatório.',
            'total_recebidos': 0,
            'total_gravados': 0,
            'erros': [],
        }

    empresa = Empresa.objects.filter(cod_empresa=cod_empresa).first()
    if not empresa:
        return {
            'sucesso': False,
            'mensagem': f'Empresa "{cod_empresa}" não encontrada no cadastro.',
            'total_recebidos': len(registros),
            'total_gravados': 0,
            'erros': [],
        }

    filial = None
    if cod_filial:
        filial = Filial.objects.filter(empresa=empresa, cod_filial=str(cod_filial).strip()).first()

    gravados = 0
    erros = []
    for i, row in enumerate(registros):
        docnum, mjahr, mblnr, defaults = _row_to_kwargs(row, empresa, filial)
        if not docnum:
            erros.append(f"Registro {i + 1}: docnum vazio ou inválido, ignorado.")
            continue
        try:
            RelatorioCusto.objects.update_or_create(
                empresa=empresa,
                docnum=docnum,
                mjahr=mjahr,
                mblnr=mblnr,
                defaults=defaults,
            )
            gravados += 1
        except Exception as e:
            erros.append(f"Registro {i + 1} (docnum={docnum}): {e}")

    return {
        'sucesso': True,
        'mensagem': f'{gravados} registro(s) gravado(s) em sap.relatorio_custo.',
        'total_recebidos': len(registros),
        'total_gravados': gravados,
        'erros': erros,
    }
