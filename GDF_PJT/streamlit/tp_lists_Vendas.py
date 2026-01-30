
colunas_amigaveis = {
    'bukrs_id': 'Empresa',
    'docnum': 'Nº Documento',
    'mjahr': 'Ano do Documento',
    'mblnr': 'Nº Documento de Material',
    'matnr': 'Nº do Material',
    'nfenum': 'Número de Documento (9 posições)',
    'series': 'Série',
    'docsta': 'Status do Documento',
    'kunnr': 'Nº Cliente',
    'name1': 'Cliente',
    'ort01': 'Cidade',
    'chave_acesso': 'Chave de Acesso',
    'itmnum': 'Nº Item do Documento',
    'pstdat': 'Data de Postagem',
    'werks': 'Local de Negócios',
    'name': 'Nome',
    'stcd1': 'CNPJ',
    'uf_origem': 'UF de Origem',
    'uf_destino': 'UF de Destino',
    'cancel': 'Status de Cancelamento',
    'maktx': 'Texto Breve do Material',
    'mtart': 'Tipo de Material',
    'matkl': 'Grupo de Mercadorias',
    'wgbez': 'Denominação do Grupo de Mercadorias',
    'cfop': 'CFOP',
    'qtd_prod': 'Quantidade de Produto',
    'unid_medida': 'Unidade de Medida de Venda',
    'meins': 'Unidade de Medida Básica',
    'umrez': 'Contador Conversão UM',
    'menge_umb': 'Qtd Convertida p/ UM Básica',
    'prc_unitario': 'Preço Unitário',
    'prc_unit_cst_liq': 'Preço Unitário Custo Líquido',
    'prc_unit_cst_adm': 'Preço Unitário Custo ADM',
    'bc_icms': 'Base de Cálculo ICMS',
    'pct_icms': 'Alíquota ICMS',
    'vlr_icms': 'Valor ICMS',
    'bc_icms_st': 'Base ICMS ST',
    'alq_st': 'Alíquota ICMS ST',
    'vlr_st': 'Valor ICMS ST',
    'bc_ipi': 'Base IPI',
    'pct_ipi': 'Alíquota IPI',
    'vlr_ipi': 'Valor IPI',
    'bc_pis': 'Base PIS',
    'pct_pis': 'Alíquota PIS',
    'vlr_pis': 'Valor PIS',
    'bc_cof': 'Base COFINS',
    'pct_cof': 'Alíquota COFINS',
    'vlr_cof': 'Valor COFINS',
    'tp_doc': 'Tipo de Documento',
    'total_impostos': 'Total de Impostos',
    'vlr_desconto': 'Valor de Desconto',
    'vlr_frete': 'Valor do Frete',
    'vlr_liquido': 'Valor Líquido',
    'vlr_tot_doc': 'Faturamento',
    'cmv': 'CMV',
    'lucro_0': 'Lucro 0',
    'margem_0': 'Margem 0',
    'margem_contrib': 'Margem Contribuição',
    'cmv_gerencial': 'V.CMV',
    'lucro_0_gerencial': 'Lucro 0 Gerencial',
    'margem_real': 'Margem Real',
    'lucro_real': 'Lucro Real',
    'margem_contrib_ger': 'M. Contribuição',
    'cmv_media': 'CMV Média',
    'per_taxa_adm': 'Percentual Taxa ADM',
    'vlr_taxa_adm': 'Valor Taxa ADM',
    'per_taxa_frt': 'Percentual Taxa Frete',
    'vlr_taxa_frt': 'Valor Taxa Frete',
    'cmv_ue': 'CMV Última Entrada'
}

campos = [
    # Filtros
    "bukrs",
    "werks",
    "cfop",
    "pstdat",

    # Dimensões
    "name1",     # Cliente
    "ort01",     # Cidade
    "wgbez",     # Grupo de Mercadorias

    # Métricas
    "vlr_tot_doc",        # Faturamento
    "cmv_gerencial",      # V.CMV
    "margem_contrib_ger", # M. Contribuição
    "total_impostos",     # Total de Impostos
    "qtd_prod",           # Quantidade de Produto
]

cfop_list = [
    "1201AA",	
    "1202AA",	
    "1410AA",
    "1411AA",	
    "2202AA",	
    "2410AA",
    "2411AA",	
    "5101AA",	
    "5102AA",	
    "5401AA",	
    "5403AA",	
    "5910AA",	
    "6101AA",	
    "6102AA",	
    "6401AA",	
    "6403AA",	
    "6910AA"
]   

periodo_list1 = [
    "Mensal",
    "Anual"
]

# Listas alinhadas ao novo modelo (NFe)
Categoria_list1_nfe = [
    "numero",
    "serie"
]

Metrica_header_nfe = [
    "Faturamento",
    "Total de Impostos"
]

Metrica_item_nfe = [
    "Valor Líquido",
    "Total de Impostos",
    "Faturamento",
    "Quantidade de Produto"
]

opcoes_ordenacao = [
    "Do maior para o menor",
    "Do menor para o maior",
]

# ============================================================
# COMPARAÇÃO - Novo Sistema de Filtros
# ============================================================
tipo_comparacao = [
    "Mês vs Mês",
    "Ano vs Ano",
    "Mês em Anos Diferentes"
]

metricas_comparacao = [
    "Faturamento",
    "Total de Impostos",
    "Quantidade Total"
]


Metrica_grpmercadoria = [
    "Faturamento",
    "Quantidade de Produto",
    "Total de Impostos"
]

#-------------- usado na classes (type_graficos) -----------------#
Metrica_valores_k = [
    "Faturamento",
    "V.CMV",
    "Valor Líquido",
    "Total de Impostos"

]

Metrica_valores_p = [
    "M. Contribuição"
]
