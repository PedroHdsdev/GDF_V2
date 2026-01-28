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
        og_estado_empresas.searchQuery = query;
        og_estado_empresas.currentPage = 1;  // Reset para página 1
        
        fn_atualizar_tabela_filtrada();
    });
    
    // ✅ Busca em tempo real enquanto digita
    inputBusca.addEventListener("input", (e) => {
        const query = e.target.value.trim().toLowerCase();
        og_estado_empresas.searchQuery = query;
        og_estado_empresas.currentPage = 1;
        
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
function fn_init_empresa_ins() {
    const btnAbrirModal = document.getElementById("btnAbrirModalEmpresaIns");
    const modalEl = document.getElementById("modalEmpresaIns");
    
    if (!btnAbrirModal || !modalEl) {
        console.error("❌ Botão ou modal não encontrado");
        return;
    }
    
    // Clique no botão Cadastrar
    btnAbrirModal.addEventListener("click", async (e) => {
        e.preventDefault();
        console.log("🔄 Clique no botão Cadastrar - buscando grupos...");
        
        // Fechar modal de UPDATE se estiver aberto
        fn_fechar_modal_aberto();
        
        // Buscar grupos ANTES de abrir o modal
        try {
            console.log("🔄 Buscando grupos em /empresa/inserir/...");
            const resp = await fetch('/empresa/inserir/', {
                method: 'GET',
                headers: { 
                    'X-Requested-With': 'XMLHttpRequest', 
                    'Accept': 'application/json' 
                }
            });
            console.log("📡 Response status:", resp.status);
            
            if (resp.ok) {
                const data = await resp.json();
                console.log("📦 Dados recebidos:", data);
                console.log("📋 Estrutura de todos_grupos:", data.todos_grupos);
                
                const grupos = data.todos_grupos || [];
                console.log(`✅ ${grupos.length} grupos encontrados`);
                
                if (grupos.length > 0) {
                    console.log("🔍 Primeiro grupo:", grupos[0]);
                }
                
                // PREENCHER select ANTES de abrir modal
                fn_preencher_select_grupos(grupos);
                
                // AGORA SIM, abrir o modal
                og_estado_empresas.modalAberto = "modalEmpresaIns";
                const modal = new bootstrap.Modal(modalEl, {
                    backdrop: "static",
                    keyboard: false
                });
                modal.show();
                console.log("✅ Modal aberto após carregar grupos");
            } else {
                console.warn('❌ Falha ao carregar grupos:', resp.status);
                alert('Erro ao carregar dados. Tente novamente.');
            }
        } catch (err) {
            console.error('💥 Erro ao buscar grupos:', err);
            alert('Erro de conexão. Tente novamente.');
        }
    });
    
    // Limpar modal ao fechar
    modalEl.addEventListener("hidden.bs.modal", () => {
        const form = modalEl.querySelector("form");
        if (form) form.reset();
        
        if (og_estado_empresas.modalAberto === "modalEmpresaIns") {
            og_estado_empresas.modalAberto = null;
        }
    });
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
            alert(`Erro ao carregar empresa: ${resp.statusText}`);
            return false;  // ✅ Retornar false se falhar
        }

        const data = await resp.json();
        console.log("✅ Dados da empresa recebidos com sucesso");

        // ✅ Preencher o formulário modal
        fn_preencher_formulario(data);
        
        return true;  // ✅ Retornar true se sucesso

    } catch (err) {
        console.error("Erro ao fazer fetch da empresa:", err);
        alert("Erro ao carregar dados da empresa");
        return false;  // ✅ Retornar false se erro
    }
}

/* ===============================
   PREENCHER FORMULÁRIO UPDATE
================================ */
function fn_preencher_formulario(data) {
  // Atualizar action dos forms com o ID da empresa
  document.getElementById('formEmpresaUpd').action = `/empresa/${data.cod_empresa}/`;
  document.getElementById('formCertUpd').action = `/empresa/${data.cod_empresa}/`;
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
  
  // Resetar botões
  document.getElementById('btn-edit-empresa').style.display = 'inline-block';
  document.getElementById('btn-save-empresa').style.display = 'none';
  document.getElementById('btn-cancel-empresa').style.display = 'none';
  
  document.getElementById('btn-edit-cert').style.display = 'inline-block';
  document.getElementById('btn-save-cert').style.display = 'none';
  document.getElementById('btn-cancel-cert').style.display = 'none';
  
  // Tornar campos readonly novamente
  const editableFields = [
    'upd_razao',
    'upd_fantasia',
    'upd_ie',
    'upd_im',
    'upd_iest',
    'upd_crt',
    'upd_cnae',
    'upd_suframa',
    'upd_grpEmpresa_id',
    'upd_chave_acesso'
  ];
  
  editableFields.forEach(fieldId => {
    const field = document.getElementById(fieldId);
    if (field) {
      field.setAttribute('readonly', 'readonly');
    }
  });
  
  // Desabilitar checkbox matriz
  const matrizCheckbox = document.getElementById('upd_matriz');
  if (matrizCheckbox) {
    matrizCheckbox.setAttribute('disabled', 'disabled');
  }
  
  // Desabilitar upload de arquivo
  const fileInput = document.getElementById('upd_cert_file');
  if (fileInput) {
    fileInput.setAttribute('disabled', 'disabled');
    fileInput.value = '';
  }
}

// Função para tornar campos editáveis na aba Empresa
function fn_editar_empresa() {
  // Campos que podem ser editados
  const editableFields = [
    'upd_razao',
    'upd_fantasia',
    'upd_ie',
    'upd_im',
    'upd_iest',
    'upd_crt',
    'upd_cnae',
    'upd_suframa',
    'upd_grpEmpresa_id',
    'upd_chave_acesso'
  ];

  editableFields.forEach(fieldId => {
    const field = document.getElementById(fieldId);
    if (field) {
      field.removeAttribute('readonly');
    }
  });

  // Habilitar checkbox matriz
  const matrizCheckbox = document.getElementById('upd_matriz');
  if (matrizCheckbox) {
    matrizCheckbox.removeAttribute('disabled');
  }

  // Trocar botões
  document.getElementById('btn-edit-empresa').style.display = 'none';
  document.getElementById('btn-save-empresa').style.display = 'inline-block';
  document.getElementById('btn-cancel-empresa').style.display = 'inline-block';
}

// Função para cancelar edição na aba Empresa
function fn_cancelar_edicao_empresa() {
  // Restaurar valores originais
  restoreOriginalFormData();

  // Tornar campos readonly novamente
  const editableFields = [
    'upd_razao',
    'upd_fantasia',
    'upd_ie',
    'upd_im',
    'upd_iest',
    'upd_crt',
    'upd_cnae',
    'upd_suframa',
    'upd_grpEmpresa_id',
    'upd_chave_acesso'
  ];

  editableFields.forEach(fieldId => {
    const field = document.getElementById(fieldId);
    if (field) {
      field.setAttribute('readonly', 'readonly');
    }
  });

  // Desabilitar checkbox matriz
  const matrizCheckbox = document.getElementById('upd_matriz');
  if (matrizCheckbox) {
    matrizCheckbox.setAttribute('disabled', 'disabled');
  }

  // Trocar botões
  document.getElementById('btn-edit-empresa').style.display = 'inline-block';
  document.getElementById('btn-save-empresa').style.display = 'none';
  document.getElementById('btn-cancel-empresa').style.display = 'none';
}

// Função para tornar campos editáveis na aba Certificado
function fn_editar_certificado() {
  // Habilitar upload de arquivo
  const fileInput = document.getElementById('upd_cert_file');
  if (fileInput) {
    fileInput.removeAttribute('disabled');
  }

  // Trocar botões
  document.getElementById('btn-edit-cert').style.display = 'none';
  document.getElementById('btn-save-cert').style.display = 'inline-block';
  document.getElementById('btn-cancel-cert').style.display = 'inline-block';
}

// Função para cancelar edição na aba Certificado
function fn_cancelar_edicao_certificado() {
  // Desabilitar upload de arquivo
  const fileInput = document.getElementById('upd_cert_file');
  if (fileInput) {
    fileInput.setAttribute('disabled', 'disabled');
    fileInput.value = '';
  }

  // Trocar botões
  document.getElementById('btn-edit-cert').style.display = 'inline-block';
  document.getElementById('btn-save-cert').style.display = 'none';
  document.getElementById('btn-cancel-cert').style.display = 'none';
}

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
   VALIDAÇÃO FORMULÁRIO INSERT
================================ */
function fn_validar_formulario_ins(event) {
    event.preventDefault();
    
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
        alert("❌ Erros:\n\n" + errors.join("\n"));
        return false;
    }
    
    event.target.submit();
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
        alert("❌ Erros:\n\n" + errors.join("\n"));
        return false;
    }
    
    event.target.submit();
}
