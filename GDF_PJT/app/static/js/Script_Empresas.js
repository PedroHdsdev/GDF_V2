/* ===============================
   GERENCIAR PAGINAÇÃO & BUSCA NO CLIENTE
================================ */

const og_estado_empresas = {
    allEmpresas: [],      // ✅ Todas as empresas carregadas uma vez
    itemsPerPage: 30,
    currentPage: 1,
    searchQuery: '',
    originalFormData: {},
    modalAberto: null     // ✅ Controlar qual modal está aberto
};

document.addEventListener("DOMContentLoaded", () => {
    // ✅ Carregar dados da tabela no HTML e armazenar em memória
    fn_extrair_empresas_html();
    
    fn_init_paginacao();
    fn_init_busca();
    fn_init_grp_empresa_ins();
    fn_init_empresa_ins();
    fn_init_empresa_upd();
});

/* ===============================
   EXTRAIR EMPRESAS DO HTML (Enviadas pelo Django)
================================ */
function fn_extrair_empresas_html() {
    const rows = document.querySelectorAll(".empresa-row");
    og_estado_empresas.allEmpresas = [];
    
    rows.forEach(row => {
        // ✅ Extrair dados estruturados da linha (seguindo ordem da tabela)
        const cells = row.querySelectorAll("td");
        const empresaData = {
            id: row.dataset.empresaId,
            html: row.innerHTML,
            // Ordem: Status, Código, Certificado, Empresa, CNPJ, Validade Cert.
            status: cells[0]?.textContent.trim() || '',
            codigo: cells[1]?.textContent.trim() || '',
            certificado: cells[2]?.textContent.trim() || '',
            empresa: cells[3]?.textContent.trim() || '',
            cnpj: cells[4]?.textContent.trim() || '',
            validade: cells[5]?.textContent.trim() || ''
        };
        
        og_estado_empresas.allEmpresas.push(empresaData);
    });
    
    console.log(`✅ ${og_estado_empresas.allEmpresas.length} empresas carregadas em memória`);
    console.log('📋 Primeira empresa:', og_estado_empresas.allEmpresas[0]);
}

/* ===============================
   BUSCA (Client-side, sem fazer requests HTTP)
================================ */
function fn_init_busca() {
    const inputBusca = document.getElementById("searchBox");
    if (!inputBusca) {
        console.warn("⚠️ Input de busca não encontrado");
        return;
    }
    
    console.log("✅ Busca inicializada");
    
    // ✅ Busca em tempo real enquanto digita
    inputBusca.addEventListener("input", (e) => {
        const query = e.target.value.trim().toLowerCase();
        console.log(`🔍 Buscando por: "${query}"`);
        og_estado_empresas.searchQuery = query;
        og_estado_empresas.currentPage = 1;  // Reset para página 1
        
        fn_atualizar_tabela_filtrada();
    });
}

/* ===============================
   FILTRAR EMPRESAS
================================ */
function fn_filtrar_empresas() {
    if (!og_estado_empresas.searchQuery) {
        return og_estado_empresas.allEmpresas;  // Sem filtro, retorna todas
    }
    
    const query = og_estado_empresas.searchQuery.toLowerCase();
    
    // ✅ Buscar em múltiplos campos
    const filtradas = og_estado_empresas.allEmpresas.filter(empresa => {
        return (
            empresa.codigo.toLowerCase().includes(query) ||
            empresa.empresa.toLowerCase().includes(query) ||
            empresa.cnpj.toLowerCase().includes(query) ||
            empresa.validade.toLowerCase().includes(query)
        );
    });
    
    console.log(`🔎 Filtradas: ${filtradas.length} de ${og_estado_empresas.allEmpresas.length}`);
    return filtradas;
}

/* ===============================
   CALCULAR PAGINAÇÃO
================================ */
function fn_calcular_paginacao(empresasFiltradas) {
    const total = empresasFiltradas.length;
    const totalPages = Math.ceil(total / og_estado_empresas.itemsPerPage);
    
    // ✅ Garantir que currentPage é válida
    if (og_estado_empresas.currentPage > totalPages) {
        og_estado_empresas.currentPage = Math.max(1, totalPages);
    }
    
    const start = (og_estado_empresas.currentPage - 1) * og_estado_empresas.itemsPerPage;
    const end = start + og_estado_empresas.itemsPerPage;
    
    return {
        itemsNoInterval: empresasFiltradas.slice(start, end),
        totalPages,
        currentPage: og_estado_empresas.currentPage,
        total
    };
}

/* ===============================
   ATUALIZAR TABELA (após busca ou paginação)
================================ */
function fn_atualizar_tabela_filtrada() {
    const empresasFiltradas = fn_filtrar_empresas();
    const paginacao = fn_calcular_paginacao(empresasFiltradas);
    
    const tbody = document.querySelector("table tbody");
    if (!tbody) return;
    
    // ✅ Se não há resultados
    if (paginacao.itemsNoInterval.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6" class="text-center py-3">
                    Nenhuma empresa encontrada
                </td>
            </tr>
        `;
    } else {
        // ✅ Renderizar apenas empresas da página atual usando HTML guardado
        tbody.innerHTML = paginacao.itemsNoInterval
            .map(empresa => `<tr class="empresa-row" data-empresa-id="${empresa.id}">${empresa.html}</tr>`)
            .join('');
        
        // Nota: Listeners de clique são gerenciados via delegação em fn_init_empresa_upd()
    }
    
    // ✅ Atualizar paginação
    fn_atualizar_paginacao(paginacao);
}

/* ===============================
   ADICIONAR LISTENERS NA TABELA
================================ */
function fn_adicionar_listeners_tabela() {
    document.querySelectorAll(".empresa-row").forEach(row => {
        row.addEventListener("click", async (e) => {
            if (e.target.closest("a, button, input, label")) return;
            
            const empresaId = row.dataset.empresaId;
            if (!empresaId) return;
            
            await fn_carregar_empresa(empresaId);
            const modal = new bootstrap.Modal(document.getElementById("modalEmpresaUpd"));
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
    og_estado_empresas.currentPage = pageNum;
    fn_atualizar_tabela_filtrada();
    window.scrollTo(0, 0);  // ✅ Scroll para o topo
}

/* ===============================
   INICIALIZAR PAGINAÇÃO
================================ */
function fn_init_paginacao() {
    // ✅ Renderizar paginação inicial
    fn_atualizar_tabela_filtrada();
    
    // Nota: Listeners de clique são gerenciados via delegação em fn_init_empresa_upd()
}

/* ===============================
   INS – INSERT EMPRESA
================================ */ 
/* ===============================
   MODAL CRIAR GRUPO DE EMPRESAS (vinculado ao cliente do usuário logado)
================================ */
function fn_init_grp_empresa_ins() {
    const modalEl = document.getElementById("modalGrpEmpresaIns");
    if (!modalEl) {
        console.warn("Script_Empresas: modal modalGrpEmpresaIns não encontrado.");
        return;
    }

    // Delegação: capturar clique no botão (mesmo que carregado depois)
    document.addEventListener("click", function(e) {
        const btn = e.target.closest("#btnAbrirModalGrpEmpresaIns");
        if (!btn) return;
        e.preventDefault();
        e.stopPropagation();

        const el = document.getElementById("modalGrpEmpresaIns");
        if (!el) return;

        fn_fechar_modal_aberto();
        og_estado_empresas.modalAberto = "modalGrpEmpresaIns";
        const modal = new bootstrap.Modal(el, { backdrop: "static", keyboard: false });
        modal.show();
    });

    modalEl.addEventListener("show.bs.modal", () => {
        if (typeof Notificacoes !== 'undefined') Notificacoes.limparModal('modalGrpEmpresaInsAlerts');
    });
    modalEl.addEventListener("hidden.bs.modal", () => {
        const form = modalEl.querySelector("form");
        if (form) form.reset();
        if (og_estado_empresas.modalAberto === "modalGrpEmpresaIns") {
            og_estado_empresas.modalAberto = null;
        }
    });
}

function fn_init_empresa_ins() {
    const btnAbrirModal = document.getElementById("btnAbrirModalEmpresaIns");
    const modalEl = document.getElementById("modalEmpresaIns");
    
    if (!btnAbrirModal || !modalEl) {
        console.error("❌ Botão ou modal não encontrado");
        return;
    }
    
    btnAbrirModal.addEventListener("click", async (e) => {
        e.preventDefault();
        fn_fechar_modal_aberto();
        const codClienteEl = document.getElementById('ins_cod_cliente');
        const qs = codClienteEl && codClienteEl.value ? '?cod_cliente=' + encodeURIComponent(codClienteEl.value) : '';
        if (codClienteEl && !codClienteEl.value) {
            og_estado_empresas.modalAberto = "modalEmpresaIns";
            const modal = new bootstrap.Modal(modalEl, { backdrop: "static", keyboard: false });
            modal.show();
            return;
        }
        try {
            const resp = await fetch('/empresa/inserir/' + qs, {
                method: 'GET',
                headers: { 'X-Requested-With': 'XMLHttpRequest', 'Accept': 'application/json' }
            });
            if (resp.ok) {
                const data = await resp.json();
                const grupos = data.todos_grupos || [];
                fn_preencher_select_grupos(grupos);
                og_estado_empresas.modalAberto = "modalEmpresaIns";
                const modal = new bootstrap.Modal(modalEl, { backdrop: "static", keyboard: false });
                modal.show();
            } else {
                Notificacoes.pagina('Erro ao carregar dados. Se for superusuário, selecione o cliente primeiro.', 'danger');
            }
        } catch (err) {
            console.error('Erro ao buscar grupos:', err);
            Notificacoes.pagina('Erro de conexão. Tente novamente.', 'danger');
        }
    });
    
    modalEl.addEventListener("show.bs.modal", () => {
        if (typeof Notificacoes !== 'undefined') Notificacoes.limparModal('modalEmpresaInsAlerts');
    });
    modalEl.addEventListener("hidden.bs.modal", () => {
        const form = modalEl.querySelector("form");
        if (form) form.reset();
        if (og_estado_empresas.modalAberto === "modalEmpresaIns") {
            og_estado_empresas.modalAberto = null;
        }
    });

    // Superuser: ao trocar o cliente, recarregar grupos do select
    const codClienteSelect = document.getElementById('ins_cod_cliente');
    if (codClienteSelect) {
        codClienteSelect.addEventListener("change", async () => {
            const cod = codClienteSelect.value;
            if (!cod) return;
            try {
                const resp = await fetch('/empresa/inserir/?cod_cliente=' + encodeURIComponent(cod), {
                    method: 'GET',
                    headers: { 'X-Requested-With': 'XMLHttpRequest', 'Accept': 'application/json' }
                });
                if (resp.ok) {
                    const data = await resp.json();
                    fn_preencher_select_grupos(data.todos_grupos || []);
                }
            } catch (err) {
                console.error('Erro ao recarregar grupos por cliente:', err);
            }
        });
    }
}

/* ===============================
   PREENCHER SELECT DE GRUPOS
================================ */
function fn_preencher_select_grupos(grupos) {
    console.log("🎯 fn_preencher_select_grupos chamado com:", grupos);
    
    const select = document.getElementById("ins_grpempresas");
    if (!select) {
        console.error("❌ Select ins_grpempresas não encontrado!");
        return;
    }
    
    console.log("✅ Select encontrado, options atuais:", select.options.length);
    
    // Limpar opções existentes (manter apenas a primeira "Selecione um grupo")
    while (select.options.length > 1) {
        select.removeChild(select.lastChild);
    }
    
    console.log("🧹 Select limpo, options restantes:", select.options.length);
    
    // Se não há grupos, mostrar aviso
    if (!grupos || grupos.length === 0) {
        console.warn("⚠️  Nenhum grupo encontrado!");
        return;
    }
    
    // Adicionar grupos
    grupos.forEach((grp, index) => {
        console.log(`  Processando grupo ${index + 1}:`, grp);
        const option = document.createElement('option');
        
        const grpValue = grp.grp_empresa || grp.id || '';
        const grpDesc = grp.descricao || grp.nome || grp.grp_empresa || grp.id || '';
        
        option.value = grpValue;
        option.textContent = `${grpValue} - ${grpDesc}`;
        
        select.appendChild(option);
        console.log(`    ✅ Adicionado: value="${option.value}" text="${option.textContent}"`);
    });
    
    console.log(`✅ Total final de options no select: ${select.options.length}`);
    console.log(`✅ ${grupos.length} grupos adicionados ao select`);
}

/* ===============================
   UPD – UPDATE EMPRESA
================================ */
function fn_init_empresa_upd() {
    const modalEl = document.getElementById("modalEmpresaUpd");
    if (!modalEl) return;

    document.addEventListener("click", async (e) => {
        const row = e.target.closest(".empresa-row");
        if (!row) return;
        
        if (e.target.closest("a, button, input, label")) return;

        const empresaId = row.dataset.empresaId;
        if (!empresaId) return;

        // ✅ Fechar modal de INSERT se estiver aberto
        fn_fechar_modal_aberto();
        
        // ✅ Marcar como modal aberto
        og_estado_empresas.modalAberto = "modalEmpresaUpd";
        
        // ✅ Aguardar dados serem carregados ANTES de abrir o modal
        const sucesso = await fn_carregar_empresa(empresaId);
        
        if (sucesso) {
            const modal = new bootstrap.Modal(modalEl, {
                backdrop: "static",
                keyboard: false
            });
            modal.show();
        } else {
            og_estado_empresas.modalAberto = null;
        }
    });

    modalEl.addEventListener("show.bs.modal", () => {
        if (typeof Notificacoes !== 'undefined') Notificacoes.limparModal('modalEmpresaUpdAlerts');
    });
    modalEl.addEventListener("hidden.bs.modal", () => {
        fn_resetar_formulario();
        
        // ✅ Desmarcar modal aberto
        if (og_estado_empresas.modalAberto === "modalEmpresaUpd") {
            og_estado_empresas.modalAberto = null;
        }
    });
}

/* ===============================
   GERENCIAR MODAIS (prevenir múltiplos abertos)
================================ */
function fn_fechar_modal_aberto() {
    if (!og_estado_empresas.modalAberto) return;
    
    const modalElement = document.getElementById(og_estado_empresas.modalAberto);
    if (modalElement) {
        const modalInstance = bootstrap.Modal.getInstance(modalElement);
        if (modalInstance) {
            console.log(`🔒 Fechando modal: ${og_estado_empresas.modalAberto}`);
            modalInstance.hide();
            og_estado_empresas.modalAberto = null;
        }
    }
}

/* ===============================
   LOAD EMPRESA (API)
================================ */
async function fn_carregar_empresa(empresaId) {
    try {
        console.log(`📥 Iniciando carregamento da empresa ${empresaId}...`);
        
        const resp = await fetch(`/empresa/${empresaId}/`, {
            headers: { 
                "X-Requested-With": "XMLHttpRequest",
                "Accept": "application/json"
            }
        });

        if (!resp.ok) {
            console.error(`Erro ao carregar empresa: ${resp.status} - ${resp.statusText}`);
            Notificacoes.modal('Erro ao carregar empresa: ' + resp.statusText, 'danger', 'modalEmpresaUpdAlerts');
            return false;  // ✅ Retornar false se falhar
        }

        const data = await resp.json();
        console.log("✅ Dados da empresa recebidos com sucesso");

        // ✅ Preencher o formulário modal
        fn_preencher_formulario(data);
        
        return true;  // ✅ Retornar true se sucesso

    } catch (err) {
        console.error("Erro ao fazer fetch da empresa:", err);
        Notificacoes.modal("Erro ao carregar dados da empresa", 'danger', 'modalEmpresaUpdAlerts');
        return false;  // ✅ Retornar false se erro
    }
}

/* ===============================
   PREENCHER FORMULÁRIO UPDATE
================================ */
function fn_preencher_formulario(data) {
  // Atualizar action do form de empresa com o ID da empresa
  document.getElementById('formEmpresaUpd').action = `/empresa/${data.cod_empresa}/`;
  // Certificado tem action estático no HTML: /empresa/Cert/
  document.getElementById('upd_empresa_id_hidden').value = data.cod_empresa || '';
  
  // Dados da empresa
  document.getElementById('upd_empresa_id').value = data.cod_empresa || '';
  document.getElementById('upd_emp_cnpj').value = data.cnpj || '';
  document.getElementById('upd_razao').value = data.razao || '';
  document.getElementById('upd_fantasia').value = data.fantasia || '';
  document.getElementById('upd_ie').value = data.ie || '';
  document.getElementById('upd_im').value = data.im || '';
  document.getElementById('upd_tipo').value = data.tipo || '';
  document.getElementById('upd_crt').value = data.crt || '';
  document.getElementById('upd_cnae').value = data.cnae || '';
  document.getElementById('upd_iest').value = data.iest || '';
  document.getElementById('upd_suframa').value = data.suframa || '';
  document.getElementById('upd_grpEmpresa_id').value = data.grp_empresa || '';
  document.getElementById('upd_chave_acesso').value = data.chave_acesso || '';
  document.getElementById('upd_cliente_id').value = data.cod_cliente || '';
    document.getElementById('upd_cert_codempresa').value = data.cod_empresa || '';
  
  // Checkbox de matriz
  const matrizCheckbox = document.getElementById('upd_matriz');
  if (matrizCheckbox) {
    matrizCheckbox.checked = data.matriz || false;
  }
  
  // Dados do certificado
  if (data.cert_empresa) {
    document.getElementById('upd_emissor').value = data.cert_empresa.emissor || '';
    document.getElementById('upd_cert_cnpj').value = data.cert_empresa.cpf_cnpj || '';
    document.getElementById('upd_dt_inicial').value = data.cert_empresa.ini_validade || '';
    document.getElementById('upd_dt_fim').value = data.cert_empresa.fim_validade || '';
  } else {
    fn_limpar_certificado();
  }
  
  // Salvar estado original
  saveOriginalFormData();
}

/* ===============================
   LIMPAR CAMPOS DO CERTIFICADO
================================ */
function fn_limpar_certificado() {
  document.getElementById('upd_emissor').value = '';
  document.getElementById('upd_cert_cnpj').value = '';
  document.getElementById('upd_dt_inicial').value = '';
  document.getElementById('upd_dt_fim').value = '';
}

/* ===============================
   RESETAR FORMULÁRIO UPDATE
================================ */
function fn_resetar_formulario() {
  // Resetar para aba inicial
  const firstTab = document.querySelector('#empresaTabs .nav-link:first-child');
  if (firstTab) {
    firstTab.click();
  }
  
  // Limpar arquivo de certificado
  const fileInput = document.getElementById('upd_cert_file');
  if (fileInput) {
    fileInput.value = '';
  }
}

/* ===============================
   VALIDAÇÃO FORMULÁRIO CERTIFICADO
================================ */
function fn_validar_certificado(event) {
  event.preventDefault();
  
  const fileInput = document.getElementById('upd_cert_file');
  const emissor = document.getElementById('upd_emissor').value.trim();
  const dtInicial = document.getElementById('upd_dt_inicial').value.trim();
  const dtFim = document.getElementById('upd_dt_fim').value.trim();
  
  // Validar se algo foi enviado
  if (!fileInput.files.length && !emissor && !dtInicial && !dtFim) {
    Notificacoes.modal('Selecione um arquivo ou preencha os dados do certificado', 'warning', 'modalEmpresaUpdAlerts');
    return false;
  }
  
  // Se há datas, validar formato
  if (dtInicial && !fn_validar_data(dtInicial)) {
    Notificacoes.modal('Formato de data inválido para Data Início. Use DD/MM/YYYY ou YYYY-MM-DD', 'warning', 'modalEmpresaUpdAlerts');
    return false;
  }
  
  if (dtFim && !fn_validar_data(dtFim)) {
    Notificacoes.modal('Formato de data inválido para Data Fim. Use DD/MM/YYYY ou YYYY-MM-DD', 'warning', 'modalEmpresaUpdAlerts');
    return false;
  }
  
  // Se passou na validação, enviar formulário
  document.getElementById('formCertUpd').submit();
}

/* ===============================
   VALIDADOR DE DATAS
================================ */
function fn_validar_data(data) {
  // Aceita formatos DD/MM/YYYY ou YYYY-MM-DD
  const regex = /^(\d{2}\/\d{2}\/\d{4}|\d{4}-\d{2}-\d{2})$/;
  return regex.test(data);
}

/* ===============================
   SALVAR/RESTAURAR ESTADO ORIGINAL
================================ */
// Salvar estado original do formulário
function saveOriginalFormData() {
  og_estado_empresas.originalFormData = {
    razao: document.getElementById('upd_razao').value,
    fantasia: document.getElementById('upd_fantasia').value,
    ie: document.getElementById('upd_ie').value,
    im: document.getElementById('upd_im').value,
    iest: document.getElementById('upd_iest').value,
    crt: document.getElementById('upd_crt').value,
    cnae: document.getElementById('upd_cnae').value,
    suframa: document.getElementById('upd_suframa').value,
    grpEmpresa: document.getElementById('upd_grpEmpresa_id').value,
    chaveAcesso: document.getElementById('upd_chave_acesso').value,
    matriz: document.getElementById('upd_matriz').checked
  };
}

// Restaurar estado original do formulário
function restoreOriginalFormData() {
  if (Object.keys(og_estado_empresas.originalFormData).length === 0) return;

  document.getElementById('upd_razao').value = og_estado_empresas.originalFormData.razao || '';
  document.getElementById('upd_fantasia').value = og_estado_empresas.originalFormData.fantasia || '';
  document.getElementById('upd_ie').value = og_estado_empresas.originalFormData.ie || '';
  document.getElementById('upd_im').value = og_estado_empresas.originalFormData.im || '';
  document.getElementById('upd_iest').value = og_estado_empresas.originalFormData.iest || '';
  document.getElementById('upd_crt').value = og_estado_empresas.originalFormData.crt || '';
  document.getElementById('upd_cnae').value = og_estado_empresas.originalFormData.cnae || '';
  document.getElementById('upd_suframa').value = og_estado_empresas.originalFormData.suframa || '';
  document.getElementById('upd_grpEmpresa_id').value = og_estado_empresas.originalFormData.grpEmpresa || '';
  document.getElementById('upd_chave_acesso').value = og_estado_empresas.originalFormData.chaveAcesso || '';
  document.getElementById('upd_matriz').checked = og_estado_empresas.originalFormData.matriz || false;
}

// Função para formatar CNPJ (opcional)
function fn_formatar_cnpj(input) {
  let value = input.value.replace(/\D/g, '');
  
  if (value.length <= 14) {
    value = value.replace(/^(\d{2})(\d)/, '$1.$2');
    value = value.replace(/^(\d{2})\.(\d{3})(\d)/, '$1.$2.$3');
    value = value.replace(/\.(\d{3})(\d)/, '.$1/$2');
    value = value.replace(/(\d{4})(\d)/, '$1-$2');
  }
  
  input.value = value;
}

// Adicionar formatação automática ao campo CNPJ no modal de inserção (opcional)
const cnpjInput = document.getElementById('ins_cnpj');
if (cnpjInput) {
  cnpjInput.addEventListener('input', function() {
    fn_formatar_cnpj(this);
  });
}

/* ===============================
   VALIDAÇÃO E ENVIO FORMULÁRIO INSERT (via AJAX para exibir erros no modal)
================================ */
function fn_validar_formulario_ins(event) {
    event.preventDefault();
    
    const form = event.target;
    const cod_empresa = document.getElementById('ins_codempresa').value.trim();
    const cnpj = document.getElementById('ins_cnpj').value.trim();
    const razao = document.getElementById('ins_razao').value.trim();
    const fantasia = document.getElementById('ins_fantasia').value.trim();
    const grp_empresa = document.getElementById('ins_grpempresas').value;
    
    const errors = [];
    if (!cod_empresa) errors.push("Código da empresa é obrigatório");
    if (!cnpj) errors.push("CNPJ é obrigatório");
    if (!razao) errors.push("Razão Social é obrigatória");
    if (!fantasia) errors.push("Nome Fantasia é obrigatório");
    if (!grp_empresa) errors.push("Selecione um Grupo de Empresas");
    
    if (errors.length > 0) {
        Notificacoes.modal("Erros:\n\n" + errors.join("\n"), 'danger', 'modalEmpresaInsAlerts');
        return false;
    }
    
    var formData = new FormData(form);
    var action = form.getAttribute('action');
    var csrfToken = document.querySelector('[name=csrfmiddlewaretoken]') ? document.querySelector('[name=csrfmiddlewaretoken]').value : '';
    
    fetch(action, {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
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
            Notificacoes.modal(result.data.message || 'Empresa cadastrada com sucesso', 'success', 'modalEmpresaInsAlerts');
            setTimeout(function() { window.location.href = window.location.pathname; }, 1500);
        } else if (result.data.erro) {
            Notificacoes.modal(result.data.erro, 'danger', 'modalEmpresaInsAlerts');
        } else {
            Notificacoes.modal('Erro ao cadastrar empresa. Tente novamente.', 'danger', 'modalEmpresaInsAlerts');
        }
    })
    .catch(function(err) {
        console.error('Erro ao enviar formulário:', err);
        Notificacoes.modal('Erro ao enviar formulário. Tente novamente.', 'danger', 'modalEmpresaInsAlerts');
    });
    
    return false;
}

/* ===============================
   VALIDAÇÃO FORMULÁRIO UPDATE
================================ */
function fn_validar_formulario_upd(event) {
    event.preventDefault();
    
    const razao = document.getElementById('upd_razao').value.trim();
    const fantasia = document.getElementById('upd_fantasia').value.trim();
    
    const errors = [];
    if (!razao) errors.push("Razão Social é obrigatória");
    if (!fantasia) errors.push("Nome Fantasia é obrigatório");
    
    if (errors.length > 0) {
        Notificacoes.modal("❌ Erros:\n\n" + errors.join("\n"), 'danger', 'modalEmpresaUpdAlerts');
        return false;
    }
    
    // ✅ Submeter via AJAX
    fn_submit_form_ajax(event.target, 'Empresa');
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
      Notificacoes.modal(data.message, tipoAlert, 'modalEmpresaUpdAlerts');
      
      // ✅ Se sucesso, recarregar tabela após 2 segundos
      if (data.success) {
        setTimeout(() => {
          location.reload();
        }, 2000);
      }
    } else {
      // ✅ Se não for JSON, considerar erro
      Notificacoes.modal('Erro ao processar requisição', 'danger', 'modalEmpresaUpdAlerts');
    }
  })
  .catch(error => {
    console.error(`[fn_submit_form_ajax] Erro:`, error);
    Notificacoes.modal('Erro ao processar requisição', 'danger', 'modalEmpresaUpdAlerts');
  });
}

// ✅ Alertas no modal: Notificacoes.modal (ver PADRAO_ALERTAS.md)
