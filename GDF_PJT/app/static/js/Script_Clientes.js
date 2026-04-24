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
    solucoesDisponiveis: [],   // ✅ Lista de soluções disponíveis para adicionar
    gruposClienteSelecionados: [],  // Grupos vinculados ao cliente
    gruposClienteDisponiveis: []    // Grupos disponíveis para adicionar
};

function fn_cli_escHtml(s) {
    const d = document.createElement('div');
    d.textContent = s == null ? '' : String(s);
    return d.innerHTML;
}

function fn_cli_escAttr(s) {
    return String(s == null ? '' : s)
        .replace(/&/g, '&amp;')
        .replace(/"/g, '&quot;')
        .replace(/</g, '&lt;');
}

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
            .map(cliente => `<tr class="cliente-row" data-cliente-id="${fn_cli_escAttr(cliente.id)}">${cliente.html}</tr>`)
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
    // NOTA: Função mantida para compatibilidade (delegação principal em fn_init_cliente_upd)
    var modalEl = document.getElementById("modalClienteUpd");
    if (!modalEl) return;
    document.querySelectorAll(".cliente-row").forEach(row => {
        row.addEventListener("click", async (e) => {
            if (e.target.closest("a, button, input, label")) return;
            const clienteId = row.dataset.clienteId;
            if (!clienteId) return;
            var sucesso = await fn_carregar_cliente(clienteId);
            if (sucesso && typeof bootstrap !== 'undefined' && bootstrap.Modal) {
                bootstrap.Modal.getOrCreateInstance(modalEl, { backdrop: 'static', keyboard: false }).show();
            }
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
        const row = e.target.closest(".cliente-row");
        if (!row) return;
        
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
        
        if (sucesso && typeof bootstrap !== 'undefined' && bootstrap.Modal) {
            const modal = bootstrap.Modal.getOrCreateInstance(modalEl, { backdrop: 'static', keyboard: false });
            modal.show();
        } else {
            og_estado_clientes.modalAberto = null;
            if (!sucesso && typeof Notificacoes !== 'undefined') {
                Notificacoes.pagina('Erro ao carregar dados do cliente. Verifique o console ou tente novamente.', 'danger');
            }
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
        
        var urlClienteUpd = (typeof window !== 'undefined' && window.APP_URLS && window.APP_URLS.clienteUpd)
            ? window.APP_URLS.clienteUpd.replace('__ID__', encodeURIComponent(clienteId))
            : ('/cliente/' + encodeURIComponent(clienteId) + '/');
        const resp = await fetch(urlClienteUpd, {
            headers: { 
                "X-Requested-With": "XMLHttpRequest",
                "Accept": "application/json"
            }
        });

        if (!resp.ok) {
            var msg = resp.statusText;
            try {
                var errBody = await resp.json();
                if (errBody && errBody.erro) msg = errBody.erro;
            } catch (e) {}
            console.error('Erro ao carregar cliente:', resp.status, msg);
            if (typeof Notificacoes !== 'undefined') {
                Notificacoes.pagina('Erro ao carregar cliente: ' + msg, 'danger');
            }
            return false;  // ✅ Retornar false se falhar
        }

        const data = await resp.json();
        console.log("✅ Dados do cliente recebidos com sucesso");

        // ✅ Preencher o formulário modal
        fn_preencher_formulario(data);
        
        return true;  // ✅ Retornar true se sucesso

    } catch (err) {
        console.error("Erro ao fazer fetch do cliente:", err);
        if (typeof Notificacoes !== 'undefined') {
            Notificacoes.pagina('Erro ao carregar dados do cliente. Verifique a conexão.', 'danger');
        }
        return false;  // ✅ Retornar false se erro
    }
}

/* ===============================
   PREENCHER FORMULÁRIO UPDATE
================================ */
function fn_preencher_formulario(data) {
  // Atualizar action dos forms com o ID do cliente
  var prefix = (typeof getUrlPrefix === 'function') ? getUrlPrefix() : '';
  var urlClienteUpd = (window.APP_URLS && window.APP_URLS.clienteUpd) ? window.APP_URLS.clienteUpd.replace('__ID__', encodeURIComponent(data.cod_cliente || '')) : (prefix || '') + '/cliente/' + (data.cod_cliente || '') + '/';
  var urlAcesso = (window.APP_URLS && window.APP_URLS.clienteAcesso) ? window.APP_URLS.clienteAcesso : (prefix || '') + '/cliente/Acesso/';
  var urlGrupos = (window.APP_URLS && window.APP_URLS.clienteGrupos) ? window.APP_URLS.clienteGrupos : (prefix || '') + '/cliente/Grupos/';
  document.getElementById('formClienteUpd').action = urlClienteUpd;
  document.getElementById('formAcessoUpd').action = urlAcesso;
  var formGruposEl = document.getElementById('formGruposUpd');
  if (formGruposEl) formGruposEl.action = urlGrupos;
  
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

  // Aba Grupo de usuários
  document.getElementById('Grupos_cliente_id').value = data.cod_cliente || '';
  og_estado_clientes.gruposClienteSelecionados = [];
  og_estado_clientes.gruposClienteDisponiveis = [];
  if (data.grupos_vinculados && Array.isArray(data.grupos_vinculados)) {
    og_estado_clientes.gruposClienteSelecionados = data.grupos_vinculados.map(g => ({
      id: Number(g.id),
      name: g.name
    }));
  }
  if (data.grupos_disponiveis && Array.isArray(data.grupos_disponiveis)) {
    og_estado_clientes.gruposClienteDisponiveis = data.grupos_disponiveis.map(g => ({
      id: Number(g.id),
      name: g.name
    }));
  }
  fn_renderizar_grupos_cliente();
  fn_preencher_select_grupos_cliente();

  // Aba Conexão SAP
  const codCliente = data.cod_cliente || '';
  document.getElementById('sap_cliente_id').value = codCliente;
  const formSap = document.getElementById('formSapUpd');
  var urlSap = (window.APP_URLS && window.APP_URLS.clienteSap) ? window.APP_URLS.clienteSap.replace('__ID__', encodeURIComponent(codCliente || '')) : (prefix || '') + '/cliente/' + (codCliente || '') + '/sap/';
  if (formSap) formSap.action = urlSap;
  const semRegistro = document.getElementById('sap-sem-registro');
  const formContainer = document.getElementById('sap-form-container');
  if (data.sap_connection) {
    semRegistro.classList.add('d-none');
    formContainer.classList.remove('d-none');
    document.getElementById('sap_id').value = data.sap_connection.id || '';
    document.getElementById('sap_ashost').value = data.sap_connection.ashost || '';
    document.getElementById('sap_sysnr').value = data.sap_connection.sysnr || '';
    document.getElementById('sap_client').value = data.sap_connection.client || '';
    document.getElementById('sap_username').value = data.sap_connection.username || '';
    document.getElementById('sap_passwd').value = data.sap_connection.passwd || '';
    document.getElementById('sap_lang').value = data.sap_connection.lang || '';
    document.getElementById('sap_active').checked = Boolean(data.sap_connection.active);
  } else {
    semRegistro.classList.remove('d-none');
    formContainer.classList.add('d-none');
    document.getElementById('sap_id').value = '';
    document.getElementById('sap_ashost').value = '';
    document.getElementById('sap_sysnr').value = '';
    document.getElementById('sap_client').value = '';
    document.getElementById('sap_username').value = '';
    document.getElementById('sap_passwd').value = '';
    document.getElementById('sap_lang').value = '';
    document.getElementById('sap_active').checked = true;
  }
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
    Notificacoes.modal('Selecione uma solução!', 'warning', 'modalClienteUpdAlerts');
    return;
  }
  
  const solCod = select.value;
  const solDescricao = select.options[select.selectedIndex].dataset.descricao;
  
  // ✅ Verificar se já foi adicionada
  if (og_estado_clientes.solucoesSelecionadas.some(s => s.cod_solucao === solCod)) {
    Notificacoes.modal('Esta solução já foi adicionada!', 'warning', 'modalClienteUpdAlerts');
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
  console.log(`[fn_toggle_solucao_status] Toggling: ${codSolucao}`);
  const solucao = og_estado_clientes.solucoesSelecionadas.find(s => s.cod_solucao === codSolucao);
  if (solucao) {
    console.log(`[fn_toggle_solucao_status] Estado antes: ${solucao.is_active}`);
    solucao.is_active = !solucao.is_active;
    console.log(`[fn_toggle_solucao_status] Estado depois: ${solucao.is_active}`);
    fn_renderizar_solucoes();
  } else {
    console.warn(`[fn_toggle_solucao_status] Solução ${codSolucao} não encontrada`);
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
    const codJs = JSON.stringify(sol.cod_solucao);
    row.innerHTML = `
      <td>${fn_cli_escHtml(sol.cod_solucao)}</td>
      <td>${fn_cli_escHtml(sol.descricao)}</td>
      <td class="text-center">
        <div class="form-check form-switch d-flex justify-content-center">
          <input 
            class="form-check-input" 
            type="checkbox" 
            ${sol.is_active ? 'checked' : ''}
            onchange="fn_toggle_solucao_status(${codJs})">
        </div>
      </td>
      <td class="text-center">
        <button 
          type="button" 
          class="btn btn-sm btn-danger" 
          onclick="fn_remover_solucao(${codJs})">
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
  
  console.log('[fn_renderizar_solucoes] hidden.value:', hidden.value);
  console.log('[fn_renderizar_solucoes] solucoesSelecionadas:', JSON.stringify(og_estado_clientes.solucoesSelecionadas));
}

/* ===============================
   PREENCHER SELECT DE GRUPOS (cliente)
================================ */
function fn_preencher_select_grupos_cliente() {
  const select = document.getElementById('upd_grupos_cliente_select');
  if (!select) return;
  while (select.options.length > 1) select.removeChild(select.lastChild);
  og_estado_clientes.gruposClienteDisponiveis.forEach(g => {
    const option = document.createElement('option');
    option.value = g.id;
    option.textContent = g.name;
    select.appendChild(option);
  });
}

/* ===============================
   RENDERIZAR GRUPOS DO CLIENTE
================================ */
function fn_renderizar_grupos_cliente() {
  const tbody = document.getElementById('upd_grupos_cliente_tbody');
  const hidden = document.getElementById('upd_grupos_cliente_hidden');
  if (!tbody) return;
  tbody.innerHTML = '';
  if (og_estado_clientes.gruposClienteSelecionados.length === 0) {
    tbody.innerHTML = '<tr><td colspan="2" class="text-center text-muted">Nenhum grupo vinculado</td></tr>';
    if (hidden) hidden.value = '';
    return;
  }
  og_estado_clientes.gruposClienteSelecionados.forEach(g => {
    const row = document.createElement('tr');
    row.innerHTML = `
      <td>${fn_cli_escHtml(g.name || '')}</td>
      <td class="text-center">
        <button type="button" class="btn btn-sm btn-danger" onclick="fn_remover_grupo_cliente(${g.id})">Remover</button>
      </td>
    `;
    tbody.appendChild(row);
  });
  if (hidden) hidden.value = og_estado_clientes.gruposClienteSelecionados.map(g => g.id).join(',');
}

/* ===============================
   ADICIONAR GRUPO AO CLIENTE
================================ */
function fn_adicionar_grupo_cliente() {
  const select = document.getElementById('upd_grupos_cliente_select');
  if (!select || !select.value) {
    Notificacoes.modal('Selecione um grupo!', 'warning', 'modalClienteUpdAlerts');
    return;
  }
  const gid = parseInt(select.value, 10);
  const gname = select.options[select.selectedIndex].text;
  if (og_estado_clientes.gruposClienteSelecionados.some(g => g.id === gid)) {
    Notificacoes.modal('Este grupo já foi adicionado!', 'warning', 'modalClienteUpdAlerts');
    return;
  }
  og_estado_clientes.gruposClienteSelecionados.push({ id: gid, name: gname });
  og_estado_clientes.gruposClienteDisponiveis = og_estado_clientes.gruposClienteDisponiveis.filter(g => g.id !== gid);
  select.value = '';
  fn_renderizar_grupos_cliente();
  fn_preencher_select_grupos_cliente();
}

/* ===============================
   REMOVER GRUPO DO CLIENTE
================================ */
function fn_remover_grupo_cliente(grupoId) {
  const g = og_estado_clientes.gruposClienteSelecionados.find(x => x.id === grupoId);
  if (!g) return;
  og_estado_clientes.gruposClienteDisponiveis.push({ id: g.id, name: g.name });
  og_estado_clientes.gruposClienteSelecionados = og_estado_clientes.gruposClienteSelecionados.filter(x => x.id !== grupoId);
  fn_renderizar_grupos_cliente();
  fn_preencher_select_grupos_cliente();
}

/* ===============================
   CONEXÃO SAP – CRIAR REGISTRO VAZIO
================================ */
async function fn_criar_sap_vazio() {
  const codCliente = document.getElementById('sap_cliente_id').value;
  if (!codCliente) {
    Notificacoes.modal('Cliente não identificado.', 'danger', 'modalClienteUpdAlerts');
    return;
  }
  const formSap = document.getElementById('formSapUpd');
  const formData = new FormData();
  formData.append('csrfmiddlewaretoken', formSap.querySelector('input[name="csrfmiddlewaretoken"]').value);
  formData.append('sap_ashost', '');
  formData.append('sap_sysnr', '');
  formData.append('sap_client', '');
  formData.append('sap_username', '');
  formData.append('sap_passwd', '');
  formData.append('sap_lang', '');
  formData.append('sap_active', 'on');
  try {
    var urlSap = (window.APP_URLS && window.APP_URLS.clienteSap) ? window.APP_URLS.clienteSap.replace('__ID__', encodeURIComponent(codCliente || '')) : ((typeof getUrlPrefix === 'function' ? getUrlPrefix() : '') || '') + '/cliente/' + encodeURIComponent(codCliente) + '/sap/';
    const resp = await fetch(urlSap, {
      method: 'POST',
      body: formData,
      headers: { 'X-Requested-With': 'XMLHttpRequest' }
    });
    const data = await resp.json();
    if (data.success && data.sap_connection) {
      document.getElementById('sap-sem-registro').classList.add('d-none');
      document.getElementById('sap-form-container').classList.remove('d-none');
      document.getElementById('sap_id').value = data.sap_connection.id || '';
      document.getElementById('sap_ashost').value = data.sap_connection.ashost || '';
      document.getElementById('sap_sysnr').value = data.sap_connection.sysnr || '';
      document.getElementById('sap_client').value = data.sap_connection.client || '';
      document.getElementById('sap_username').value = data.sap_connection.username || '';
      document.getElementById('sap_passwd').value = data.sap_connection.passwd || '';
      document.getElementById('sap_lang').value = data.sap_connection.lang || '';
      document.getElementById('sap_active').checked = Boolean(data.sap_connection.active);
      Notificacoes.modal(data.message || 'Conexão SAP criada. Preencha os dados e salve.', 'success', 'modalClienteUpdAlerts');
    } else {
      Notificacoes.modal(data.erro || 'Erro ao criar conexão SAP.', 'danger', 'modalClienteUpdAlerts');
    }
  } catch (err) {
    console.error(err);
    Notificacoes.modal('Erro ao criar conexão SAP.', 'danger', 'modalClienteUpdAlerts');
  }
}

/* ===============================
   CONEXÃO SAP – SALVAR FORMULÁRIO
================================ */
async function fn_submit_sap(form) {
  const codCliente = document.getElementById('sap_cliente_id').value;
  if (!codCliente) {
    Notificacoes.modal('Cliente não identificado.', 'danger', 'modalClienteUpdAlerts');
    return false;
  }
  const formData = new FormData(form);
  try {
    const resp = await fetch(form.action, {
      method: 'POST',
      body: formData,
      headers: { 'X-Requested-With': 'XMLHttpRequest' }
    });
    const data = await resp.json();
    if (data.success) {
      Notificacoes.modal(data.message || 'Conexão SAP salva.', 'success', 'modalClienteUpdAlerts');
      if (data.sap_connection) {
        document.getElementById('sap_id').value = data.sap_connection.id || '';
      }
    } else {
      Notificacoes.modal(data.erro || 'Erro ao salvar conexão SAP.', 'danger', 'modalClienteUpdAlerts');
    }
  } catch (err) {
    console.error(err);
    Notificacoes.modal('Erro ao salvar conexão SAP.', 'danger', 'modalClienteUpdAlerts');
  }
  return false;
}

/* ===============================
   CONEXÃO SAP – TESTAR CONEXÃO
================================ */
async function fn_testar_sap() {
  const codCliente = document.getElementById('sap_cliente_id').value;
  if (!codCliente) {
    Notificacoes.modal('Cliente não identificado.', 'danger', 'modalClienteUpdAlerts');
    return;
  }
  const btn = document.getElementById('btn-testar-sap');
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Testando...';
  }
  try {
    const csrf = document.querySelector('#formSapUpd input[name="csrfmiddlewaretoken"]');
    var prefix = (typeof getUrlPrefix === 'function') ? getUrlPrefix() : '';
    const resp = await fetch((prefix || '') + '/api/sap/testar-conexao/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Requested-With': 'XMLHttpRequest',
        'X-CSRFToken': csrf ? csrf.value : ''
      },
      body: JSON.stringify({ cod_cliente: codCliente })
    });
    const data = await resp.json();
    if (data.sucesso) {
      Notificacoes.modal(data.mensagem || 'Conexão SAP OK.', 'success', 'modalClienteUpdAlerts');
    } else {
      Notificacoes.modal(data.mensagem || 'Falha ao testar conexão SAP.', 'danger', 'modalClienteUpdAlerts');
    }
  } catch (err) {
    console.error(err);
    Notificacoes.modal('Erro ao testar conexão SAP.', 'danger', 'modalClienteUpdAlerts');
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = '<i class="bi bi-plug"></i> Testar conexão';
    }
  }
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
    
    var form = event.target;
    var codigo = (form.querySelector('input[name="m_cliente_id"]') || {}).value.trim();
    var cnpj = (form.querySelector('input[name="m_cnpj"]') || {}).value.trim();
    var razao = (form.querySelector('input[name="m_razao"]') || {}).value.trim();
    
    var errors = [];
    if (!codigo) errors.push("Código do cliente é obrigatório");
    if (!cnpj) errors.push("CNPJ é obrigatório");
    if (!razao) errors.push("Razão Social é obrigatória");
    
    if (errors.length > 0) {
        Notificacoes.modal("Erros:\n\n" + errors.join("\n"), 'danger', 'modalClienteInsAlerts');
        return false;
    }
    
    var formData = new FormData(form);
    var action = form.getAttribute('action');
    
    fetch(action, {
        method: 'POST',
        body: formData,
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
    })
    .then(function(response) {
        return response.json().then(function(data) {
            return { ok: response.ok, data: data };
        }).catch(function() {
            return { ok: response.ok, data: {} };
        });
    })
    .then(function(result) {
        if (result.ok && result.data.success) {
            Notificacoes.modal(result.data.message || 'Cliente cadastrado!', 'success', 'modalClienteInsAlerts');
            setTimeout(function() { window.location.href = window.location.pathname; }, 1500);
        } else if (result.data.erro) {
            Notificacoes.modal(result.data.erro, 'danger', 'modalClienteInsAlerts');
        } else {
            Notificacoes.modal('Erro ao cadastrar cliente. Tente novamente.', 'danger', 'modalClienteInsAlerts');
        }
    })
    .catch(function(err) {
        console.error('Erro ao enviar formulário:', err);
        Notificacoes.modal('Erro ao enviar formulário. Tente novamente.', 'danger', 'modalClienteInsAlerts');
    });
    
    return false;
}

function fn_validar_formulario_upd(event) {
    event.preventDefault();
    
    const razao = document.getElementById('upd_razao').value.trim();
    const cnpj = document.getElementById('upd_cnpj').value.trim();
    
    const errors = [];
    if (!razao) errors.push("Razão Social é obrigatória");
    if (!cnpj) errors.push("CNPJ é obrigatório");
    
    if (errors.length > 0) {
        Notificacoes.modal("❌ Erros:\n\n" + errors.join("\n"), 'danger', 'modalClienteUpdAlerts');
        return false;
    }
    
    // ✅ Submeter via AJAX ao invés de form.submit()
    fn_submit_form_ajax(event.target, 'Cliente');
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
      
      // ✅ Submeter via AJAX
      fn_submit_form_ajax(this, 'Acesso');
    });
  }

  const formGrupos = document.getElementById('formGruposUpd');
  if (formGrupos) {
    formGrupos.addEventListener('submit', function(event) {
      event.preventDefault();
      fn_renderizar_grupos_cliente();
      fn_submit_form_ajax(this, 'Grupos');
    });
  }

  // Botão Criar conexão SAP (quando não existe registro)
  const btnCriarSap = document.getElementById('btn-criar-sap');
  if (btnCriarSap) {
    btnCriarSap.addEventListener('click', fn_criar_sap_vazio);
  }

  // Form Conexão SAP
  const formSap = document.getElementById('formSapUpd');
  if (formSap) {
    formSap.addEventListener('submit', function(event) {
      event.preventDefault();
      fn_submit_sap(event.target);
    });
  }

  // Botão Testar conexão SAP
  const btnTestarSap = document.getElementById('btn-testar-sap');
  if (btnTestarSap) {
    btnTestarSap.addEventListener('click', fn_testar_sap);
  }
});

// ✅ Submeter formulário via AJAX e mostrar mensagem no modal
function fn_submit_form_ajax(form, tipo) {
  const formData = new FormData(form);
  const action = form.action;
  
  console.log(`[fn_submit_form_ajax] Enviando ${tipo}...`);
  
  fetch(action, {
    method: 'POST',
    body: formData,
    headers: {
      'X-Requested-With': 'XMLHttpRequest'
    }
  })
  .then(response => {
    console.log(`[fn_submit_form_ajax] Response status: ${response.status}`);
    return response.json().catch(() => response.text());
  })
  .then(data => {
    console.log(`[fn_submit_form_ajax] Resposta:`, data);
    
    // ✅ Se for JSON com success/message
    if (typeof data === 'object' && data.success !== undefined) {
      const tipoAlert = data.success ? 'success' : 'danger';
      Notificacoes.modal(data.message, tipoAlert, 'modalClienteUpdAlerts');
      
      // ✅ Se sucesso, recarregar tabela após 2 segundos
      if (data.success) {
        setTimeout(() => {
          location.reload();
        }, 2000);
      }
    } else {
      // ✅ Se não for JSON, considerar erro
      Notificacoes.modal('Erro ao processar requisição', 'danger', 'modalClienteUpdAlerts');
    }
  })
  .catch(error => {
    console.error(`[fn_submit_form_ajax] Erro:`, error);
    Notificacoes.modal('Erro ao processar requisição', 'danger', 'modalClienteUpdAlerts');
  });
}

// ✅ Alertas no modal: padrão Notificacoes.modal (ver PADRAO_ALERTAS.md)

// Limpar alertas ao abrir/fechar modais
function fn_init_modal_message_cleanup() {
  const modalIns = document.getElementById('modalClienteIns');
  const modalUpd = document.getElementById('modalClienteUpd');

  if (modalIns) {
    modalIns.addEventListener('show.bs.modal', function() {
      Notificacoes.limparModal('modalClienteInsAlerts');
      const form = this.querySelector('form');
      if (form) form.reset();
    });
  }

  if (modalUpd) {
    modalUpd.addEventListener('show.bs.modal', function() {
      Notificacoes.limparModal('modalClienteUpdAlerts');
    });
    modalUpd.addEventListener('hidden.bs.modal', function() {
      Notificacoes.limparModal('modalClienteUpdAlerts');
    });
  }
}
