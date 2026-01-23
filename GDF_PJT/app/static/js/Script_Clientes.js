/* ===============================
   GERENCIAR PAGINAÇÃO & BUSCA NO CLIENTE
================================ */

const clientesState = {
    allClientes: [],      // ✅ Todos os clientes carregados uma vez
    itemsPerPage: 30,
    currentPage: 1,
    searchQuery: '',
    originalFormData: {}
};

document.addEventListener("DOMContentLoaded", () => {
    // ✅ Carregar dados da tabela no HTML e armazenar em memória
    extrairClientesDoHTML();
    
    initPaginacao();
    initBusca();
    initClienteIns();
    initClienteUpd();
});

/* ===============================
   EXTRAIR CLIENTES DO HTML (Enviados pelo Django)
================================ */
function extrairClientesDoHTML() {
    const rows = document.querySelectorAll(".cliente-row");
    clientesState.allClientes = [];
    
    rows.forEach(row => {
        // ✅ Extrair dados estruturados da linha (seguindo ordem da tabela)
        const cells = row.querySelectorAll("td");
        const clienteData = {
            id: row.dataset.clienteId,
            html: row.innerHTML,
            // Ordem: Código, Razão Social, CNPJ, Ativo, Data de Cadastro
            codigo: cells[0]?.textContent.trim() || '',
            razao: cells[1]?.textContent.trim() || '',
            cnpj: cells[2]?.textContent.trim() || '',
            ativo: cells[3]?.textContent.trim() || '',
            data_cadastro: cells[4]?.textContent.trim() || ''
        };
        clientesState.allClientes.push(clienteData);
    });
    
    console.log(`✅ ${clientesState.allClientes.length} clientes carregados em memória`);
    console.log('📋 Primeiro cliente:', clientesState.allClientes[0]);
}

/* ===============================
   BUSCA (Client-side, sem fazer requests HTTP)
================================ */
function initBusca() {
    const formBusca = document.querySelector("form");
    if (!formBusca) {
        console.warn("⚠️ Formulário de busca não encontrado");
        return;
    }
    
    const inputBusca = formBusca.querySelector("input[name='Buscar']");
    if (!inputBusca) {
        console.warn("⚠️ Input de busca não encontrado");
        return;
    }
    
    console.log("✅ Busca inicializada");
    
    // ✅ Prevenir form submit tradicional, usar busca no cliente
    formBusca.addEventListener("submit", (e) => {
        e.preventDefault();
        
        const query = inputBusca.value.trim().toLowerCase();
        console.log(`🔍 Buscando por: "${query}"`);
        clientesState.searchQuery = query;
        clientesState.currentPage = 1;  // Reset para página 1
        
        atualizarTabelaFiltrada();
    });
    
    // ✅ Busca em tempo real enquanto digita
    inputBusca.addEventListener("input", (e) => {
        const query = e.target.value.trim().toLowerCase();
        clientesState.searchQuery = query;
        clientesState.currentPage = 1;
        
        atualizarTabelaFiltrada();
    });
}

/* ===============================
   FILTRAR CLIENTES
================================ */
function filtrarClientes() {
    if (!clientesState.searchQuery) {
        return clientesState.allClientes;  // Sem filtro, retorna todos
    }
    
    const query = clientesState.searchQuery.toLowerCase();
    
    // ✅ Buscar em múltiplos campos
    const filtrados = clientesState.allClientes.filter(cliente => {
        return (
            cliente.codigo.toLowerCase().includes(query) ||
            cliente.razao.toLowerCase().includes(query) ||
            cliente.cnpj.toLowerCase().includes(query) ||
            cliente.data_cadastro.toLowerCase().includes(query)
        );
    });
    
    console.log(`🔎 Filtrados: ${filtrados.length} de ${clientesState.allClientes.length}`);
    return filtrados;
}

/* ===============================
   CALCULAR PAGINAÇÃO
================================ */
function calcularPaginacao(clientesFiltrados) {
    const total = clientesFiltrados.length;
    const totalPages = Math.ceil(total / clientesState.itemsPerPage);
    
    // ✅ Garantir que currentPage é válida
    if (clientesState.currentPage > totalPages) {
        clientesState.currentPage = Math.max(1, totalPages);
    }
    
    const start = (clientesState.currentPage - 1) * clientesState.itemsPerPage;
    const end = start + clientesState.itemsPerPage;
    
    return {
        itemsNoInterval: clientesFiltrados.slice(start, end),
        totalPages,
        currentPage: clientesState.currentPage,
        total
    };
}

/* ===============================
   ATUALIZAR TABELA (após busca ou paginação)
================================ */
function atualizarTabelaFiltrada() {
    const clientesFiltrados = filtrarClientes();
    const paginacao = calcularPaginacao(clientesFiltrados);
    
    const tbody = document.querySelector("table tbody");
    if (!tbody) return;
    
    // ✅ Se não há resultados
    if (paginacao.itemsNoInterval.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="5" class="text-center py-3">
                    Nenhum cliente encontrado
                </td>
            </tr>
        `;
    } else {
        // ✅ Renderizar apenas clientes da página atual usando HTML guardado
        tbody.innerHTML = paginacao.itemsNoInterval
            .map(cliente => `<tr class="cliente-row" data-cliente-id="${cliente.id}">${cliente.html}</tr>`)
            .join('');
        
        // ✅ Re-adicionar listeners de clique após renderizar
        adicionarListenersDaTabela();
    }
    
    // ✅ Atualizar paginação
    atualizarPaginacao(paginacao);
}

/* ===============================
   ADICIONAR LISTENERS NA TABELA
================================ */
function adicionarListenersDaTabela() {
    document.querySelectorAll(".cliente-row").forEach(row => {
        row.addEventListener("click", async (e) => {
            if (e.target.closest("a, button, input, label")) return;
            
            const clienteId = row.dataset.clienteId;
            if (!clienteId) return;
            
            await loadCliente(clienteId);
            const modal = new bootstrap.Modal(document.getElementById("modalClienteUpd"));
            modal.show();
        });
    });
}

/* ===============================
   ATUALIZAR CONTROLES DE PAGINAÇÃO
================================ */
function atualizarPaginacao(paginacao) {
    const nav = document.querySelector("nav ul.pagination");
    if (!nav) return;
    
    let html = '';
    
    // ✅ Botão "Anterior"
    if (paginacao.currentPage > 1) {
        html += `
            <li class="page-item">
                <a class="page-link" href="#" onclick="irParaPagina(${paginacao.currentPage - 1}); return false;">
                    Anterior
                </a>
            </li>
        `;
    }
    
    // ✅ Números de página (mostrar 5 em torno da atual)
    const start = Math.max(1, paginacao.currentPage - 2);
    const end = Math.min(paginacao.totalPages, paginacao.currentPage + 2);
    
    for (let i = start; i <= end; i++) {
        if (i === paginacao.currentPage) {
            html += `<li class="page-item active"><span class="page-link">${i}</span></li>`;
        } else {
            html += `
                <li class="page-item">
                    <a class="page-link" href="#" onclick="irParaPagina(${i}); return false;">
                        ${i}
                    </a>
                </li>
            `;
        }
    }
    
    // ✅ Botão "Próxima"
    if (paginacao.currentPage < paginacao.totalPages) {
        html += `
            <li class="page-item">
                <a class="page-link" href="#" onclick="irParaPagina(${paginacao.currentPage + 1}); return false;">
                    Próxima
                </a>
            </li>
        `;
    }
    
    nav.innerHTML = html;
}

/* ===============================
   IR PARA PÁGINA (Chamado pelos links)
================================ */
function irParaPagina(pageNum) {
    clientesState.currentPage = pageNum;
    atualizarTabelaFiltrada();
    window.scrollTo(0, 0);  // ✅ Scroll para o topo
}

/* ===============================
   INICIALIZAR PAGINAÇÃO
================================ */
function initPaginacao() {
    // ✅ Paginação já é gerenciada via irParaPagina()
    // Aqui apenas garantimos a primeira renderização
}

/* ===============================
   INS – INSERT CLIENTE
================================ */ 
function initClienteIns() {
    const modalEl = document.getElementById("modalClienteIns");
    if (!modalEl) return;

    modalEl.addEventListener("hidden.bs.modal", () => {
        const form = modalEl.querySelector("form");
        if (form) form.reset();
    });
}

/* ===============================
   UPD – UPDATE CLIENTE
================================ */
function initClienteUpd() {
    const modalEl = document.getElementById("modalClienteUpd");
    if (!modalEl) return;

    document.addEventListener("click", async (e) => {
        const row = e.target.closest(".cliente-row");
        if (!row) return;
        
        if (e.target.closest("a, button, input, label")) return;

        const clienteId = row.dataset.clienteId;
        if (!clienteId) return;

        await loadCliente(clienteId);
        const modal = new bootstrap.Modal(modalEl, {
            backdrop: "static",
            keyboard: false
        });
        modal.show();
    });

    modalEl.addEventListener("hidden.bs.modal", () => {
        resetarFormularioUpd();
    });
}

/* ===============================
   LOAD CLIENTE (API)
================================ */
async function loadCliente(clienteId) {
    try {
        const resp = await fetch(`/cliente/${clienteId}/`, {
            headers: { 
                "X-Requested-With": "XMLHttpRequest",
                "Accept": "application/json"
            }
        });

        if (!resp.ok) {
            console.error(`Erro ao carregar cliente: ${resp.status} - ${resp.statusText}`);
            alert(`Erro ao carregar cliente: ${resp.statusText}`);
            return;
        }

        const data = await resp.json();
        console.log("📥 Dados do cliente recebidos:", data);

        // ✅ Preencher o formulário modal
        preencherFormularioCliente(data);

    } catch (err) {
        console.error("Erro ao fazer fetch do cliente:", err);
        alert("Erro ao carregar dados do cliente");
    }
}

/* ===============================
   PREENCHER FORMULÁRIO UPDATE
================================ */
function preencherFormularioCliente(data) {
  // Atualizar action dos forms com o ID do cliente
  document.getElementById('formClienteUpd').action = `/cliente/${data.cod_cliente}/`;
  document.getElementById('formAcessoUpd').action = `/cliente/${data.cod_cliente}/`;
  
  // Dados do cliente
  document.getElementById('upd_cliente_id').value = data.cod_cliente || '';
  document.getElementById('upd_cliente_id_acesso').value = data.cod_cliente || '';
  document.getElementById('upd_codigo').value = data.cod_cliente || '';
  document.getElementById('upd_razao').value = data.razao || '';
  document.getElementById('upd_fantasia').value = data.fantasia || '';
  document.getElementById('upd_cnpj').value = data.cnpj || '';
  document.getElementById('upd_ie').value = data.ie || '';
  document.getElementById('upd_im').value = data.im || '';
  document.getElementById('upd_inscricao_municipal').value = data.inscricao_municipal || '';
  document.getElementById('upd_tipo').value = data.tipo || '';
  document.getElementById('upd_ativo').checked = data.is_active || false;
  
  // Endereço
  document.getElementById('upd_endereco').value = data.endereco || '';
  document.getElementById('upd_numero').value = data.numero || '';
  document.getElementById('upd_complemento').value = data.complemento || '';
  document.getElementById('upd_bairro').value = data.bairro || '';
  document.getElementById('upd_cidade').value = data.cidade || '';
  document.getElementById('upd_estado').value = data.estado || '';
  document.getElementById('upd_cep').value = data.cep || '';
  
  // Contato
  document.getElementById('upd_telefone').value = data.telefone || '';
  document.getElementById('upd_email').value = data.email || '';
  
  // Salvar estado original
  saveOriginalFormData();
}

/* ===============================
   RESETAR FORMULÁRIO UPDATE
================================ */
function resetarFormularioUpd() {
  // Resetar para aba inicial
  const firstTab = document.querySelector('#clienteTabs .nav-link:first-child');
  if (firstTab) {
    firstTab.click();
  }
  
  // Resetar botões
  document.getElementById('btn-edit').style.display = 'inline-block';
  document.getElementById('btn-save').style.display = 'none';
  document.getElementById('btn-cancel').style.display = 'none';
  
  // Tornar campos readonly novamente
  const editableFields = [
    'upd_razao',
    'upd_fantasia',
    'upd_ie',
    'upd_im',
    'upd_inscricao_municipal',
    'upd_tipo',
    'upd_endereco',
    'upd_numero',
    'upd_complemento',
    'upd_bairro',
    'upd_cidade',
    'upd_estado',
    'upd_cep',
    'upd_telefone',
    'upd_email'
  ];
  
  editableFields.forEach(fieldId => {
    const field = document.getElementById(fieldId);
    if (field) {
      field.setAttribute('readonly', 'readonly');
    }
  });
  
  // Desabilitar checkbox ativo
  const ativoCheckbox = document.getElementById('upd_ativo');
  if (ativoCheckbox) {
    ativoCheckbox.setAttribute('disabled', 'disabled');
  }
}

// Função para tornar campos editáveis
function makeEditable() {
  const editableFields = [
    'upd_razao',
    'upd_fantasia',
    'upd_ie',
    'upd_im',
    'upd_inscricao_municipal',
    'upd_tipo',
    'upd_endereco',
    'upd_numero',
    'upd_complemento',
    'upd_bairro',
    'upd_cidade',
    'upd_estado',
    'upd_cep',
    'upd_telefone',
    'upd_email'
  ];

  editableFields.forEach(fieldId => {
    const field = document.getElementById(fieldId);
    if (field) {
      field.removeAttribute('readonly');
    }
  });

  // Habilitar checkbox ativo
  const ativoCheckbox = document.getElementById('upd_ativo');
  if (ativoCheckbox) {
    ativoCheckbox.removeAttribute('disabled');
  }

  // Trocar botões
  document.getElementById('btn-edit').style.display = 'none';
  document.getElementById('btn-save').style.display = 'inline-block';
  document.getElementById('btn-cancel').style.display = 'inline-block';
}

// Função para cancelar edição
function cancelChanges() {
  // Restaurar valores originais
  restoreOriginalFormData();

  // Tornar campos readonly novamente
  const editableFields = [
    'upd_razao',
    'upd_fantasia',
    'upd_ie',
    'upd_im',
    'upd_inscricao_municipal',
    'upd_tipo',
    'upd_endereco',
    'upd_numero',
    'upd_complemento',
    'upd_bairro',
    'upd_cidade',
    'upd_estado',
    'upd_cep',
    'upd_telefone',
    'upd_email'
  ];

  editableFields.forEach(fieldId => {
    const field = document.getElementById(fieldId);
    if (field) {
      field.setAttribute('readonly', 'readonly');
    }
  });

  // Desabilitar checkbox ativo
  const ativoCheckbox = document.getElementById('upd_ativo');
  if (ativoCheckbox) {
    ativoCheckbox.setAttribute('disabled', 'disabled');
  }

  // Trocar botões
  document.getElementById('btn-edit').style.display = 'inline-block';
  document.getElementById('btn-save').style.display = 'none';
  document.getElementById('btn-cancel').style.display = 'none';
}

// Salvar estado original do formulário
function saveOriginalFormData() {
  clientesState.originalFormData = {
    razao: document.getElementById('upd_razao').value,
    fantasia: document.getElementById('upd_fantasia').value,
    ie: document.getElementById('upd_ie').value,
    im: document.getElementById('upd_im').value,
    inscricao_municipal: document.getElementById('upd_inscricao_municipal').value,
    tipo: document.getElementById('upd_tipo').value,
    ativo: document.getElementById('upd_ativo').checked,
    endereco: document.getElementById('upd_endereco').value,
    numero: document.getElementById('upd_numero').value,
    complemento: document.getElementById('upd_complemento').value,
    bairro: document.getElementById('upd_bairro').value,
    cidade: document.getElementById('upd_cidade').value,
    estado: document.getElementById('upd_estado').value,
    cep: document.getElementById('upd_cep').value,
    telefone: document.getElementById('upd_telefone').value,
    email: document.getElementById('upd_email').value
  };
}

// Restaurar estado original do formulário
function restoreOriginalFormData() {
  if (Object.keys(clientesState.originalFormData).length === 0) return;

  document.getElementById('upd_razao').value = clientesState.originalFormData.razao || '';
  document.getElementById('upd_fantasia').value = clientesState.originalFormData.fantasia || '';
  document.getElementById('upd_ie').value = clientesState.originalFormData.ie || '';
  document.getElementById('upd_im').value = clientesState.originalFormData.im || '';
  document.getElementById('upd_inscricao_municipal').value = clientesState.originalFormData.inscricao_municipal || '';
  document.getElementById('upd_tipo').value = clientesState.originalFormData.tipo || '';
  document.getElementById('upd_ativo').checked = clientesState.originalFormData.ativo || false;
  document.getElementById('upd_endereco').value = clientesState.originalFormData.endereco || '';
  document.getElementById('upd_numero').value = clientesState.originalFormData.numero || '';
  document.getElementById('upd_complemento').value = clientesState.originalFormData.complemento || '';
  document.getElementById('upd_bairro').value = clientesState.originalFormData.bairro || '';
  document.getElementById('upd_cidade').value = clientesState.originalFormData.cidade || '';
  document.getElementById('upd_estado').value = clientesState.originalFormData.estado || '';
  document.getElementById('upd_cep').value = clientesState.originalFormData.cep || '';
  document.getElementById('upd_telefone').value = clientesState.originalFormData.telefone || '';
  document.getElementById('upd_email').value = clientesState.originalFormData.email || '';
}

// Função para formatar CNPJ (opcional)
function formatCNPJ(input) {
  let value = input.value.replace(/\D/g, '');
  
  if (value.length <= 14) {
    value = value.replace(/^(\d{2})(\d)/, '$1.$2');
    value = value.replace(/^(\d{2})\.(\d{3})(\d)/, '$1.$2.$3');
    value = value.replace(/\.(\d{3})(\d)/, '.$1/$2');
    value = value.replace(/(\d{4})(\d)/, '$1-$2');
  }
  
  input.value = value;
}

// Adicionar formatação automática ao campo CNPJ
document.addEventListener('DOMContentLoaded', () => {
  const cnpjInputs = document.querySelectorAll('input[name="cnpj"], input[name="upd_cnpj"]');
  cnpjInputs.forEach(input => {
    input.addEventListener('input', function() {
      formatCNPJ(this);
    });
  });
});

function validarFormularioIns(event) {
    event.preventDefault();
    
    const cnpj = document.querySelector('input[name="m_cnpj"]').value.trim();
    const razao = document.querySelector('input[name="m_razao"]').value.trim();
    
    const errors = [];
    if (!cnpj) errors.push("CNPJ é obrigatório");
    if (!razao) errors.push("Razão Social é obrigatória");
    
    if (errors.length > 0) {
        alert("❌ Erros:\n\n" + errors.join("\n"));
        return false;
    }
    
    event.target.submit();
}

function validarFormularioUpd(event) {
    event.preventDefault();
    
    const razao = document.getElementById('upd_razao').value.trim();
    const cnpj = document.getElementById('upd_cnpj').value.trim();
    
    const errors = [];
    if (!razao) errors.push("Razão Social é obrigatória");
    if (!cnpj) errors.push("CNPJ é obrigatório");
    
    if (errors.length > 0) {
        alert("❌ Erros:\n\n" + errors.join("\n"));
        return false;
    }
    
    event.target.submit();
}
