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
document.addEventListener('DOMContentLoaded', function () {
    // Tabela principal: parâmetros + filtros ativo/inativo
    carregarParametrosPrincipais();
    inicializarEventosFiltroParametrosPrincipais();
    inicializarEventosParametros();
    carregarParametrosAtivos();
    inicializarDragDropInputFiles();
    inicializarEventosJobsRenderizados();
    
    // a aba automática carrega parâmetros sempre que for mostrada
    const tabAutomatico = document.getElementById('tab-automatico');
    if (tabAutomatico) {
        tabAutomatico.addEventListener('shown.bs.tab', function () {
            carregarParametrosAtivos();
        });
    }
});

function obterCsrfToken() {
    const token = document.querySelector('[name=csrfmiddlewaretoken]');
    return token ? token.value : '';
}

/* ===============================
   INICIALIZAR DRAG & DROP E INPUT FILES
================================ */
function inicializarDragDropInputFiles() {
    // Inicializar drag & drop para diretório
    const dropZoneDiretorio = document.getElementById('drop-zone-diretorio');
    const inputDiretorio = document.getElementById('file-input-diretorio');

    if (dropZoneDiretorio && inputDiretorio) {
        dropZoneDiretorio.addEventListener('click', () => inputDiretorio.click());

        inputDiretorio.addEventListener('change', function(e) {
            if (e.target.files && e.target.files.length > 0) {
                estadoCargaXml.modoDiretorio = true;
                estadoCargaXml.nomePasta = extrairNomePasta(e.target.files);
                processarArquivos(e.target.files);
                exibirPreviewArquivos();
            }
        });
    }

    // Inicializar botão enviar
    const btnEnviar = document.getElementById('btn-enviar-xml');
    if (btnEnviar) {
        btnEnviar.addEventListener('click', function() {
            iniciarUpload();
        });
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

    fetch('/api/cargaxml/parametros/')
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
                <td colspan="4" class="text-center text-muted py-4">
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

    fetch(`/api/cargaxml/jobs/?parametro_id=${paramId}`)
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
    fetch(`/api/cargaxml/parametros/${paramId}/`)
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
    fetch('/api/cargaxml/jobs/')
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
                mostrarAlerta('Erro ao carregar jobs: Cliente não identificado', 'error');
                estadoCargaXml.todasCargas = [];
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
                // Se o template já renderizou jobs (server-side), não sobrescrever
                const serverRows = document.querySelectorAll('#tabela-cargas tbody .job-row');
                if (serverRows && serverRows.length > 0) {
                    console.log('Mantendo jobs renderizados pelo servidor (nenhuma alteração pela API).');
                    // não alterar estadoCargaXml.todasCargas nem re-renderizar
                    return;
                }
                estadoCargaXml.todasCargas = [];
            } else {
                console.error('Erro ao carregar jobs:', data.mensagem);
                mostrarAlerta(data.mensagem || 'Erro ao carregar jobs', 'error');
                estadoCargaXml.todasCargas = [];
            }
            aplicarFiltrosCarga();
            renderizarTabelaCargas();
        })
        .catch(erro => {
            console.error('Erro na requisição:', erro);
            mostrarAlerta('Erro ao conectar na API: ' + erro.message, 'error');
            estadoCargaXml.todasCargas = [];
            aplicarFiltrosCarga();
            renderizarTabelaCargas();
        });
}

/* ===============================
   EVENTOS DE FILTROS
================================ */


function abrirModalJob(jobId) {
    fetch(`/api/cargaxml/jobs/${jobId}/`)
        .then(resp => resp.json())
        .then(data => {
            if (!data.sucesso) {
                mostrarAlerta('❌ Não foi possível carregar detalhes do job', 'error');
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
                log.forEach((line, idx) => {
                    const tr = document.createElement('tr');
                    tr.innerHTML = `<td>${idx+1}</td><td>${line}</td>`;
                    tbodyLog.appendChild(tr);
                });
            }
            var modal = new bootstrap.Modal(document.getElementById('modalJobDetails'));
            modal.show();
        })
        .catch(() => {
            mostrarAlerta('❌ Falha ao carregar detalhes do job', 'error');
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
    const origemDados = document.getElementById('param-origem-dados')?.value || 'LOCAL';
    const diretorio = document.getElementById('param-diretorio')?.value || '';
    const empresaId = document.getElementById('param-edit-empresa')?.value || '';
    const ativo = document.getElementById('param-ativo')?.checked || false;

    if (!horario || !diretorio || !empresaId) {
        mostrarAlerta('⚠️ Preencha horario, diretorio e empresa', 'warning');
        return;
    }

    fetch('/api/cargaxml/parametros/', {
        method: 'POST',
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
                mostrarAlerta(`❌ ${data.mensagem || 'Erro ao salvar parametros'}`, 'error');
                return;
            }
            mostrarAlerta('✅ Parametros salvos com sucesso', 'success');
            carregarParametrosAtivos();
            carregarParametrosPrincipais();
        })
        .catch(() => {
            mostrarAlerta('❌ Falha ao salvar parametros', 'error');
        });
}

function carregarParametrosAtivos() {
    const tabela = document.querySelector('#tabela-parametros tbody');
    if (!tabela) return;

    fetch('/api/cargaxml/parametros/?ativo=1')
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
        mostrarAlerta('Selecione um arquivo ZIP', 'warning');
        return;
    }
    const file = fileInput.files[0];
    if (!file.name.toLowerCase().endsWith('.zip')) {
        mostrarAlerta('O arquivo deve ser .zip', 'warning');
        return;
    }
    const formData = new FormData();
    formData.append('arquivo_zip', file);
    formData.append('csrfmiddlewaretoken', obterCsrfToken());

    const btn = document.getElementById('btn-confirmar-upload-zip');
    btn.disabled = true;

    fetch(`/api/cargaxml/parametros/${paramId}/upload-zip/`, {
        method: 'POST',
        body: formData
    })
        .then(response => response.json())
        .then(data => {
            btn.disabled = false;
            if (data.sucesso) {
                mostrarAlerta(data.mensagem || 'ZIP enviado com sucesso.', 'success');
                bootstrap.Modal.getInstance(document.getElementById('modalUploadZip')).hide();
                fileInput.value = '';
            } else {
                mostrarAlerta(data.mensagem || 'Erro ao enviar ZIP', 'error');
            }
        })
        .catch(() => {
            btn.disabled = false;
            mostrarAlerta('Erro ao enviar ZIP', 'error');
        });
}

function atualizarParametroCarga() {
    const id = document.getElementById('param-edit-id')?.value;
    if (!id) {
        mostrarAlerta('⚠️ Parâmetro não identificado para edição', 'warning');
        return;
    }

    const horario = document.getElementById('param-edit-horario')?.value || '';
    const origemDados = document.getElementById('param-edit-origem-dados')?.value || 'LOCAL';
    const diretorio = document.getElementById('param-edit-diretorio')?.value || '';
    const empresaId = document.getElementById('param-edit-empresa')?.value || '';
    const ativo = document.getElementById('param-edit-ativo')?.checked || false;

    if (!horario || !diretorio || !empresaId) {
        mostrarAlerta('⚠️ Preencha horário, diretório e empresa', 'warning');
        return;
    }

    fetch(`/api/cargaxml/parametros/${id}/`, {
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
                mostrarAlerta(`❌ ${data.mensagem || 'Erro ao atualizar parâmetro'}`, 'error');
                return;
            }
            mostrarAlerta('✅ Parâmetro atualizado com sucesso', 'success');
            carregarParametrosPrincipais();
            carregarParametrosAtivos();
        })
        .catch(() => {
            mostrarAlerta('❌ Falha ao atualizar parâmetro', 'error');
        });
}

function toggleParametro(paramId, ativoAtual) {
    fetch(`/api/cargaxml/parametros/${paramId}/toggle/`, {
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
                mostrarAlerta('❌ Erro ao atualizar parametro', 'error');
                return;
            }
            carregarParametrosAtivos();
        })
        .catch(() => {
            mostrarAlerta('❌ Erro ao atualizar parametro', 'error');
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
================================ */
function processarArquivos(files) {
    const arquivosValidos = [];

    for (let file of files) {
        // Validar extensão
        if (!file.name.toLowerCase().endsWith('.xml')) {
            mostrarAlerta(`❌ ${file.name} não é um arquivo XML válido`, 'error');
            continue;
        }

        // Validar tamanho (máximo 50MB)
        if (file.size > 50 * 1024 * 1024) {
            mostrarAlerta(`❌ ${file.name} excede o tamanho máximo de 50MB`, 'error');
            continue;
        }

        arquivosValidos.push(file);
    }

    if (arquivosValidos.length > 0) {
        estadoCargaXml.arquivos = arquivosValidos;
        estadoCargaXml.totalArquivos = arquivosValidos.length;
        exibirPreviewArquivos();
    }
}

/* ===============================
   INICIAR UPLOAD
================================ */
function iniciarUpload() {
    if (estadoCargaXml.uploadEmProgresso || estadoCargaXml.arquivos.length === 0) {
        return;
    }

    estadoCargaXml.uploadEmProgresso = true;
    estadoCargaXml.uploadosRealizados = 0;

    estadoCargaXml.arquivos.forEach((file, index) => {
        uploadArquivo(file, index);
    });
}

/* ===============================
   EXIBIR PREVIEW DOS ARQUIVOS
================================ */
function exibirPreviewArquivos(files) {
    if (files) {
        processarArquivos(files);
    }
    
    const tbody = document.querySelector('#tabela-uploads tbody');
    const contador = document.getElementById('contador-arquivos');

    if (!tbody) return;
    
    if (contador) {
        contador.textContent = estadoCargaXml.arquivos.length;
    }

    tbody.innerHTML = '';

    if (estadoCargaXml.arquivos.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" class="text-center text-muted">Nenhum arquivo selecionado</td></tr>';
        return;
    }

    // MODO DIRETÓRIO: Mostrar apenas resumo da pasta
    if (estadoCargaXml.modoDiretorio) {
        const linha = document.createElement('tr');
        linha.id = 'linha-diretorio';
        linha.innerHTML = `
            <td>
                <i class="fas fa-folder" style="color: #ffc107; margin-right: 8px;"></i>
                <strong>${estadoCargaXml.nomePasta}</strong>
            </td>
            <td>${estadoCargaXml.arquivos.length} arquivo(s)</td>
            <td>
                <span class="badge-status badge-info">
                    <span class="spinner-carga" style="margin-right: 5px;"></span>
                    Aguardando
                </span>
            </td>
            <td>
                <button class="btn btn-sm btn-outline-danger" onclick="limparSelecao()">
                    <i class="fas fa-times"></i> Limpar
                </button>
            </td>
        `;
        tbody.appendChild(linha);
        return;
    }

    // MODO INDIVIDUAL: Mostrar cada arquivo
    estadoCargaXml.arquivos.forEach((file, index) => {
        const linha = document.createElement('tr');
        linha.innerHTML = `
            <td>
                <i class="fas fa-file-code" style="color: #007bff; margin-right: 8px;"></i>
                ${file.name}
            </td>
            <td>${formatarTamanhoArquivo(file.size)}</td>
            <td>
                <span class="badge-status badge-info">
                    <span class="spinner-carga" style="margin-right: 5px;"></span>
                    Aguardando
                </span>
            </td>
            <td>
                <button class="btn btn-sm btn-outline-danger" onclick="removerArquivo(${index})">
                    <i class="fas fa-trash"></i> Remover
                </button>
            </td>
        `;
        tbody.appendChild(linha);
    });
}

/* ===============================
   INICIAR UPLOAD
================================ */
function iniciarUpload() {
    if (estadoCargaXml.uploadEmProgresso || estadoCargaXml.arquivos.length === 0) {
        mostrarAlerta('⚠️ Selecione pelo menos um arquivo XML', 'warning');
        return;
    }

    // Obter tipo de documento e origem
    const tipoDocumento = document.getElementById('select-tipo-documento')?.value || 'NFe';
    const origemDados = document.getElementById('select-origem-dados')?.value || 'LOCAL';
    const empresaId = document.getElementById('select-empresa-manual')?.value || '';

    if (!empresaId) {
        mostrarAlerta('⚠️ Selecione a empresa para a carga manual', 'warning');
        return;
    }

    estadoCargaXml.uploadEmProgresso = true;
    
    // Marcar todos como processando
    estadoCargaXml.arquivos.forEach((file, index) => {
        atualizarStatusUpload(index, 'processing', 'Processando...');
    });

    // Enviar todos os arquivos de uma vez
    uploadArquivosLote(estadoCargaXml.arquivos, tipoDocumento, origemDados, empresaId);
}

/* ===============================
   UPLOAD EM LOTE
================================ */
function uploadArquivosLote(arquivos, tipoDocumento, origemDados, empresaId) {
    const formData = new FormData();
    
    // Adicionar todos os arquivos
    arquivos.forEach(file => {
        formData.append('arquivo', file);
    });
    
    // Adicionar tipo, origem e empresa
    formData.append('type_xml', tipoDocumento);
    formData.append('origem_dados', origemDados);
    if (empresaId) {
        formData.append('empresa_id', empresaId);
    }

    // Obter CSRF token
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';

    // Marcar como processando
    atualizarStatusUpload(0, 'processing', 'Enviando arquivos...');

    fetch('/api/processar-xml/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrfToken
        },
        body: formData
    })
        .then(response => response.json())
        .then(data => {
            if (data.sucesso) {
                // MODO DIRETÓRIO: Atualizar status geral
                if (estadoCargaXml.modoDiretorio) {
                    const totalSucesso = data.detalhes?.success?.length || 0;
                    const totalErro = data.detalhes?.errors?.length || 0;
                    const mensagemStatus = `${totalSucesso} processado(s), ${totalErro} erro(s)`;
                    
                    if (totalErro === 0) {
                        atualizarStatusUpload(arquivos.length - 1, 'success', `✓ ${mensagemStatus}`);
                    } else {
                        atualizarStatusUpload(arquivos.length - 1, 'error', `⚠️ ${mensagemStatus}`);
                    }
                } else {
                    // MODO INDIVIDUAL: Atualizar cada arquivo
                    if (data.detalhes && data.detalhes.success) {
                        data.detalhes.success.forEach((fileName, idx) => {
                            const index = arquivos.findIndex(f => f.name === fileName);
                            if (index !== -1) {
                                atualizarStatusUpload(index, 'success', '✓ Processado');
                            }
                        });
                    }
                    
                    // Atualizar status de arquivos com erro
                    if (data.detalhes && data.detalhes.errors) {
                        data.detalhes.errors.forEach(erro => {
                            const index = arquivos.findIndex(f => f.name === erro.file);
                            if (index !== -1) {
                                atualizarStatusUpload(index, 'error', `✗ ${erro.error}`);
                            }
                        });
                    }
                }
                
                mostrarAlerta(data.mensagem, 'success');
            } else {
                mostrarAlerta(data.mensagem || 'Erro ao processar XMLs', 'error');
                // Marcar todos como erro
                arquivos.forEach((file, index) => {
                    atualizarStatusUpload(index, 'error', '✗ Erro no processamento');
                });
            }
            
            estadoCargaXml.uploadEmProgresso = false;
            finalizarCargas();
        })
        .catch(error => {
            console.error('Erro ao fazer upload:', error);
            mostrarAlerta('Erro ao enviar arquivos: ' + error.message, 'error');
            
            // Marcar todos como erro
            arquivos.forEach((file, index) => {
                atualizarStatusUpload(index, 'error', '✗ Erro de conexão');
            });
            
            estadoCargaXml.uploadEmProgresso = false;
            finalizarCargas();
        });
}

/* ===============================
   ATUALIZAR STATUS
================================ */
function atualizarStatusUpload(index, status, mensagem) {
    // MODO DIRETÓRIO: Atualizar linha única
    if (estadoCargaXml.modoDiretorio) {
        const linhaDiretorio = document.getElementById('linha-diretorio');
        if (linhaDiretorio) {
            const statusCell = linhaDiretorio.querySelector('td:nth-child(3)');
            
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

            statusCell.innerHTML = `
                <span class="badge-status ${badgeClass}" title="${mensagem}">
                    ${iconHtml}${statusTexto}
                </span>
            `;
        }
        return;
    }

    // MODO INDIVIDUAL: Atualizar linha específica
    const linhas = document.querySelectorAll('#tabela-uploads tbody tr');

    if (linhas[index]) {
        const statusCell = linhas[index].querySelector('td:nth-child(3)');

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

        statusCell.innerHTML = `
            <span class="badge-status ${badgeClass}" title="${mensagem}">
                ${iconHtml}${statusTexto}
            </span>
        `;
    }
}

/* ===============================
   FINALIZAR CARGAS
================================ */
function finalizarCargas() {
    const sucessos = document.querySelectorAll('.badge-success').length;
    const erros = document.querySelectorAll('.badge-danger').length;

    const mensagem = `Upload finalizado: ${sucessos} sucesso(s) e ${erros} erro(s)`;

    if (erros === 0) {
        mostrarAlerta(`✅ ${mensagem}`, 'success');
    } else {
        mostrarAlerta(`⚠️ ${mensagem}`, 'warning');
    }

    // forçar atualização da lista de jobs para que o job recém-criado apareça
    carregarTodasAsCargas();

    // Limpar após 3 segundos
    setTimeout(() => {
        limparSelecao();
    }, 3000);
}

/* ===============================
   LIMPAR SELEÇÃO
================================ */
function limparSelecao() {
    const inputDiretorio = document.getElementById('file-input-diretorio');
    const inputArquivo = document.getElementById('file-input-arquivo');
    
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
    
    // Pegar o caminho do primeiro arquivo
    const primeiroArquivo = files[0];
    
    // Se tem webkitRelativePath, extrair nome da pasta
    if (primeiroArquivo.webkitRelativePath) {
        const partes = primeiroArquivo.webkitRelativePath.split('/');
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
   MOSTRAR ALERTA
================================ */
function mostrarAlerta(mensagem, tipo = 'info') {
    const container = document.getElementById('alertas-container');

    if (!container) return;

    const alert = document.createElement('div');
    alert.className = `alert-upload ${tipo}`;
    alert.innerHTML = `
        <strong>${mensagem}</strong>
        <button type="button" class="close" onclick="this.parentElement.style.display='none';">
            <span>&times;</span>
        </button>
    `;

    container.appendChild(alert);

    // Auto-remover após 5 segundos
    setTimeout(() => {
        if (alert.parentElement) {
            alert.style.transition = 'opacity 0.3s ease';
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 300);
        }
    }, 5000);
}

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
