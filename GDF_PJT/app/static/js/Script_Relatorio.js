/* Relatório Fiscal - Filtro mês ao abrir, clique na linha abre modal com abas (cabeçalho, itens, pagamento/parcelas, etc.) */

function relatorioParams() {
    return {
        empresa_id: (document.getElementById('relatorio-empresa') && document.getElementById('relatorio-empresa').value.trim()) || '',
        data_inicio: (document.getElementById('relatorio-data-inicio') && document.getElementById('relatorio-data-inicio').value.trim()) || '',
        data_fim: (document.getElementById('relatorio-data-fim') && document.getElementById('relatorio-data-fim').value.trim()) || '',
        busca: (document.getElementById('relatorio-busca') && document.getElementById('relatorio-busca').value.trim()) || '',
        parcelas: (document.getElementById('relatorio-parcelas') && document.getElementById('relatorio-parcelas').value.trim()) || '',
        tipo_operacao: (document.getElementById('relatorio-tipo-operacao') && document.getElementById('relatorio-tipo-operacao').value.trim()) || '',
        tipo_pagamento: (document.getElementById('relatorio-tipo-pagamento') && document.getElementById('relatorio-tipo-pagamento').value.trim()) || ''
    };
}

function relatorioBuildUrl(base, params) {
    var q = new URLSearchParams();
    if (params.empresa_id) q.set('empresa_id', params.empresa_id);
    if (params.data_inicio) q.set('data_inicio', params.data_inicio);
    if (params.data_fim) q.set('data_fim', params.data_fim);
    if (params.busca) q.set('busca', params.busca);
    if (params.parcelas) q.set('parcelas', params.parcelas);
    if (params.tipo_operacao) q.set('tipo_operacao', params.tipo_operacao);
    if (params.tipo_pagamento) q.set('tipo_pagamento', params.tipo_pagamento);
    var s = q.toString();
    return s ? base + '?' + s : base;
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
    pix_tipo_chave_desc: 'PIX tipo de chave', pix_tipo_chave: 'PIX tipo (cód.)', pix_chave: 'Chave PIX'
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

function arrayParaTabela(arr, columns) {
    if (!arr || !arr.length) return '<p class="text-muted">Nenhum registro</p>';
    var allKeys = arr[0] ? Object.keys(arr[0]) : [];
    columns = columns || allKeys;
    columns = columns.filter(function (c) { return !isChaveCampo(c); });
    if (!columns.length) columns = allKeys.filter(function (c) { return !isChaveCampo(c); });
    var html = '<div class="table-responsive"><table class="table table-sm table-detalhe table-hover table-bordered"><thead><tr>';
    columns.forEach(function (c) { html += '<th>' + escapeHtml(labelCampo(c)) + '</th>'; });
    html += '</thead><tbody>';
    arr.forEach(function (row) {
        html += '<tr>';
        columns.forEach(function (col) {
            var val = row[col];
            if (val !== null && val !== undefined && typeof val === 'object' && typeof val.toISOString === 'function') val = val.toISOString ? val.toISOString().slice(0, 10) : String(val);
            else if (val !== null && val !== undefined && typeof val === 'number' && val % 1 !== 0) val = Number(val).toFixed(2);
            html += '<td>' + escapeHtml(val !== undefined && val !== null ? String(val) : '') + '</td>';
        });
        html += '</tr>';
    });
    html += '</tbody></table></div>';
    return html;
}

function abrirDetalhe(tipo, id) {
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

    var url = '/api/relatorio/' + tipo.toLowerCase() + '/' + id + '/';
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
    if (cab.identificacao) h += '<div class="relatorio-bloco"><h6>Identificação</h6>' + objParaTabela(cab.identificacao, [], 'relatorio-cab') + '</div>';
    if (cab.emitente) h += '<div class="relatorio-bloco"><h6>Emitente</h6>' + objParaTabela(cab.emitente, [], 'relatorio-cab') + '</div>';
    if (cab.emitente_endereco) h += '<div class="relatorio-bloco"><h6>Endereço do emitente</h6>' + objParaTabela(cab.emitente_endereco, [], 'relatorio-cab') + '</div>';
    if (cab.destinatario) h += '<div class="relatorio-bloco"><h6>Destinatário</h6>' + objParaTabela(cab.destinatario, [], 'relatorio-cab') + '</div>';
    if (cab.destinatario_endereco) h += '<div class="relatorio-bloco"><h6>Endereço do destinatário</h6>' + objParaTabela(cab.destinatario_endereco, [], 'relatorio-cab') + '</div>';
    if (cab.nfe) h += '<div class="relatorio-bloco"><h6>NFe (status / origem)</h6>' + objParaTabela(cab.nfe, [], 'relatorio-cab') + '</div>';
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
    if (cab.identificacao) h += '<div class="relatorio-bloco"><h6>Identificação</h6>' + objParaTabela(cab.identificacao, [], 'relatorio-cab') + '</div>';
    if (cab.emitente) h += '<div class="relatorio-bloco"><h6>Emitente</h6>' + objParaTabela(cab.emitente, [], 'relatorio-cab') + '</div>';
    if (cab.destinatario) h += '<div class="relatorio-bloco"><h6>Destinatário</h6>' + objParaTabela(cab.destinatario, [], 'relatorio-cab') + '</div>';
    if (cab.cte) h += '<div class="relatorio-bloco"><h6>CTe</h6>' + objParaTabela(cab.cte, [], 'relatorio-cab') + '</div>';
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
    if (cab.identificacao) h += '<div class="relatorio-bloco"><h6>Identificação</h6>' + objParaTabela(cab.identificacao, [], 'relatorio-cab') + '</div>';
    if (cab.prestador) h += '<div class="relatorio-bloco"><h6>Prestador</h6>' + objParaTabela(cab.prestador, [], 'relatorio-cab') + '</div>';
    if (cab.tomador) h += '<div class="relatorio-bloco"><h6>Tomador</h6>' + objParaTabela(cab.tomador, [], 'relatorio-cab') + '</div>';
    if (cab.nfse) h += '<div class="relatorio-bloco"><h6>NFSe</h6>' + objParaTabela(cab.nfse, [], 'relatorio-cab') + '</div>';
    return h || '<p class="text-muted">Sem dados</p>';
}

function preencherModalSped(data, tabsContainer, tabContentContainer) {
    var tabs = [
        { id: 'cab', label: 'Cabeçalho', content: wrapBloco(objParaTabela(data.cabecalho, [], 'relatorio-cab')) },
        { id: 'fiscal', label: 'Registros Fiscal', content: wrapBloco(arrayParaTabela(data.registros_fiscal, ['bloco', 'registro', 'linha', 'conteudo'])) },
        { id: 'contrib', label: 'Registros Contribuição', content: wrapBloco(arrayParaTabela(data.registros_contribuicao, ['bloco', 'registro', 'linha', 'conteudo'])) }
    ];
    renderTabs(tabs, tabsContainer, tabContentContainer);
}

function renderTabs(tabs, tabsContainer, tabContentContainer) {
    tabs.forEach(function (t, i) {
        var active = i === 0 ? ' active' : '';
        var show = i === 0 ? ' show active' : '';
        tabsContainer.innerHTML += '<li class="nav-item"><button class="nav-link' + active + '" data-bs-toggle="tab" data-bs-target="#modal-tab-' + t.id + '" type="button">' + escapeHtml(t.label) + '</button></li>';
        tabContentContainer.innerHTML += '<div class="tab-pane fade' + show + '" id="modal-tab-' + t.id + '" role="tabpanel">' + t.content + '</div>';
    });
}

function relatorioAtualizarContador(tipo, total) {
    var el = document.getElementById('relatorio-contador-num');
    if (!el) return;
    var label = tipo === 'sped' ? 'arquivo(s)' : 'nota(s)';
    if (total === 0) {
        el.textContent = 'Nenhuma ' + label + ' exibida';
    } else {
        el.textContent = total + ' ' + label + ' exibida' + (total === 1 ? '' : 's');
    }
}

function relatorioCarregarNFe() {
    var tbody = document.querySelector('#tabela-rel-nfe tbody');
    if (!tbody) return;
    tbody.innerHTML = '<tr><td colspan="8" class="text-center">Carregando...</td></tr>';
    var url = relatorioBuildUrl('/api/relatorio/nfe/', relatorioParams());
    fetch(url)
        .then(function (r) { return r.json(); })
        .then(function (data) {
            var items = data.items || [];
            relatorioAtualizarContador('nfe', items.length);
            if (items.length === 0) {
                tbody.innerHTML = '<tr><td colspan="8" class="text-center text-muted">Nenhum registro</td></tr>';
                return;
            }
            tbody.innerHTML = items.map(function (x) {
                return '<tr class="tr-relatorio-click" data-tipo="nfe" data-id="' + (x.id_nfe || '') + '">' +
                    '<td>' + (x.numero || '-') + '</td><td>' + (x.serie || '-') + '</td>' +
                    '<td class="small text-truncate" style="max-width:120px" title="' + (x.chave || '').replace(/"/g, '&quot;') + '">' + (x.chave || '-') + '</td>' +
                    '<td>' + (x.emissao ? x.emissao.slice(0, 10) : '-') + '</td>' +
                    '<td>' + (x.tipo_operacao === '1' ? 'Saída' : 'Entrada') + '</td><td>' + (x.status || '-') + '</td>' +
                    '<td>' + (x.empresa || '-') + '</td>' +
                    '<td class="text-truncate" style="max-width:150px" title="' + (x.natureza || '').replace(/"/g, '&quot;') + '">' + (x.natureza || '-') + '</td></tr>';
            }).join('');
            tbody.querySelectorAll('tr[data-id]').forEach(function (tr) {
                tr.addEventListener('click', function () { abrirDetalhe(tr.getAttribute('data-tipo'), tr.getAttribute('data-id')); });
            });
        })
        .catch(function () { tbody.innerHTML = '<tr><td colspan="8" class="text-center text-danger">Erro ao carregar</td></tr>'; relatorioAtualizarContador('nfe', 0); });
}

function relatorioCarregarCTe() {
    var tbody = document.querySelector('#tabela-rel-cte tbody');
    if (!tbody) return;
    tbody.innerHTML = '<tr><td colspan="5" class="text-center">Carregando...</td></tr>';
    var url = relatorioBuildUrl('/api/relatorio/cte/', relatorioParams());
    fetch(url)
        .then(function (r) { return r.json(); })
        .then(function (data) {
            var items = data.items || [];
            relatorioAtualizarContador('cte', items.length);
            if (items.length === 0) {
                tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">Nenhum registro</td></tr>';
                return;
            }
            tbody.innerHTML = items.map(function (x) {
                return '<tr class="tr-relatorio-click" data-tipo="cte" data-id="' + (x.id_cte || '') + '">' +
                    '<td>' + (x.numero || '-') + '</td><td>' + (x.serie || '-') + '</td>' +
                    '<td class="small text-truncate" style="max-width:120px">' + (x.chave || '-') + '</td>' +
                    '<td>' + (x.emissao ? x.emissao.slice(0, 10) : '-') + '</td><td>' + (x.empresa || '-') + '</td></tr>';
            }).join('');
            tbody.querySelectorAll('tr[data-id]').forEach(function (tr) {
                tr.addEventListener('click', function () { abrirDetalhe(tr.getAttribute('data-tipo'), tr.getAttribute('data-id')); });
            });
        })
        .catch(function () { tbody.innerHTML = '<tr><td colspan="5" class="text-center text-danger">Erro ao carregar</td></tr>'; relatorioAtualizarContador('cte', 0); });
}

function relatorioCarregarNFSe() {
    var tbody = document.querySelector('#tabela-rel-nfse tbody');
    if (!tbody) return;
    tbody.innerHTML = '<tr><td colspan="4" class="text-center">Carregando...</td></tr>';
    var url = relatorioBuildUrl('/api/relatorio/nfse/', relatorioParams());
    fetch(url)
        .then(function (r) { return r.json(); })
        .then(function (data) {
            var items = data.items || [];
            relatorioAtualizarContador('nfse', items.length);
            if (items.length === 0) {
                tbody.innerHTML = '<tr><td colspan="4" class="text-center text-muted">Nenhum registro</td></tr>';
                return;
            }
            tbody.innerHTML = items.map(function (x) {
                return '<tr class="tr-relatorio-click" data-tipo="nfse" data-id="' + (x.id_nfse || '') + '">' +
                    '<td>' + (x.numero || '-') + '</td>' +
                    '<td class="small text-truncate" style="max-width:120px">' + (x.chave || '-') + '</td>' +
                    '<td>' + (x.emissao ? x.emissao.slice(0, 10) : '-') + '</td><td>' + (x.empresa || '-') + '</td></tr>';
            }).join('');
            tbody.querySelectorAll('tr[data-id]').forEach(function (tr) {
                tr.addEventListener('click', function () { abrirDetalhe(tr.getAttribute('data-tipo'), tr.getAttribute('data-id')); });
            });
        })
        .catch(function () { tbody.innerHTML = '<tr><td colspan="4" class="text-center text-danger">Erro ao carregar</td></tr>'; relatorioAtualizarContador('nfse', 0); });
}

function relatorioCarregarSped() {
    var tbody = document.querySelector('#tabela-rel-sped tbody');
    if (!tbody) return;
    tbody.innerHTML = '<tr><td colspan="5" class="text-center">Carregando...</td></tr>';
    fetch(relatorioBuildUrl('/api/relatorio/sped/', relatorioParams()))
        .then(function (r) { return r.json(); })
        .then(function (data) {
            var items = data.items || [];
            relatorioAtualizarContador('sped', items.length);
            if (items.length === 0) {
                tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">Nenhum registro</td></tr>';
                return;
            }
            tbody.innerHTML = items.map(function (x) {
                return '<tr class="tr-relatorio-click" data-tipo="sped" data-id="' + (x.id_arquivo || '') + '">' +
                    '<td>' + (x.tipo_display || x.tipo || '-') + '</td>' +
                    '<td>' + (x.competencia ? x.competencia.slice(0, 10) : '-') + '</td>' +
                    '<td class="text-truncate" style="max-width:200px">' + (x.nome_arquivo || '-') + '</td>' +
                    '<td>' + (x.data_carga ? x.data_carga.slice(0, 16) : '-') + '</td><td>' + (x.empresa || '-') + '</td></tr>';
            }).join('');
            tbody.querySelectorAll('tr[data-id]').forEach(function (tr) {
                tr.addEventListener('click', function () { abrirDetalhe(tr.getAttribute('data-tipo'), tr.getAttribute('data-id')); });
            });
        })
        .catch(function () { tbody.innerHTML = '<tr><td colspan="5" class="text-center text-danger">Erro ao carregar</td></tr>'; relatorioAtualizarContador('sped', 0); });
}

function relatorioAplicar() {
    var tab = document.querySelector('.tab-pane.active');
    if (!tab) return;
    if (tab.id === 'rel-nfe') relatorioCarregarNFe();
    else if (tab.id === 'rel-cte') relatorioCarregarCTe();
    else if (tab.id === 'rel-nfse') relatorioCarregarNFSe();
    else if (tab.id === 'rel-sped') relatorioCarregarSped();
}

document.addEventListener('DOMContentLoaded', function () {
    relatorioInicializarDatasMes();
    document.getElementById('relatorio-btn-aplicar').addEventListener('click', relatorioAplicar);
    document.querySelectorAll('#tab-rel-nfe, #tab-rel-cte, #tab-rel-nfse, #tab-rel-sped').forEach(function (btn) {
        btn.addEventListener('shown.bs.tab', function () { relatorioAplicar(); });
    });
});
