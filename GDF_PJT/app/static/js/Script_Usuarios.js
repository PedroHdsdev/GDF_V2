/* ===============================
   GERENCIAR PAGINAÇÃO & BUSCA NO CLIENTE
================================ */

const og_estado_usuarios = {
    allUsers: [],      // ✅ Todos os usuários carregados uma vez
    itemsPerPage: 30,
    currentPage: 1,
    searchQuery: '',
    empresasSelecionadas: [],  // ✅ Array de empresas selecionadas para adicionar
    gruposSelecionados: [],    // ✅ Array de grupos selecionados para adicionar
    todasEmpresas: [],         // ✅ Lista completa de empresas disponíveis
    todosGrupos: [],           // ✅ Lista completa de grupos disponíveis
    modalAberto: null          // ✅ Controlar qual modal está aberto
};

/* ===============================
   VALIDAÇÃO DO FORMULÁRIO INSERT
================================ */
function fn_validar_formulario_ins(event) {
    event.preventDefault(); // Previne submit automático
    
    const username = document.querySelector('input[name="username"]').value.trim();
    const email = document.querySelector('input[name="email"]').value.trim();
    const password = document.querySelector('input[name="password"]').value.trim();
    const password_conf = document.querySelector('input[name="password_confirm"]').value.trim();
    const empresas_hidden = document.getElementById('ins_empresas_hidden').value.trim();
    const grupos_hidden = document.getElementById('ins_grupos_hidden').value.trim();
    
    // ✅ Validações
    const errors = [];
    
    if (!username) errors.push("Username é obrigatório");
    if (!email) errors.push("Email é obrigatório");
    if (!password) errors.push("Senha é obrigatória");
    if (password !== password_conf) errors.push("Senhas não conferem");
    if (!empresas_hidden) errors.push("Selecione pelo menos 1 empresa");
    if (!grupos_hidden) errors.push("Selecione pelo menos 1 grupo");
    
    if (errors.length > 0) {
        Notificacoes.modal("Erros ao preencher formulário:\n\n" + errors.join("\n"), 'danger', 'modalUsuarioInsAlerts');
        return false;
    }
    
    console.log("✅ Formulário validado com sucesso!");
    console.log("   Empresas:", empresas_hidden);
    console.log("   Grupos:", grupos_hidden);
    
    // ✅ Se passou em todas validações, enviar formulário
    event.target.submit();
}

/* ===============================
   VALIDAÇÃO DO FORMULÁRIO UPDATE
================================ */
function fn_validar_formulario_upd(event) {
    event.preventDefault();
    
    const email = document.getElementById('upd_email').value.trim();
    const empresas_hidden = document.getElementById('upd_empresas_hidden').value.trim();
    const grupos_hidden = document.getElementById('upd_grupos_hidden').value.trim();
    
    const errors = [];
    if (!email) errors.push("Email é obrigatório");
    if (!empresas_hidden) errors.push("Selecione pelo menos 1 empresa");
    if (!grupos_hidden) errors.push("Selecione pelo menos 1 grupo");
    
    if (errors.length > 0) {
        Notificacoes.modal("❌ Erros:\n\n" + errors.join("\n"), 'danger', 'modalUsuarioUpdAlerts');
        return false;
    }
    
    // ✅ Submeter via AJAX
    fn_submit_form_ajax(event.target, 'Usuario');
}

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
      Notificacoes.modal(data.message, tipoAlert, 'modalUsuarioUpdAlerts');
      
      // ✅ Se sucesso, recarregar tabela após 2 segundos
      if (data.success) {
        setTimeout(() => {
          location.reload();
        }, 2000);
      }
    } else {
      // ✅ Se não for JSON, considerar erro
      Notificacoes.modal('Erro ao processar requisição', 'danger', 'modalUsuarioUpdAlerts');
    }
  })
  .catch(error => {
    console.error(`[fn_submit_form_ajax] Erro:`, error);
    Notificacoes.modal('Erro ao processar requisição', 'danger', 'modalUsuarioUpdAlerts');
  });
}

// ✅ Alertas no modal: Notificacoes.modal (ver PADRAO_ALERTAS.md)

function fn_fechar_modal_aberto() {
    if (!og_estado_usuarios.modalAberto) return;
    
    const modalElement = document.getElementById(og_estado_usuarios.modalAberto);
    if (modalElement) {
        const modalInstance = bootstrap.Modal.getInstance(modalElement);
        if (modalInstance) {
            console.log(`🔒 Fechando modal: ${og_estado_usuarios.modalAberto}`);
            modalInstance.hide();
            og_estado_usuarios.modalAberto = null;
        }
    }
}

document.addEventListener("DOMContentLoaded", () => {
    // ✅ Carregar dados da tabela no HTML e armazenar em memória
    fn_extrair_usuarios_html();
    
    fn_init_paginacao();
    fn_init_busca();
    fn_init_usuario_ins();
    fn_init_usuario_upd();
});

/* ===============================
   EXTRAIR USUÁRIOS DO HTML (Enviados pelo Django)
================================ */
function fn_extrair_usuarios_html() {
    const rows = document.querySelectorAll(".user-row");
    og_estado_usuarios.allUsers = [];
    
    rows.forEach(row => {
        // ✅ Extrair dados estruturados da linha (seguindo ordem da tabela)
        const cells = row.querySelectorAll("td");
        const userData = {
            id: row.dataset.userId,
            html: row.innerHTML,
            // Ordem: ID, Empresa, Status, Usuário, E-mail, Data, Admin
            user_id: cells[0]?.textContent.trim() || '',
            empresa_id: cells[1]?.textContent.trim() || '',
            is_active: cells[2]?.textContent.trim() || '',
            username: cells[3]?.textContent.trim() || '',
            email: cells[4]?.textContent.trim() || '',
            date_joined: cells[5]?.textContent.trim() || '',
            is_superuser: cells[6]?.textContent.trim() || ''
        };
        og_estado_usuarios.allUsers.push(userData);
    });
    
    console.log(`✅ ${og_estado_usuarios.allUsers.length} usuários carregados em memória`);
    console.log('📋 Primeiro usuário:', og_estado_usuarios.allUsers[0]);
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
        og_estado_usuarios.searchQuery = query;
        og_estado_usuarios.currentPage = 1;  // Reset para página 1
        
        fn_atualizar_tabela_filtrada();
    });
    
    // ✅ Busca em tempo real enquanto digita
    inputBusca.addEventListener("input", (e) => {
        const query = e.target.value.trim().toLowerCase();
        og_estado_usuarios.searchQuery = query;
        og_estado_usuarios.currentPage = 1;
        
        fn_atualizar_tabela_filtrada();
    });
}

/* ===============================
   FILTRAR USUÁRIOS
================================ */
function fn_filtrar_usuarios() {
    if (!og_estado_usuarios.searchQuery) {
        return og_estado_usuarios.allUsers;  // Sem filtro, retorna todos
    }
    
    const query = og_estado_usuarios.searchQuery.toLowerCase();
    
    // ✅ Buscar em múltiplos campos
    const filtrados = og_estado_usuarios.allUsers.filter(user => {
        return (
            user.username.toLowerCase().includes(query) ||
            user.email.toLowerCase().includes(query) ||
            user.empresa_id.toLowerCase().includes(query) ||
            user.user_id.toLowerCase().includes(query) ||
            user.date_joined.toLowerCase().includes(query)
        );
    });
    
    console.log(`🔎 Filtrados: ${filtrados.length} de ${og_estado_usuarios.allUsers.length}`);
    return filtrados;
}

/* ===============================
   CALCULAR PAGINAÇÃO
================================ */
function fn_calcular_paginacao(usuariosFiltrados) {
    const total = usuariosFiltrados.length;
    const totalPages = Math.ceil(total / og_estado_usuarios.itemsPerPage);
    
    // ✅ Garantir que currentPage é válida
    if (og_estado_usuarios.currentPage > totalPages) {
        og_estado_usuarios.currentPage = Math.max(1, totalPages);
    }
    
    const start = (og_estado_usuarios.currentPage - 1) * og_estado_usuarios.itemsPerPage;
    const end = start + og_estado_usuarios.itemsPerPage;
    
    return {
        itemsNoInterval: usuariosFiltrados.slice(start, end),
        totalPages,
        currentPage: og_estado_usuarios.currentPage,
        total
    };
}

/* ===============================
   ATUALIZAR TABELA (após busca ou paginação)
================================ */
function fn_atualizar_tabela_filtrada() {
    const usuariosFiltrados = fn_filtrar_usuarios();
    const paginacao = fn_calcular_paginacao(usuariosFiltrados);
    
    const tbody = document.querySelector("table tbody");
    if (!tbody) return;
    
    // ✅ Se não há resultados
    if (paginacao.itemsNoInterval.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="7" class="text-center py-3">
                    Nenhum usuário encontrado
                </td>
            </tr>
        `;
    } else {
        // ✅ Renderizar apenas usuários da página atual usando HTML guardado
        tbody.innerHTML = paginacao.itemsNoInterval
            .map(user => `<tr class="user-row" data-user-id="${user.id}">${user.html}</tr>`)
            .join('');
        
        // ✅ Re-adicionar listeners de clique após renderizar
        fn_adicionar_listeners_tabela();
    }
    
    // ✅ Atualizar paginação
    fn_atualizar_paginacao(paginacao);
}

/* ===============================
   ADICIONAR LISTENERS NA TABELA
================================ */
function fn_adicionar_listeners_tabela() {
    document.querySelectorAll(".user-row").forEach(row => {
        row.addEventListener("click", async (e) => {
            if (e.target.closest("a, button, input, label")) return;
            
            const userId = row.dataset.userId;
            if (!userId) return;
            
            await fn_carregar_usuario(userId);
            const modal = new bootstrap.Modal(document.getElementById("modalUsuarioUpd"));
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
                <a class="page-link" href="#" onclick="fn_ir_para_pagina(${paginacao.currentPage - 1}); return false;">
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
                    <a class="page-link" href="#" onclick="fn_ir_para_pagina(${i}); return false;">
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
                <a class="page-link" href="#" onclick="fn_ir_para_pagina(${paginacao.currentPage + 1}); return false;">
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
function fn_ir_para_pagina(pageNum) {
    og_estado_usuarios.currentPage = pageNum;
    fn_atualizar_tabela_filtrada();
    window.scrollTo(0, 0);  // ✅ Scroll para o topo
}

/* ===============================
   INICIALIZAR PAGINAÇÃO
================================ */
function fn_init_paginacao() {
    // ✅ Paginação já é gerenciada via fn_ir_para_pagina()
    // Aqui apenas garantimos a primeira renderização
}

/* ===============================
   INS – INSERT USER
================================ */ 
function fn_init_usuario_ins() {
    const modalEl = document.getElementById("modalUsuarioIns");
    if (!modalEl) return;

    modalEl.addEventListener("show.bs.modal", async () => {
        try {
            if (typeof Notificacoes !== 'undefined') Notificacoes.limparModal('modalUsuarioInsAlerts');
            fn_fechar_modal_aberto();
            og_estado_usuarios.modalAberto = "modalUsuarioIns";
            const codClienteEl = document.getElementById('ins_cod_cliente');
            if (codClienteEl && !codClienteEl.value) {
                return;
            }
            const qs = codClienteEl && codClienteEl.value ? '?cod_cliente=' + encodeURIComponent(codClienteEl.value) : '';
            var urlIns = (window.APP_URLS && window.APP_URLS.usuarioInserir) ? window.APP_URLS.usuarioInserir + (qs ? (qs.charAt(0) === '?' ? qs : '?' + qs) : '') : ((typeof getUrlPrefix === 'function' ? getUrlPrefix() : '') || '') + '/usuario/inserir/' + (qs || '');
            const resp = await fetch(urlIns, {
                headers: { 'X-Requested-With': 'XMLHttpRequest', 'Accept': 'application/json' }
            });
            if (resp.ok) {
                const data = await resp.json();
                const empresas = data.Todas_Empresas || data.todas_empresas || data.TodasEmpresas || [];
                const grupos = data.Todos_Grupos || data.todos_grupos || data.TodosGrupos || [];
                fn_preencher_select_ins_empresas(empresas);
                fn_preencher_select_ins_grupos(grupos);
            } else {
                console.warn('Falha ao carregar dados para modal INSERT. Se for superusuário, selecione o cliente.', resp.status);
            }
        } catch (err) {
            console.error('Erro ao buscar dados para modal INSERT:', err);
        }
    });

    const codClienteSelect = document.getElementById('ins_cod_cliente');
    if (codClienteSelect) {
        codClienteSelect.addEventListener("change", async () => {
            const cod = codClienteSelect.value;
            if (!cod) return;
            try {
                var urlIns = (window.APP_URLS && window.APP_URLS.usuarioInserir) ? window.APP_URLS.usuarioInserir + '?cod_cliente=' + encodeURIComponent(cod) : ((typeof getUrlPrefix === 'function' ? getUrlPrefix() : '') || '') + '/usuario/inserir/?cod_cliente=' + encodeURIComponent(cod);
                const resp = await fetch(urlIns, {
                    headers: { 'X-Requested-With': 'XMLHttpRequest', 'Accept': 'application/json' }
                });
                if (resp.ok) {
                    const data = await resp.json();
                    const empresas = data.Todas_Empresas || data.todas_empresas || data.TodasEmpresas || [];
                    const grupos = data.Todos_Grupos || data.todos_grupos || data.TodosGrupos || [];
                    fn_preencher_select_ins_empresas(empresas);
                    fn_preencher_select_ins_grupos(grupos);
                }
            } catch (err) {
                console.error('Erro ao recarregar dados por cliente:', err);
            }
        });
    }

    modalEl.addEventListener("hidden.bs.modal", () => {
        const form = modalEl.querySelector("form");
        if (form) form.reset();
        
        // ✅ Limpar também os arrays de empresas e grupos
        og_estado_usuarios.empresasSelecionadas = [];
        og_estado_usuarios.gruposSelecionados = [];
        
        // ✅ Limpar as tabelas e hidden inputs
        fn_renderizar_empresas_selecionadas_ins();
        fn_renderizar_grupos_selecionados_ins();
        
        // ✅ Desmarcar modal aberto
        if (og_estado_usuarios.modalAberto === "modalUsuarioIns") {
            og_estado_usuarios.modalAberto = null;
        }
    });
}

/* ===============================
   UPD – UPDATE USER
================================ */
function fn_init_usuario_upd() {
    const modalEl = document.getElementById("modalUsuarioUpd");
    if (!modalEl) return;
    
    // ✅ Prevenir submit ao clicar nas abas
    const form = modalEl.querySelector("form");
    if (form) {
        form.addEventListener("submit", (e) => {
            // Permitir submit apenas se clicou no botão "Salvar alterações"
            if (e.submitter && e.submitter.textContent.includes("Salvar")) {
                // Deixa o form fazer submit normal
                return;
            }
            // Prevenir para qualquer outro caso
            if (e.target.classList.contains("nav-link")) {
                e.preventDefault();
            }
        });
    }

    document.addEventListener("click", async (e) => {
        const row = e.target.closest(".user-row");
        if (!row) return;
        
        if (e.target.closest("a, button, input, label")) return;

        const userId = row.dataset.userId;
        if (!userId) return;

        // ✅ Fechar modal de INSERT se estiver aberto
        fn_fechar_modal_aberto();
        
        // ✅ Marcar como modal aberto
        og_estado_usuarios.modalAberto = "modalUsuarioUpd";
        
        // ✅ Aguardar dados serem carregados ANTES de abrir o modal
        const sucesso = await fn_carregar_usuario(userId);
        
        if (sucesso) {
            const modal = new bootstrap.Modal(modalEl, {
                backdrop: "static",
                keyboard: false
            });
            modal.show();
        } else {
            og_estado_usuarios.modalAberto = null;
        }
    });

    modalEl.addEventListener("show.bs.modal", () => {
        if (typeof Notificacoes !== 'undefined') Notificacoes.limparModal('modalUsuarioUpdAlerts');
    });
    // ✅ Desmarcar modal aberto ao fechar
    modalEl.addEventListener("hidden.bs.modal", () => {
        if (og_estado_usuarios.modalAberto === "modalUsuarioUpd") {
            og_estado_usuarios.modalAberto = null;
        }
    });
}

/* ===============================
   LOAD USER (API)
================================ */
async function fn_carregar_usuario(userId) {
    try {
        console.log(`📥 Iniciando carregamento do usuário ${userId}...`);
        
        var urlUpd = (window.APP_URLS && window.APP_URLS.usuarioUpd) ? window.APP_URLS.usuarioUpd.replace('__ID__', userId) : ((typeof getUrlPrefix === 'function' ? getUrlPrefix() : '') || '') + '/usuario/' + userId + '/';
        const resp = await fetch(urlUpd, {
            headers: { 
                "X-Requested-With": "XMLHttpRequest",
                "Accept": "application/json"
            }
        });

        if (!resp.ok) {
            console.error(`Erro ao carregar usuário: ${resp.status} - ${resp.statusText}`);
            Notificacoes.modal('Erro ao carregar usuário: ' + resp.statusText, 'danger', 'modalUsuarioUpdAlerts');
            return false;  // ✅ Retornar false se falhar
        }

        const data = await resp.json();
        console.log("✅ Dados do usuário recebidos com sucesso");
        console.log("📊 grupos_disponiveis:", data.grupos_disponiveis);
        
        // ✅ Preencher modal com dados
        fn_preencher_modal_usuario(data);
        
        return true;  // ✅ Retornar true se sucesso
    } catch (error) {
        console.error("Erro na requisição:", error);
        Notificacoes.modal("Erro ao carregar usuário. Tente novamente.", 'danger', 'modalUsuarioUpdAlerts');
        return false;  // ✅ Retornar false se erro
    }
}

/* ===============================
   FILL MODAL
================================ */
function fn_preencher_modal_usuario(user) {
    document.getElementById("upd_user_id").value = user.id;
    document.getElementById("upd_username").value = user.username;
    document.getElementById("upd_email").value = user.email;
    document.getElementById("upd_first_name").value = user.first_name;
    document.getElementById("upd_last_name").value = user.last_name;

    const checkbox = document.getElementById("upd_is_active");
    if (checkbox) {
        checkbox.checked = Boolean(user.is_active);
    }
    
    // ✅ Atualizar action do formulário dinamicamente
    const form = document.getElementById("formUsuarioUpd");
    if (form) {
        var urlUpd = (window.APP_URLS && window.APP_URLS.usuarioUpd) ? window.APP_URLS.usuarioUpd.replace('__ID__', user.id) : ((typeof getUrlPrefix === 'function' ? getUrlPrefix() : '') || '') + '/usuario/' + user.id + '/';
        form.action = urlUpd;
    }

    // ✅ Limpar e preencher empresas
    og_estado_usuarios.empresasSelecionadas = [];
    user.empresas.forEach(emp => {
        og_estado_usuarios.empresasSelecionadas.push({
            id: emp.cod_empresa,
            nome: emp.fantasia || emp.razao || emp.cod_empresa
        });
    });
    fn_renderizar_empresas_selecionadas();
    
    // ✅ Limpar e preencher grupos
    og_estado_usuarios.gruposSelecionados = [];
    user.grupos.forEach(grp => {
        og_estado_usuarios.gruposSelecionados.push({
            id: grp.id,
            nome: grp.name
        });
    });
    fn_renderizar_grupos_selecionados();
    
    // ✅ Preencher selects com dados disponíveis (aceitar variações de key names)
    const empresasDisp = user.empresas_disponiveis || user.Empresas_Disponiveis || user.empresasDisponiveis || user.Empresas_Disponiveis || [];
    const gruposDisp = user.grupos_disponiveis || user.Grupos_Disponiveis || user.gruposDisponiveis || user.Grupos_Disponiveis || [];

    console.log("🏢 Empresas disponíveis para preencher:", empresasDisp);
    console.log("👥 Grupos disponíveis para preencher:", gruposDisp);

    if (Array.isArray(empresasDisp) && empresasDisp.length > 0) {
        console.log("✅ Preenchendo empresas...");
        fn_preencher_select_empresas(empresasDisp);
    } else {
        console.warn("⚠️ Nenhuma empresa disponível encontrada");
    }

    if (Array.isArray(gruposDisp) && gruposDisp.length > 0) {
        console.log("✅ Preenchendo grupos...");
        fn_preencher_select_grupos(gruposDisp);
    } else {
        console.warn("⚠️ Nenhum grupo disponível encontrado");
    }
}

/* ===============================
   PREENCHER SELECT COM EMPRESAS DISPONÍVEIS
================================ */
function fn_preencher_select_empresas(empresas) {
    const select = document.getElementById("upd_empresas_select");
    if (!select) return;
    
    // Limpar options existentes (mantendo o primeiro placeholder)
    while (select.options.length > 1) {
        select.removeChild(select.lastChild);
    }
    
    // Adicionar opções disponíveis
    empresas.forEach(emp => {
        const option = document.createElement("option");
        // aceitar formatos: {cod_empresa, fantasia, razao} ou {id, nome}
        option.value = emp.cod_empresa || emp.id || emp.cod || emp.codigo || '';
        option.textContent = emp.fantasia || emp.nome || emp.razao || emp.codigo || emp.id || option.value;
        option.dataset.nome = option.textContent;
        select.appendChild(option);
    });
}

/* ===============================
   PREENCHER SELECT COM GRUPOS DISPONÍVEIS
================================ */
function fn_preencher_select_grupos(grupos) {
    const select = document.getElementById("upd_grupos_select");
    if (!select) {
        console.error("❌ Select 'upd_grupos_select' não encontrado!");
        return;
    }
    
    console.log("📝 Limpando select e adicionando opções...");
    // Limpar options existentes (mantendo o primeiro placeholder)
    while (select.options.length > 1) {
        select.removeChild(select.lastChild);
    }
    
    // Adicionar opções disponíveis
    grupos.forEach((grp, index) => {
        console.log(`  Grupo ${index}:`, grp);
        const option = document.createElement("option");
        // aceitar: {id, name} ou {group__id, group__name}
        option.value = grp.id || grp.group__id || grp.group_id || grp.group || '';
        option.textContent = grp.name || grp.group__name || grp.group_name || grp.nome || option.value;
        console.log(`    → value: "${option.value}", text: "${option.textContent}"`);
        select.appendChild(option);
    });
    console.log(`✅ Total de grupos adicionados: ${grupos.length}`);
}

/* ===============================
   INSERT: PREENCHER SELECTS (dados vindos da view /usuario_ins/)
================================ */
function fn_preencher_select_ins_empresas(empresas) {
    const select = document.getElementById("ins_empresas_select");
    if (!select) return;
    while (select.options.length > 1) select.removeChild(select.lastChild);

    empresas.forEach(emp => {
        const option = document.createElement('option');
        option.value = emp.cod_empresa || emp.id || emp.cod || '';
        option.textContent = emp.fantasia || emp.razao || emp.nome || option.value;
        option.dataset.nome = option.textContent;
        select.appendChild(option);
    });
}

function fn_preencher_select_ins_grupos(grupos) {
    const select = document.getElementById("ins_grupos_select");
    if (!select) return;
    while (select.options.length > 1) select.removeChild(select.lastChild);

    grupos.forEach(grp => {
        const option = document.createElement('option');
        option.value = grp.id || grp.group_id || '';
        option.textContent = grp.name || grp.nome || option.value;
        select.appendChild(option);
    });
}

/* ===============================
   ADICIONAR/REMOVER EMPRESAS
================================ */
function fn_adicionar_empresa() {
    const select = document.getElementById("upd_empresas_select");
    if (!select.value) {
        Notificacoes.modal("Selecione uma empresa!", 'warning', 'modalUsuarioUpdAlerts');
        return;
    }
    
    const empId = select.value;
    const empNome = select.options[select.selectedIndex].text;
    
    // ✅ Verificar se já foi adicionada
    if (og_estado_usuarios.empresasSelecionadas.some(e => e.id == empId)) {
        Notificacoes.modal("Esta empresa já foi adicionada!", 'warning', 'modalUsuarioUpdAlerts');
        return;
    }
    
    og_estado_usuarios.empresasSelecionadas.push({
        id: empId,
        nome: empNome
    });
    
    select.value = ""; // ✅ Limpar select
    fn_renderizar_empresas_selecionadas();
}

function fn_remover_empresa(empId) {
    og_estado_usuarios.empresasSelecionadas = og_estado_usuarios.empresasSelecionadas.filter(
        e => e.id != empId
    );
    fn_renderizar_empresas_selecionadas();
}

function fn_renderizar_empresas_selecionadas() {
    const tbody = document.getElementById("upd_empresas_tbody");
    const hidden = document.getElementById("upd_empresas_hidden");
    
    if (!tbody) return;
    
    // ✅ Limpar tbody
    tbody.innerHTML = "";
    
    // ✅ Adicionar linhas
    og_estado_usuarios.empresasSelecionadas.forEach(emp => {
        const row = document.createElement("tr");
        row.innerHTML = `
            <td>${emp.nome}</td>
            <td>
                <button type="button" class="btn btn-sm btn-danger" 
                        onclick="fn_remover_empresa(${emp.id})">
                    Remover
                </button>
            </td>
        `;
        tbody.appendChild(row);
    });
    
    // ✅ Atualizar hidden input com IDs separados por vírgula
    hidden.value = og_estado_usuarios.empresasSelecionadas
        .map(e => e.id)
        .join(",");
}

/* ===============================
   ADICIONAR/REMOVER GRUPOS
================================ */
function fn_adicionar_grupo() {
    const select = document.getElementById("upd_grupos_select");
    if (!select.value) {
        Notificacoes.modal("Selecione um grupo!", 'warning', 'modalUsuarioUpdAlerts');
        return;
    }
    
    const grupoId = select.value;
    const grupoNome = select.options[select.selectedIndex].text;
    
    // ✅ Verificar se já foi adicionado
    if (og_estado_usuarios.gruposSelecionados.some(g => g.id == grupoId)) {
        Notificacoes.modal("Este grupo já foi adicionado!", 'warning', 'modalUsuarioUpdAlerts');
        return;
    }
    
    og_estado_usuarios.gruposSelecionados.push({
        id: grupoId,
        nome: grupoNome
    });
    
    select.value = ""; // ✅ Limpar select
    fn_renderizar_grupos_selecionados();
}

function fn_remover_grupo(grupoId) {
    og_estado_usuarios.gruposSelecionados = og_estado_usuarios.gruposSelecionados.filter(
        g => g.id != grupoId
    );
    fn_renderizar_grupos_selecionados();
}

function fn_renderizar_grupos_selecionados() {
    const tbody = document.getElementById("upd_grupos_tbody");
    const hidden = document.getElementById("upd_grupos_hidden");
    
    if (!tbody) return;
    
    // ✅ Limpar tbody
    tbody.innerHTML = "";
    
    // ✅ Adicionar linhas
    og_estado_usuarios.gruposSelecionados.forEach(grp => {
        const row = document.createElement("tr");
        row.innerHTML = `
            <td>${grp.nome}</td>
            <td>
                <button type="button" class="btn btn-sm btn-danger" 
                        onclick="fn_remover_grupo(${grp.id})">
                    Remover
                </button>
            </td>
        `;
        tbody.appendChild(row);
    });
    
    // ✅ Atualizar hidden input com IDs separados por vírgula
    hidden.value = og_estado_usuarios.gruposSelecionados
        .map(g => g.id)
        .join(",");
}

/* ===============================
   INSERT: ADICIONAR/REMOVER EMPRESAS
================================ */
function fn_adicionar_empresa_ins() {
    const select = document.getElementById("ins_empresas_select");
    if (!select.value) {
        Notificacoes.modal("Selecione uma empresa!", 'warning', 'modalUsuarioInsAlerts');
        return;
    }
    
    const empId = select.value;
    const empNome = select.options[select.selectedIndex].text;
    
    // ✅ Verificar se já foi adicionada
    if (og_estado_usuarios.empresasSelecionadas.some(e => e.id == empId)) {
        Notificacoes.modal("Esta empresa já foi adicionada!", 'warning', 'modalUsuarioInsAlerts');
        return;
    }
    
    og_estado_usuarios.empresasSelecionadas.push({
        id: empId,
        nome: empNome
    });
    
    select.value = ""; // ✅ Limpar select
    fn_renderizar_empresas_selecionadas_ins();
}

function fn_remover_empresa_ins(empId) {
    og_estado_usuarios.empresasSelecionadas = og_estado_usuarios.empresasSelecionadas.filter(
        e => e.id != empId
    );
    fn_renderizar_empresas_selecionadas_ins();
}

function fn_renderizar_empresas_selecionadas_ins() {
    const tbody = document.getElementById("ins_empresas_tbody");
    const hidden = document.getElementById("ins_empresas_hidden");
    
    if (!tbody) return;
    
    // ✅ Limpar tbody
    tbody.innerHTML = "";
    
    // ✅ Adicionar linhas
    og_estado_usuarios.empresasSelecionadas.forEach(emp => {
        const row = document.createElement("tr");
        row.innerHTML = `
            <td>${emp.nome}</td>
            <td>
                <button type="button" class="btn btn-sm btn-danger" 
                        onclick="fn_remover_empresa_ins(${emp.id})">
                    Remover
                </button>
            </td>
        `;
        tbody.appendChild(row);
    });
    
    // ✅ Atualizar hidden input com IDs separados por vírgula
    hidden.value = og_estado_usuarios.empresasSelecionadas
        .map(e => e.id)
        .join(",");
    
    // ✅ Feedback visual
    const count = og_estado_usuarios.empresasSelecionadas.length;
    if (count > 0) {
        console.log(`✅ ${count} empresa(s) selecionada(s)`);
    }
}

/* ===============================
   INSERT: ADICIONAR/REMOVER GRUPOS
================================ */
function fn_adicionar_grupo_ins() {
    const select = document.getElementById("ins_grupos_select");
    if (!select.value) {
        Notificacoes.modal("Selecione um grupo!", 'warning', 'modalUsuarioInsAlerts');
        return;
    }
    
    const grupoId = select.value;
    const grupoNome = select.options[select.selectedIndex].text;
    
    // ✅ Verificar se já foi adicionado
    if (og_estado_usuarios.gruposSelecionados.some(g => g.id == grupoId)) {
        Notificacoes.modal("Este grupo já foi adicionado!", 'warning', 'modalUsuarioInsAlerts');
        return;
    }
    
    og_estado_usuarios.gruposSelecionados.push({
        id: grupoId,
        nome: grupoNome
    });
    
    select.value = ""; // ✅ Limpar select
    fn_renderizar_grupos_selecionados_ins();
}

function fn_remover_grupo_ins(grupoId) {
    og_estado_usuarios.gruposSelecionados = og_estado_usuarios.gruposSelecionados.filter(
        g => g.id != grupoId
    );
    fn_renderizar_grupos_selecionados_ins();
}

function fn_renderizar_grupos_selecionados_ins() {
    const tbody = document.getElementById("ins_grupos_tbody");
    const hidden = document.getElementById("ins_grupos_hidden");
    
    if (!tbody) return;
    
    // ✅ Limpar tbody
    tbody.innerHTML = "";
    
    // ✅ Adicionar linhas
    og_estado_usuarios.gruposSelecionados.forEach(grp => {
        const row = document.createElement("tr");
        row.innerHTML = `
            <td>${grp.nome}</td>
            <td>
                <button type="button" class="btn btn-sm btn-danger" 
                        onclick="fn_remover_grupo_ins(${grp.id})">
                    Remover
                </button>
            </td>
        `;
        tbody.appendChild(row);
    });
    
    // ✅ Atualizar hidden input com IDs separados por vírgula
    hidden.value = og_estado_usuarios.gruposSelecionados
        .map(g => g.id)
        .join(",");
}

/* ===============================
   INSERT: PREENCHER SELECTS (dados vindos da view /usuario/inserir/)
================================ */
function fn_preencher_select_ins_empresas(empresas) {
    const select = document.getElementById('ins_empresas_select');
    if (!select) return;
    // manter placeholder e limpar demais options
    while (select.options.length > 1) select.removeChild(select.lastChild);

    empresas.forEach(emp => {
        const val = emp.cod_empresa || emp.id || emp.codigo || '';
        const text = emp.fantasia || emp.razao || emp.nome || val;
        const option = document.createElement('option');
        option.value = val;
        option.textContent = text;
        option.dataset.nome = text;
        select.appendChild(option);
    });
}

function fn_preencher_select_ins_grupos(grupos) {
    const select = document.getElementById('ins_grupos_select');
    if (!select) return;
    while (select.options.length > 1) select.removeChild(select.lastChild);

    grupos.forEach(grp => {
        const val = grp.id || grp.group_id || '';
        const text = grp.name || grp.nome || val;
        const option = document.createElement('option');
        option.value = val;
        option.textContent = text;
        select.appendChild(option);
    });
}



