/* ===============================
   GERENCIAR PAGINAÇÃO & BUSCA NO CLIENTE
================================ */

const clientesState = {
    allClientes: [],      // ✅ Todos os clientes carregados uma vez
    itemsPerPage: 30,
    currentPage: 1,
    searchQuery: '',
    originalFormData: {},
    modalAberto: null,    // ✅ Controlar qual modal está aberto
    solucoesSelecionadas: [],  // ✅ Array de soluções selecionadas
    solucoesDisponiveis: []    // ✅ Lista de soluções disponíveis para adicionar
};

document.addEventListener("DOMContentLoaded", () => {
    // ✅ Carregar dados da tabela no HTML e armazenar em memória
    extrairClientesDoHTML();
    
    initPaginacao();
    initBusca();
    initClienteIns();
    initClienteUpd();
    initModalMessageCleanup();  // ✅ NOVO: Limpar messages ao abrir/fechar modal
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

    modalEl.addEventListener("show.bs.modal", () => {
        // ✅ Fechar modal de UPDATE se estiver aberto
        fecharModalAbertoCliente();
        
        // ✅ Marcar como modal aberto
        clientesState.modalAberto = "modalClienteIns";
        console.log("✅ Modal INSERT aberto");
    });

    modalEl.addEventListener("hidden.bs.modal", () => {
        const form = modalEl.querySelector("form");
        if (form) form.reset();
        
        // ✅ Desmarcar modal aberto
        if (clientesState.modalAberto === "modalClienteIns") {
            clientesState.modalAberto = null;
        }
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

        // ✅ Fechar modal de INSERT se estiver aberto
        fecharModalAbertoCliente();
        
        // ✅ Marcar como modal aberto
        clientesState.modalAberto = "modalClienteUpd";
        
        // ✅ Aguardar dados serem carregados ANTES de abrir o modal
        const sucesso = await loadCliente(clienteId);
        
        if (sucesso) {
            const modal = new bootstrap.Modal(modalEl, {
                backdrop: "static",
                keyboard: false
            });
            modal.show();
        } else {
            clientesState.modalAberto = null;
        }
    });

    modalEl.addEventListener("hidden.bs.modal", () => {
        resetarFormularioUpd();
        
        // ✅ Desmarcar modal aberto
        if (clientesState.modalAberto === "modalClienteUpd") {
            clientesState.modalAberto = null;
        }
    });
}

/* ===============================
   GERENCIAR MODAIS (prevenir múltiplos abertos)
================================ */
function fecharModalAbertoCliente() {
    if (!clientesState.modalAberto) return;
    
    const modalElement = document.getElementById(clientesState.modalAberto);
    if (modalElement) {
        const modalInstance = bootstrap.Modal.getInstance(modalElement);
        if (modalInstance) {
            console.log(`🔒 Fechando modal: ${clientesState.modalAberto}`);
            modalInstance.hide();
            clientesState.modalAberto = null;
        }
    }
}

/* ===============================
   LOAD CLIENTE (API)
================================ */
async function loadCliente(clienteId) {
    try {
        console.log(`📥 Iniciando carregamento do cliente ${clienteId}...`);
        
        const resp = await fetch(`/cliente/${clienteId}/`, {
            headers: { 
                "X-Requested-With": "XMLHttpRequest",
                "Accept": "application/json"
            }
        });

        if (!resp.ok) {
            console.error(`Erro ao carregar cliente: ${resp.status} - ${resp.statusText}`);
            alert(`Erro ao carregar cliente: ${resp.statusText}`);
            return false;  // ✅ Retornar false se falhar
        }

        const data = await resp.json();
        console.log("✅ Dados do cliente recebidos com sucesso");

        // ✅ Preencher o formulário modal
        preencherFormularioCliente(data);
        
        return true;  // ✅ Retornar true se sucesso

    } catch (err) {
        console.error("Erro ao fazer fetch do cliente:", err);
        alert("Erro ao carregar dados do cliente");
        return false;  // ✅ Retornar false se erro
    }
}

/* ===============================
   PREENCHER FORMULÁRIO UPDATE
================================ */
function preencherFormularioCliente(data) {
  // Atualizar action dos forms com o ID do cliente
  document.getElementById('formClienteUpd').action = `/cliente/${data.cod_cliente}/`;
  document.getElementById('formAcessoUpd').action = `/cliente/Acesso/`;
  
  // Dados do cliente
  document.getElementById('upd_cliente_id').value = data.cod_cliente || '';
  document.getElementById('Acesso_cliente_id').value = data.cod_cliente || '';
  document.getElementById('upd_codigo').value = data.cod_cliente || '';
  document.getElementById('upd_razao').value = data.razao || '';
  document.getElementById('upd_cnpj').value = data.cnpj || '';
  document.getElementById('upd_clie_active').checked = Boolean(data.is_active) || false;
  
  // ✅ Processar soluções já vinculadas ao cliente
  clientesState.solucoesSelecionadas = [];
  clientesState.solucoesDisponiveis = [];
  
  if (data.solucoes_acesso && Array.isArray(data.solucoes_acesso)) {
    clientesState.solucoesSelecionadas = data.solucoes_acesso.map(sol => ({
      cod_solucao: sol.cod_solucao,
      descricao: sol.solucao_descricao,
      is_active: sol.is_active
    }));
  }
  
  // ✅ Processar soluções disponíveis (não vinculadas ainda)
  if (data.solucoes_disponiveis && Array.isArray(data.solucoes_disponiveis)) {
    clientesState.solucoesDisponiveis = data.solucoes_disponiveis.map(sol => ({
      cod_solucao: sol.cod_solucao,
      descricao: sol.descricao
    }));
  }
  
  renderizarSolucoesSelecionadas();
  preencherSelectSolucoes();
}

/* ===============================
   PREENCHER SELECT DE SOLUÇÕES DISPONÍVEIS
================================ */
function preencherSelectSolucoes() {
  const select = document.getElementById('upd_solucoes_select');
  if (!select) return;
  
  // Limpar options existentes (mantendo o primeiro placeholder)
  while (select.options.length > 1) {
    select.removeChild(select.lastChild);
  }
  
  // Adicionar soluções disponíveis
  clientesState.solucoesDisponiveis.forEach(sol => {
    const option = document.createElement('option');
    option.value = sol.cod_solucao;
    option.textContent = `${sol.cod_solucao} - ${sol.descricao}`;
    option.dataset.descricao = sol.descricao;
    select.appendChild(option);
  });
}

/* ===============================
   ADICIONAR SOLUÇÃO
================================ */
function adicionarSolucao() {
  const select = document.getElementById('upd_solucoes_select');
  if (!select.value) {
    alert('Selecione uma solução!');
    return;
  }
  
  const solCod = select.value;
  const solDescricao = select.options[select.selectedIndex].dataset.descricao;
  
  // ✅ Verificar se já foi adicionada
  if (clientesState.solucoesSelecionadas.some(s => s.cod_solucao === solCod)) {
    alert('Esta solução já foi adicionada!');
    return;
  }
  
  // Mover de disponíveis para selecionadas
  clientesState.solucoesSelecionadas.push({
    cod_solucao: solCod,
    descricao: solDescricao,
    is_active: true
  });
  
  clientesState.solucoesDisponiveis = clientesState.solucoesDisponiveis.filter(
    s => s.cod_solucao !== solCod
  );
  
  select.value = '';
  renderizarSolucoesSelecionadas();
  preencherSelectSolucoes();
}

/* ===============================
   REMOVER SOLUÇÃO
================================ */
function removerSolucao(codSolucao) {
  const solucao = clientesState.solucoesSelecionadas.find(s => s.cod_solucao === codSolucao);
  if (!solucao) return;
  
  // Mover de volta para disponíveis
  clientesState.solucoesDisponiveis.push({
    cod_solucao: solucao.cod_solucao,
    descricao: solucao.descricao
  });
  
  clientesState.solucoesSelecionadas = clientesState.solucoesSelecionadas.filter(
    s => s.cod_solucao !== codSolucao
  );
  
  renderizarSolucoesSelecionadas();
  preencherSelectSolucoes();
}

/* ===============================
   TOGGLE STATUS SOLUÇÃO
================================ */
function toggleSolucaoStatus(codSolucao) {
  const solucao = clientesState.solucoesSelecionadas.find(s => s.cod_solucao === codSolucao);
  if (solucao) {
    solucao.is_active = !solucao.is_active;
    renderizarSolucoesSelecionadas();
  }
}

/* ===============================
   RENDERIZAR SOLUÇÕES SELECIONADAS
================================ */
function renderizarSolucoesSelecionadas() {
  const tbody = document.getElementById('upd_solucoes_tbody');
  const hidden = document.getElementById('upd_solucoes_hidden');
  
  if (!tbody) return;
  
  // ✅ Limpar tbody
  tbody.innerHTML = '';
  
  if (clientesState.solucoesSelecionadas.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="4" class="text-center text-muted">
          Nenhuma solução vinculada
        </td>
      </tr>
    `;
    hidden.value = '';
    return;
  }
  
  // ✅ Adicionar linhas
  clientesState.solucoesSelecionadas.forEach(sol => {
    const row = document.createElement('tr');
    row.innerHTML = `
      <td>${sol.cod_solucao}</td>
      <td>${sol.descricao}</td>
      <td class="text-center">
        <div class="form-check form-switch d-flex justify-content-center">
          <input 
            class="form-check-input" 
            type="checkbox" 
            ${sol.is_active ? 'checked' : ''}
            onchange="toggleSolucaoStatus('${sol.cod_solucao}')">
        </div>
      </td>
      <td class="text-center">
        <button 
          type="button" 
          class="btn btn-sm btn-danger" 
          onclick="removerSolucao('${sol.cod_solucao}')">
          Remover
        </button>
      </td>
    `;
    tbody.appendChild(row);
  });
  
  // ✅ Atualizar hidden input no formato: cod1:status,cod2:status
  hidden.value = clientesState.solucoesSelecionadas
    .map(s => `${s.cod_solucao}:${s.is_active ? '1' : '0'}`)
    .join(',');
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
}

// Função para formatar CNPJ
function formatCNPJ(input) {
  let value = input.value.replace(/\D/g, '');
  
  if (value.length <= 14) {
    value = value.replace(/^(\d{2})(\d)/, '$1.$2');
    value = value.replace(/^(\d{2})\.(\d{3})(\d)/, '$1.$2.$3');
    value = value.replace(/^(\d{2})\.(\d{3})\.(\d{3})(\d)/, '$1.$2.$3/$4');
    value = value.replace(/^(\d{2})\.(\d{3})\.(\d{3})\/(\d{4})(\d)/, '$1.$2.$3/$4-$5');
  }
  
  input.value = value;
}

// Adicionar formatação automática ao campo CNPJ
document.addEventListener('DOMContentLoaded', () => {
  const cnpjInputs = document.querySelectorAll('input[name="m_cnpj"], input[name="upd_cnpj"]');
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

// ✅ Handler para enviar acessos
document.addEventListener('DOMContentLoaded', () => {
  const formAcesso = document.getElementById('formAcessoUpd');
  if (formAcesso) {
    formAcesso.addEventListener('submit', function(event) {
      event.preventDefault();
      
      console.log('[formAcessoUpd] Enviando dados de acesso...');
      console.log('[formAcessoUpd] Action:', this.action);
      console.log('[formAcessoUpd] ls_solucoes:', document.getElementById('upd_solucoes_hidden').value);
      
      // Submit do formulário
      this.submit();
    });
  }
});

// ✅ NOVO: Limpar messages ao abrir/fechar modais
function initModalMessageCleanup() {
  const modalIns = document.getElementById('modalClienteIns');
  const modalUpd = document.getElementById('modalClienteUpd');
  
  if (modalIns) {
    // Limpar messages do INSERT ao fechar
    modalIns.addEventListener('hidden.bs.modal', function() {
      const alerts = this.querySelectorAll('.alert');
      alerts.forEach(alert => {
        alert.remove();  // Remove da DOM
      });
      console.log('✅ Messages do INSERT limpas');
    });
    
    // Limpar formulário ao abrir
    modalIns.addEventListener('show.bs.modal', function() {
      const form = this.querySelector('form');
      if (form) form.reset();
      console.log('✅ Formulário INSERT resetado');
    });
  }
  
  if (modalUpd) {
    // Limpar messages do UPDATE ao fechar
    modalUpd.addEventListener('hidden.bs.modal', function() {
      const alerts = this.querySelectorAll('.alert');
      alerts.forEach(alert => {
        alert.remove();  // Remove da DOM
      });
      console.log('✅ Messages do UPDATE limpas');
    });
  }
}
