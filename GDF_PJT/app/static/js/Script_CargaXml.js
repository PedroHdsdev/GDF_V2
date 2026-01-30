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
        tipos: ['NFe', 'CTe', 'NFSe']
    },
    currentPage: 1,
    itemsPerPage: 10,
    modoDiretorio: false,
    nomePasta: ''
};

/* ===============================
   INICIALIZAR ELEMENTOS
================================ */
document.addEventListener('DOMContentLoaded', function () {
    carregarTodasAsCargas();
    inicializarEventosFiltros();
});

/* ===============================
   CARREGAR TODAS AS CARGAS
================================ */
function carregarTodasAsCargas() {
    // Dados de exemplo (substituir com API real)
    estadoCargaXml.todasCargas = [
        {
            id: 1,
            arquivo: 'NF-2024-001.xml',
            tipo: 'NFe',
            numero: '123456789012345',
            empresa: 'Empresa A',
            data: '2024-01-15 10:30',
            status: 'Sucesso'
        },
        {
            id: 2,
            arquivo: 'CT-2024-001.xml',
            tipo: 'CTe',
            numero: '987654321098765',
            empresa: 'Empresa B',
            data: '2024-01-16 14:20',
            status: 'Sucesso'
        },
        {
            id: 3,
            arquivo: 'FS-2024-001.xml',
            tipo: 'NFSe',
            numero: '555666777888999',
            empresa: 'Empresa A',
            data: '2024-01-17 09:15',
            status: 'Processando'
        }
    ];
    aplicarFiltrosCarga();
    renderizarTabelaCargas();
}

/* ===============================
   EVENTOS DE FILTROS
================================ */
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
    const checkboxNFe = document.getElementById('filtro-nfe');
    const checkboxCTe = document.getElementById('filtro-cte');
    const checkboxNFSe = document.getElementById('filtro-nfse');

    if (checkboxNFe) {
        checkboxNFe.addEventListener('change', atualizarFiltrosTipo);
    }
    if (checkboxCTe) {
        checkboxCTe.addEventListener('change', atualizarFiltrosTipo);
    }
    if (checkboxNFSe) {
        checkboxNFSe.addEventListener('change', atualizarFiltrosTipo);
    }
}

function atualizarFiltrosTipo() {
    estadoCargaXml.filtros.tipos = [];

    if (document.getElementById('filtro-nfe')?.checked) {
        estadoCargaXml.filtros.tipos.push('NFe');
    }
    if (document.getElementById('filtro-cte')?.checked) {
        estadoCargaXml.filtros.tipos.push('CTe');
    }
    if (document.getElementById('filtro-nfse')?.checked) {
        estadoCargaXml.filtros.tipos.push('NFSe');
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
            const temBusca =
                carga.arquivo.toLowerCase().includes(busca) ||
                carga.numero.toLowerCase().includes(busca) ||
                carga.empresa.toLowerCase().includes(busca);

            if (!temBusca) return false;
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
        linha.innerHTML = `
            <td>
                ${iconeTipo}
                <strong>${carga.arquivo}</strong>
            </td>
            <td>
                <span class="badge" style="background-color: ${obterCorTipo(carga.tipo)}; color: white;">
                    ${carga.tipo}
                </span>
            </td>
            <td>${carga.numero}</td>
            <td>${carga.empresa}</td>
            <td>${carga.data}</td>
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

    estadoCargaXml.uploadEmProgresso = true;
    
    // Marcar todos como processando
    estadoCargaXml.arquivos.forEach((file, index) => {
        atualizarStatusUpload(index, 'processing', 'Processando...');
    });

    // Enviar todos os arquivos de uma vez
    uploadArquivosLote(estadoCargaXml.arquivos, tipoDocumento, origemDados);
}

/* ===============================
   UPLOAD EM LOTE
================================ */
function uploadArquivosLote(arquivos, tipoDocumento, origemDados) {
    const formData = new FormData();
    
    // Adicionar todos os arquivos
    arquivos.forEach(file => {
        formData.append('arquivo', file);
    });
    
    // Adicionar tipo e origem
    formData.append('type_xml', tipoDocumento);
    formData.append('origem_dados', origemDados);

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
        'NFSe': '<i class="fas fa-receipt" style="color: #fd7e14; margin-right: 8px;"></i>'
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
        'Pendente': '<span class="badge-status badge-warning">⏳ Pendente</span>'
    };
    return badges[status] || '<span class="badge-status">' + status + '</span>';
}
