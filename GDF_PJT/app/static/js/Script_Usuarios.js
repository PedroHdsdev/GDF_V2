/* ===============================
   GERENCIAR PAGINAÇÃO & BUSCA NO CLIENTE
================================ */

const usuariosState = {
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
function validarFormularioIns(event) {
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
        alert("❌ Erros ao preencher formulário:\n\n" + errors.join("\n"));
        return false;
    }
    
    console.log("✅ Formulário validado com sucesso!");
    console.log("   Empresas:", empresas_hidden);
    console.log("   Grupos:", grupos_hidden);
    
    // ✅ Se passou em todas validações, enviar formulário
    event.target.submit();
}

/* ===============================
   GERENCIAR MODAIS (prevenir múltiplos abertos)
================================ */
function fecharModalAberto() {
    if (!usuariosState.modalAberto) return;
    
    const modalElement = document.getElementById(usuariosState.modalAberto);
    if (modalElement) {
        const modalInstance = bootstrap.Modal.getInstance(modalElement);
        if (modalInstance) {
            console.log(`🔒 Fechando modal: ${usuariosState.modalAberto}`);
            modalInstance.hide();
            usuariosState.modalAberto = null;
        }
    }
}

document.addEventListener("DOMContentLoaded", () => {
    // ✅ Carregar dados da tabela no HTML e armazenar em memória
    extrairUsuariosDoHTML();
    
    initPaginacao();
    initBusca();
    initUsuarioIns();
    initUsuarioUpd();
});

/* ===============================
   EXTRAIR USUÁRIOS DO HTML (Enviados pelo Django)
================================ */
function extrairUsuariosDoHTML() {
    const rows = document.querySelectorAll(".user-row");
    usuariosState.allUsers = [];
    
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
        usuariosState.allUsers.push(userData);
    });
    
    console.log(`✅ ${usuariosState.allUsers.length} usuários carregados em memória`);
    console.log('📋 Primeiro usuário:', usuariosState.allUsers[0]);
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
        usuariosState.searchQuery = query;
        usuariosState.currentPage = 1;  // Reset para página 1
        
        atualizarTabelaFiltrada();
    });
    
    // ✅ Busca em tempo real enquanto digita
    inputBusca.addEventListener("input", (e) => {
        const query = e.target.value.trim().toLowerCase();
        usuariosState.searchQuery = query;
        usuariosState.currentPage = 1;
        
        atualizarTabelaFiltrada();
    });
}

/* ===============================
   FILTRAR USUÁRIOS
================================ */
function filtrarUsuarios() {
    if (!usuariosState.searchQuery) {
        return usuariosState.allUsers;  // Sem filtro, retorna todos
    }
    
    const query = usuariosState.searchQuery.toLowerCase();
    
    // ✅ Buscar em múltiplos campos
    const filtrados = usuariosState.allUsers.filter(user => {
        return (
            user.username.toLowerCase().includes(query) ||
            user.email.toLowerCase().includes(query) ||
            user.empresa_id.toLowerCase().includes(query) ||
            user.user_id.toLowerCase().includes(query) ||
            user.date_joined.toLowerCase().includes(query)
        );
    });
    
    console.log(`🔎 Filtrados: ${filtrados.length} de ${usuariosState.allUsers.length}`);
    return filtrados;
}

/* ===============================
   CALCULAR PAGINAÇÃO
================================ */
function calcularPaginacao(usuariosFiltrados) {
    const total = usuariosFiltrados.length;
    const totalPages = Math.ceil(total / usuariosState.itemsPerPage);
    
    // ✅ Garantir que currentPage é válida
    if (usuariosState.currentPage > totalPages) {
        usuariosState.currentPage = Math.max(1, totalPages);
    }
    
    const start = (usuariosState.currentPage - 1) * usuariosState.itemsPerPage;
    const end = start + usuariosState.itemsPerPage;
    
    return {
        itemsNoInterval: usuariosFiltrados.slice(start, end),
        totalPages,
        currentPage: usuariosState.currentPage,
        total
    };
}

/* ===============================
   ATUALIZAR TABELA (após busca ou paginação)
================================ */
function atualizarTabelaFiltrada() {
    const usuariosFiltrados = filtrarUsuarios();
    const paginacao = calcularPaginacao(usuariosFiltrados);
    
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
        adicionarListenersDaTabela();
    }
    
    // ✅ Atualizar paginação
    atualizarPaginacao(paginacao);
}

/* ===============================
   ADICIONAR LISTENERS NA TABELA
================================ */
function adicionarListenersDaTabela() {
    document.querySelectorAll(".user-row").forEach(row => {
        row.addEventListener("click", async (e) => {
            if (e.target.closest("a, button, input, label")) return;
            
            const userId = row.dataset.userId;
            if (!userId) return;
            
            await loadUser(userId);
            const modal = new bootstrap.Modal(document.getElementById("modalUsuarioUpd"));
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
    usuariosState.currentPage = pageNum;
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
   INS – INSERT USER
================================ */ 
function initUsuarioIns() {
    const modalEl = document.getElementById("modalUsuarioIns");
    if (!modalEl) return;

    // Ao abrir o modal, buscar dados do servidor para popular selects
    modalEl.addEventListener("show.bs.modal", async () => {
        try {
            // ✅ Fechar modal de UPDATE se estiver aberto
            fecharModalAberto();
            
            // ✅ Marcar como modal aberto
            usuariosState.modalAberto = "modalUsuarioIns";
            
            const resp = await fetch('/usuario/inserir/', {
                headers: { 'X-Requested-With': 'XMLHttpRequest', 'Accept': 'application/json' }
            });
            if (resp.ok) {
                const data = await resp.json();
                // aceitar várias possíveis chaves retornadas pela view
                const empresas = data.Todas_Empresas || data.todas_empresas || data.TodasEmpresas || [];
                const grupos = data.Todos_Grupos || data.todos_grupos || data.TodosGrupos || [];
                preencherSelectInsEmpresas(empresas);
                preencherSelectInsGrupos(grupos);
                console.log("✅ Modal INSERT: Dados carregados com sucesso");
            } else {
                console.warn('Falha ao carregar dados para modal INSERT:', resp.status, resp.statusText);
            }
        } catch (err) {
            console.error('Erro ao buscar dados para modal INSERT:', err);
        }
    });

    modalEl.addEventListener("hidden.bs.modal", () => {
        const form = modalEl.querySelector("form");
        if (form) form.reset();
        
        // ✅ Limpar também os arrays de empresas e grupos
        usuariosState.empresasSelecionadas = [];
        usuariosState.gruposSelecionados = [];
        
        // ✅ Limpar as tabelas e hidden inputs
        renderizarEmpresasSelecionadasIns();
        renderizarGruposSelecionadosIns();
        
        // ✅ Desmarcar modal aberto
        if (usuariosState.modalAberto === "modalUsuarioIns") {
            usuariosState.modalAberto = null;
        }
    });
}

/* ===============================
   UPD – UPDATE USER
================================ */
function initUsuarioUpd() {
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
        fecharModalAberto();
        
        // ✅ Marcar como modal aberto
        usuariosState.modalAberto = "modalUsuarioUpd";
        
        // ✅ Aguardar dados serem carregados ANTES de abrir o modal
        const sucesso = await loadUser(userId);
        
        if (sucesso) {
            const modal = new bootstrap.Modal(modalEl, {
                backdrop: "static",
                keyboard: false
            });
            modal.show();
        } else {
            usuariosState.modalAberto = null;
        }
    });

    // ✅ Desmarcar modal aberto ao fechar
    modalEl.addEventListener("hidden.bs.modal", () => {
        if (usuariosState.modalAberto === "modalUsuarioUpd") {
            usuariosState.modalAberto = null;
        }
    });
}

/* ===============================
   LOAD USER (API)
================================ */
async function loadUser(userId) {
    try {
        console.log(`📥 Iniciando carregamento do usuário ${userId}...`);
        
        const resp = await fetch(`/usuario/${userId}/`, {
            headers: { 
                "X-Requested-With": "XMLHttpRequest",
                "Accept": "application/json"
            }
        });

        if (!resp.ok) {
            console.error(`Erro ao carregar usuário: ${resp.status} - ${resp.statusText}`);
            alert(`Erro ao carregar usuário: ${resp.statusText}`);
            return false;  // ✅ Retornar false se falhar
        }

        const data = await resp.json();
        console.log("✅ Dados do usuário recebidos com sucesso");
        console.log("📊 grupos_disponiveis:", data.grupos_disponiveis);
        
        // ✅ Preencher modal com dados
        fillUserModal(data);
        
        return true;  // ✅ Retornar true se sucesso
    } catch (error) {
        console.error("Erro na requisição:", error);
        alert("Erro ao carregar usuário. Tente novamente.");
        return false;  // ✅ Retornar false se erro
    }
}

/* ===============================
   FILL MODAL
================================ */
function fillUserModal(user) {
    document.getElementById("upd_user_id").value = user.id;
    document.getElementById("upd_username").value = user.username;
    document.getElementById("upd_email").value = user.email;
    document.getElementById("upd_first_name").value = user.first_name;
    document.getElementById("upd_last_name").value = user.last_name;

    const checkbox = document.getElementById("upd_is_active");
    if (checkbox) {
        checkbox.checked = Boolean(user.is_active);
    }

    // ✅ Limpar e preencher empresas
    usuariosState.empresasSelecionadas = [];
    user.empresas.forEach(emp => {
        usuariosState.empresasSelecionadas.push({
            id: emp.cod_empresa,
            nome: emp.fantasia || emp.razao || emp.cod_empresa
        });
    });
    renderizarEmpresasSelecionadas();
    
    // ✅ Limpar e preencher grupos
    usuariosState.gruposSelecionados = [];
    user.grupos.forEach(grp => {
        usuariosState.gruposSelecionados.push({
            id: grp.id,
            nome: grp.name
        });
    });
    renderizarGruposSelecionados();
    
    // ✅ Preencher selects com dados disponíveis (aceitar variações de key names)
    const empresasDisp = user.empresas_disponiveis || user.Empresas_Disponiveis || user.empresasDisponiveis || user.Empresas_Disponiveis || [];
    const gruposDisp = user.grupos_disponiveis || user.Grupos_Disponiveis || user.gruposDisponiveis || user.Grupos_Disponiveis || [];

    console.log("🏢 Empresas disponíveis para preencher:", empresasDisp);
    console.log("👥 Grupos disponíveis para preencher:", gruposDisp);

    if (Array.isArray(empresasDisp) && empresasDisp.length > 0) {
        console.log("✅ Preenchendo empresas...");
        preencherSelectEmpresas(empresasDisp);
    } else {
        console.warn("⚠️ Nenhuma empresa disponível encontrada");
    }

    if (Array.isArray(gruposDisp) && gruposDisp.length > 0) {
        console.log("✅ Preenchendo grupos...");
        preencherSelectGrupos(gruposDisp);
    } else {
        console.warn("⚠️ Nenhum grupo disponível encontrado");
    }
}

/* ===============================
   PREENCHER SELECT COM EMPRESAS DISPONÍVEIS
================================ */
function preencherSelectEmpresas(empresas) {
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
function preencherSelectGrupos(grupos) {
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
function preencherSelectInsEmpresas(empresas) {
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

function preencherSelectInsGrupos(grupos) {
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
function adicionarEmpresa() {
    const select = document.getElementById("upd_empresas_select");
    if (!select.value) {
        alert("Selecione uma empresa!");
        return;
    }
    
    const empId = select.value;
    const empNome = select.options[select.selectedIndex].text;
    
    // ✅ Verificar se já foi adicionada
    if (usuariosState.empresasSelecionadas.some(e => e.id == empId)) {
        alert("Esta empresa já foi adicionada!");
        return;
    }
    
    usuariosState.empresasSelecionadas.push({
        id: empId,
        nome: empNome
    });
    
    select.value = ""; // ✅ Limpar select
    renderizarEmpresasSelecionadas();
}

function removerEmpresa(empId) {
    usuariosState.empresasSelecionadas = usuariosState.empresasSelecionadas.filter(
        e => e.id != empId
    );
    renderizarEmpresasSelecionadas();
}

function renderizarEmpresasSelecionadas() {
    const tbody = document.getElementById("upd_empresas_tbody");
    const hidden = document.getElementById("upd_empresas_hidden");
    
    if (!tbody) return;
    
    // ✅ Limpar tbody
    tbody.innerHTML = "";
    
    // ✅ Adicionar linhas
    usuariosState.empresasSelecionadas.forEach(emp => {
        const row = document.createElement("tr");
        row.innerHTML = `
            <td>${emp.nome}</td>
            <td>
                <button type="button" class="btn btn-sm btn-danger" 
                        onclick="removerEmpresa(${emp.id})">
                    Remover
                </button>
            </td>
        `;
        tbody.appendChild(row);
    });
    
    // ✅ Atualizar hidden input com IDs separados por vírgula
    hidden.value = usuariosState.empresasSelecionadas
        .map(e => e.id)
        .join(",");
}

/* ===============================
   ADICIONAR/REMOVER GRUPOS
================================ */
function adicionarGrupo() {
    const select = document.getElementById("upd_grupos_select");
    if (!select.value) {
        alert("Selecione um grupo!");
        return;
    }
    
    const grupoId = select.value;
    const grupoNome = select.options[select.selectedIndex].text;
    
    // ✅ Verificar se já foi adicionado
    if (usuariosState.gruposSelecionados.some(g => g.id == grupoId)) {
        alert("Este grupo já foi adicionado!");
        return;
    }
    
    usuariosState.gruposSelecionados.push({
        id: grupoId,
        nome: grupoNome
    });
    
    select.value = ""; // ✅ Limpar select
    renderizarGruposSelecionados();
}

function removerGrupo(grupoId) {
    usuariosState.gruposSelecionados = usuariosState.gruposSelecionados.filter(
        g => g.id != grupoId
    );
    renderizarGruposSelecionados();
}

function renderizarGruposSelecionados() {
    const tbody = document.getElementById("upd_grupos_tbody");
    const hidden = document.getElementById("upd_grupos_hidden");
    
    if (!tbody) return;
    
    // ✅ Limpar tbody
    tbody.innerHTML = "";
    
    // ✅ Adicionar linhas
    usuariosState.gruposSelecionados.forEach(grp => {
        const row = document.createElement("tr");
        row.innerHTML = `
            <td>${grp.nome}</td>
            <td>
                <button type="button" class="btn btn-sm btn-danger" 
                        onclick="removerGrupo(${grp.id})">
                    Remover
                </button>
            </td>
        `;
        tbody.appendChild(row);
    });
    
    // ✅ Atualizar hidden input com IDs separados por vírgula
    hidden.value = usuariosState.gruposSelecionados
        .map(g => g.id)
        .join(",");
}

/* ===============================
   INSERT: ADICIONAR/REMOVER EMPRESAS
================================ */
function adicionarEmpresaIns() {
    const select = document.getElementById("ins_empresas_select");
    if (!select.value) {
        alert("Selecione uma empresa!");
        return;
    }
    
    const empId = select.value;
    const empNome = select.options[select.selectedIndex].text;
    
    // ✅ Verificar se já foi adicionada
    if (usuariosState.empresasSelecionadas.some(e => e.id == empId)) {
        alert("Esta empresa já foi adicionada!");
        return;
    }
    
    usuariosState.empresasSelecionadas.push({
        id: empId,
        nome: empNome
    });
    
    select.value = ""; // ✅ Limpar select
    renderizarEmpresasSelecionadasIns();
}

function removerEmpresaIns(empId) {
    usuariosState.empresasSelecionadas = usuariosState.empresasSelecionadas.filter(
        e => e.id != empId
    );
    renderizarEmpresasSelecionadasIns();
}

function renderizarEmpresasSelecionadasIns() {
    const tbody = document.getElementById("ins_empresas_tbody");
    const hidden = document.getElementById("ins_empresas_hidden");
    
    if (!tbody) return;
    
    // ✅ Limpar tbody
    tbody.innerHTML = "";
    
    // ✅ Adicionar linhas
    usuariosState.empresasSelecionadas.forEach(emp => {
        const row = document.createElement("tr");
        row.innerHTML = `
            <td>${emp.nome}</td>
            <td>
                <button type="button" class="btn btn-sm btn-danger" 
                        onclick="removerEmpresaIns(${emp.id})">
                    Remover
                </button>
            </td>
        `;
        tbody.appendChild(row);
    });
    
    // ✅ Atualizar hidden input com IDs separados por vírgula
    hidden.value = usuariosState.empresasSelecionadas
        .map(e => e.id)
        .join(",");
    
    // ✅ Feedback visual
    const count = usuariosState.empresasSelecionadas.length;
    if (count > 0) {
        console.log(`✅ ${count} empresa(s) selecionada(s)`);
    }
}

/* ===============================
   INSERT: ADICIONAR/REMOVER GRUPOS
================================ */
function adicionarGrupoIns() {
    const select = document.getElementById("ins_grupos_select");
    if (!select.value) {
        alert("Selecione um grupo!");
        return;
    }
    
    const grupoId = select.value;
    const grupoNome = select.options[select.selectedIndex].text;
    
    // ✅ Verificar se já foi adicionado
    if (usuariosState.gruposSelecionados.some(g => g.id == grupoId)) {
        alert("Este grupo já foi adicionado!");
        return;
    }
    
    usuariosState.gruposSelecionados.push({
        id: grupoId,
        nome: grupoNome
    });
    
    select.value = ""; // ✅ Limpar select
    renderizarGruposSelecionadosIns();
}

function removerGrupoIns(grupoId) {
    usuariosState.gruposSelecionados = usuariosState.gruposSelecionados.filter(
        g => g.id != grupoId
    );
    renderizarGruposSelecionadosIns();
}

function renderizarGruposSelecionadosIns() {
    const tbody = document.getElementById("ins_grupos_tbody");
    const hidden = document.getElementById("ins_grupos_hidden");
    
    if (!tbody) return;
    
    // ✅ Limpar tbody
    tbody.innerHTML = "";
    
    // ✅ Adicionar linhas
    usuariosState.gruposSelecionados.forEach(grp => {
        const row = document.createElement("tr");
        row.innerHTML = `
            <td>${grp.nome}</td>
            <td>
                <button type="button" class="btn btn-sm btn-danger" 
                        onclick="removerGrupoIns(${grp.id})">
                    Remover
                </button>
            </td>
        `;
        tbody.appendChild(row);
    });
    
    // ✅ Atualizar hidden input com IDs separados por vírgula
    hidden.value = usuariosState.gruposSelecionados
        .map(g => g.id)
        .join(",");
}

/* ===============================
   INSERT: PREENCHER SELECTS (dados vindos da view /usuario/inserir/)
================================ */
function preencherSelectInsEmpresas(empresas) {
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

function preencherSelectInsGrupos(grupos) {
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


