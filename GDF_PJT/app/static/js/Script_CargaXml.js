/* ===============================
   GERENCIAR CARGA XML
================================ */

const estadoCargaXml = {
    arquivos: [],
    uploadEmProgresso: false,
    totalArquivos: 0,
    uploadosRealizados: 0,
    todasCargas: [],
    cargasFiltradas: [],
    filtros: {
        busca: '',
        tipos: ['Automático', 'Manual']
    },
    currentPage: 1,
    itemsPerPage: 10,
    modoDiretorio: false,
    nomePasta: ''
};

// Estado para a tabela principal de parâmetros
const estadoParametros = {
    todos: [],
    filtrados: [],
    filtros: {
        busca: '',
        mostrarAtivos: true,
        mostrarInativos: true,
    },
    currentPage: 1,
    itemsPerPage: 10,
};

/* ===============================
   INICIALIZAR ELEMENTOS
================================ */
var intervaloResumoCargaXml = null;

document.addEventListener('DOMContentLoaded', function () {
    // Tabela principal: parâmetros + filtros ativo/inativo
    carregarParametrosPrincipais();
    inicializarEventosFiltroParametrosPrincipais();
    inicializarEventosParametros();
    carregarParametrosAtivos();
    inicializarDragDropInputFiles();
    inicializarEventosJobsRenderizados();
    carregarAvisosCargaXml();
    carregarResumoCargaXml();
    carregarTodasAsCargas();

    var btnAtualizarResumo = document.getElementById('btn-atualizar-resumo-cargaxml');
    if (btnAtualizarResumo) btnAtualizarResumo.addEventListener('click', function () {
        carregarResumoCargaXml();
        carregarTodasAsCargas();
    });

    // Modal Avisos: ao abrir, recarrega lista de logs
    const modalAvisos = document.getElementById('modalAvisosCargaXml');
    if (modalAvisos) {
        modalAvisos.addEventListener('show.bs.modal', function () {
            carregarAvisosCargaXml(true);
        });
    }

    // a aba automática carrega parâmetros sempre que for mostrada
    const tabAutomatico = document.getElementById('tab-automatico');
    if (tabAutomatico) {
        tabAutomatico.addEventListener('shown.bs.tab', function () {
            carregarParametrosAtivos();
        });
    }

    // Limpar alertas ao abrir cada modal (erros/avisos exibidos dentro do modal)
    ['modalCargaXml', 'modalUploadZip', 'modalParametroDetails'].forEach(function (modalId) {
        var el = document.getElementById(modalId);
        if (el) {
            el.addEventListener('show.bs.modal', function () {
                var alertsId = modalId + 'Alerts';
                if (typeof Notificacoes !== 'undefined') Notificacoes.limparModal(alertsId);
            });
        }
    });
});

function obterCsrfToken() {
    const token = document.querySelector('[name=csrfmiddlewaretoken]');
    return token ? token.value : '';
}

/** Prefixo da aplicação (ex: '' ou '/gdf') para chamadas à API quando o app está em subpath. */
function getApiBase() {
    var el = document.querySelector('.layout-page[data-url-prefix], [data-url-prefix]');
    var prefix = (el && el.getAttribute('data-url-prefix')) || '';
    if (!prefix && typeof getUrlPrefix === 'function') prefix = getUrlPrefix();
    return prefix || '';
}

/* ===============================
   RESUMO DOS JOBS (Total, Concluídos, Com erros, Em andamento)
================================ */
function carregarResumoCargaXml() {
    fetch(getApiBase() + '/api/cargaxml/resumo/', { method: 'GET', headers: { 'X-CSRFToken': obterCsrfToken() } })
        .then(function (r) { return r.json(); })
        .then(function (data) {
            if (!data.sucesso) return;
            var elTotal = document.getElementById('resumo-cargaxml-total');
            var elConcluidos = document.getElementById('resumo-cargaxml-concluidos');
            var elErros = document.getElementById('resumo-cargaxml-com-erros');
            var elAndamento = document.getElementById('resumo-cargaxml-em-andamento');
            if (elTotal) elTotal.textContent = data.total || 0;
            if (elConcluidos) elConcluidos.textContent = data.concluidos || 0;
            if (elErros) elErros.textContent = data.com_erros || 0;
            if (elAndamento) elAndamento.textContent = data.em_andamento || 0;
            if (data.em_andamento > 0 && !intervaloResumoCargaXml) {
                intervaloResumoCargaXml = setInterval(function () {
                    carregarResumoCargaXml();
                    carregarTodasAsCargas();
                }, 3000);
            } else if (data.em_andamento === 0 && intervaloResumoCargaXml) {
                clearInterval(intervaloResumoCargaXml);
                intervaloResumoCargaXml = null;
            }
        })
        .catch(function () {});
}

/* ===============================
   AVISOS – LOGS DE CARGAS COM ERROS
================================ */
function carregarAvisosCargaXml(preencherModal) {
    fetch(getApiBase() + '/api/cargaxml/avisos/', {
        method: 'GET',
        headers: { 'X-CSRFToken': obterCsrfToken() },
    })
        .then(function (r) { return r.json(); })
        .then(function (data) {
            var total = (data.sucesso && data.total_erros) ? data.total_erros : 0;
            var badge = document.getElementById('avisos-badge-cargaxml');
            if (badge) {
                if (total > 0) {
                    badge.textContent = total > 99 ? '99+' : total;
                    badge.style.display = 'inline-block';
                } else {
                    badge.style.display = 'none';
                }
            }
            if (preencherModal) {
                preencherModalAvisosCargaXml(data.items || []);
            }
            if (data.items && data.items.length > 0) {
                renderizarLogsResumo(data.items);
            } else {
                renderizarLogsResumo([]);
            }
        })
        .catch(function () {
            var badge = document.getElementById('avisos-badge-cargaxml');
            if (badge) badge.style.display = 'none';
        });
}

function preencherModalAvisosCargaXml(items) {
    var emptyEl = document.getElementById('modal-avisos-cargaxml-empty');
    var listEl = document.getElementById('modal-avisos-cargaxml-list');
    if (!emptyEl || !listEl) return;
    if (items.length === 0) {
        emptyEl.style.display = 'block';
        listEl.style.display = 'none';
        listEl.innerHTML = '';
        return;
    }
    emptyEl.style.display = 'none';
    listEl.style.display = 'block';
    function formatDt(iso) {
        if (!iso) return '-';
        try {
            var d = new Date(iso);
            return d.toLocaleString('pt-BR', { dateStyle: 'short', timeStyle: 'short' });
        } catch (e) { return iso; }
    }
    function escapeHtml(s) {
        return (s || '').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    }
    function classForLogLine(line) {
        var t = (line || '').trim();
        if (t.indexOf('ERRO:') === 0) return 'aviso-log-erro';
        if (t.indexOf('PENDENTES') === 0) return 'aviso-log-pendente';
        if (t.indexOf('OK:') === 0) return 'aviso-log-ok';
        return 'aviso-log-outro';
    }
    function ordemPrioridadeLog(line) {
        var t = (line || '').trim();
        if (t.indexOf('ERRO:') === 0) return 0;
        if (t.indexOf('PENDENTES') === 0) return 1;
        if (t.indexOf('OK:') === 0) return 2;
        return 3;
    }
    var html = '';
    items.forEach(function (job) {
        var totalErro = job.total_erro || 0;
        var totalOk = job.total_sucesso || 0;
        var logLines = (job.log && job.log.length) ? job.log.slice() : [];
        if (logLines.length) {
            logLines.sort(function (a, b) {
                var pa = ordemPrioridadeLog(a);
                var pb = ordemPrioridadeLog(b);
                return pa - pb;
            });
            // Nos detalhes do aviso mostrar só erros e pendentes (não mostrar OK)
            logLines = logLines.filter(function (l) {
                var t = (l || '').trim();
                return t.indexOf('OK:') !== 0;
            });
        }
        var logHtml = '';
        if (logLines.length) {
            logHtml = '<div class="aviso-dados-adicionais">';
            logHtml += '<div class="aviso-dados-titulo small fw-600 text-uppercase text-muted mb-2">Erros e pendentes</div>';
            logHtml += '<div class="aviso-log-lines">';
            logLines.forEach(function (l) {
                var cssClass = classForLogLine(l);
                logHtml += '<div class="aviso-log-line ' + cssClass + '">' + escapeHtml(l) + '</div>';
            });
            logHtml += '</div></div>';
        } else {
            logHtml = '<div class="aviso-dados-adicionais"><div class="text-muted small">Sem log</div></div>';
        }
        html += '<div class="aviso-item layout-subcard">';
        html += '  <div class="aviso-item-header d-flex justify-content-between align-items-center" role="button" tabindex="0">';
        html += '    <span class="aviso-item-info"><strong>Job #' + job.id + '</strong> &middot; ' + formatDt(job.started_at) + ' <span class="text-muted small ms-1">(clique para detalhes)</span></span>';
        html += '    <span class="d-flex align-items-center gap-2">';
        if (totalOk > 0) html += '<span class="badge aviso-badge-ok">' + totalOk + ' OK</span>';
        html += '<span class="badge aviso-badge-erro">' + totalErro + ' erro(s)</span> <i class="fas fa-chevron-right aviso-chevron small"></i></span>';
        html += '  </div>';
        html += '  <div class="aviso-item-body d-none">' + logHtml + '</div>';
        html += '</div>';
    });
    listEl.innerHTML = html;
    listEl.querySelectorAll('.aviso-item-header').forEach(function (header) {
        header.addEventListener('click', function () {
            var card = header.closest('.aviso-item');
            var body = card.querySelector('.aviso-item-body');
            var chevron = header.querySelector('.aviso-chevron');
            body.classList.toggle('d-none');
            chevron.classList.toggle('fa-chevron-right');
            chevron.classList.toggle('fa-chevron-down');
        });
        header.addEventListener('keydown', function (e) {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                header.click();
            }
        });
    });
}

/* ===============================
   INICIALIZAR DRAG & DROP E INPUT FILES
================================ */
function inicializarDragDropInputFiles() {
    var dropZoneArquivo = document.getElementById('drop-zone-xml-arquivo');
    var dropZonePasta = document.getElementById('drop-zone-xml-pasta');
    var fileInputArquivo = document.getElementById('file-input-xml');
    var fileInputPasta = document.getElementById('file-input-diretorio');

    if (dropZoneArquivo && fileInputArquivo) {
        dropZoneArquivo.addEventListener('click', function () { fileInputArquivo.value = ''; fileInputArquivo.click(); });
        dropZoneArquivo.addEventListener('keydown', function (e) { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); fileInputArquivo.click(); } });
    }
    if (dropZonePasta && fileInputPasta) {
        dropZonePasta.addEventListener('click', function () { fileInputPasta.value = ''; fileInputPasta.click(); });
        dropZonePasta.addEventListener('keydown', function (e) { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); fileInputPasta.click(); } });
    }
    if (fileInputArquivo) {
        fileInputArquivo.addEventListener('change', function () {
            if (this.files && this.files.length > 0) {
                estadoCargaXml.modoDiretorio = false;
                estadoCargaXml.nomePasta = '';
                processarArquivos(this.files);
            }
        });
    }
    if (fileInputPasta) {
        fileInputPasta.addEventListener('change', function () {
            if (this.files && this.files.length > 0) {
                estadoCargaXml.modoDiretorio = true;
                estadoCargaXml.nomePasta = extrairNomePasta(this.files);
                processarArquivos(this.files);
            }
            this.value = '';
        });
    }

    const btnEnviar = document.getElementById('btn-enviar-xml');
    if (btnEnviar) {
        btnEnviar.addEventListener('click', function () { iniciarUpload(); });
    }
}

/* ===============================
   INICIALIZAR EVENTOS DOS JOBS RENDERIZADOS
================================ */
function inicializarEventosJobsRenderizados() {
    // Adicionar listeners aos jobs renderizados pelo Django
    const jobRows = document.querySelectorAll('.job-row');
    jobRows.forEach(row => {
        const jobId = row.getAttribute('data-job-id');
        if (jobId) {
            row.addEventListener('click', function() {
                abrirModalJob(jobId);
            });
        }
    });
}

/* ===============================
   PARÂMETROS - TABELA PRINCIPAL
================================ */

function carregarParametrosPrincipais() {
    const tbody = document.querySelector('#tabela-parametros-main tbody');
    if (!tbody) return;

    fetch(getApiBase() + '/api/cargaxml/parametros/')
        .then(response => response.json())
        .then(data => {
            const items = data.items || [];
            if (!data.sucesso || items.length === 0) {
                estadoParametros.todos = [];
                estadoParametros.filtrados = [];
                renderizarTabelaParametrosPrincipais();
                return;
            }

            estadoParametros.todos = items.map(item => ({
                id: item.id,
                horario: item.horario || '',
                origem_dados: item.origem_dados || '',
                diretorio: item.diretorio || '',
                empresa_id: item.empresa_id || '',
                empresa_nome: item.empresa_nome || '',
                ativo: !!item.ativo,
            }));

            aplicarFiltrosParametrosPrincipais();
            renderizarTabelaParametrosPrincipais();
        })
        .catch(() => {
            estadoParametros.todos = [];
            estadoParametros.filtrados = [];
            renderizarTabelaParametrosPrincipais();
        });
}

function inicializarEventosFiltroParametrosPrincipais() {
    const inputBusca = document.getElementById('filtro-param-busca');
    if (inputBusca) {
        inputBusca.addEventListener('keyup', function (e) {
            estadoParametros.filtros.busca = e.target.value.toLowerCase();
            estadoParametros.currentPage = 1;
            aplicarFiltrosParametrosPrincipais();
            renderizarTabelaParametrosPrincipais();
        });
    }

    const chkAtivos = document.getElementById('filtro-param-ativos');
    const chkInativos = document.getElementById('filtro-param-inativos');

    if (chkAtivos) {
        chkAtivos.addEventListener('change', function () {
            estadoParametros.filtros.mostrarAtivos = this.checked;
            estadoParametros.currentPage = 1;
            aplicarFiltrosParametrosPrincipais();
            renderizarTabelaParametrosPrincipais();
        });
    }

    if (chkInativos) {
        chkInativos.addEventListener('change', function () {
            estadoParametros.filtros.mostrarInativos = this.checked;
            estadoParametros.currentPage = 1;
            aplicarFiltrosParametrosPrincipais();
            renderizarTabelaParametrosPrincipais();
        });
    }
}

function aplicarFiltrosParametrosPrincipais() {
    estadoParametros.filtrados = estadoParametros.todos.filter(p => {
        const { busca, mostrarAtivos, mostrarInativos } = estadoParametros.filtros;

        // filtro status
        if (p.ativo && !mostrarAtivos) return false;
        if (!p.ativo && !mostrarInativos) return false;

        // filtro texto
        if (busca) {
            const texto = `${p.horario} ${p.origem_dados} ${p.diretorio} ${p.empresa_nome}`.toLowerCase();
            if (!texto.includes(busca)) return false;
        }

        return true;
    });
}

function renderizarTabelaParametrosPrincipais() {
    const tbody = document.querySelector('#tabela-parametros-main tbody');
    const paginacao = document.getElementById('paginacao-cargas');

    if (!tbody) return;

    tbody.innerHTML = '';

    if (!estadoParametros.filtrados.length) {
        tbody.innerHTML = `
            <tr>
                <td colspan="5" class="text-center text-muted py-4">
                    <i class="fas fa-list" style="font-size: 32px; margin-bottom: 10px; display: block; opacity: 0.5;"></i>
                    Nenhum parâmetro cadastrado
                </td>
            </tr>
        `;

        if (paginacao) paginacao.innerHTML = '';
        return;
    }

    const inicio = (estadoParametros.currentPage - 1) * estadoParametros.itemsPerPage;
    const fim = inicio + estadoParametros.itemsPerPage;
    const pagina = estadoParametros.filtrados.slice(inicio, fim);

    pagina.forEach(p => {
        const tr = document.createElement('tr');
        tr.style.cursor = 'pointer';
        tr.innerHTML = `
            <td>${p.horario || '-'}</td>
            <td>${p.origem_dados || '-'}</td>
            <td>${p.diretorio || '-'}</td>
            <td>${p.empresa_nome || '-'}</td>
            <td>
                <span class="badge-status ${p.ativo ? 'badge-success' : 'badge-warning'}">
                    ${p.ativo ? 'Ativo' : 'Inativo'}
                </span>
            </td>
        `;
        tr.addEventListener('click', function () {
            abrirModalParametro(p.id);
        });
        tbody.appendChild(tr);
    });

    if (paginacao) {
        const totalPages = Math.ceil(estadoParametros.filtrados.length / estadoParametros.itemsPerPage);
        paginacao.innerHTML = '';

        if (totalPages > 1) {
            for (let i = 1; i <= totalPages; i++) {
                const li = document.createElement('li');
                li.className = 'page-item' + (i === estadoParametros.currentPage ? ' active' : '');

                const btn = document.createElement('button');
                btn.className = 'page-link';
                btn.textContent = i;
                btn.onclick = () => {
                    estadoParametros.currentPage = i;
                    renderizarTabelaParametrosPrincipais();
                    window.scrollTo({ top: 0, behavior: 'smooth' });
                };

                li.appendChild(btn);
                paginacao.appendChild(li);
            }
        }
    }
}

/* ===============================
   MODAL DETALHES DO PARÂMETRO
================================ */

function preencherFormularioParametro(param) {
    if (!param) return;
    const id = param.id;
    const horario = param.horario || '';
    const origem = param.origem_dados || param.origem || '';
    const diretorio = param.diretorio || '';
    const empresa_id = param.empresa_id || '';
    const ativo = !!param.ativo;

    const idInput = document.getElementById('param-edit-id');
    const idLabel = document.getElementById('param-edit-id-label');
    const inputHorario = document.getElementById('param-edit-horario');
    const selectOrigem = document.getElementById('param-edit-origem-dados');
    const inputDiretorio = document.getElementById('param-edit-diretorio');
    const selectEmpresa = document.getElementById('param-edit-empresa');
    const chkAtivo = document.getElementById('param-edit-ativo');

    if (idInput) idInput.value = id || '';
    if (idLabel) idLabel.textContent = id || '';
    if (inputHorario) inputHorario.value = horario;
    if (selectOrigem) selectOrigem.value = origem || 'SAP';
    if (inputDiretorio) inputDiretorio.value = diretorio;
    if (selectEmpresa) selectEmpresa.value = empresa_id || '';
    if (chkAtivo) chkAtivo.checked = ativo;
}

function carregarJobsDoParametro(paramId) {
    const tbody = document.querySelector('#tabela-jobs-param tbody');
    if (!tbody) return;

    tbody.innerHTML = `
        <tr>
            <td colspan="4" class="text-center text-muted py-3">
                Carregando jobs...
            </td>
        </tr>
    `;

    fetch(getApiBase() + `/api/cargaxml/jobs/?parametro_id=${paramId}`)
        .then(resp => resp.json())
        .then(data => {
            const items = data.items || [];
            tbody.innerHTML = '';

            if (!data.sucesso || items.length === 0) {
                tbody.innerHTML = `
                    <tr>
                        <td colspan="4" class="text-center text-muted py-3">
                            Nenhum job encontrado para este parâmetro
                        </td>
                    </tr>
                `;
                return;
            }

            items.forEach(j => {
                const totalArq = j.total_arquivos || 0;
                const sucesso = j.total_sucesso || 0;
                const erro = j.total_erro || 0;
                const resumo = totalArq > 0 ? `${totalArq} arq(s) - ${sucesso}✓/${erro}✗` : '-';
                const dataHora = j.started_at || '';
                let dataStr = '';
                let horaStr = '';
                if (dataHora.includes('T')) {
                    const [d, t] = dataHora.split('T');
                    dataStr = d;
                    horaStr = (t || '').substring(0, 5);
                }

                const tr = document.createElement('tr');
                tr.style.cursor = 'pointer';
                tr.innerHTML = `
                    <td>Job #${j.id}</td>
                    <td>${dataStr} ${horaStr}</td>
                    <td>${obterBadgeStatusCarga(j.status)}</td>
                    <td>${resumo}</td>
                `;
                tr.addEventListener('click', function (e) {
                    e.stopPropagation();
                    abrirModalJob(j.id);
                });
                tbody.appendChild(tr);
            });
        })
        .catch(() => {
            tbody.innerHTML = `
                <tr>
                    <td colspan="4" class="text-center text-muted py-3">
                        Erro ao carregar jobs deste parâmetro
                    </td>
                </tr>
            `;
        });
}

function abrirModalParametro(paramId) {
    // Tenta usar dados já carregados em memória
    const paramLocal = estadoParametros.todos.find(p => p.id === paramId);
    if (paramLocal) {
        preencherFormularioParametro(paramLocal);
    }

    // Recarrega dados detalhados do parâmetro (caso backend forneça)
    fetch(getApiBase() + `/api/cargaxml/parametros/${paramId}/`)
        .then(resp => resp.json())
        .then(data => {
            if (data.sucesso && data.parametro) {
                preencherFormularioParametro(data.parametro);
            }
        })
        .catch(() => {
            // Se der erro, segue com os dados locais já preenchidos
        });

    carregarJobsDoParametro(paramId);

    const modalEl = document.getElementById('modalParametroDetails');
    if (modalEl) {
        const modal = new bootstrap.Modal(modalEl);
        modal.show();
    }
}

/* ===============================
   CARREGAR TODAS AS CARGAS
================================ */
function carregarTodasAsCargas() {
    fetch(getApiBase() + '/api/cargaxml/jobs/')
        .then(resp => {
            console.log('API Response Status:', resp.status);
            return resp.json().then(data => {
                console.log('API Response Data:', data);
                return { status: resp.status, data };
            });
        })
        .then(({ status, data }) => {
            if (status === 403) {
                console.error('Erro 403: Cliente não identificado');
                Notificacoes.pagina('Erro ao carregar jobs: Cliente não identificado', 'error');
                estadoCargaXml.todasCargas = [];
                renderizarEmExecucao();
                renderizarJaExecutado();
            } else if (data.sucesso && data.items && data.items.length > 0) {
                console.log('Jobs carregados:', data.items.length);
                // mapear para formato compatível
                estadoCargaXml.todasCargas = data.items.map(j => {
                    const totalArq = j.total_arquivos || 0;
                    const sucesso = j.total_sucesso || 0;
                    const erro = j.total_erro || 0;
                    const resumo = totalArq > 0 ? `${sucesso}✓/${erro}✗` : '-';
                    
                    return {
                        id: j.id,
                        arquivo: `Job #${j.id}`,
                        resumo: `${totalArq} arquivo(s) - ${resumo}`,
                        tipo: j.parametro_id ? 'Automático' : 'Manual',
                        numero: '',
                        empresa: '',
                        data: j.started_at ? j.started_at.split('T')[0] : '',
                        hora: j.started_at ? j.started_at.split('T')[1]?.substring(0, 5) : '',
                        status: j.status,
                        detalhes: j,
                    };
                });
            } else if (data.sucesso && (!data.items || data.items.length === 0)) {
                console.log('Nenhum job encontrado');
                estadoCargaXml.todasCargas = [];
            } else {
                console.error('Erro ao carregar jobs:', data.mensagem);
                Notificacoes.pagina(data.mensagem || 'Erro ao carregar jobs', 'error');
                estadoCargaXml.todasCargas = [];
            }
            aplicarFiltrosCarga();
            renderizarEmExecucao();
            renderizarJaExecutado();
        })
        .catch(erro => {
            console.error('Erro na requisição:', erro);
            Notificacoes.pagina('Erro ao conectar na API: ' + erro.message, 'error');
            estadoCargaXml.todasCargas = [];
            aplicarFiltrosCarga();
            renderizarEmExecucao();
            renderizarJaExecutado();
        });
}

/* ===============================
   EM EXECUÇÃO / JÁ EXECUTADO (containers tipo Home)
================================ */
function renderizarEmExecucao() {
    const lista = document.getElementById('lista-em-execucao');
    if (!lista) return;

    const emExecucao = estadoCargaXml.todasCargas.filter(function (c) {
        var s = (c.status || '').toUpperCase();
        return s === 'RUNNING' || s === 'PENDING';
    });

    lista.innerHTML = '';
    if (emExecucao.length === 0) {
        lista.innerHTML = '<li class="cargaxml-lista-empty text-muted py-3 text-center"><i class="fas fa-check-circle fa-2x mb-2 d-block opacity-50"></i>Nenhum job em execução no momento.</li>';
        return;
    }

    emExecucao.forEach(function (carga) {
        var li = document.createElement('li');
        li.className = 'home-activity-item cargaxml-job-item';
        li.style.cursor = 'pointer';
        li.setAttribute('data-job-id', carga.id);
        var dataHora = (carga.detalhes && carga.detalhes.started_at) ? carga.detalhes.started_at : (carga.data + 'T' + (carga.hora || ''));
        var dataStr = dataHora ? (dataHora.split('T')[0] + ' ' + (dataHora.split('T')[1] || '').substring(0, 5)) : '-';
        li.innerHTML = '<span class="home-activity-type home-activity-type-xml">' + (carga.tipo || 'XML') + '</span>' +
            '<div class="home-activity-detail">' +
            '<span class="home-activity-status home-activity-status-running">Em execução</span>' +
            '<span class="home-activity-meta">' + (carga.resumo || '') + '</span></div>' +
            '<div class="home-activity-time">' + dataStr + '</div>' +
            '<a href="#" class="home-activity-link" data-job-id="' + carga.id + '" title="Ver detalhes">→</a>';
        li.addEventListener('click', function (e) {
            e.preventDefault();
            abrirModalJob(carga.id);
        });
        var link = li.querySelector('a.home-activity-link');
        if (link) link.addEventListener('click', function (e) { e.preventDefault(); abrirModalJob(carga.id); });
        lista.appendChild(li);
    });
}

function renderizarJaExecutado() {
    const lista = document.getElementById('lista-ja-executado');
    if (!lista) return;

    const jaExecutado = estadoCargaXml.todasCargas.filter(function (c) {
        var s = (c.status || '').toUpperCase();
        return s === 'SUCCESS' || s === 'ERROR';
    }).slice(0, 25);

    lista.innerHTML = '';
    if (jaExecutado.length === 0) {
        lista.innerHTML = '<li class="cargaxml-lista-empty text-muted py-3 text-center"><i class="fas fa-inbox fa-2x mb-2 d-block opacity-50"></i>Nenhuma execução recente.</li>';
        return;
    }

    jaExecutado.forEach(function (carga) {
        var li = document.createElement('li');
        li.className = 'home-activity-item cargaxml-job-item';
        li.style.cursor = 'pointer';
        var statusClass = (carga.status || '').toUpperCase() === 'ERROR' ? 'home-activity-status-error' : 'home-activity-status-success';
        var dataHora = (carga.detalhes && carga.detalhes.started_at) ? carga.detalhes.started_at : (carga.data + 'T' + (carga.hora || ''));
        var dataStr = dataHora ? (dataHora.split('T')[0] + ' ' + (dataHora.split('T')[1] || '').substring(0, 5)) : '-';
        li.innerHTML = '<span class="home-activity-type home-activity-type-xml">' + (carga.tipo || 'XML') + '</span>' +
            '<div class="home-activity-detail">' +
            '<span class="home-activity-status ' + statusClass + '">' + (carga.status === 'SUCCESS' ? 'Concluído' : 'Erro') + '</span>' +
            '<span class="home-activity-meta">' + (carga.resumo || '') + '</span></div>' +
            '<div class="home-activity-time">' + dataStr + '</div>' +
            '<a href="#" class="home-activity-link" data-job-id="' + carga.id + '" title="Ver log">→</a>';
        li.addEventListener('click', function (e) {
            e.preventDefault();
            abrirModalJob(carga.id);
        });
        var linkJa = li.querySelector('a.home-activity-link');
        if (linkJa) linkJa.addEventListener('click', function (e) { e.preventDefault(); abrirModalJob(carga.id); });
        lista.appendChild(li);
    });
}

/* ===============================
   LOGS RESUMO (card na página)
================================ */
function renderizarLogsResumo(items) {
    var emptyEl = document.getElementById('logs-resumo-empty');
    var contentEl = document.getElementById('logs-resumo-content');
    if (!emptyEl || !contentEl) return;

    if (!items || items.length === 0) {
        emptyEl.style.display = 'block';
        contentEl.style.display = 'none';
        contentEl.innerHTML = '';
        return;
    }

    emptyEl.style.display = 'none';
    contentEl.style.display = 'block';

    function formatDt(iso) {
        if (!iso) return '-';
        try {
            var d = new Date(iso);
            return d.toLocaleString('pt-BR', { dateStyle: 'short', timeStyle: 'short' });
        } catch (e) { return iso; }
    }
    function escapeHtml(s) {
        return (s || '').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    }
    function classLog(line) {
        var t = (line || '').trim();
        if (t.indexOf('ERRO:') === 0) return 'aviso-log-erro';
        if (t.indexOf('PENDENTES') === 0) return 'aviso-log-pendente';
        if (t.indexOf('OK:') === 0) return 'aviso-log-ok';
        return 'aviso-log-outro';
    }

    var html = '';
    items.slice(0, 3).forEach(function (job) {
        var logLines = (job.log && job.log.length) ? job.log.filter(function (l) {
            var t = (l || '').trim();
            return t.indexOf('ERRO:') === 0 || t.indexOf('PENDENTES') === 0;
        }).slice(0, 5) : [];
        html += '<div class="cargaxml-log-job mb-3">';
        html += '<div class="small fw-600 text-secondary mb-1">Job #' + job.id + ' &middot; ' + formatDt(job.started_at) + '</div>';
        if (logLines.length === 0) {
            html += '<div class="small text-muted">Sem linhas de log</div>';
        } else {
            logLines.forEach(function (l) {
                html += '<div class="cargaxml-log-line ' + classLog(l) + '">' + escapeHtml(l) + '</div>';
            });
        }
        html += '</div>';
    });
    contentEl.innerHTML = html;
}

/* ===============================
   EVENTOS DE FILTROS
================================ */


function abrirModalJob(jobId) {
    fetch(getApiBase() + `/api/cargaxml/jobs/${jobId}/`)
        .then(resp => resp.json())
        .then(data => {
            if (!data.sucesso) {
                Notificacoes.pagina('❌ Não foi possível carregar detalhes do job', 'error');
                return;
            }
            const job = data.job;
            const param = data.parametro;
            const log = data.log || [];
            document.getElementById('modal-job-id').textContent = job.id;
            document.getElementById('modal-job-status').textContent = job.status;
            document.getElementById('modal-job-started').textContent = job.started_at || '-';
            document.getElementById('modal-job-finished').textContent = job.finished_at || '-';
            if (param) {
                document.getElementById('modal-param-horario').value = param.horario || '';
                document.getElementById('modal-param-origem').value = param.origem_dados || '';
                document.getElementById('modal-param-diretorio').value = param.diretorio || '';
                document.getElementById('modal-param-empresa').value = param.empresa_nome || param.empresa_id || '';
            } else {
                document.getElementById('modal-param-horario').value = '';
                document.getElementById('modal-param-origem').value = '';
                document.getElementById('modal-param-diretorio').value = '';
                document.getElementById('modal-param-empresa').value = '';
            }
            const tbodyLog = document.querySelector('#tabela-log tbody');
            tbodyLog.innerHTML = '';
            if (log.length === 0) {
                tbodyLog.innerHTML = '<tr><td colspan="2" class="text-center text-muted">Sem registros</td></tr>';
            } else {
                var logOrdenado = log.slice();
                logOrdenado.sort(function (a, b) {
                    var pa = (function (line) {
                        var t = (line || '').trim();
                        if (t.indexOf('ERRO:') === 0) return 0;
                        if (t.indexOf('PENDENTES') === 0) return 1;
                        if (t.indexOf('OK:') === 0) return 2;
                        return 3;
                    })(a);
                    var pb = (function (line) {
                        var t = (line || '').trim();
                        if (t.indexOf('ERRO:') === 0) return 0;
                        if (t.indexOf('PENDENTES') === 0) return 1;
                        if (t.indexOf('OK:') === 0) return 2;
                        return 3;
                    })(b);
                    return pa - pb;
                });
                logOrdenado.forEach(function (line, idx) {
                    var tr = document.createElement('tr');
                    var t = (line || '').trim();
                    var rowClass = '';
                    if (t.indexOf('ERRO:') === 0) rowClass = 'aviso-log-erro';
                    else if (t.indexOf('PENDENTES') === 0) rowClass = 'aviso-log-pendente';
                    else if (t.indexOf('OK:') === 0) rowClass = 'aviso-log-ok';
                    if (rowClass) tr.className = rowClass;
                    var text = (line || '').replace(/</g, '&lt;').replace(/>/g, '&gt;');
                    tr.innerHTML = '<td>' + (idx + 1) + '</td><td>' + text + '</td>';
                    tbodyLog.appendChild(tr);
                });
            }
            var modal = new bootstrap.Modal(document.getElementById('modalJobDetails'));
            modal.show();
        })
        .catch(() => {
            Notificacoes.pagina('❌ Falha ao carregar detalhes do job', 'error');
        });
}


function inicializarEventosFiltros() {
    // Filtro de busca
    const inputBusca = document.getElementById('filtro-busca');
    if (inputBusca) {
        inputBusca.addEventListener('keyup', function (e) {
            estadoCargaXml.filtros.busca = e.target.value.toLowerCase();
            estadoCargaXml.currentPage = 1;
            aplicarFiltrosCarga();
            renderizarTabelaCargas();
        });
    }

    // Checkboxes de tipo
    const checkboxAutomatico = document.getElementById('filtro-automatico');
    const checkboxManual = document.getElementById('filtro-manual');

    if (checkboxAutomatico) {
        checkboxAutomatico.addEventListener('change', atualizarFiltrosTipo);
    }
    if (checkboxManual) {
        checkboxManual.addEventListener('change', atualizarFiltrosTipo);
    }
}

function atualizarFiltrosTipo() {
    estadoCargaXml.filtros.tipos = [];

    if (document.getElementById('filtro-automatico')?.checked) {
        estadoCargaXml.filtros.tipos.push('Automático');
    }
    if (document.getElementById('filtro-manual')?.checked) {
        estadoCargaXml.filtros.tipos.push('Manual');
    }

    estadoCargaXml.currentPage = 1;
    aplicarFiltrosCarga();
    renderizarTabelaCargas();
}

/* ===============================
   APLICAR FILTROS
================================ */
function aplicarFiltrosCarga() {
    estadoCargaXml.cargasFiltradas = estadoCargaXml.todasCargas.filter(carga => {
        // Filtro de busca
        if (estadoCargaXml.filtros.busca) {
            const busca = estadoCargaXml.filtros.busca;
            if (!carga.arquivo.toLowerCase().includes(busca)) {
                return false;
            }
        }

        // Filtro de tipo
        if (!estadoCargaXml.filtros.tipos.includes(carga.tipo)) {
            return false;
        }

        return true;
    });
}

/* ===============================
   RENDERIZAR TABELA CARGAS
================================ */
function renderizarTabelaCargas() {
    const tbody = document.querySelector('#tabela-cargas tbody');
    if (!tbody) return;

    const inicio = (estadoCargaXml.currentPage - 1) * estadoCargaXml.itemsPerPage;
    const fim = inicio + estadoCargaXml.itemsPerPage;
    const paginados = estadoCargaXml.cargasFiltradas.slice(inicio, fim);

    tbody.innerHTML = '';

    if (paginados.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6" class="text-center text-muted py-4">
                    <i class="fas fa-inbox" style="font-size: 24px; margin-bottom: 10px; display: block; opacity: 0.5;"></i>
                    Nenhum arquivo encontrado
                </td>
            </tr>
        `;
        renderizarPaginacaoCarga(0);
        return;
    }

    paginados.forEach(carga => {
        const iconeTipo = obterIconeTipo(carga.tipo);
        const badgeStatus = obterBadgeStatusCarga(carga.status);

        const linha = document.createElement('tr');
        linha.style.cursor = 'pointer';
        linha.onclick = () => abrirModalJob(carga.id);
        linha.innerHTML = `
            <td>
                ${iconeTipo}
                <div>
                    <strong>${carga.arquivo}</strong>
                    <br>
                    <small class="text-muted">${carga.resumo}</small>
                </div>
            </td>
            <td>
                <span class="badge" style="background-color: ${obterCorTipo(carga.tipo)}; color: white;">
                    ${carga.tipo}
                </span>
            </td>
            <td>
                <div>${carga.data}</div>
                <small class="text-muted">${carga.hora || ''}</small>
            </td>
            <td>${badgeStatus}</td>
        `;
        tbody.appendChild(linha);
    });

    renderizarPaginacaoCarga(estadoCargaXml.cargasFiltradas.length);
}

/* ===============================
   RENDERIZAR PAGINAÇÃO
================================ */
function renderizarPaginacaoCarga(totalItems) {
    const container = document.getElementById('paginacao-cargas');
    if (!container) return;

    const totalPages = Math.ceil(totalItems / estadoCargaXml.itemsPerPage);
    container.innerHTML = '';

    if (totalPages <= 1) return;

    for (let i = 1; i <= totalPages; i++) {
        const link = document.createElement('li');
        link.className = 'page-item' + (i === estadoCargaXml.currentPage ? ' active' : '');

        const btn = document.createElement('button');
        btn.className = 'page-link';
        btn.textContent = i;
        btn.onclick = () => {
            estadoCargaXml.currentPage = i;
            renderizarTabelaCargas();
            window.scrollTo({ top: 0, behavior: 'smooth' });
        };

        link.appendChild(btn);
        container.appendChild(link);
    }
}

/* ===============================
   PARAMETROS DE CARGA
================================ */
function inicializarEventosParametros() {
    const form = document.getElementById('form-parametros');
    if (form) {
        form.addEventListener('submit', function (e) {
            e.preventDefault();
            criarParametroCarga();
        });
    }

    const btnRecarregar = document.getElementById('btn-recarregar-parametros');
    if (btnRecarregar) {
        btnRecarregar.addEventListener('click', function () {
            carregarParametrosAtivos();
        });
    }

    const modalCarga = document.getElementById('modalCargaXml');
    if (modalCarga) {
        modalCarga.addEventListener('shown.bs.modal', function () {
            carregarParametrosAtivos();
        });
    }

    const btnConfirmarUploadZip = document.getElementById('btn-confirmar-upload-zip');
    if (btnConfirmarUploadZip) {
        btnConfirmarUploadZip.addEventListener('click', enviarZipParaPasta);
    }

    // show/hide upload button depending on active tab
    const btnEnviar = document.getElementById('btn-enviar-xml');
    const tabManual = document.getElementById('tab-manual');
    const tabAutomatico = document.getElementById('tab-automatico');
    function ajustarBotaoEnvio() {
        if (!btnEnviar) return;
        const manualActive = document.querySelector('#tab-manual').classList.contains('active');
        btnEnviar.style.display = manualActive ? '' : 'none';
    }
    if (tabManual) {
        tabManual.addEventListener('shown.bs.tab', ajustarBotaoEnvio);
    }
    if (tabAutomatico) {
        tabAutomatico.addEventListener('shown.bs.tab', ajustarBotaoEnvio);
    }
    // initial state when script loads
    ajustarBotaoEnvio();

    // salvar edição de parâmetro (modal principal)
    const formEdit = document.getElementById('form-param-edit');
    if (formEdit) {
        formEdit.addEventListener('submit', function (e) {
            e.preventDefault();
            atualizarParametroCarga();
        });
    }
}

function criarParametroCarga() {
    const horario = document.getElementById('param-horario')?.value || '';
    const origemDados = document.getElementById('param-origem-dados')?.value || 'SAP';
    const diretorio = document.getElementById('param-diretorio')?.value || '';
    const ativo = document.getElementById('param-ativo')?.checked || false;

    if (!horario || !diretorio) {
        Notificacoes.modal('Preencha horário e diretório', 'warning', 'modalCargaXmlAlerts');
        return;
    }

    fetch(getApiBase() + '/api/cargaxml/parametros/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': obterCsrfToken(),
        },
        body: JSON.stringify({
            horario: horario,
            origem_dados: origemDados,
            diretorio: diretorio,
            empresa_id: '',
            ativo: ativo,
        })
    })
        .then(response => response.json().then(data => ({ ok: response.ok, data })))
        .then(({ ok, data }) => {
            if (!ok || !data.sucesso) {
                Notificacoes.modal(data.mensagem || 'Erro ao salvar parametros', 'danger', 'modalCargaXmlAlerts');
                return;
            }
            Notificacoes.modal('Parametros salvos com sucesso', 'success', 'modalCargaXmlAlerts');
            carregarParametrosAtivos();
            carregarParametrosPrincipais();
        })
        .catch(() => {
            Notificacoes.modal('Falha ao salvar parametros', 'danger', 'modalCargaXmlAlerts');
        });
}

function carregarParametrosAtivos() {
    const tabela = document.querySelector('#tabela-parametros tbody');
    if (!tabela) return;

    fetch(getApiBase() + '/api/cargaxml/parametros/?ativo=1')
        .then(response => response.json())
        .then(data => {
            tabela.innerHTML = '';
            const items = data.items || [];

            if (!data.sucesso || items.length === 0) {
                tabela.innerHTML = '<tr><td colspan="6" class="text-center text-muted">Nenhum parametro ativo</td></tr>';
                return;
            }

            items.forEach(item => {
                const linha = document.createElement('tr');
                linha.innerHTML = `
                    <td>${item.horario}</td>
                    <td>${item.origem_dados}</td>
                    <td>${item.diretorio}</td>
                    <td>${item.empresa_nome || '-'}</td>
                    <td>
                        <span class="badge-status ${item.ativo ? 'badge-success' : 'badge-warning'}">
                            ${item.ativo ? 'Ativo' : 'Inativo'}
                        </span>
                    </td>
                    <td>
                        <button class="btn btn-sm btn-outline-secondary me-1" onclick="toggleParametro(${item.id}, ${item.ativo})">
                            ${item.ativo ? 'Desativar' : 'Ativar'}
                        </button>
                        <button class="btn btn-sm btn-outline-primary" onclick="abrirModalUploadZip(${item.id})" title="Enviar ZIP para pasta do job">
                            <i class="fas fa-file-archive"></i> Enviar ZIP
                        </button>
                    </td>
                `;
                tabela.appendChild(linha);
            });
        })
        .catch(() => {
            tabela.innerHTML = '<tr><td colspan="6" class="text-center text-muted">Erro ao carregar parametros</td></tr>';
        });
}

function abrirModalUploadZip(paramId) {
    document.getElementById('upload-zip-param-id').value = paramId;
    document.getElementById('upload-zip-file').value = '';
    const modal = new bootstrap.Modal(document.getElementById('modalUploadZip'));
    modal.show();
}

function enviarZipParaPasta() {
    const paramId = document.getElementById('upload-zip-param-id').value;
    const fileInput = document.getElementById('upload-zip-file');
    if (!paramId || !fileInput || !fileInput.files || !fileInput.files.length) {
        Notificacoes.modal('Selecione um arquivo ZIP', 'warning', 'modalUploadZipAlerts');
        return;
    }
    const file = fileInput.files[0];
    if (!file.name.toLowerCase().endsWith('.zip')) {
        Notificacoes.modal('O arquivo deve ser .zip', 'warning', 'modalUploadZipAlerts');
        return;
    }
    const formData = new FormData();
    formData.append('arquivo_zip', file);
    formData.append('csrfmiddlewaretoken', obterCsrfToken());

    const btn = document.getElementById('btn-confirmar-upload-zip');
    btn.disabled = true;

    fetch(getApiBase() + `/api/cargaxml/parametros/${paramId}/upload-zip/`, {
        method: 'POST',
        body: formData
    })
        .then(response => response.json())
        .then(data => {
            btn.disabled = false;
            if (data.sucesso) {
                Notificacoes.modal(data.mensagem || 'ZIP enviado com sucesso.', 'success', 'modalUploadZipAlerts');
                bootstrap.Modal.getInstance(document.getElementById('modalUploadZip')).hide();
                fileInput.value = '';
            } else {
                Notificacoes.modal(data.mensagem || 'Erro ao enviar ZIP', 'danger', 'modalUploadZipAlerts');
            }
        })
        .catch(() => {
            btn.disabled = false;
            Notificacoes.modal('Erro ao enviar ZIP', 'danger', 'modalUploadZipAlerts');
        });
}

function atualizarParametroCarga() {
    const id = document.getElementById('param-edit-id')?.value;
    if (!id) {
        Notificacoes.modal('Parâmetro não identificado para edição', 'warning', 'modalParametroDetailsAlerts');
        return;
    }

    const horario = document.getElementById('param-edit-horario')?.value || '';
    const origemDados = document.getElementById('param-edit-origem-dados')?.value || 'SAP';
    const diretorio = document.getElementById('param-edit-diretorio')?.value || '';
    const empresaId = document.getElementById('param-edit-empresa')?.value || '';
    const ativo = document.getElementById('param-edit-ativo')?.checked || false;

    if (!horario || !diretorio) {
        Notificacoes.modal('Preencha horário e diretório', 'warning', 'modalParametroDetailsAlerts');
        return;
    }

    fetch(getApiBase() + `/api/cargaxml/parametros/${id}/`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': obterCsrfToken(),
        },
        body: JSON.stringify({
            horario: horario,
            origem_dados: origemDados,
            diretorio: diretorio,
            empresa_id: empresaId,
            ativo: ativo,
        })
    })
        .then(response => response.json().then(data => ({ ok: response.ok, data })))
        .then(({ ok, data }) => {
            if (!ok || !data.sucesso) {
                Notificacoes.modal(data.mensagem || 'Erro ao atualizar parâmetro', 'danger', 'modalParametroDetailsAlerts');
                return;
            }
            Notificacoes.modal('Parâmetro atualizado com sucesso', 'success', 'modalParametroDetailsAlerts');
            carregarParametrosPrincipais();
            carregarParametrosAtivos();
        })
        .catch(() => {
            Notificacoes.modal('Falha ao atualizar parâmetro', 'danger', 'modalParametroDetailsAlerts');
        });
}

function toggleParametro(paramId, ativoAtual) {
    fetch(getApiBase() + `/api/cargaxml/parametros/${paramId}/toggle/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': obterCsrfToken(),
        },
        body: JSON.stringify({ ativo: !ativoAtual })
    })
        .then(response => response.json())
        .then(data => {
            if (!data.sucesso) {
                Notificacoes.pagina('Erro ao atualizar parametro', 'danger');
                return;
            }
            carregarParametrosAtivos();
        })
        .catch(() => {
            Notificacoes.pagina('Erro ao atualizar parametro', 'danger');
        });
}

/* ===============================
   DRAG & DROP
================================ */
function prevenirPadraoEventos(e) {
    e.preventDefault();
    e.stopPropagation();
}

/* ===============================
   INPUT FILE
================================ */
function inicializarInputFile() {
    const fileInput = document.getElementById('file-input-xml');

    if (!fileInput) return;

    fileInput.addEventListener('change', function (e) {
        processarArquivos(e.target.files);
    });
}

/* ===============================
   PROCESSAR ARQUIVOS SELECIONADOS
   Aceita pasta (webkitdirectory) com .xml e .zip; ignora outros tipos.
================================ */
function processarArquivos(files) {
    var arquivosValidos = [];
    var list = Array.from(files || []);

    for (var i = 0; i < list.length; i++) {
        var file = list[i];
        var nome = (file.name || '').toLowerCase();
        if (!nome.endsWith('.xml') && !nome.endsWith('.zip')) {
            continue;
        }
        if (file.size > 50 * 1024 * 1024) {
            continue;
        }
        arquivosValidos.push(file);
    }

    estadoCargaXml.arquivos = arquivosValidos;
    estadoCargaXml.totalArquivos = arquivosValidos.length;
    exibirPreviewArquivos();
}

/* ===============================
   EXIBIR PREVIEW DOS ARQUIVOS (apenas contador)
================================ */
function exibirPreviewArquivos(files) {
    if (files) {
        processarArquivos(files);
        return;
    }
    var contador = document.getElementById('contador-arquivos');
    if (contador) {
        contador.textContent = estadoCargaXml.arquivos.length;
    }
}

/* ===============================
   INICIAR UPLOAD
================================ */
function iniciarUpload() {
    if (estadoCargaXml.uploadEmProgresso || estadoCargaXml.arquivos.length === 0) {
        Notificacoes.modal('Selecione pelo menos um arquivo XML ou ZIP', 'warning', 'modalCargaXmlAlerts');
        return;
    }

    var tipoDocumento = (document.getElementById('select-tipo-documento') && document.getElementById('select-tipo-documento').value) || 'NFe';
    var origemDados = (document.getElementById('select-origem-dados') && document.getElementById('select-origem-dados').value) || 'SAP';

    estadoCargaXml.uploadEmProgresso = true;
    var btn = document.getElementById('btn-enviar-xml');
    if (btn) btn.disabled = true;
    uploadArquivosLote(estadoCargaXml.arquivos, tipoDocumento, origemDados);
}

/* ===============================
   UPLOAD EM LOTE
   Com muitos arquivos (ex.: pasta): envia em lotes de 50 para evitar 400 e ERR_CONTENT_LENGTH_MISMATCH.
================================ */
var TAMANHO_LOTE_CARGA_XML = 100;

function enviarUmLoteXml(arquivosLote, tipoDocumento, origemDados, apiUrl, csrfToken, jobId, ultimoLote) {
    var formData = new FormData();
    arquivosLote.forEach(function (f) { formData.append('arquivo', f); });
    formData.append('type_xml', tipoDocumento);
    formData.append('origem_dados', origemDados);
    if (jobId) formData.append('job_id', String(jobId));
    if (ultimoLote) formData.append('ultimo_lote', '1');
    return fetch(apiUrl, {
        method: 'POST',
        headers: { 'X-CSRFToken': csrfToken },
        body: formData
    }).then(function (response) {
        var status = response.status;
        if (status === 413) {
            return { status: 413, data: { sucesso: false, mensagem: 'Arquivo(s) muito grande (413). Configure Nginx: client_max_body_size 100M; ou envie menos arquivos.' } };
        }
        return response.text().then(function (text) {
            var data;
            try { data = text ? JSON.parse(text) : {}; } catch (e) { data = {}; }
            if (!data.mensagem && data.sucesso === undefined) data = { sucesso: false, mensagem: 'Resposta inválida (status ' + status + ')' };
            return { status: status, data: data };
        });
    });
}

function finalizarUploadCargaXml(erroMsg) {
    estadoCargaXml.uploadEmProgresso = false;
    var btn = document.getElementById('btn-enviar-xml');
    if (btn) btn.disabled = false;
    finalizarCargas();
    if (erroMsg) {
        fecharModalCargaXml();
        if (typeof Notificacoes !== 'undefined' && Notificacoes.pagina) {
            Notificacoes.pagina(erroMsg, 'danger');
        } else { alert(erroMsg); }
    }
}

function uploadArquivosLote(arquivos, tipoDocumento, origemDados) {
    var apiUrl = (document.querySelector('.layout-page') && document.querySelector('.layout-page').getAttribute('data-api-processar-xml')) || '/api/processar-xml/';
    var csrfToken = (document.querySelector('[name=csrfmiddlewaretoken]') && document.querySelector('[name=csrfmiddlewaretoken]').value) || (typeof window.getCsrfToken === 'function' ? window.getCsrfToken() : '');
    var total = arquivos.length;
    var usarLotes = total > TAMANHO_LOTE_CARGA_XML;

    atualizarStatusUpload(0, 'processing', usarLotes ? 'Enviando em lotes (evita erro de rede)...' : 'Enviando arquivos...');

    if (usarLotes) {
        var lotes = [];
        for (var i = 0; i < total; i += TAMANHO_LOTE_CARGA_XML) {
            lotes.push(arquivos.slice(i, i + TAMANHO_LOTE_CARGA_XML));
        }
        var numLotes = lotes.length;
        var loteAtual = 0;
        var jobIdUnico = null;
        function enviarProximoLote() {
            if (loteAtual >= numLotes) {
                fecharModalCargaXml();
                if (typeof Notificacoes !== 'undefined' && Notificacoes.pagina) {
                    Notificacoes.pagina('Job #' + (jobIdUnico || '') + ' criado com ' + total + ' arquivo(s). Atualize o painel para acompanhar.', 'success');
                } else { alert('Job criado. Atualize o painel.'); }
                carregarResumoCargaXml();
                carregarTodasAsCargas();
                finalizarUploadCargaXml();
                return;
            }
            var ehUltimoLote = (loteAtual === numLotes - 1);
            atualizarStatusUpload(0, 'processing', 'Enviando lote ' + (loteAtual + 1) + '/' + numLotes + ' (' + lotes[loteAtual].length + ' arquivos)...');
            enviarUmLoteXml(lotes[loteAtual], tipoDocumento, origemDados, apiUrl, csrfToken, jobIdUnico || null, ehUltimoLote)
                .then(function (result) {
                    if (result.status === 413) {
                        finalizarUploadCargaXml(result.data.mensagem || 'Erro 413.');
                        return;
                    }
                    if (result.status === 400) {
                        finalizarUploadCargaXml((result.data && result.data.mensagem) ? result.data.mensagem : 'Erro 400 no lote ' + (loteAtual + 1) + '.');
                        return;
                    }
                    if (result.status !== 200 && result.status !== 202) {
                        finalizarUploadCargaXml((result.data && result.data.mensagem) ? result.data.mensagem : 'Erro no lote ' + (loteAtual + 1) + '.');
                        return;
                    }
                    if (result.data && result.data.job_id) jobIdUnico = result.data.job_id;
                    loteAtual++;
                    if (result.status === 202) {
                        enviarProximoLote();
                    } else {
                        enviarProximoLote();
                    }
                })
                .catch(function (err) {
                    var msg = 'Erro ao enviar lote ' + (loteAtual + 1) + ': ' + (err.message || 'Falha na rede. Tente novamente ou envie um ZIP.');
                    if (err.message && (err.message.indexOf('fetch') !== -1 || err.message.indexOf('Failed') !== -1)) {
                        msg = 'Conexão interrompida (rede/proxy). Tente de novo ou envie a pasta em um .zip.';
                    }
                    finalizarUploadCargaXml(msg);
                });
        }
        enviarProximoLote();
        return;
    }

    enviarUmLoteXml(arquivos, tipoDocumento, origemDados, apiUrl, csrfToken)
        .then(function (result) {
            var status = result.status;
            var data = result.data;

            if (status === 413) {
                finalizarUploadCargaXml(data.mensagem || 'Erro 413: arquivo(s) muito grande.');
                return;
            }
            if (status === 400) {
                var msg = (data && data.mensagem) ? data.mensagem : 'Requisição inválida (400). Envie apenas .xml ou .zip.';
                if (typeof Notificacoes !== 'undefined' && Notificacoes.pagina) {
                    Notificacoes.pagina(msg, 'danger');
                } else { alert(msg); }
                arquivos.forEach(function (file, index) { atualizarStatusUpload(index, 'error', '✗ ' + (data.mensagem || 'Erro 400')); });
                finalizarUploadCargaXml();
                return;
            }
            if (status === 202) {
                fecharModalCargaXml();
                if (typeof Notificacoes !== 'undefined' && Notificacoes.pagina) {
                    Notificacoes.pagina(data.mensagem || 'Job criado e em execução. Atualize o painel para acompanhar.', 'success');
                } else { alert(data.mensagem || 'Job criado e em execução.'); }
                carregarResumoCargaXml();
                carregarTodasAsCargas();
                finalizarUploadCargaXml();
                return;
            }
            if (data.sucesso) {
                if (estadoCargaXml.modoDiretorio) {
                    var totalSucesso = (data.detalhes && data.detalhes.success) ? data.detalhes.success.length : 0;
                    var totalErro = (data.detalhes && data.detalhes.errors) ? data.detalhes.errors.length : 0;
                    var mensagemStatus = totalSucesso + ' processado(s), ' + totalErro + ' erro(s)';
                    atualizarStatusUpload(arquivos.length - 1, totalErro === 0 ? 'success' : 'error', (totalErro === 0 ? '✓ ' : '⚠️ ') + mensagemStatus);
                } else {
                    if (data.detalhes && data.detalhes.success) {
                        data.detalhes.success.forEach(function (fileName) {
                            var idx = arquivos.findIndex(function (f) { return f.name === fileName; });
                            if (idx !== -1) atualizarStatusUpload(idx, 'success', '✓ Processado');
                        });
                    }
                    if (data.detalhes && data.detalhes.errors) {
                        data.detalhes.errors.forEach(function (erro) {
                            var idx = arquivos.findIndex(function (f) { return f.name === erro.file; });
                            if (idx !== -1) atualizarStatusUpload(idx, 'error', '✗ ' + (erro.error || ''));
                        });
                    }
                }
                fecharModalCargaXml();
                if (typeof Notificacoes !== 'undefined' && Notificacoes.pagina) {
                    Notificacoes.pagina(data.mensagem, 'success');
                } else { alert(data.mensagem); }
            } else {
                fecharModalCargaXml();
                if (typeof Notificacoes !== 'undefined' && Notificacoes.pagina) {
                    Notificacoes.pagina(data.mensagem || 'Erro ao processar XMLs', 'danger');
                } else { alert(data.mensagem || 'Erro ao processar XMLs'); }
                arquivos.forEach(function (file, index) { atualizarStatusUpload(index, 'error', '✗ Erro no processamento'); });
            }
            finalizarUploadCargaXml();
        })
        .catch(function (error) {
            console.error('Erro ao fazer upload:', error);
            var msg = 'Erro ao enviar arquivos: ' + (error.message || 'Erro de conexão');
            if (error.message && (String(error.message).indexOf('fetch') !== -1 || String(error.message).indexOf('Failed') !== -1)) {
                msg = 'Conexão falhou (rede ou proxy cortou a requisição). Se escolheu uma pasta com muitos arquivos, tente: (1) enviar de novo – o envio em lotes já está ativo para pastas grandes – ou (2) compactar em .zip e enviar o ZIP.';
            }
            fecharModalCargaXml();
            if (typeof Notificacoes !== 'undefined' && Notificacoes.pagina) {
                Notificacoes.pagina(msg, 'danger');
            } else { alert(msg); }
            arquivos.forEach(function (file, index) { atualizarStatusUpload(index, 'error', '✗ Erro de conexão'); });
            finalizarUploadCargaXml();
        });
}

/* ===============================
   ATUALIZAR STATUS
================================ */
function atualizarStatusUpload(index, status, mensagem) {
    try {
    if (estadoCargaXml.modoDiretorio) {
        var linhaDiretorio = document.getElementById('linha-diretorio');
        if (linhaDiretorio) {
            var statusCell = linhaDiretorio.querySelector('td:nth-child(3)');
            
            let badgeClass = 'badge-info';
            let statusTexto = 'Aguardando';
            let iconHtml = '<span class="spinner-carga" style="margin-right: 5px;"></span>';

            if (status === 'processing') {
                badgeClass = 'badge-warning';
                statusTexto = `Processando... (${index + 1}/${estadoCargaXml.arquivos.length})`;
                iconHtml = '<span class="spinner-carga" style="margin-right: 5px;"></span>';
            } else if (status === 'success') {
                badgeClass = 'badge-success';
                statusTexto = mensagem || '✓ Concluído';
                iconHtml = '';
            } else if (status === 'error') {
                badgeClass = 'badge-danger';
                statusTexto = mensagem || '✗ Concluído com erros';
                iconHtml = '';
            }

            if (statusCell) statusCell.innerHTML = '<span class="badge-status ' + badgeClass + '" title="' + (mensagem || '') + '">' + iconHtml + statusTexto + '</span>';
        }
        return;
    }

    var linhas = document.querySelectorAll('#tabela-uploads tbody tr');
    if (linhas[index]) {
        var statusCell = linhas[index].querySelector('td:nth-child(3)');

        let badgeClass = 'badge-info';
        let statusTexto = 'Aguardando';
        let iconHtml = '<span class="spinner-carga" style="margin-right: 5px;"></span>';

        if (status === 'processing') {
            badgeClass = 'badge-warning';
            statusTexto = mensagem || 'Processando...';
            iconHtml = '<span class="spinner-carga" style="margin-right: 5px;"></span>';
        } else if (status === 'success') {
            badgeClass = 'badge-success';
            statusTexto = mensagem || '✓ Sucesso';
            iconHtml = '';
        } else if (status === 'error') {
            badgeClass = 'badge-danger';
            statusTexto = mensagem || '✗ Erro';
            iconHtml = '';
        }

        if (statusCell) statusCell.innerHTML = '<span class="badge-status ' + badgeClass + '" title="' + (mensagem || '') + '">' + iconHtml + statusTexto + '</span>';
    }
    } catch (e) { console.warn('atualizarStatusUpload:', e); }
}

function fecharModalCargaXml() {
    var modal = document.getElementById('modalCargaXml');
    if (!modal) return;
    try {
        if (typeof bootstrap !== 'undefined' && bootstrap.Modal) {
            var inst = bootstrap.Modal.getInstance(modal) || bootstrap.Modal.getOrCreateInstance(modal);
            if (inst) inst.hide();
        } else {
            modal.classList.remove('show');
            modal.style.display = 'none';
            document.body.classList.remove('modal-open');
            var backdrop = document.querySelector('.modal-backdrop');
            if (backdrop) backdrop.remove();
        }
    } catch (e) {
        console.warn('fecharModalCargaXml:', e);
    }
}

/* ===============================
   FINALIZAR CARGAS
================================ */
function finalizarCargas() {
    var tabela = document.querySelector('#tabela-uploads');
    if (tabela) {
        var sucessos = tabela.querySelectorAll('.badge-success').length;
        var erros = tabela.querySelectorAll('.badge-danger').length;
        var mensagem = 'Upload finalizado: ' + sucessos + ' sucesso(s) e ' + erros + ' erro(s)';
        Notificacoes.modal(mensagem, erros === 0 ? 'success' : 'warning', 'modalCargaXmlAlerts');
    }
    carregarTodasAsCargas();
    setTimeout(function () { limparSelecao(); }, 3000);
}

/* ===============================
   LIMPAR SELEÇÃO
================================ */
function limparSelecao() {
    var inputDiretorio = document.getElementById('file-input-diretorio');
    var inputArquivo = document.getElementById('file-input-xml');
    if (inputDiretorio) inputDiretorio.value = '';
    if (inputArquivo) inputArquivo.value = '';
    estadoCargaXml.arquivos = [];
    estadoCargaXml.modoDiretorio = false;
    estadoCargaXml.nomePasta = '';
    exibirPreviewArquivos();
}

/* ===============================
   EXTRAIR NOME DA PASTA
================================ */
function extrairNomePasta(files) {
    if (!files || files.length === 0) return '';
    var primeiroArquivo = files[0];
    if (primeiroArquivo.webkitRelativePath) {
        var partes = primeiroArquivo.webkitRelativePath.split('/');
        return partes[0] || 'Pasta selecionada';
    }
    return 'Arquivos selecionados';
}

/* ===============================
   REMOVER ARQUIVO
================================ */
function removerArquivo(index) {
    estadoCargaXml.arquivos.splice(index, 1);
    exibirPreviewArquivos();

    if (estadoCargaXml.arquivos.length === 0) {
        document.querySelector('#tabela-uploads tbody').innerHTML = `
            <tr>
                <td colspan="4" class="text-center text-muted">
                    Nenhum arquivo selecionado
                </td>
            </tr>
        `;
    }
}

/* ===============================
   ALERTAS: usar Notificacoes.pagina(mensagem, tipo) - ver PADRAO_ALERTAS.md
================================ */

/* ===============================
   UTILITÁRIOS
================================ */
function formatarTamanhoArquivo(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
}

function obterIconeTipo(tipo) {
    const ícones = {
        'NFe': '<i class="fas fa-file-invoice" style="color: #007bff; margin-right: 8px;"></i>',
        'CTe': '<i class="fas fa-truck" style="color: #28a745; margin-right: 8px;"></i>',
        'NFSe': '<i class="fas fa-receipt" style="color: #fd7e14; margin-right: 8px;"></i>',
        'Automático': '<i class="fas fa-cogs" style="color: #17a2b8; margin-right: 8px;"></i>',
        'Manual': '<i class="fas fa-hand-paper" style="color: #6c757d; margin-right: 8px;"></i>'
    };
    return ícones[tipo] || '<i class="fas fa-file-code" style="margin-right: 8px;"></i>';
}

function obterCorTipo(tipo) {
    const cores = {
        'NFe': '#007bff',
        'CTe': '#28a745',
        'NFSe': '#fd7e14'
    };
    return cores[tipo] || '#6c757d';
}

function obterBadgeStatusCarga(status) {
    const badges = {
        'Sucesso': '<span class="badge-status badge-success">✓ Sucesso</span>',
        'Processando': '<span class="badge-status badge-info"><span class="spinner-carga" style="margin-right: 5px;"></span>Processando</span>',
        'Erro': '<span class="badge-status badge-danger">✗ Erro</span>',
        'Pendente': '<span class="badge-status badge-warning">⏳ Pendente</span>',
        'SUCCESS': '<span class="badge-status badge-success">✓ Success</span>',
        'ERROR': '<span class="badge-status badge-danger">✗ Error</span>',
        'RUNNING': '<span class="badge-status badge-info">⏳ Running</span>',
        'PENDING': '<span class="badge-status badge-warning">⏳ Pending</span>'
    };
    return badges[status] || '<span class="badge-status">' + status + '</span>';
}
