/* ===============================
   GERENCIAR REPROCESSAMENTO
================================ */

const estadoReprocessamento = {
    dados: [],
    dadosFiltrados: [],
    filtros: {
        dataInicio: '',
        dataFim: '',
        status: 'todos',
        empresa: '',
        busca: ''
    },
    currentPage: 1,
    itemsPerPage: 15,
    modalAberto: null
};

function reprocessamentoEsc(s) {
    const d = document.createElement('div');
    d.textContent = s == null ? '' : String(s);
    return d.innerHTML;
}

/* ===============================
   INICIALIZAR
================================ */
document.addEventListener('DOMContentLoaded', function () {
    carregarDadosReprocessamento();
    inicializarEventosFiltros();
    inicializarEventosTabela();
});

/* ===============================
   CARREGAR DADOS
================================ */
function apiUrl(path) {
    var prefix = (typeof getUrlPrefix === 'function') ? getUrlPrefix() : '';
    return (prefix || '') + (path.charAt(0) === '/' ? path : '/' + path);
}
function carregarDadosReprocessamento() {
    mostrarCarregando(true);

    fetch(apiUrl('api/reprocessamento/'), {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json'
        }
    })
        .then(response => response.json())
        .then(data => {
            estadoReprocessamento.dados = data.dados || [];
            aplicarFiltros();
            renderizarTabela();
            mostrarCarregando(false);
        })
        .catch(error => {
            console.error('Erro ao carregar:', error);
            Notificacoes.pagina('❌ Erro ao carregar dados', 'error');
            mostrarCarregando(false);
        });
}

/* ===============================
   EVENTOS DE FILTROS
================================ */
function inicializarEventosFiltros() {
    // Botão processar
    const btnProcessar = document.getElementById('btn-processar');
    if (btnProcessar) {
        btnProcessar.addEventListener('click', executarReprocessamento);
    }

    // Botão limpar
    const btnLimpar = document.getElementById('btn-limpar');
    if (btnLimpar) {
        btnLimpar.addEventListener('click', limparFiltros);
    }

    // Botão exportar
    const btnExportar = document.getElementById('btn-exportar');
    if (btnExportar) {
        btnExportar.addEventListener('click', exportarDados);
    }

    // Filtro de busca em tempo real
    const inputBusca = document.getElementById('filtro-busca');
    if (inputBusca) {
        inputBusca.addEventListener('keyup', function (e) {
            estadoReprocessamento.filtros.busca = e.target.value.toLowerCase();
            estadoReprocessamento.currentPage = 1;
            aplicarFiltros();
            renderizarTabela();
        });
    }

    // Filtro de data
    const dataInicio = document.getElementById('filtro-data-inicio');
    const dataFim = document.getElementById('filtro-data-fim');

    if (dataInicio) {
        dataInicio.addEventListener('change', function (e) {
            estadoReprocessamento.filtros.dataInicio = e.target.value;
            estadoReprocessamento.currentPage = 1;
            aplicarFiltros();
            renderizarTabela();
        });
    }

    if (dataFim) {
        dataFim.addEventListener('change', function (e) {
            estadoReprocessamento.filtros.dataFim = e.target.value;
            estadoReprocessamento.currentPage = 1;
            aplicarFiltros();
            renderizarTabela();
        });
    }

    // Filtro de status
    const selectStatus = document.getElementById('filtro-status');
    if (selectStatus) {
        selectStatus.addEventListener('change', function (e) {
            estadoReprocessamento.filtros.status = e.target.value;
            estadoReprocessamento.currentPage = 1;
            aplicarFiltros();
            renderizarTabela();
        });
    }

    // Filtro de empresa
    const selectEmpresa = document.getElementById('filtro-empresa');
    if (selectEmpresa) {
        selectEmpresa.addEventListener('change', function (e) {
            estadoReprocessamento.filtros.empresa = e.target.value;
            estadoReprocessamento.currentPage = 1;
            aplicarFiltros();
            renderizarTabela();
        });
    }
}

/* ===============================
   APLICAR FILTROS
================================ */
function aplicarFiltros() {
    let filtrados = estadoReprocessamento.dados.filter(item => {
        // Filtro de busca
        if (estadoReprocessamento.filtros.busca) {
            const busca = estadoReprocessamento.filtros.busca;
            const temBusca =
                (item.id && item.id.toString().includes(busca)) ||
                (item.numero && item.numero.toLowerCase().includes(busca)) ||
                (item.descricao && item.descricao.toLowerCase().includes(busca));

            if (!temBusca) return false;
        }

        // Filtro de status
        if (estadoReprocessamento.filtros.status !== 'todos' && item.status !== estadoReprocessamento.filtros.status) {
            return false;
        }

        // Filtro de empresa
        if (estadoReprocessamento.filtros.empresa && item.empresa_id !== estadoReprocessamento.filtros.empresa) {
            return false;
        }

        // Filtro de data
        if (estadoReprocessamento.filtros.dataInicio) {
            const dataItem = new Date(item.data_criacao);
            const dataFiltro = new Date(estadoReprocessamento.filtros.dataInicio);
            if (dataItem < dataFiltro) return false;
        }

        if (estadoReprocessamento.filtros.dataFim) {
            const dataItem = new Date(item.data_criacao);
            const dataFiltro = new Date(estadoReprocessamento.filtros.dataFim);
            dataFiltro.setDate(dataFiltro.getDate() + 1);
            if (dataItem > dataFiltro) return false;
        }

        return true;
    });

    estadoReprocessamento.dadosFiltrados = filtrados;
}

/* ===============================
   RENDERIZAR TABELA
================================ */
function renderizarTabela() {
    const tbody = document.querySelector('#tabela-reprocessamento tbody');
    if (!tbody) return;

    const inicio = (estadoReprocessamento.currentPage - 1) * estadoReprocessamento.itemsPerPage;
    const fim = inicio + estadoReprocessamento.itemsPerPage;
    const paginados = estadoReprocessamento.dadosFiltrados.slice(inicio, fim);

    tbody.innerHTML = '';

    if (paginados.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6" class="text-center text-muted" style="padding: 30px;">
                    <i class="fas fa-inbox" style="font-size: 24px; margin-bottom: 10px; display: block;"></i>
                    Nenhum registro encontrado
                </td>
            </tr>
        `;
        renderizarPaginacao(0);
        return;
    }

    paginados.forEach(item => {
        const statusBadge = obterBadgeStatus(item.status);
        const linha = document.createElement('tr');

        if (item.status === 'processando') {
            linha.classList.add('em-processamento');
        } else if (item.status === 'concluido') {
            linha.classList.add('processado');
        }

        linha.innerHTML = `
            <td><strong>#${reprocessamentoEsc(item.id)}</strong></td>
            <td>${reprocessamentoEsc(item.numero) || '—'}</td>
            <td>${reprocessamentoEsc(item.empresa) || '—'}</td>
            <td>${reprocessamentoEsc(formatarData(item.data_criacao))}</td>
            <td>${statusBadge}</td>
            <td>
                <div class="acoes-cell">
                    <button class="btn-acao btn-acao-detalhes" onclick="exibirDetalhes(${item.id})" title="Detalhes">
                        <i class="fas fa-eye"></i>
                    </button>
                    <button class="btn-acao btn-acao-reprocessar" onclick="reprocessarItem(${item.id})" title="Reprocessar">
                        <i class="fas fa-sync"></i>
                    </button>
                    <button class="btn-acao btn-acao-deletar" onclick="deletarItem(${item.id})" title="Deletar">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </td>
        `;

        tbody.appendChild(linha);
    });

    renderizarPaginacao(estadoReprocessamento.dadosFiltrados.length);
}

/* ===============================
   EVENTOS DA TABELA
================================ */
function inicializarEventosTabela() {
    // Seá vinculado ao clicar nos botões
}

/* ===============================
   REPROCESSAR ITEM
================================ */
function reprocessarItem(id) {
    if (!confirm('Deseja reprocessar este item?')) return;

    mostrarCarregando(true);

    fetch(apiUrl('api/reprocessamento/' + id + '/'), {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': obterCSRFToken()
        },
        body: JSON.stringify({ acao: 'reprocessar' })
    })
        .then(response => response.json())
        .then(data => {
            if (data.sucesso) {
                Notificacoes.pagina('✅ Item reprocessado com sucesso!', 'success');
                carregarDadosReprocessamento();
            } else {
                Notificacoes.pagina('❌ Erro ao reprocessar: ' + data.mensagem, 'error');
            }
            mostrarCarregando(false);
        })
        .catch(error => {
            console.error('Erro:', error);
            Notificacoes.pagina('❌ Erro ao reprocessar', 'error');
            mostrarCarregando(false);
        });
}

/* ===============================
   DELETAR ITEM
================================ */
function deletarItem(id) {
    if (!confirm('Tem certeza que deseja deletar este item? Esta ação não pode ser desfeita.')) return;

    mostrarCarregando(true);

    fetch(apiUrl('api/reprocessamento/' + id + '/'), {
        method: 'DELETE',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': obterCSRFToken()
        }
    })
        .then(response => response.json())
        .then(data => {
            if (data.sucesso) {
                Notificacoes.pagina('✅ Item deletado com sucesso!', 'success');
                carregarDadosReprocessamento();
            } else {
                Notificacoes.pagina('❌ Erro ao deletar: ' + data.mensagem, 'error');
            }
            mostrarCarregando(false);
        })
        .catch(error => {
            console.error('Erro:', error);
            Notificacoes.pagina('❌ Erro ao deletar', 'error');
            mostrarCarregando(false);
        });
}

/* ===============================
   EXIBIR DETALHES
================================ */
function exibirDetalhes(id) {
    const item = estadoReprocessamento.dados.find(d => d.id === id);

    if (!item) {
        Notificacoes.pagina('Item não encontrado', 'error');
        return;
    }

    const modal = document.getElementById('modal-detalhes');
    if (!modal) return;

    const conteudo = modal.querySelector('.modal-reprocessamento-content');

    conteudo.innerHTML = `
        <div class="modal-reprocessamento-header">
            <h5>Detalhes do Reprocessamento #${reprocessamentoEsc(item.id)}</h5>
            <button class="close-modal" onclick="fecharModal('modal-detalhes')">&times;</button>
        </div>
        <div class="modal-reprocessamento-body">
            <div class="detalhe-item">
                <label>ID:</label>
                <div class="detalhe-item-value">${reprocessamentoEsc(item.id)}</div>
            </div>
            <div class="detalhe-item">
                <label>Número:</label>
                <div class="detalhe-item-value">${reprocessamentoEsc(item.numero) || '—'}</div>
            </div>
            <div class="detalhe-item">
                <label>Empresa:</label>
                <div class="detalhe-item-value">${reprocessamentoEsc(item.empresa) || '—'}</div>
            </div>
            <div class="detalhe-item">
                <label>Status:</label>
                <div class="detalhe-item-value">${obterBadgeStatus(item.status)}</div>
            </div>
            <div class="detalhe-item">
                <label>Data Criação:</label>
                <div class="detalhe-item-value">${reprocessamentoEsc(formatarDataCompleta(item.data_criacao))}</div>
            </div>
            <div class="detalhe-item">
                <label>Descrição:</label>
                <div class="detalhe-item-value">${reprocessamentoEsc(item.descricao) || '—'}</div>
            </div>
        </div>
        <div style="text-align: right; gap: 10px; display: flex; justify-content: flex-end;">
            <button class="btn-acao btn-acao-reprocessar" onclick="reprocessarItem(${item.id})">
                <i class="fas fa-sync"></i> Reprocessar
            </button>
            <button class="btn-filtro btn-limpar" onclick="fecharModal('modal-detalhes')">
                Fechar
            </button>
        </div>
    `;

    modal.style.display = 'block';
    estadoReprocessamento.modalAberto = 'modal-detalhes';
}

/* ===============================
   FECHAR MODAL
================================ */
function fecharModal(id) {
    const modal = document.getElementById(id);
    if (modal) {
        modal.style.display = 'none';
        estadoReprocessamento.modalAberto = null;
    }
}

/* ===============================
   EXECUTAR REPROCESSAMENTO
================================ */
function executarReprocessamento() {
    if (estadoReprocessamento.dadosFiltrados.length === 0) {
        Notificacoes.pagina('⚠️ Nenhum item para reprocessar', 'warning');
        return;
    }

    if (!confirm(`Deseja reprocessar ${estadoReprocessamento.dadosFiltrados.length} item(ns)?`)) return;

    mostrarCarregando(true);

    const ids = estadoReprocessamento.dadosFiltrados.map(d => d.id);

    fetch(apiUrl('api/reprocessamento/batch/'), {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': obterCSRFToken()
        },
        body: JSON.stringify({ ids: ids, acao: 'reprocessar' })
    })
        .then(response => response.json())
        .then(data => {
            if (data.sucesso) {
                Notificacoes.pagina(`✅ ${data.processados} item(ns) reprocessado(s)!`, 'success');
                carregarDadosReprocessamento();
            } else {
                Notificacoes.pagina('❌ Erro ao reprocessar: ' + data.mensagem, 'error');
            }
            mostrarCarregando(false);
        })
        .catch(error => {
            console.error('Erro:', error);
            Notificacoes.pagina('❌ Erro ao reprocessar', 'error');
            mostrarCarregando(false);
        });
}

/* ===============================
   EXPORTAR DADOS
================================ */
function exportarDados() {
    if (estadoReprocessamento.dadosFiltrados.length === 0) {
        Notificacoes.pagina('⚠️ Nenhum dado para exportar', 'warning');
        return;
    }

    const dados = estadoReprocessamento.dadosFiltrados.map(item => ({
        ID: item.id,
        Número: item.numero,
        Empresa: item.empresa,
        'Data Criação': formatarData(item.data_criacao),
        Status: item.status,
        Descrição: item.descricao
    }));

    exportarCSV(dados, 'reprocessamento.csv');
    Notificacoes.pagina('✅ Dados exportados com sucesso!', 'success');
}

/* ===============================
   LIMPAR FILTROS
================================ */
function limparFiltros() {
    estadoReprocessamento.filtros = {
        dataInicio: '',
        dataFim: '',
        status: 'todos',
        empresa: '',
        busca: ''
    };

    // Limpar inputs
    document.getElementById('filtro-busca').value = '';
    document.getElementById('filtro-data-inicio').value = '';
    document.getElementById('filtro-data-fim').value = '';
    document.getElementById('filtro-status').value = 'todos';
    document.getElementById('filtro-empresa').value = '';

    estadoReprocessamento.currentPage = 1;
    aplicarFiltros();
    renderizarTabela();
}

/* ===============================
   RENDERIZAR PAGINAÇÃO
================================ */
function renderizarPaginacao(totalItems) {
    const container = document.getElementById('paginacao-reprocessamento');
    if (!container) return;

    const totalPages = Math.ceil(totalItems / estadoReprocessamento.itemsPerPage);
    container.innerHTML = '';

    if (totalPages <= 1) return;

    for (let i = 1; i <= totalPages; i++) {
        const link = document.createElement('button');
        link.className = 'page-link';
        if (i === estadoReprocessamento.currentPage) {
            link.classList.add('active');
        }
        link.textContent = i;
        link.onclick = () => {
            estadoReprocessamento.currentPage = i;
            renderizarTabela();
            window.scrollTo({ top: 0, behavior: 'smooth' });
        };
        container.appendChild(link);
    }
}

/* ===============================
   UTILITÁRIOS
================================ */
function obterBadgeStatus(status) {
    const badges = {
        pendente: '<span class="status-badge status-pending">⏳ Pendente</span>',
        processando: '<span class="status-badge status-processing"><span class="spinner-reprocessamento"></span> Processando</span>',
        concluido: '<span class="status-badge status-success">✓ Concluído</span>',
        erro: '<span class="status-badge status-error">✗ Erro</span>'
    };
    return badges[status] || '<span class="status-badge">' + status + '</span>';
}

function formatarData(data) {
    if (!data) return '-';
    const d = new Date(data);
    return d.toLocaleDateString('pt-BR');
}

function formatarDataCompleta(data) {
    if (!data) return '-';
    const d = new Date(data);
    return d.toLocaleDateString('pt-BR') + ' ' + d.toLocaleTimeString('pt-BR');
}

function obterCSRFToken() {
    return document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
}

function mostrarCarregando(mostrar) {
    // Implementar de acordo com seu sistema de loading
    console.log(mostrar ? 'Carregando...' : 'Carregamento completo');
}

function exportarCSV(dados, nome) {
    const headers = Object.keys(dados[0]);
    const csv = [
        headers.join(','),
        ...dados.map(row => headers.map(h => `"${row[h]}"`).join(','))
    ].join('\n');

    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);

    link.setAttribute('href', url);
    link.setAttribute('download', nome);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

// Fechar modal ao clicar fora
window.onclick = function (event) {
    const modal = document.getElementById('modal-detalhes');
    if (modal && event.target === modal) {
        fecharModal('modal-detalhes');
    }
};
