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
    todosGrupos: []            // ✅ Lista completa de grupos disponíveis
};

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
        usuariosState.allUsers.push({
            id: row.dataset.userId,
            html: row.innerHTML  // ✅ Guardar HTML para reutilizar
        });
    });
    
    console.log(`✅ ${usuariosState.allUsers.length} usuários carregados em memória`);
}

/* ===============================
   BUSCA (Client-side, sem fazer requests HTTP)
================================ */
function initBusca() {
    const formBusca = document.querySelector("form[action*='Dm_Usuarios']");
    if (!formBusca) return;
    
    const inputBusca = formBusca.querySelector("input[name='Buscar']");
    if (!inputBusca) return;
    
    // ✅ Prevenir form submit tradicional, usar AJAX
    formBusca.addEventListener("submit", (e) => {
        e.preventDefault();
        
        const query = inputBusca.value.trim().toLowerCase();
        usuariosState.searchQuery = query;
        usuariosState.currentPage = 1;  // Reset para página 1
        
        atualizarTabelaFiltrada();
    });
    
    // ✅ Busca em tempo real enquanto digita (opcional)
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
    
    const query = usuariosState.searchQuery;
    
    // ✅ Buscar nas propriedades do HTML renderizado
    return usuariosState.allUsers.filter(user => {
        const html = user.html.toLowerCase();
        return html.includes(query);
    });
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
        // ✅ Renderizar apenas usuários da página atual
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

    modalEl.addEventListener("hidden.bs.modal", () => {
        const form = modalEl.querySelector("form");
        if (form) form.reset();
        
        // ✅ Limpar também os arrays de empresas e grupos
        usuariosState.empresasSelecionadas = [];
        usuariosState.gruposSelecionados = [];
        
        // ✅ Limpar as tabelas e hidden inputs
        renderizarEmpresasSelecionadasIns();
        renderizarGruposSelecionadosIns();
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

        await loadUser(userId);
        const modal = new bootstrap.Modal(modalEl, {
            backdrop: "static",
            keyboard: false
        });
        modal.show();
    });
}

/* ===============================
   LOAD USER (API)
================================ */
async function loadUser(userId) {
    try {
        const resp = await fetch(`/usuario/${userId}/`, {
            headers: { 
                "X-Requested-With": "XMLHttpRequest",
                "Accept": "application/json"
            }
        });

        if (!resp.ok) {
            console.error(`Erro ao carregar usuário: ${resp.status} - ${resp.statusText}`);
            alert(`Erro ao carregar usuário: ${resp.statusText}`);
            return;
        }

        const data = await resp.json();
        fillUserModal(data);
    } catch (error) {
        console.error("Erro na requisição:", error);
        alert("Erro ao carregar usuário. Tente novamente.");
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
    document.getElementById("upd_is_active").checked = user.is_active;
    
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


