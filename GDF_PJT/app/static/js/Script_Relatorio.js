/* Relatório Fiscal - Filtro mês ao abrir, clique na linha abre modal com abas (cabeçalho, itens, pagamento/parcelas, etc.) */

function relatorioTabAtivo() {
    var tab = document.querySelector('.tab-pane.active');
    return tab ? tab.id : 'rel-nfe';
}

var relatorioPaginaAtual = 1;

/** Ordenação por aba (coluna + direção enviadas à API). */
var relatorioSortState = {
    'rel-nfe': { field: 'emissao', dir: 'desc' },
    'rel-cte': { field: 'emissao', dir: 'desc' },
    'rel-nfse': { field: 'emissao', dir: 'desc' },
    'rel-sped': { field: 'data_carga', dir: 'desc' }
};

function relatorioParams() {
    var params = {
        empresa_id: (document.getElementById('relatorio-empresa') && document.getElementById('relatorio-empresa').value.trim()) || '',
        filial_id: (document.getElementById('relatorio-filial') && document.getElementById('relatorio-filial').value.trim()) || '',
        data_inicio: (document.getElementById('relatorio-data-inicio') && document.getElementById('relatorio-data-inicio').value.trim()) || '',
        data_fim: (document.getElementById('relatorio-data-fim') && document.getElementById('relatorio-data-fim').value.trim()) || '',
        busca: (document.getElementById('relatorio-busca') && document.getElementById('relatorio-busca').value.trim()) || '',
        page: relatorioPaginaAtual,
        page_size: 50
    };
    var tab = relatorioTabAtivo();
    if (tab === 'rel-nfe') {
        params.parcelas = (document.getElementById('relatorio-parcelas') && document.getElementById('relatorio-parcelas').value.trim()) || '';
        params.tipo_operacao = (document.getElementById('relatorio-tipo-operacao') && document.getElementById('relatorio-tipo-operacao').value.trim()) || '';
        params.tipo_pagamento = (document.getElementById('relatorio-tipo-pagamento') && document.getElementById('relatorio-tipo-pagamento').value.trim()) || '';
    } else if (tab === 'rel-sped') {
        params.tipo_sped = (document.getElementById('relatorio-tipo-sped') && document.getElementById('relatorio-tipo-sped').value.trim()) || '';
    }
    if (tab === 'rel-nfe' || tab === 'rel-cte' || tab === 'rel-nfse') {
        var tsap = document.getElementById('relatorio-tem-sap');
        var vsap = tsap && tsap.value.trim();
        if (vsap) params.tem_sap = vsap;
    }
    var sort = relatorioSortState[tab];
    if (sort && sort.field) {
        params.order = sort.field;
        params.dir = sort.dir || 'desc';
    }
    return params;
}

function relatorioGetPrefix() {
    var prefix = (typeof getUrlPrefix === 'function') ? getUrlPrefix() : '';
    return prefix || '';
}
function relatorioBuildUrl(base, params) {
    var q = new URLSearchParams();
    if (params.empresa_id) q.set('empresa_id', params.empresa_id);
    if (params.filial_id) q.set('filial_id', params.filial_id);
    if (params.data_inicio) q.set('data_inicio', params.data_inicio);
    if (params.data_fim) q.set('data_fim', params.data_fim);
    if (params.busca) q.set('busca', params.busca);
    if (params.parcelas !== undefined && params.parcelas) q.set('parcelas', params.parcelas);
    if (params.tipo_operacao) q.set('tipo_operacao', params.tipo_operacao);
    if (params.tipo_pagamento) q.set('tipo_pagamento', params.tipo_pagamento);
    if (params.tipo_sped) q.set('tipo_sped', params.tipo_sped);
    if (params.tem_sap) q.set('tem_sap', params.tem_sap);
    if (params.order) q.set('order', params.order);
    if (params.dir) q.set('dir', params.dir);
    if (params.page) q.set('page', String(params.page));
    if (params.page_size) q.set('page_size', String(params.page_size));
    var s = q.toString();
    return s ? base + '?' + s : base;
}

function relatorioFiltrarFilialPorEmpresa() {
    var emp = document.getElementById('relatorio-empresa');
    var sel = document.getElementById('relatorio-filial');
    if (!emp || !sel) return;
    var cod = emp.value.trim();
    var cur = sel.value;
    Array.from(sel.options).forEach(function (opt, i) {
        if (i === 0) {
            opt.disabled = false;
            return;
        }
        var oe = opt.getAttribute('data-cod-empresa') || '';
        opt.disabled = !!(cod && oe !== cod);
    });
    if (cur) {
        var idx = sel.selectedIndex;
        var selected = sel.options[idx];
        if (selected && selected.disabled) sel.value = '';
    }
}

function relatorioAtualizarIndicadoresSort() {
    ['rel-nfe', 'rel-cte', 'rel-nfse', 'rel-sped'].forEach(function (tid) {
        var pane = document.getElementById(tid);
        if (!pane) return;
        var st = relatorioSortState[tid] || { field: '', dir: 'desc' };
        pane.querySelectorAll('th.relatorio-th-sort').forEach(function (th) {
            th.classList.remove('is-sorted-asc', 'is-sorted-desc');
            var f = th.getAttribute('data-sort');
            if (f && st.field === f) {
                th.classList.add(st.dir === 'asc' ? 'is-sorted-asc' : 'is-sorted-desc');
            }
        });
    });
}

function relatorioOrdenarColuna(tabPaneId, field) {
    var st = relatorioSortState[tabPaneId];
    if (!st || !field) return;
    if (st.field === field) {
        st.dir = st.dir === 'asc' ? 'desc' : 'asc';
    } else {
        st.field = field;
        st.dir = 'desc';
    }
    relatorioPaginaAtual = 1;
    relatorioAtualizarIndicadoresSort();
    relatorioAplicar(false);
}

function relatorioRegistrarSortHeaders() {
    document.addEventListener('click', function (e) {
        var th = e.target && e.target.closest && e.target.closest('th.relatorio-th-sort');
        if (!th) return;
        var tbl = th.closest('table');
        if (!tbl || !tbl.id || tbl.id.indexOf('tabela-rel-') !== 0) return;
        e.preventDefault();
        var pane = th.closest('.tab-pane');
        if (!pane || !pane.id) return;
        var field = th.getAttribute('data-sort');
        if (!field) return;
        relatorioOrdenarColuna(pane.id, field);
    });
}

function relatorioMostrarFiltrosTab() {
    var tab = relatorioTabAtivo();
    document.querySelectorAll('.filtros-por-tab').forEach(function (el) {
        el.classList.add('d-none');
    });
    var sapWrap = document.getElementById('relatorio-filtros-xml-sap-wrap');
    if (sapWrap) {
        if (tab === 'rel-nfe' || tab === 'rel-cte' || tab === 'rel-nfse') sapWrap.classList.remove('d-none');
        else sapWrap.classList.add('d-none');
    }
    if (tab === 'rel-nfe') {
        var nfe = document.getElementById('relatorio-filtros-nfe');
        if (nfe) nfe.classList.remove('d-none');
    } else if (tab === 'rel-sped') {
        var sped = document.getElementById('relatorio-filtros-sped');
        if (sped) sped.classList.remove('d-none');
    }
}

function relatorioInicializarDatasMes() {
    var now = new Date();
    var primeiro = new Date(now.getFullYear(), now.getMonth(), 1);
    var ultimo = new Date(now.getFullYear(), now.getMonth() + 1, 0);
    function pad(n) { return n < 10 ? '0' + n : n; }
    var dataInicio = document.getElementById('relatorio-data-inicio');
    var dataFim = document.getElementById('relatorio-data-fim');
    if (dataInicio) dataInicio.value = primeiro.getFullYear() + '-' + pad(primeiro.getMonth() + 1) + '-' + pad(primeiro.getDate());
    if (dataFim) dataFim.value = ultimo.getFullYear() + '-' + pad(ultimo.getMonth() + 1) + '-' + pad(ultimo.getDate());
}

function isChaveCampo(key) {
    if (!key || typeof key !== 'string') return false;
    return key === 'pk' || key.indexOf('id_') === 0 || key.lastIndexOf('_id') === key.length - 3;
}

var LABEL_CAMPO = {
    chave_acesso: 'Chave de acesso', numero: 'Número', serie: 'Série', emissao: 'Emissão', tipo_operacao: 'Tipo operação',
    natureza_operacao: 'Natureza da operação', status: 'Status', protocolo_autorizacao: 'Protocolo de autorização',
    cnpj: 'CNPJ', cpf: 'CPF', razao_social: 'Razão social', nome_fantasia: 'Nome fantasia', inscricao_estadual: 'Inscrição estadual',
    logradouro: 'Logradouro', numero_endereco: 'Número', complemento: 'Complemento', bairro: 'Bairro', cidade: 'Cidade',
    uf: 'UF', cep: 'CEP', codigo_pais: 'País', nome_pais: 'Nome do país',
    valor_subtotal_produtos: 'Subtotal produtos', valor_frete: 'Frete', valor_seguro: 'Seguro', valor_desconto: 'Desconto',
    valor_outras_despesas: 'Outras despesas', valor_total_tributos: 'Total tributos', valor_base_icms: 'Base ICMS',
    valor_icms: 'Valor ICMS', valor_icms_st: 'Valor ICMS ST', valor_ipi: 'Valor IPI', valor_pis: 'Valor PIS', valor_cofins: 'Valor COFINS',
    valor_total_nfe: 'Total NFe', valor_servicos: 'Serviços', valor_base_pis: 'Base PIS', valor_base_cofins: 'Base COFINS',
    numero_parcela: 'Parcela', data_vencimento: 'Vencimento', valor_parcela: 'Valor', valor_desconto: 'Desconto',
    valor_base_calculo: 'Base de cálculo', aliquota: 'Alíquota %', valor_icms_st: 'ICMS ST', cst: 'CST',
    data_criacao: 'Data criação', tipo: 'Tipo', competencia: 'Competência', nome_arquivo: 'Arquivo', data_carga: 'Data carga',
    bloco: 'Bloco', registro: 'Registro', linha: 'Linha', conteudo: 'Conteúdo',
    descricao: 'Descrição', quantidade: 'Quantidade', valor_unitario: 'Valor unitário', valor_total: 'Valor total',
    codigo_servico: 'Código serviço', aliquota_issqn: 'Alíquota ISSQN', numero_rps: 'Nº RPS', serie_rps: 'Série RPS',
    valor_rps: 'Valor RPS', status_rps: 'Status RPS', data_emissao_rps: 'Emissão RPS',
    tipo_pagamento: 'Tipo de pagamento', meio_pagamento: 'Meio (código)', valor_pago: 'Valor pago',
    bandeira_cartao: 'Bandeira do cartão', cartao_cnpj: 'CNPJ adquirente', cartao_numero_autoriza: 'Nº autorização',
    pix_tipo_chave_desc: 'PIX tipo de chave', pix_tipo_chave: 'PIX tipo (cód.)', pix_chave: 'Chave PIX',
    cod_ver: 'Versão layout', dt_ini: 'Data início', dt_fin: 'Data fim', ind_mov: 'Ind. movimento',
    chv_nfe: 'Chave NFe', dt_doc: 'Data doc.', vl_doc: 'Valor doc.', vl_item: 'Valor item',
    chv_cte: 'Chave CT-e', vl_icms: 'Valor ICMS', cod_part: 'Cód. participante',
    cod_item: 'Cód. item', descr_item: 'Descrição item', unid_inv: 'Unid. inventário', cod_ncm: 'NCM',
    fantasia: 'Fantasia', end: 'Endereço', descr_compl: 'Descr. complementar', unid: 'Unidade', descr: 'Descrição',
    tem_sap: 'Chave localizada no SAP', sap_nome_tabela: 'Tabela SAP'
};

function labelCampo(key) {
    if (!key || typeof key !== 'string') return key;
    var k = key;
    if (LABEL_CAMPO[k]) return LABEL_CAMPO[k];
    return k.replace(/_/g, ' ').replace(/\b\w/g, function (c) { return c.toUpperCase(); });
}

function objParaTabela(obj, skipKeys, tableClass) {
    if (!obj || typeof obj !== 'object') return '<p class="text-muted">Sem dados</p>';
    skipKeys = skipKeys || [];
    tableClass = tableClass ? ' table-detalhe ' + tableClass : ' table-detalhe ';
    var html = '<table class="table table-sm' + tableClass + 'table-bordered"><tbody>';
    for (var k in obj) {
        if (skipKeys.indexOf(k) !== -1 || isChaveCampo(k)) continue;
        var v = obj[k];
        if (v === null || v === undefined || v === '') continue;
        if (typeof v === 'object' && v !== null && !(v instanceof Date)) continue;
        var disp = v;
        if (typeof v === 'string' && v.length > 80) disp = v.substring(0, 80) + '...';
        html += '<tr><th>' + escapeHtml(labelCampo(k)) + '</th><td>' + escapeHtml(String(disp)) + '</td></tr>';
    }
    html += '</tbody></table>';
    return html;
}

function escapeHtml(s) {
    var div = document.createElement('div');
    div.textContent = s;
    return div.innerHTML;
}

function relatorioFmtFilialCelula(x) {
    if (!x || !x.filial) return '—';
    return escapeHtml(String(x.filial));
}

/** Coluna listagem: indicador SAP + tooltip com nome da tabela. */
function relatorioFmtSapCelula(x) {
    if (!x) return '—';
    var tem = x.tem_sap === true;
    var tabela = (x.sap_nome_tabela || '').trim();
    var tip = tabela ? ' title="' + escapeHtml(tabela).replace(/"/g, '&quot;') + '"' : '';
    if (tem) return '<span class="text-success"' + tip + '>Sim</span>';
    return '<span class="text-muted">Não</span>';
}

function buildBlocoSapCabecalho(docObj) {
    if (!docObj || typeof docObj !== 'object') return '';
    var tem = docObj.tem_sap === true;
    var tabela = (docObj.sap_nome_tabela != null && docObj.sap_nome_tabela !== undefined) ? String(docObj.sap_nome_tabela).trim() : '';
    var html = '<div class="relatorio-bloco"><h6>Integração SAP</h6>';
    html += '<table class="table table-sm table-detalhe relatorio-cab table-bordered"><tbody>';
    html += '<tr><th>Chave localizada no SAP</th><td>' + (tem ? '<span class="text-success">Sim</span>' : '<span class="text-muted">Não</span>') + '</td></tr>';
    html += '<tr><th>Tabela SAP</th><td>' + (tabela ? escapeHtml(tabela) : '—') + '</td></tr>';
    html += '</tbody></table></div>';
    return html;
}

function fmtNum(v) {
    if (v === null || v === undefined || v === '') return '';
    var n = Number(v);
    if (isNaN(n)) return escapeHtml(String(v));
    return n % 1 === 0 ? String(n) : n.toFixed(2).replace('.', ',');
}

function fmtMoeda(v) {
    if (v === null || v === undefined || v === '') return '—';
    var n = Number(v);
    if (isNaN(n)) return escapeHtml(String(v));
    return 'R$ ' + n.toFixed(2).replace('.', ',').replace(/\B(?=(\d{3})+(?!\d))/g, '.');
}

function wrapBloco(html) {
    if (!html || html.indexOf('Sem dados') !== -1) return html;
    return '<div class="relatorio-bloco">' + html + '</div>';
}

function arrayParaTabela(arr, columns, formatCols) {
    if (!arr || !arr.length) return '<p class="text-muted">Nenhum registro</p>';
    var allKeys = arr[0] ? Object.keys(arr[0]) : [];
    columns = columns || allKeys;
    columns = columns.filter(function (c) { return !isChaveCampo(c); });
    if (!columns.length) columns = allKeys.filter(function (c) { return !isChaveCampo(c); });
    formatCols = formatCols || {};
    var html = '<div class="table-responsive"><table class="table table-sm table-detalhe table-hover table-bordered"><thead><tr>';
    columns.forEach(function (c) {
        var thClass = formatCols[c] === 'moeda' ? ' relatorio-moeda' : (formatCols[c] === 'numero' ? ' relatorio-num' : '');
        html += '<th class="' + thClass + '">' + escapeHtml(labelCampo(c)) + '</th>';
    });
    html += '</thead><tbody>';
    arr.forEach(function (row) {
        html += '<tr>';
        columns.forEach(function (col) {
            var val = row[col];
            var fmt = formatCols[col];
            var disp = '';
            if (val !== null && val !== undefined) {
                if (fmt === 'moeda') disp = fmtMoeda(val);
                else if (fmt === 'numero') disp = fmtNum(val);
                else if (typeof val === 'object' && typeof val.toISOString === 'function') disp = val.toISOString ? val.toISOString().slice(0, 10) : String(val);
                else if (typeof val === 'number' && val % 1 !== 0 && !fmt) disp = Number(val).toFixed(2);
                else disp = String(val);
            }
            var tdClass = fmt === 'moeda' ? ' relatorio-moeda' : (fmt === 'numero' ? ' relatorio-num' : '');
            html += '<td class="' + tdClass + '">' + (disp ? escapeHtml(disp) : '') + '</td>';
        });
        html += '</tr>';
    });
    html += '</tbody></table></div>';
    return html;
}

function abrirDetalhe(tipo, id, tipoSped) {
    var modal = document.getElementById('modalRelatorioDetalhe');
    var loading = document.getElementById('modal-rel-loading');
    var content = document.getElementById('modal-rel-content');
    var titulo = document.getElementById('modal-rel-titulo');
    var tabsContainer = document.getElementById('modal-rel-tabs');
    var tabContentContainer = document.getElementById('modal-rel-tab-content');
    if (!modal || !loading || !content) return;

    titulo.textContent = 'Detalhe - ' + (tipo.toUpperCase()) + ' #' + id;
    loading.classList.remove('d-none');
    content.classList.add('d-none');
    tabsContainer.innerHTML = '';
    tabContentContainer.innerHTML = '';
    var modalBs = new bootstrap.Modal(modal);
    modalBs.show();

    var p = relatorioGetPrefix();
    var url = (tipo === 'sped' && tipoSped)
        ? p + '/api/relatorio/sped/' + tipoSped + '/' + id + '/'
        : p + '/api/relatorio/' + tipo.toLowerCase() + '/' + id + '/';
    fetch(url)
        .then(function (r) { return r.json(); })
        .then(function (data) {
            loading.classList.add('d-none');
            content.classList.remove('d-none');
            if (!data.sucesso) {
                tabContentContainer.innerHTML = '<p class="text-danger">Erro ao carregar detalhe.</p>';
                return;
            }
            if (tipo === 'nfe') preencherModalNFe(data, tabsContainer, tabContentContainer);
            else if (tipo === 'cte') preencherModalCTe(data, tabsContainer, tabContentContainer);
            else if (tipo === 'nfse') preencherModalNFSe(data, tabsContainer, tabContentContainer);
            else if (tipo === 'sped') preencherModalSped(data, tabsContainer, tabContentContainer);
        })
        .catch(function () {
            loading.classList.add('d-none');
            content.classList.remove('d-none');
            tabContentContainer.innerHTML = '<p class="text-danger">Erro na requisição.</p>';
        });
}

function buildItensComImpostosNFe(itens) {
    if (!itens || !itens.length) return '<p class="text-muted">Nenhum item</p>';
    var groupRow = '<thead class="relatorio-thead-grupo"><tr>' +
        '<th colspan="8">Produto</th><th colspan="5">ICMS</th><th colspan="4">PIS</th><th colspan="4">COFINS</th><th colspan="1">IPI</th></tr></thead>';
    var colRow = '<thead class="relatorio-thead-col"><tr>' +
        '<th>Item</th><th>Descrição</th><th>NCM</th><th>CFOP</th><th>Qtd</th><th>Un</th><th>V. Unit.</th><th>V. Total</th>' +
        '<th>CST</th><th>BC</th><th>Alíq %</th><th>Valor</th><th>Valor ST</th>' +
        '<th>CST</th><th>BC</th><th>Alíq %</th><th>Valor</th>' +
        '<th>CST</th><th>BC</th><th>Alíq %</th><th>Valor</th>' +
        '<th>Valor</th></tr></thead>';
    var tbody = '<tbody>';
    itens.forEach(function (x) {
        var icms = x.icms || {};
        var pis = x.pis || {};
        var cofins = x.cofins || {};
        var ipi = x.ipi || {};
        tbody += '<tr>' +
            '<td>' + escapeHtml(x.numero_item != null ? String(x.numero_item) : '') + '</td>' +
            '<td style="max-width:200px" title="' + escapeHtml(x.descricao || '') + '">' + escapeHtml(x.descricao || '—') + '</td>' +
            '<td>' + escapeHtml(x.ncm || '—') + '</td><td>' + escapeHtml(x.cfop || '—') + '</td>' +
            '<td class="relatorio-num">' + fmtNum(x.quantidade) + '</td><td>' + escapeHtml(x.unidade || '—') + '</td>' +
            '<td class="relatorio-moeda">' + fmtMoeda(x.valor_unitario) + '</td><td class="relatorio-moeda">' + fmtMoeda(x.valor_total) + '</td>' +
            '<td>' + escapeHtml(icms.cst != null ? String(icms.cst) : '—') + '</td>' +
            '<td class="relatorio-moeda">' + fmtMoeda(icms.valor_base_calculo) + '</td><td class="relatorio-num">' + fmtNum(icms.aliquota) + '</td>' +
            '<td class="relatorio-moeda">' + fmtMoeda(icms.valor_icms) + '</td><td class="relatorio-moeda">' + fmtMoeda(icms.valor_icms_st) + '</td>' +
            '<td>' + escapeHtml(pis.cst != null ? String(pis.cst) : '—') + '</td>' +
            '<td class="relatorio-moeda">' + fmtMoeda(pis.valor_base_calculo) + '</td><td class="relatorio-num">' + fmtNum(pis.aliquota) + '</td>' +
            '<td class="relatorio-moeda">' + fmtMoeda(pis.valor_pis) + '</td>' +
            '<td>' + escapeHtml(cofins.cst != null ? String(cofins.cst) : '—') + '</td>' +
            '<td class="relatorio-moeda">' + fmtMoeda(cofins.valor_base_calculo) + '</td><td class="relatorio-num">' + fmtNum(cofins.aliquota) + '</td>' +
            '<td class="relatorio-moeda">' + fmtMoeda(cofins.valor_cofins) + '</td>' +
            '<td class="relatorio-moeda">' + fmtMoeda(ipi.valor_ipi) + '</td></tr>';
    });
    tbody += '</tbody>';
    return '<div class="relatorio-itens-wrapper"><table class="table table-sm table-hover table-bordered table-detalhe">' + groupRow + colRow + tbody + '</table></div>';
}

function preencherModalNFe(data, tabsContainer, tabContentContainer) {
    var cab = data.cabecalho || {};
    var tabs = [
        { id: 'cab', label: 'Cabeçalho', content: buildCabecalhoNFe(cab) },
        { id: 'itens', label: 'Itens', content: buildItensComImpostosNFe(data.itens) },
        { id: 'pag', label: 'Pagamento e Parcelas', content: buildPagamentoParcelasNFe(data) },
        { id: 'transp', label: 'Transporte', content: wrapBloco(objParaTabela(data.transporte, [], 'relatorio-cab')) },
        { id: 'total', label: 'Totalização', content: wrapBloco(objParaTabela(data.totalizacao, [], 'relatorio-cab')) },
        { id: 'info', label: 'Informações Adicionais', content: wrapBloco(objParaTabela(data.informacoes_adicionais, [], 'relatorio-cab')) }
    ];
    renderTabs(tabs, tabsContainer, tabContentContainer);
}

function buildCabecalhoNFe(cab) {
    var h = '';
    if (cab.nfe) h += buildBlocoSapCabecalho(cab.nfe);
    if (cab.identificacao) h += '<div class="relatorio-bloco"><h6>Identificação</h6>' + objParaTabela(cab.identificacao, [], 'relatorio-cab') + '</div>';
    if (cab.emitente) h += '<div class="relatorio-bloco"><h6>Emitente</h6>' + objParaTabela(cab.emitente, [], 'relatorio-cab') + '</div>';
    if (cab.emitente_endereco) h += '<div class="relatorio-bloco"><h6>Endereço do emitente</h6>' + objParaTabela(cab.emitente_endereco, [], 'relatorio-cab') + '</div>';
    if (cab.destinatario) h += '<div class="relatorio-bloco"><h6>Destinatário</h6>' + objParaTabela(cab.destinatario, [], 'relatorio-cab') + '</div>';
    if (cab.destinatario_endereco) h += '<div class="relatorio-bloco"><h6>Endereço do destinatário</h6>' + objParaTabela(cab.destinatario_endereco, [], 'relatorio-cab') + '</div>';
    if (cab.nfe) h += '<div class="relatorio-bloco"><h6>NFe (status / origem)</h6>' + objParaTabela(cab.nfe, ['tem_sap', 'sap_nome_tabela'], 'relatorio-cab') + '</div>';
    return h || '<p class="text-muted">Sem dados</p>';
}

/** Usa o código retornado da tabela/API e busca o texto no JSON (Tipo_pagamento.json). */
function descricaoTipoPagamento(codigo) {
    var mapa = window.TIPO_PAGAMENTO_DESC || {};
    if (codigo === null || codigo === undefined || codigo === '') return 'Não informado';
    var key = String(codigo).trim();
    if (/^\d+$/.test(key) && key.length <= 2) key = key.padStart(2, '0');
    var desc = mapa[key];
    return desc || ('Outros (' + String(codigo) + ')');
}

function buildPagamentoParcelasNFe(data) {
    var h = '';
    // Código vem da tabela (meio_pagamento); o texto é buscado no JSON
    h += '<div class="relatorio-bloco"><h6>Tipo de pagamento</h6>';
    if (data.pagamento && typeof data.pagamento === 'object' && data.pagamento.meio_pagamento !== undefined) {
        var codigoTabela = data.pagamento.meio_pagamento;
        var textoJson = descricaoTipoPagamento(codigoTabela);
        h += '<p class="mb-0">' + escapeHtml(String(codigoTabela)) + ': ' + escapeHtml(textoJson) + '</p>';
    } else {
        h += '<p class="text-muted mb-0">Não informado</p>';
    }
    h += '</div>';
    if (data.parcelas && data.parcelas.length) h += '<div class="relatorio-bloco"><h6>Parcelas</h6>' + arrayParaTabela(data.parcelas, ['numero_parcela', 'data_vencimento', 'valor_parcela', 'valor_desconto']) + '</div>';
    // Pagamento: valor pago e demais dados (sem repetir meio_pagamento)
    h += '<div class="relatorio-bloco"><h6>Pagamento</h6>';
    if (data.pagamento && typeof data.pagamento === 'object') {
        var pagHtml = objParaTabela(data.pagamento, ['meio_pagamento', 'tipo_pagamento'], 'relatorio-cab');
        if (pagHtml && pagHtml.indexOf('Sem dados') !== -1) {
            h += '<p class="text-muted mb-0">Nenhum dado de pagamento para esta NFe.</p>';
        } else {
            h += pagHtml;
        }
    } else {
        h += '<p class="text-muted mb-0">Nenhum registro de pagamento para esta NFe.</p>';
    }
    h += '</div>';
    return h || '<p class="text-muted">Sem dados de pagamento ou parcelas.</p>';
}

function preencherModalCTe(data, tabsContainer, tabContentContainer) {
    var cab = data.cabecalho || {};
    var tabs = [
        { id: 'cab', label: 'Cabeçalho', content: buildCabecalhoCTe(cab) },
        { id: 'valor', label: 'Valor', content: wrapBloco(objParaTabela(data.valor, [], 'relatorio-cab')) },
        { id: 'transp', label: 'Transporte', content: wrapBloco(objParaTabela(data.transporte, [], 'relatorio-cab')) },
        { id: 'carga', label: 'Carga', content: wrapBloco(objParaTabela(data.carga, [], 'relatorio-cab')) },
        { id: 'servico', label: 'Serviço', content: wrapBloco(objParaTabela(data.servico, [], 'relatorio-cab')) },
        { id: 'veiculo', label: 'Veículo', content: wrapBloco(objParaTabela(data.veiculo, [], 'relatorio-cab')) },
        { id: 'motorista', label: 'Motorista', content: wrapBloco(objParaTabela(data.motorista, [], 'relatorio-cab')) },
        { id: 'percurso', label: 'Percurso', content: wrapBloco(objParaTabela(data.percurso, [], 'relatorio-cab')) },
        { id: 'fiscal', label: 'Fiscal', content: wrapBloco(objParaTabela(data.fiscal, [], 'relatorio-cab')) }
    ];
    renderTabs(tabs, tabsContainer, tabContentContainer);
}

function buildCabecalhoCTe(cab) {
    var h = '';
    if (cab.cte) h += buildBlocoSapCabecalho(cab.cte);
    if (cab.identificacao) h += '<div class="relatorio-bloco"><h6>Identificação</h6>' + objParaTabela(cab.identificacao, [], 'relatorio-cab') + '</div>';
    if (cab.emitente) h += '<div class="relatorio-bloco"><h6>Emitente</h6>' + objParaTabela(cab.emitente, [], 'relatorio-cab') + '</div>';
    if (cab.destinatario) h += '<div class="relatorio-bloco"><h6>Destinatário</h6>' + objParaTabela(cab.destinatario, [], 'relatorio-cab') + '</div>';
    if (cab.cte) h += '<div class="relatorio-bloco"><h6>CTe</h6>' + objParaTabela(cab.cte, ['tem_sap', 'sap_nome_tabela'], 'relatorio-cab') + '</div>';
    return h || '<p class="text-muted">Sem dados</p>';
}

function preencherModalNFSe(data, tabsContainer, tabContentContainer) {
    var cab = data.cabecalho || {};
    var tabs = [
        { id: 'cab', label: 'Cabeçalho', content: buildCabecalhoNFSe(cab) },
        { id: 'servicos', label: 'Serviços', content: wrapBloco(arrayParaTabela(data.servicos, ['descricao', 'quantidade', 'valor_unitario', 'valor_total', 'codigo_servico', 'aliquota_issqn'])) },
        { id: 'rps', label: 'RPS', content: wrapBloco(arrayParaTabela(data.rps, ['numero_rps', 'serie_rps', 'valor_rps', 'status_rps', 'data_emissao_rps'])) },
        { id: 'retencao', label: 'Retenção', content: wrapBloco(objParaTabela(data.retencao, [], 'relatorio-cab')) },
        { id: 'pagamento', label: 'Pagamento', content: wrapBloco(objParaTabela(data.pagamento, [], 'relatorio-cab')) }
    ];
    renderTabs(tabs, tabsContainer, tabContentContainer);
}

function buildCabecalhoNFSe(cab) {
    var h = '';
    if (cab.nfse) h += buildBlocoSapCabecalho(cab.nfse);
    if (cab.identificacao) h += '<div class="relatorio-bloco"><h6>Identificação</h6>' + objParaTabela(cab.identificacao, [], 'relatorio-cab') + '</div>';
    if (cab.prestador) h += '<div class="relatorio-bloco"><h6>Prestador</h6>' + objParaTabela(cab.prestador, [], 'relatorio-cab') + '</div>';
    if (cab.tomador) h += '<div class="relatorio-bloco"><h6>Tomador</h6>' + objParaTabela(cab.tomador, [], 'relatorio-cab') + '</div>';
    if (cab.nfse) h += '<div class="relatorio-bloco"><h6>NFSe</h6>' + objParaTabela(cab.nfse, ['tem_sap', 'sap_nome_tabela'], 'relatorio-cab') + '</div>';
    return h || '<p class="text-muted">Sem dados</p>';
}

function fmtCnpj(v) {
    if (v === null || v === undefined || v === '') return '—';
    var s = String(v).replace(/\D/g, '');
    if (s.length !== 14) return escapeHtml(String(v));
    return escapeHtml(s.replace(/^(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})$/, '$1.$2.$3/$4-$5'));
}

function buildCabecalhoSped(cab) {
    var c = cab || {};
    var tipoDisp = (c.tipo === 'F' ? 'Fiscal (ICMS/IPI)' : (c.tipo === 'C' ? 'Contribuição' : (c.tipo || '—')));
    var html = '<div class="relatorio-bloco relatorio-sped-resumo">';
    html += '<h6><i class="fas fa-file-alt me-2"></i>Resumo do arquivo</h6>';
    html += '<div class="row g-3">';
    html += '<div class="col-md-4"><div class="relatorio-sped-campo"><span class="text-muted small">Tipo</span><div class="fw-600">' + escapeHtml(tipoDisp) + '</div></div></div>';
    html += '<div class="col-md-4"><div class="relatorio-sped-campo"><span class="text-muted small">Arquivo</span><div class="text-truncate" title="' + escapeHtml(c.nome_arquivo || '') + '">' + escapeHtml(c.nome_arquivo || '—') + '</div></div></div>';
    html += '<div class="col-md-4"><div class="relatorio-sped-campo"><span class="text-muted small">Competência</span><div>' + (c.competencia ? c.competencia.slice(0, 10) : '—') + '</div></div></div>';
    html += '<div class="col-md-4"><div class="relatorio-sped-campo"><span class="text-muted small">Empresa</span><div>' + escapeHtml(c.empresa || '—') + '</div></div></div>';
    html += '<div class="col-md-4"><div class="relatorio-sped-campo"><span class="text-muted small">Data da carga</span><div>' + (c.data_carga ? c.data_carga.slice(0, 16).replace('T', ' ') : '—') + '</div></div></div>';
    html += '</div></div>';
    return html;
}

function buildTabelaC100ComImpostos(regs) {
    if (!regs || !regs.length) return '<p class="text-muted">Nenhum documento C100</p>';
    var groupRow = '<thead class="relatorio-thead-grupo"><tr>' +
        '<th colspan="5">Documento</th><th colspan="6">Impostos</th></tr></thead>';
    var colRow = '<thead class="relatorio-thead-col"><tr>' +
        '<th>Linha</th><th>Chave NFe</th><th>Data</th><th>Nº Doc</th><th>Valor Doc.</th>' +
        '<th>BC ICMS</th><th>ICMS</th><th>BC ST</th><th>ICMS ST</th><th>PIS</th><th>COFINS</th><th>IPI</th></tr></thead>';
    var tbody = '<tbody>';
    regs.forEach(function (r) {
        tbody += '<tr>' +
            '<td>' + (r.linha != null ? r.linha : '') + '</td>' +
            '<td class="small font-monospace" style="min-width:300px; word-break:break-all" title="' + escapeHtml(r.chv_nfe || '') + '">' + escapeHtml(r.chv_nfe || '—') + '</td>' +
            '<td>' + (r.dt_doc || '—') + '</td><td>' + escapeHtml(r.num_doc || '—') + '</td>' +
            '<td class="relatorio-moeda">' + fmtMoeda(r.vl_doc) + '</td>' +
            '<td class="relatorio-moeda">' + fmtMoeda(r.vl_bc_icms) + '</td><td class="relatorio-moeda">' + fmtMoeda(r.vl_icms) + '</td>' +
            '<td class="relatorio-moeda">' + fmtMoeda(r.vl_bc_icms_st) + '</td><td class="relatorio-moeda">' + fmtMoeda(r.vl_icms_st) + '</td>' +
            '<td class="relatorio-moeda">' + fmtMoeda(r.vl_pis) + '</td><td class="relatorio-moeda">' + fmtMoeda(r.vl_cofins) + '</td>' +
            '<td class="relatorio-moeda">' + fmtMoeda(r.vl_ipi) + '</td></tr>';
    });
    tbody += '</tbody>';
    return '<div class="relatorio-itens-wrapper"><table class="table table-sm table-hover table-bordered table-detalhe">' + groupRow + colRow + tbody + '</table></div>';
}

function buildTabelaC170ComImpostos(regs) {
    if (!regs || !regs.length) return '<p class="text-muted">Nenhum item C170</p>';
    var groupRow = '<thead class="relatorio-thead-grupo"><tr>' +
        '<th colspan="7">Produto</th><th colspan="5">ICMS</th><th colspan="4">PIS</th><th colspan="4">COFINS</th></tr></thead>';
    var colRow = '<thead class="relatorio-thead-col"><tr>' +
        '<th>Item</th><th>Cód.</th><th>Descrição</th><th>Qtd</th><th>Un</th><th>V. Item</th><th>Desconto</th>' +
        '<th>CST</th><th>BC</th><th>Alíq %</th><th>ICMS</th><th>ICMS ST</th>' +
        '<th>CST</th><th>BC</th><th>Alíq %</th><th>PIS</th>' +
        '<th>CST</th><th>BC</th><th>Alíq %</th><th>COFINS</th></tr></thead>';
    var tbody = '<tbody>';
    regs.forEach(function (r) {
        tbody += '<tr>' +
            '<td>' + escapeHtml(r.num_item != null ? String(r.num_item) : '') + '</td>' +
            '<td>' + escapeHtml(r.cod_item || '—') + '</td>' +
            '<td style="max-width:180px" title="' + escapeHtml(r.descr_compl || '') + '">' + escapeHtml(r.descr_compl || '—') + '</td>' +
            '<td class="relatorio-num">' + fmtNum(r.qtd) + '</td><td>' + escapeHtml(r.unid || '—') + '</td>' +
            '<td class="relatorio-moeda">' + fmtMoeda(r.vl_item) + '</td><td class="relatorio-moeda">' + fmtMoeda(r.vl_desc) + '</td>' +
            '<td>' + escapeHtml(r.cst_icms != null ? String(r.cst_icms) : '—') + '</td>' +
            '<td class="relatorio-moeda">' + fmtMoeda(r.vl_bc_icms) + '</td><td class="relatorio-num">' + fmtNum(r.aliq_icms) + '</td>' +
            '<td class="relatorio-moeda">' + fmtMoeda(r.vl_icms) + '</td><td class="relatorio-moeda">' + fmtMoeda(r.vl_icms_st) + '</td>' +
            '<td>' + escapeHtml(r.cst_pis != null ? String(r.cst_pis) : '—') + '</td>' +
            '<td class="relatorio-moeda">' + fmtMoeda(r.vl_bc_pis) + '</td><td class="relatorio-num">' + fmtNum(r.aliq_pis) + '</td>' +
            '<td class="relatorio-moeda">' + fmtMoeda(r.vl_pis) + '</td>' +
            '<td>' + escapeHtml(r.cst_cofins != null ? String(r.cst_cofins) : '—') + '</td>' +
            '<td class="relatorio-moeda">' + fmtMoeda(r.vl_bc_cofins) + '</td><td class="relatorio-num">' + fmtNum(r.aliq_cofins) + '</td>' +
            '<td class="relatorio-moeda">' + fmtMoeda(r.vl_cofins) + '</td></tr>';
    });
    tbody += '</tbody>';
    return '<div class="relatorio-itens-wrapper"><table class="table table-sm table-hover table-bordered table-detalhe">' + groupRow + colRow + tbody + '</table></div>';
}

function buildReg0000Card(regs) {
    if (!regs || !regs.length) return '<p class="text-muted">Nenhum registro 0000</p>';
    var r = regs[0];
    var html = '<div class="relatorio-bloco relatorio-sped-0000">';
    html += '<h6><i class="fas fa-info-circle me-2"></i>Registro 0000 – Abertura do arquivo</h6>';
    html += '<div class="row g-3">';
    html += '<div class="col-md-6"><div class="relatorio-sped-campo"><span class="text-muted small">Razão social / Nome</span><div class="fw-600">' + escapeHtml(r.nome || '—') + '</div></div></div>';
    html += '<div class="col-md-6"><div class="relatorio-sped-campo"><span class="text-muted small">CNPJ</span><div>' + fmtCnpj(r.cnpj) + '</div></div></div>';
    html += '<div class="col-md-4"><div class="relatorio-sped-campo"><span class="text-muted small">Versão layout</span><div>' + escapeHtml(r.cod_ver || '—') + '</div></div></div>';
    html += '<div class="col-md-4"><div class="relatorio-sped-campo"><span class="text-muted small">Período início</span><div>' + (r.dt_ini || '—') + '</div></div></div>';
    html += '<div class="col-md-4"><div class="relatorio-sped-campo"><span class="text-muted small">Período fim</span><div>' + (r.dt_fin || '—') + '</div></div></div>';
    html += '</div></div>';
    return html;
}

function preencherModalSped(data, tabsContainer, tabContentContainer) {
    var r0000 = data.reg_0000 || [], r0001 = data.reg_0001 || [], r0005 = data.reg_0005 || [];
    var r0150 = data.reg_0150 || [], r0190 = data.reg_0190 || [], r0200 = data.reg_0200 || [];
    var rC001 = data.reg_c001 || [], rC100 = data.reg_c100 || [], rC170 = data.reg_c170 || [];
    var rC190 = data.reg_c190 || [], rD100 = data.reg_d100 || [], registros = data.registros || [];
    var moedaColsC100 = { vl_doc: 'moeda', vl_bc_icms: 'moeda', vl_icms: 'moeda', vl_bc_icms_st: 'moeda', vl_icms_st: 'moeda', vl_ipi: 'moeda', vl_pis: 'moeda', vl_cofins: 'moeda' };
    var moedaColsC170 = { vl_item: 'moeda', vl_desc: 'moeda', vl_bc_icms: 'moeda', vl_icms: 'moeda', vl_bc_icms_st: 'moeda', vl_icms_st: 'moeda', vl_bc_pis: 'moeda', vl_pis: 'moeda', vl_bc_cofins: 'moeda', vl_cofins: 'moeda' };
    var moedaColsC190 = { vl_opr: 'moeda', vl_bc_icms: 'moeda', vl_icms: 'moeda', vl_bc_icms_st: 'moeda', vl_icms_st: 'moeda', vl_red_bc: 'moeda', vl_ipi: 'moeda' };
    var numColsC170 = { qtd: 'numero', aliq_icms: 'numero', aliq_st: 'numero', aliq_pis: 'numero', aliq_cofins: 'numero' };
    var numColsC190 = { aliq_icms: 'numero' };
    Object.assign(moedaColsC170, numColsC170);
    Object.assign(moedaColsC190, numColsC190);

    var tabs = [
        { id: 'resumo', label: 'Resumo', content: buildCabecalhoSped(data.cabecalho) + buildReg0000Card(r0000) },
        { id: 'reg0005', label: '0005 Dados complementares' + (r0005.length ? ' (' + r0005.length + ')' : ''), content: wrapBloco(arrayParaTabela(r0005, ['linha', 'fantasia', 'end', 'bairro', 'email'], {})) },
        { id: 'reg0150', label: '0150 Participantes' + (r0150.length ? ' (' + r0150.length + ')' : ''), content: wrapBloco(arrayParaTabela(r0150, ['linha', 'cod_part', 'nome', 'cnpj', 'end'], {})) },
        { id: 'reg0190', label: '0190 Unidades' + (r0190.length ? ' (' + r0190.length + ')' : ''), content: wrapBloco(arrayParaTabela(r0190, ['linha', 'unid', 'descr'], {})) },
        { id: 'reg0200', label: '0200 Itens' + (r0200.length ? ' (' + r0200.length + ')' : ''), content: wrapBloco(arrayParaTabela(r0200, ['linha', 'cod_item', 'descr_item', 'unid_inv', 'cod_ncm'], {})) },
        { id: 'regc100', label: 'C100 Documentos fiscais (impostos)' + (rC100.length ? ' (' + rC100.length + ')' : ''), content: wrapBloco(buildTabelaC100ComImpostos(rC100)) },
        { id: 'regc170', label: 'C170 Itens com impostos' + (rC170.length ? ' (' + rC170.length + ')' : ''), content: wrapBloco(buildTabelaC170ComImpostos(rC170)) },
        { id: 'regc190', label: 'C190 Analítico ICMS' + (rC190.length ? ' (' + rC190.length + ')' : ''), content: wrapBloco(arrayParaTabela(rC190, ['linha', 'cst_icms', 'cfop', 'vl_opr', 'vl_bc_icms', 'aliq_icms', 'vl_icms', 'vl_bc_icms_st', 'vl_icms_st', 'vl_red_bc', 'vl_ipi'], moedaColsC190)) },
        { id: 'regd100', label: 'D100 Transporte (CT-e)' + (rD100.length ? ' (' + rD100.length + ')' : ''), content: wrapBloco(arrayParaTabela(rD100, ['linha', 'chv_cte', 'dt_doc', 'vl_doc'], { vl_doc: 'moeda' })) },
        { id: 'registros', label: 'Outros registros' + (registros.length ? ' (' + registros.length + ')' : ''), content: buildOutrosRegistrosSped(registros) }
    ];
    renderTabs(tabs, tabsContainer, tabContentContainer);
}

function buildOutrosRegistrosSped(registros) {
    if (!registros || !registros.length) return '<p class="text-muted">Nenhum outro registro</p>';
    var porTipo = {};
    registros.forEach(function (r) {
        var t = r.registro || '?';
        if (!porTipo[t]) porTipo[t] = [];
        porTipo[t].push(r);
    });
    var html = '';
    Object.keys(porTipo).sort().forEach(function (tipo) {
        var itens = porTipo[tipo];
        html += '<div class="relatorio-bloco"><h6>Registro ' + escapeHtml(tipo) + ' (' + itens.length + ')</h6>';
        html += '<div class="table-responsive"><table class="table table-sm table-detalhe table-hover table-bordered"><thead><tr><th>Linha</th><th>Conteúdo</th></tr></thead><tbody>';
        itens.slice(0, 50).forEach(function (r) {
            var conteudo = (r.conteudo || '').substring(0, 120);
            if ((r.conteudo || '').length > 120) conteudo += '…';
            html += '<tr><td>' + (r.linha != null ? r.linha : '') + '</td><td class="small font-monospace" style="word-break:break-all">' + escapeHtml(conteudo || '') + '</td></tr>';
        });
        html += '</tbody></table></div>';
        if (itens.length > 50) html += '<p class="small text-muted mt-2">Exibindo 50 de ' + itens.length + ' registros.</p>';
        html += '</div>';
    });
    return html || '<p class="text-muted">Nenhum outro registro</p>';
}

function renderTabs(tabs, tabsContainer, tabContentContainer) {
    tabs.forEach(function (t, i) {
        var active = i === 0 ? ' active' : '';
        var show = i === 0 ? ' show active' : '';
        tabsContainer.innerHTML += '<li class="nav-item"><button class="nav-link' + active + '" data-bs-toggle="tab" data-bs-target="#modal-tab-' + t.id + '" type="button">' + escapeHtml(t.label) + '</button></li>';
        tabContentContainer.innerHTML += '<div class="tab-pane fade' + show + '" id="modal-tab-' + t.id + '" role="tabpanel">' + t.content + '</div>';
    });
}

function relatorioAtualizarContador(tipo, total, paginacao) {
    var el = document.getElementById('relatorio-contador-num');
    if (!el) return;
    var label = tipo === 'sped' ? 'arquivo(s)' : 'nota(s)';
    if (total === 0) {
        el.textContent = 'Nenhuma ' + label;
    } else if (paginacao && paginacao.total_pages > 1) {
        var from = (paginacao.page - 1) * paginacao.page_size + 1;
        var to = Math.min(paginacao.page * paginacao.page_size, total);
        el.textContent = 'Exibindo ' + from + ' a ' + to + ' de ' + total + ' ' + label;
    } else {
        el.textContent = total + ' ' + label + ' exibida' + (total === 1 ? '' : 's');
    }
}

function relatorioRenderizarPaginacao(paginacao) {
    var nav = document.getElementById('relatorio-paginacao');
    var ul = nav ? nav.querySelector('ul.pagination') : null;
    if (!ul) return;
    ul.innerHTML = '';
    if (!paginacao || paginacao.total_pages <= 1) {
        nav.classList.add('d-none');
        return;
    }
    nav.classList.remove('d-none');
    var page = paginacao.page;
    var totalPages = paginacao.total_pages;
    var add = function (label, num, disabled) {
        var li = document.createElement('li');
        li.className = 'page-item' + (disabled ? ' disabled' : '') + (num === page ? ' active' : '');
        var a = document.createElement('a');
        a.className = 'page-link';
        a.href = '#';
        a.setAttribute('data-page', String(num !== undefined ? num : ''));
        a.textContent = label;
        a.addEventListener('click', function (e) {
            e.preventDefault();
            if (disabled || num === page) return;
            if (num !== undefined) {
                relatorioPaginaAtual = num;
                relatorioAplicar(false);
            }
        });
        li.appendChild(a);
        ul.appendChild(li);
    };
    add('Anterior', page - 1, page <= 1);
    var maxBotoes = 7;
    var ini = Math.max(1, page - Math.floor(maxBotoes / 2));
    var fim = Math.min(totalPages, ini + maxBotoes - 1);
    if (fim - ini + 1 < maxBotoes) ini = Math.max(1, fim - maxBotoes + 1);
    if (ini > 1) {
        add('1', 1, false);
        if (ini > 2) add('…', undefined, true);
    }
    for (var p = ini; p <= fim; p++) add(String(p), p, false);
    if (fim < totalPages) {
        if (fim < totalPages - 1) add('…', undefined, true);
        add(String(totalPages), totalPages, false);
    }
    add('Próxima', page + 1, page >= totalPages);
}

function relatorioCarregarNFe() {
    var tbody = document.querySelector('#tabela-rel-nfe tbody');
    if (!tbody) return;
    tbody.innerHTML = '<tr><td colspan="10" class="text-center">Carregando...</td></tr>';
    var url = relatorioGetPrefix() + relatorioBuildUrl('/api/relatorio/nfe/', relatorioParams());
    fetch(url)
        .then(function (r) { return r.json(); })
        .then(function (data) {
            var items = data.items || [];
            var pag = { total: data.total || items.length, page: data.page || 1, page_size: data.page_size || 50, total_pages: data.total_pages || 1 };
            relatorioAtualizarContador('nfe', pag.total, pag);
            relatorioRenderizarPaginacao(pag);
            if (items.length === 0) {
                tbody.innerHTML = '<tr><td colspan="10" class="text-center text-muted">Nenhum registro</td></tr>';
                return;
            }
            tbody.innerHTML = items.map(function (x) {
                return '<tr class="tr-relatorio-click" data-tipo="nfe" data-id="' + (x.id_nfe || '') + '">' +
                    '<td>' + (x.numero || '-') + '</td><td>' + (x.serie || '-') + '</td>' +
                    '<td class="small text-truncate" style="max-width:120px" title="' + (x.chave || '').replace(/"/g, '&quot;') + '">' + (x.chave || '-') + '</td>' +
                    '<td>' + (x.emissao ? x.emissao.slice(0, 10) : '-') + '</td>' +
                    '<td>' + (x.tipo_operacao === '1' ? 'Saída' : 'Entrada') + '</td><td>' + (x.status || '-') + '</td>' +
                    '<td>' + (x.empresa || '-') + '</td>' +
                    '<td class="text-truncate" style="max-width:140px">' + relatorioFmtFilialCelula(x) + '</td>' +
                    '<td class="text-truncate" style="max-width:150px" title="' + (x.natureza || '').replace(/"/g, '&quot;') + '">' + (x.natureza || '-') + '</td>' +
                    '<td class="text-center">' + relatorioFmtSapCelula(x) + '</td></tr>';
            }).join('');
            tbody.querySelectorAll('tr[data-id]').forEach(function (tr) {
                tr.addEventListener('click', function () { abrirDetalhe(tr.getAttribute('data-tipo'), tr.getAttribute('data-id')); });
            });
            relatorioAtualizarIndicadoresSort();
        })
        .catch(function () { tbody.innerHTML = '<tr><td colspan="10" class="text-center text-danger">Erro ao carregar</td></tr>'; relatorioAtualizarContador('nfe', 0); relatorioRenderizarPaginacao(null); });
}

function relatorioCarregarCTe() {
    var tbody = document.querySelector('#tabela-rel-cte tbody');
    if (!tbody) return;
    tbody.innerHTML = '<tr><td colspan="7" class="text-center">Carregando...</td></tr>';
    var url = relatorioGetPrefix() + relatorioBuildUrl('/api/relatorio/cte/', relatorioParams());
    fetch(url)
        .then(function (r) { return r.json(); })
        .then(function (data) {
            var items = data.items || [];
            var pag = { total: data.total || items.length, page: data.page || 1, page_size: data.page_size || 50, total_pages: data.total_pages || 1 };
            relatorioAtualizarContador('cte', pag.total, pag);
            relatorioRenderizarPaginacao(pag);
            if (items.length === 0) {
                tbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted">Nenhum registro</td></tr>';
                return;
            }
            tbody.innerHTML = items.map(function (x) {
                return '<tr class="tr-relatorio-click" data-tipo="cte" data-id="' + (x.id_cte || '') + '">' +
                    '<td>' + (x.numero || '-') + '</td><td>' + (x.serie || '-') + '</td>' +
                    '<td class="small text-truncate" style="max-width:120px">' + (x.chave || '-') + '</td>' +
                    '<td>' + (x.emissao ? x.emissao.slice(0, 10) : '-') + '</td><td>' + (x.empresa || '-') + '</td>' +
                    '<td class="text-truncate" style="max-width:140px">' + relatorioFmtFilialCelula(x) + '</td>' +
                    '<td class="text-center">' + relatorioFmtSapCelula(x) + '</td></tr>';
            }).join('');
            tbody.querySelectorAll('tr[data-id]').forEach(function (tr) {
                tr.addEventListener('click', function () { abrirDetalhe(tr.getAttribute('data-tipo'), tr.getAttribute('data-id')); });
            });
            relatorioAtualizarIndicadoresSort();
        })
        .catch(function () { tbody.innerHTML = '<tr><td colspan="7" class="text-center text-danger">Erro ao carregar</td></tr>'; relatorioAtualizarContador('cte', 0); relatorioRenderizarPaginacao(null); });
}

function relatorioCarregarNFSe() {
    var tbody = document.querySelector('#tabela-rel-nfse tbody');
    if (!tbody) return;
    tbody.innerHTML = '<tr><td colspan="6" class="text-center">Carregando...</td></tr>';
    var url = relatorioGetPrefix() + relatorioBuildUrl('/api/relatorio/nfse/', relatorioParams());
    fetch(url)
        .then(function (r) { return r.json(); })
        .then(function (data) {
            var items = data.items || [];
            var pag = { total: data.total || items.length, page: data.page || 1, page_size: data.page_size || 50, total_pages: data.total_pages || 1 };
            relatorioAtualizarContador('nfse', pag.total, pag);
            relatorioRenderizarPaginacao(pag);
            if (items.length === 0) {
                tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted">Nenhum registro</td></tr>';
                return;
            }
            tbody.innerHTML = items.map(function (x) {
                return '<tr class="tr-relatorio-click" data-tipo="nfse" data-id="' + (x.id_nfse || '') + '">' +
                    '<td>' + (x.numero || '-') + '</td>' +
                    '<td class="small text-truncate" style="max-width:120px">' + (x.chave || '-') + '</td>' +
                    '<td>' + (x.emissao ? x.emissao.slice(0, 10) : '-') + '</td><td>' + (x.empresa || '-') + '</td>' +
                    '<td class="text-truncate" style="max-width:140px">' + relatorioFmtFilialCelula(x) + '</td>' +
                    '<td class="text-center">' + relatorioFmtSapCelula(x) + '</td></tr>';
            }).join('');
            tbody.querySelectorAll('tr[data-id]').forEach(function (tr) {
                tr.addEventListener('click', function () { abrirDetalhe(tr.getAttribute('data-tipo'), tr.getAttribute('data-id')); });
            });
            relatorioAtualizarIndicadoresSort();
        })
        .catch(function () { tbody.innerHTML = '<tr><td colspan="6" class="text-center text-danger">Erro ao carregar</td></tr>'; relatorioAtualizarContador('nfse', 0); relatorioRenderizarPaginacao(null); });
}

function relatorioCarregarSped() {
    var tbody = document.querySelector('#tabela-rel-sped tbody');
    if (!tbody) return;
    tbody.innerHTML = '<tr><td colspan="5" class="text-center">Carregando...</td></tr>';
    fetch(relatorioGetPrefix() + relatorioBuildUrl('/api/relatorio/sped/', relatorioParams()))
        .then(function (r) { return r.json(); })
        .then(function (data) {
            var items = data.items || [];
            var pag = { total: data.total || items.length, page: data.page || 1, page_size: data.page_size || 50, total_pages: data.total_pages || 1 };
            relatorioAtualizarContador('sped', pag.total, pag);
            relatorioRenderizarPaginacao(pag);
            if (items.length === 0) {
                tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">Nenhum registro</td></tr>';
                return;
            }
            tbody.innerHTML = items.map(function (x) {
                return '<tr class="tr-relatorio-click" data-tipo="sped" data-id="' + (x.id_arquivo || '') + '" data-tipo-sped="' + (x.tipo || 'F') + '">' +
                    '<td>' + (x.tipo_display || x.tipo || '-') + '</td>' +
                    '<td>' + (x.competencia ? x.competencia.slice(0, 10) : '-') + '</td>' +
                    '<td class="text-truncate" style="max-width:200px">' + (x.nome_arquivo || '-') + '</td>' +
                    '<td>' + (x.data_carga ? x.data_carga.slice(0, 16) : '-') + '</td><td>' + (x.empresa || '-') + '</td></tr>';
            }).join('');
            tbody.querySelectorAll('tr[data-id]').forEach(function (tr) {
                var t = tr.getAttribute('data-tipo');
                var id = tr.getAttribute('data-id');
                var tipoSped = tr.getAttribute('data-tipo-sped');
                tr.addEventListener('click', function () { abrirDetalhe(t, id, tipoSped); });
            });
            relatorioAtualizarIndicadoresSort();
        })
        .catch(function () { tbody.innerHTML = '<tr><td colspan="5" class="text-center text-danger">Erro ao carregar</td></tr>'; relatorioAtualizarContador('sped', 0); relatorioRenderizarPaginacao(null); });
}

function relatorioAplicar(resetarPagina) {
    if (resetarPagina !== false) relatorioPaginaAtual = 1;
    var tab = document.querySelector('.tab-pane.active');
    if (!tab) return;
    if (tab.id === 'rel-nfe') relatorioCarregarNFe();
    else if (tab.id === 'rel-cte') relatorioCarregarCTe();
    else if (tab.id === 'rel-nfse') relatorioCarregarNFSe();
    else if (tab.id === 'rel-sped') relatorioCarregarSped();
}

document.addEventListener('DOMContentLoaded', function () {
    relatorioInicializarDatasMes();
    relatorioMostrarFiltrosTab();
    relatorioRegistrarSortHeaders();
    relatorioAtualizarIndicadoresSort();
    var empSel = document.getElementById('relatorio-empresa');
    if (empSel) {
        empSel.addEventListener('change', relatorioFiltrarFilialPorEmpresa);
        relatorioFiltrarFilialPorEmpresa();
    }
    var btnAplicar = document.getElementById('relatorio-btn-aplicar');
    if (btnAplicar) btnAplicar.addEventListener('click', relatorioAplicar);
    document.querySelectorAll('#tab-rel-nfe, #tab-rel-cte, #tab-rel-nfse, #tab-rel-sped').forEach(function (btn) {
        btn.addEventListener('shown.bs.tab', function () {
            relatorioMostrarFiltrosTab();
            relatorioAplicar();
        });
    });
});
