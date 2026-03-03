/* Relatório Fiscal - Filtro mês ao abrir, clique na linha abre modal com abas (cabeçalho, itens, pagamento/parcelas, etc.) */

function relatorioParams() {
    return {
        empresa_id: (document.getElementById('relatorio-empresa') && document.getElementById('relatorio-empresa').value.trim()) || '',
        data_inicio: (document.getElementById('relatorio-data-inicio') && document.getElementById('relatorio-data-inicio').value.trim()) || '',
        data_fim: (document.getElementById('relatorio-data-fim') && document.getElementById('relatorio-data-fim').value.trim()) || '',
        busca: (document.getElementById('relatorio-busca') && document.getElementById('relatorio-busca').value.trim()) || ''
    };
}

function relatorioBuildUrl(base, params) {
    var q = new URLSearchParams();
    if (params.empresa_id) q.set('empresa_id', params.empresa_id);
    if (params.data_inicio) q.set('data_inicio', params.data_inicio);
    if (params.data_fim) q.set('data_fim', params.data_fim);
    if (params.busca) q.set('busca', params.busca);
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

function objParaTabela(obj, skipKeys) {
    if (!obj || typeof obj !== 'object') return '<p class="text-muted">Sem dados</p>';
    skipKeys = skipKeys || [];
    var html = '<table class="table table-sm table-detalhe table-bordered"><tbody>';
    for (var k in obj) {
        if (skipKeys.indexOf(k) !== -1) continue;
        var v = obj[k];
        if (v === null || v === undefined || v === '') continue;
        if (typeof v === 'object' && v !== null && !(v instanceof Date)) continue;
        var disp = v;
        if (typeof v === 'string' && v.length > 80) disp = v.substring(0, 80) + '...';
        html += '<tr><th>' + k + '</th><td>' + escapeHtml(String(disp)) + '</td></tr>';
    }
    html += '</tbody></table>';
    return html;
}

function escapeHtml(s) {
    var div = document.createElement('div');
    div.textContent = s;
    return div.innerHTML;
}

function arrayParaTabela(arr, columns) {
    if (!arr || !arr.length) return '<p class="text-muted">Nenhum registro</p>';
    columns = columns || (arr[0] ? Object.keys(arr[0]) : []);
    var html = '<div class="table-responsive"><table class="table table-sm table-hover table-bordered"><thead><tr>';
    columns.forEach(function (c) { html += '<th>' + escapeHtml(c) + '</th>'; });
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

function preencherModalNFe(data, tabsContainer, tabContentContainer) {
    var cab = data.cabecalho || {};
    var tabs = [
        { id: 'cab', label: 'Cabeçalho', content: buildCabecalhoNFe(cab) },
        { id: 'itens', label: 'Itens', content: arrayParaTabela(data.itens, ['numero_item', 'descricao', 'ncm', 'cfop', 'quantidade', 'valor_unitario', 'valor_total', 'unidade']) },
        { id: 'pag', label: 'Pagamento e Parcelas', content: buildPagamentoParcelasNFe(data) },
        { id: 'transp', label: 'Transporte', content: objParaTabela(data.transporte) },
        { id: 'total', label: 'Totalização', content: objParaTabela(data.totalizacao) },
        { id: 'info', label: 'Informações Adicionais', content: objParaTabela(data.informacoes_adicionais) }
    ];
    renderTabs(tabs, tabsContainer, tabContentContainer);
}

function buildCabecalhoNFe(cab) {
    var h = '';
    if (cab.identificacao) h += '<h6>Identificação</h6>' + objParaTabela(cab.identificacao);
    if (cab.emitente) h += '<h6 class="mt-3">Emitente</h6>' + objParaTabela(cab.emitente);
    if (cab.emitente_endereco) h += '<h6 class="mt-2">Endereço Emitente</h6>' + objParaTabela(cab.emitente_endereco);
    if (cab.destinatario) h += '<h6 class="mt-3">Destinatário</h6>' + objParaTabela(cab.destinatario);
    if (cab.destinatario_endereco) h += '<h6 class="mt-2">Endereço Destinatário</h6>' + objParaTabela(cab.destinatario_endereco);
    if (cab.nfe) h += '<h6 class="mt-3">NFe (status/origem)</h6>' + objParaTabela(cab.nfe);
    return h || '<p class="text-muted">Sem dados</p>';
}

function buildPagamentoParcelasNFe(data) {
    var h = '';
    if (data.cobranca) h += '<h6>Cobrança (dados bancários)</h6>' + objParaTabela(data.cobranca);
    if (data.parcelas && data.parcelas.length) h += '<h6 class="mt-3">Parcelas</h6>' + arrayParaTabela(data.parcelas, ['numero_parcela', 'data_vencimento', 'valor_parcela', 'valor_desconto']);
    if (data.pagamento) h += '<h6 class="mt-3">Pagamento</h6>' + objParaTabela(data.pagamento);
    return h || '<p class="text-muted">Sem dados de pagamento/parcelas</p>';
}

function preencherModalCTe(data, tabsContainer, tabContentContainer) {
    var cab = data.cabecalho || {};
    var tabs = [
        { id: 'cab', label: 'Cabeçalho', content: buildCabecalhoCTe(cab) },
        { id: 'valor', label: 'Valor', content: objParaTabela(data.valor) },
        { id: 'transp', label: 'Transporte', content: objParaTabela(data.transporte) },
        { id: 'carga', label: 'Carga', content: objParaTabela(data.carga) },
        { id: 'servico', label: 'Serviço', content: objParaTabela(data.servico) },
        { id: 'veiculo', label: 'Veículo', content: objParaTabela(data.veiculo) },
        { id: 'motorista', label: 'Motorista', content: objParaTabela(data.motorista) },
        { id: 'percurso', label: 'Percurso', content: objParaTabela(data.percurso) },
        { id: 'fiscal', label: 'Fiscal', content: objParaTabela(data.fiscal) }
    ];
    renderTabs(tabs, tabsContainer, tabContentContainer);
}

function buildCabecalhoCTe(cab) {
    var h = '';
    if (cab.identificacao) h += '<h6>Identificação</h6>' + objParaTabela(cab.identificacao);
    if (cab.emitente) h += '<h6 class="mt-3">Emitente</h6>' + objParaTabela(cab.emitente);
    if (cab.destinatario) h += '<h6 class="mt-3">Destinatário</h6>' + objParaTabela(cab.destinatario);
    if (cab.cte) h += '<h6 class="mt-3">CTe</h6>' + objParaTabela(cab.cte);
    return h || '<p class="text-muted">Sem dados</p>';
}

function preencherModalNFSe(data, tabsContainer, tabContentContainer) {
    var cab = data.cabecalho || {};
    var tabs = [
        { id: 'cab', label: 'Cabeçalho', content: buildCabecalhoNFSe(cab) },
        { id: 'servicos', label: 'Serviços', content: arrayParaTabela(data.servicos, ['descricao', 'quantidade', 'valor_unitario', 'valor_total', 'codigo_servico', 'aliquota_issqn']) },
        { id: 'rps', label: 'RPS', content: arrayParaTabela(data.rps, ['numero_rps', 'serie_rps', 'valor_rps', 'status_rps', 'data_emissao_rps']) },
        { id: 'retencao', label: 'Retenção', content: objParaTabela(data.retencao) },
        { id: 'pagamento', label: 'Pagamento', content: objParaTabela(data.pagamento) }
    ];
    renderTabs(tabs, tabsContainer, tabContentContainer);
}

function buildCabecalhoNFSe(cab) {
    var h = '';
    if (cab.identificacao) h += '<h6>Identificação</h6>' + objParaTabela(cab.identificacao);
    if (cab.prestador) h += '<h6 class="mt-3">Prestador</h6>' + objParaTabela(cab.prestador);
    if (cab.tomador) h += '<h6 class="mt-3">Tomador</h6>' + objParaTabela(cab.tomador);
    if (cab.nfse) h += '<h6 class="mt-3">NFSe</h6>' + objParaTabela(cab.nfse);
    return h || '<p class="text-muted">Sem dados</p>';
}

function preencherModalSped(data, tabsContainer, tabContentContainer) {
    var tabs = [
        { id: 'cab', label: 'Cabeçalho', content: objParaTabela(data.cabecalho) },
        { id: 'fiscal', label: 'Registros Fiscal', content: arrayParaTabela(data.registros_fiscal, ['bloco', 'registro', 'linha', 'conteudo']) },
        { id: 'contrib', label: 'Registros Contribuição', content: arrayParaTabela(data.registros_contribuicao, ['bloco', 'registro', 'linha', 'conteudo']) }
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

function relatorioCarregarNFe() {
    var tbody = document.querySelector('#tabela-rel-nfe tbody');
    if (!tbody) return;
    tbody.innerHTML = '<tr><td colspan="8" class="text-center">Carregando...</td></tr>';
    var url = relatorioBuildUrl('/api/relatorio/nfe/', relatorioParams());
    fetch(url)
        .then(function (r) { return r.json(); })
        .then(function (data) {
            var items = data.items || [];
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
        .catch(function () { tbody.innerHTML = '<tr><td colspan="8" class="text-center text-danger">Erro ao carregar</td></tr>'; });
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
        .catch(function () { tbody.innerHTML = '<tr><td colspan="5" class="text-center text-danger">Erro ao carregar</td></tr>'; });
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
        .catch(function () { tbody.innerHTML = '<tr><td colspan="4" class="text-center text-danger">Erro ao carregar</td></tr>'; });
}

function relatorioCarregarSped() {
    var tbody = document.querySelector('#tabela-rel-sped tbody');
    if (!tbody) return;
    tbody.innerHTML = '<tr><td colspan="5" class="text-center">Carregando...</td></tr>';
    fetch(relatorioBuildUrl('/api/relatorio/sped/', relatorioParams()))
        .then(function (r) { return r.json(); })
        .then(function (data) {
            var items = data.items || [];
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
        .catch(function () { tbody.innerHTML = '<tr><td colspan="5" class="text-center text-danger">Erro ao carregar</td></tr>'; });
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
