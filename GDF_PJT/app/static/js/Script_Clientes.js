/* ===============================
   GERENCIAR PAGINAÇÃO & BUSCA NO CLIENTE
================================ */

const og_estado_clientes = {
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
    fn_extrair_clientes_html();
    
    fn_init_paginacao();
    fn_init_busca();
    fn_init_cliente_ins();
    fn_init_cliente_upd();
    fn_init_modal_message_cleanup();  // ✅ NOVO: Limpar messages ao abrir/fechar modal
});

/* ===============================
   EXTRAIR CLIENTES DO HTML (Enviados pelo Django)
================================ */
function fn_extrair_clientes_html() {
    const rows = document.querySelectorAll(".cliente-row");
    og_estado_clientes.allClientes = [];
    
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
        og_estado_clientes.allClientes.push(clienteData);
    });
    
    console.log(`✅ ${og_estado_clientes.allClientes.length} clientes carregados em memória`);
    console.log('📋 IDs extraídos:', og_estado_clientes.allClientes.map(c => c.id));
    console.log('📋 Primeiro cliente:', og_estado_clientes.allClientes[0]);
}

/* ===============================
   BUSCA (Client-side, sem fazer requests HTTP)
================================ */
function fn_init_busca() {
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
        og_estado_clientes.searchQuery = query;
        og_estado_clientes.currentPage = 1;  // Reset para página 1
        
        fn_atualizar_tabela_filtrada();
    });
    
    // ✅ Busca em tempo real enquanto digita
    inputBusca.addEventListener("input", (e) => {
        const query = e.target.value.trim().toLowerCase();
        og_estado_clientes.searchQuery = query;
        og_estado_clientes.currentPage = 1;
        
        fn_atualizar_tabela_filtrada();
    });
}

/* ===============================
   FILTRAR CLIENTES
================================ */
function fn_filtrar_clientes() {
    if (!og_estado_clientes.searchQuery) {
        return og_estado_clientes.allClientes;  // Sem filtro, retorna todos
    }
    
    const query = og_estado_clientes.searchQuery.toLowerCase();
    
    // ✅ Buscar em múltiplos campos
    const filtrados = og_estado_clientes.allClientes.filter(cliente => {
        return (
            cliente.codigo.toLowerCase().includes(query) ||
            cliente.razao.toLowerCase().includes(query) ||
            cliente.cnpj.toLowerCase().includes(query) ||
            cliente.data_cadastro.toLowerCase().includes(query)
        );
    });
    
    console.log(`🔎 Filtrados: ${filtrados.length} de ${og_estado_clientes.allClientes.length}`);
    return filtrados;
}

/* ===============================
   CALCULAR PAGINAÇÃO
================================ */
function fn_calcular_paginacao(clientesFiltrados) {
    const total = clientesFiltrados.length;
    const totalPages = Math.ceil(total / og_estado_clientes.itemsPerPage);
    
    // ✅ Garantir que currentPage é válida
    if (og_estado_clientes.currentPage > totalPages) {
        og_estado_clientes.currentPage = Math.max(1, totalPages);
    }
    
    const start = (og_estado_clientes.currentPage - 1) * og_estado_clientes.itemsPerPage;
    const end = start + og_estado_clientes.itemsPerPage;
    
    return {
        itemsNoInterval: clientesFiltrados.slice(start, end),
        totalPages,
        currentPage: og_estado_clientes.currentPage,
        total
    };
}

/* ===============================
   ATUALIZAR TABELA (após busca ou paginação)
================================ */
function fn_atualizar_tabela_filtrada() {
    const clientesFiltrados = fn_filtrar_clientes();
    const paginacao = fn_calcular_paginacao(clientesFiltrados);
    
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
        
        // Nota: Listeners de clique são gerenciados via delegação em fn_init_cliente_upd()
    }
    
    // ✅ Atualizar paginação
    fn_atualizar_paginacao(paginacao);
}

/* ===============================
   ADICIONAR LISTENERS NA TABELA (não usado - usar delegação)
================================ */
function fn_adicionar_listeners_tabela() {
    // NOTA: Função mantida para compatibilidade mas não usada
    // Event listeners são gerenciados via delegação em fn_init_cliente_upd()
    document.querySelectorAll(".cliente-row").forEach(row => {
        row.addEventListener("click", async (e) => {
            if (e.target.closest("a, button, input, label")) return;
            
            const clienteId = row.dataset.clienteId;
            if (!clienteId) return;
            
            await fn_carregar_cliente(clienteId);
            const modal = new bootstrap.Modal(document.getElementById("modalClienteUpd"));
            modal.show();
        });
    });
}

/* ===============================
   ATUALIZAR CONTROLES DE PAGINAÇÃO
================================ */
function fn_atualizar_paginacao(paginacao) {
    const nav = document.querySelector("nav ul.pagination");
    if (!nav) return;
    
    let html = '';
    
    // ✅ Botão "Anterior"
    if (paginacao.currentPage > 1) {
        html += `
            <li class="page-item">
                <a class="page-link" href="#" onclick="fn_ir_pagina(${paginacao.currentPage - 1}); return false;">
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
                    <a class="page-link" href="#" onclick="fn_ir_pagina(${i}); return false;">
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
                <a class="page-link" href="#" onclick="fn_ir_pagina(${paginacao.currentPage + 1}); return false;">
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
function fn_ir_pagina(pageNum) {
    og_estado_clientes.currentPage = pageNum;
    fn_atualizar_tabela_filtrada();
    window.scrollTo(0, 0);  // ✅ Scroll para o topo
}

/* ===============================
   INICIALIZAR PAGINAÇÃO
================================ */
function fn_init_paginacao() {
    // ✅ Renderizar paginação inicial
    fn_atualizar_tabela_filtrada();
}

/* ===============================
   INS – INSERT CLIENTE
================================ */ 
function fn_init_cliente_ins() {
    const modalEl = document.getElementById("modalClienteIns");
    if (!modalEl) return;

    modalEl.addEventListener("show.bs.modal", () => {
        // ✅ Fechar modal de UPDATE se estiver aberto
        fn_fechar_modal_aberto();
        
        // ✅ Marcar como modal aberto
        og_estado_clientes.modalAberto = "modalClienteIns";
        console.log("✅ Modal INSERT aberto");
    });

    modalEl.addEventListener("hidden.bs.modal", () => {
        const form = modalEl.querySelector("form");
        if (form) form.reset();
        
        // ✅ Desmarcar modal aberto
        if (og_estado_clientes.modalAberto === "modalClienteIns") {
            og_estado_clientes.modalAberto = null;
        }
    });
}

/* ===============================
   UPD – UPDATE CLIENTE
================================ */
function fn_init_cliente_upd() {
    const modalEl = document.getElementById("modalClienteUpd");
    if (!modalEl) {
        console.warn("⚠️ Modal modalClienteUpd não encontrado");
        return;
    }

    document.addEventListener("click", async (e) => {
        console.log("🖱️ Clique geral detectado:", e.target);
        
        const row = e.target.closest(".cliente-row");
        if (!row) {
            console.log("❌ Não é uma linha de cliente");
            return;
        }
        
        console.log("✅ Linha de cliente encontrada:", row);
        
        // ✅ Ignorar cliques em elementos interativos (exceto imagens)
        if (e.target.closest("a, button, input, label, .btn")) {
            console.log("⛔ Clique em elemento interativo, ignorando");
            return;
        }

        const clienteId = row.dataset.clienteId;
        console.log(`🎯 Cliente ID capturado: "${clienteId}"`);
        
        if (!clienteId) {
            console.warn("⚠️ clienteId não encontrado no dataset da row");
            console.log("Dataset completo:", row.dataset);
            return;
        }

        // ✅ Fechar modal de INSERT se estiver aberto
        fn_fechar_modal_aberto();
        
        // ✅ Marcar como modal aberto
        og_estado_clientes.modalAberto = "modalClienteUpd";
        
        // ✅ Aguardar dados serem carregados ANTES de abrir o modal
        const sucesso = await fn_carregar_cliente(clienteId);
        
        if (sucesso) {
            const modal = new bootstrap.Modal(modalEl, {
                backdrop: "static",
                keyboard: false
            });
            modal.show();
        } else {
            og_estado_clientes.modalAberto = null;
        }
    });

    modalEl.addEventListener("hidden.bs.modal", () => {
        fn_resetar_formulario();
        
        // ✅ Desmarcar modal aberto
        if (og_estado_clientes.modalAberto === "modalClienteUpd") {
            og_estado_clientes.modalAberto = null;
        }
    });
}

/* ===============================
   GERENCIAR MODAIS (prevenir múltiplos abertos)
================================ */
function fn_fechar_modal_aberto() {
    if (!og_estado_clientes.modalAberto) return;
    
    const modalElement = document.getElementById(og_estado_clientes.modalAberto);
    if (modalElement) {
        const modalInstance = bootstrap.Modal.getInstance(modalElement);
        if (modalInstance) {
            console.log(`🔒 Fechando modal: ${og_estado_clientes.modalAberto}`);
            modalInstance.hide();
            og_estado_clientes.modalAberto = null;
        }
    }
}

/* ===============================
   LOAD CLIENTE (API)
================================ */
async function fn_carregar_cliente(clienteId) {
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
        fn_preencher_formulario(data);
        
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
function fn_preencher_formulario(data) {
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
  og_estado_clientes.solucoesSelecionadas = [];
  og_estado_clientes.solucoesDisponiveis = [];
  
  if (data.solucoes_acesso && Array.isArray(data.solucoes_acesso)) {
    og_estado_clientes.solucoesSelecionadas = data.solucoes_acesso.map(sol => ({
      cod_solucao: sol.cod_solucao,
      descricao: sol.solucao_descricao,
      is_active: sol.is_active
    }));
  }
  
  // ✅ Processar soluções disponíveis (não vinculadas ainda)
  if (data.solucoes_disponiveis && Array.isArray(data.solucoes_disponiveis)) {
    og_estado_clientes.solucoesDisponiveis = data.solucoes_disponiveis.map(sol => ({
      cod_solucao: sol.cod_solucao,
      descricao: sol.descricao
    }));
  }
  
  fn_renderizar_solucoes();
  fn_preencher_select_solucoes();
}

/* ===============================
   PREENCHER SELECT DE SOLUÇÕES DISPONÍVEIS
================================ */
function fn_preencher_select_solucoes() {
  const select = document.getElementById('upd_solucoes_select');
  if (!select) return;
  
  // Limpar options existentes (mantendo o primeiro placeholder)
  while (select.options.length > 1) {
    select.removeChild(select.lastChild);
  }
  
  // Adicionar soluções disponíveis
  og_estado_clientes.solucoesDisponiveis.forEach(sol => {
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
function fn_adicionar_solucao() {
  const select = document.getElementById('upd_solucoes_select');
  if (!select.value) {
    alert('Selecione uma solução!');
    return;
  }
  
  const solCod = select.value;
  const solDescricao = select.options[select.selectedIndex].dataset.descricao;
  
  // ✅ Verificar se já foi adicionada
  if (og_estado_clientes.solucoesSelecionadas.some(s => s.cod_solucao === solCod)) {
    alert('Esta solução já foi adicionada!');
    return;
  }
  
  // Mover de disponíveis para selecionadas
  og_estado_clientes.solucoesSelecionadas.push({
    cod_solucao: solCod,
    descricao: solDescricao,
    is_active: true
  });
  
  og_estado_clientes.solucoesDisponiveis = og_estado_clientes.solucoesDisponiveis.filter(
    s => s.cod_solucao !== solCod
  );
  
  select.value = '';
  fn_renderizar_solucoes();
  fn_preencher_select_solucoes();
}

/* ===============================
   REMOVER SOLUÇÃO
================================ */
function fn_remover_solucao(codSolucao) {
  const solucao = og_estado_clientes.solucoesSelecionadas.find(s => s.cod_solucao === codSolucao);
  if (!solucao) return;
  
  // Mover de volta para disponíveis
  og_estado_clientes.solucoesDisponiveis.push({
    cod_solucao: solucao.cod_solucao,
    descricao: solucao.descricao
  });
  
  og_estado_clientes.solucoesSelecionadas = og_estado_clientes.solucoesSelecionadas.filter(
    s => s.cod_solucao !== codSolucao
  );
  
  fn_renderizar_solucoes();
  fn_preencher_select_solucoes();
}

/* ===============================
   TOGGLE STATUS SOLUÇÃO
================================ */
function fn_toggle_solucao_status(codSolucao) {
  const solucao = og_estado_clientes.solucoesSelecionadas.find(s => s.cod_solucao === codSolucao);
  if (solucao) {
    solucao.is_active = !solucao.is_active;
    fn_renderizar_solucoes();
  }
}

/* ===============================
   RENDERIZAR SOLUÇÕES SELECIONADAS
================================ */
function fn_renderizar_solucoes() {
  const tbody = document.getElementById('upd_solucoes_tbody');
  const hidden = document.getElementById('upd_solucoes_hidden');
  
  if (!tbody) return;
  
  // ✅ Limpar tbody
  tbody.innerHTML = '';
  
  if (og_estado_clientes.solucoesSelecionadas.length === 0) {
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
  og_estado_clientes.solucoesSelecionadas.forEach(sol => {
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
            onchange="fn_toggle_solucao_status('${sol.cod_solucao}')">
        </div>
      </td>
      <td class="text-center">
        <button 
          type="button" 
          class="btn btn-sm btn-danger" 
          onclick="fn_remover_solucao('${sol.cod_solucao}')">
          Remover
        </button>
      </td>
    `;
    tbody.appendChild(row);
  });
  
  // ✅ Atualizar hidden input no formato: cod1:status,cod2:status
  hidden.value = og_estado_clientes.solucoesSelecionadas
    .map(s => `${s.cod_solucao}:${s.is_active ? '1' : '0'}`)
    .join(',');
}

/* ===============================
   RESETAR FORMULÁRIO UPDATE
================================ */
function fn_resetar_formulario() {
  // Resetar para aba inicial
  const firstTab = document.querySelector('#clienteTabs .nav-link:first-child');
  if (firstTab) {
    firstTab.click();
  }
}

// Função para formatar CNPJ
function fn_formatar_cnpj(input) {
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
      fn_formatar_cnpj(this);
    });
  });
});

function fn_validar_formulario_ins(event) {
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

function fn_validar_formulario_upd(event) {
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
function fn_init_modal_message_cleanup() {
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
