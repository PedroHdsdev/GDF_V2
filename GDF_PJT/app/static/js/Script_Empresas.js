/* ===============================
   GERENCIAR PAGINAÇÃO & BUSCA NO CLIENTE
================================ */

const og_estado_empresas = {
    allEmpresas: [],      // ✅ Todas as empresas carregadas uma vez
    itemsPerPage: 30,
    currentPage: 1,
    searchQuery: '',
    originalFormData: {},
    modalAberto: null,    // ✅ Controlar qual modal está aberto
    codEmpresaAtual: '',  // empresa aberta no modal (aba Filiais)
    filiaisCache: []      // última lista de filiais carregada (metadados)
};

function fn_empresas_escAttr(s) {
    return String(s == null ? '' : s)
        .replace(/&/g, '&amp;')
        .replace(/"/g, '&quot;')
        .replace(/</g, '&lt;');
}

document.addEventListener("DOMContentLoaded", () => {
    // ✅ Carregar dados da tabela no HTML e armazenar em memória
    fn_extrair_empresas_html();
    
    fn_init_paginacao();
    fn_init_busca();
    fn_init_empresa_ins();
    fn_init_empresa_upd();
    fn_init_emp_tab_filiais();
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
            .map(empresa => `<tr class="empresa-row" data-empresa-id="${fn_empresas_escAttr(empresa.id)}">${empresa.html}</tr>`)
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
    var modalEl = document.getElementById("modalEmpresaUpd");
    if (!modalEl) return;
    document.querySelectorAll(".empresa-row").forEach(row => {
        row.addEventListener("click", async (e) => {
            if (e.target.closest("a, button, input, label")) return;
            const empresaId = row.dataset.empresaId;
            if (!empresaId) return;
            var sucesso = await fn_carregar_empresa(empresaId);
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
            var prefix = (typeof getUrlPrefix === 'function') ? getUrlPrefix() : '';
            var urlInserir = (window.APP_URLS && window.APP_URLS.empresaInserir) ? window.APP_URLS.empresaInserir + (qs ? (qs.charAt(0) === '?' ? qs : '?' + qs) : '') : (prefix || '') + '/empresa/inserir/' + (qs || '');
            const resp = await fetch(urlInserir, {
                method: 'GET',
                headers: { 'X-Requested-With': 'XMLHttpRequest', 'Accept': 'application/json' }
            });
            if (resp.ok) {
                const data = await resp.json();
                og_estado_empresas.modalAberto = "modalEmpresaIns";
                const modal = new bootstrap.Modal(modalEl, { backdrop: "static", keyboard: false });
                modal.show();
            } else {
                Notificacoes.pagina('Erro ao carregar dados. Se for superusuário, selecione o cliente primeiro.', 'danger');
            }
        } catch (err) {
            console.error('Erro ao carregar dados:', err);
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
        
        if (sucesso && typeof bootstrap !== 'undefined' && bootstrap.Modal) {
            const modal = bootstrap.Modal.getOrCreateInstance(modalEl, { backdrop: 'static', keyboard: false });
            modal.show();
        } else {
            og_estado_empresas.modalAberto = null;
            if (!sucesso && typeof Notificacoes !== 'undefined') {
                Notificacoes.pagina('Erro ao carregar dados da empresa. Verifique o console ou tente novamente.', 'danger');
            }
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
        
        var urlUpd = (window.APP_URLS && window.APP_URLS.empresaUpd) ? window.APP_URLS.empresaUpd.replace('__ID__', encodeURIComponent(empresaId)) : ((typeof getUrlPrefix === 'function' ? getUrlPrefix() : '') || '') + '/empresa/' + encodeURIComponent(empresaId) + '/';
        const resp = await fetch(urlUpd, {
            headers: { 
                "X-Requested-With": "XMLHttpRequest",
                "Accept": "application/json"
            }
        });

        if (!resp.ok) {
            console.error(`Erro ao carregar empresa: ${resp.status} - ${resp.statusText}`);
            if (typeof Notificacoes !== 'undefined') {
                Notificacoes.pagina('Erro ao carregar empresa: ' + resp.statusText, 'danger');
            }
            return false;  // ✅ Retornar false se falhar
        }

        const data = await resp.json();
        console.log("✅ Dados da empresa recebidos com sucesso");

        // ✅ Preencher o formulário modal
        fn_preencher_formulario(data);
        
        return true;  // ✅ Retornar true se sucesso

    } catch (err) {
        console.error("Erro ao fazer fetch da empresa:", err);
        if (typeof Notificacoes !== 'undefined') {
            Notificacoes.pagina('Erro ao carregar dados da empresa. Verifique a conexão.', 'danger');
        }
        return false;  // ✅ Retornar false se erro
    }
}

/* ===============================
   PREENCHER FORMULÁRIO UPDATE
================================ */
function fn_preencher_formulario(data) {
  // Atualizar action do form de empresa com o ID da empresa
  var urlUpd = (window.APP_URLS && window.APP_URLS.empresaUpd) ? window.APP_URLS.empresaUpd.replace('__ID__', encodeURIComponent(data.cod_empresa || '')) : ((typeof getUrlPrefix === 'function' ? getUrlPrefix() : '') || '') + '/empresa/' + (data.cod_empresa || '') + '/';
  document.getElementById('formEmpresaUpd').action = urlUpd;
  var formCert = document.getElementById('formCertUpd');
  if (formCert && !(window.APP_URLS && window.APP_URLS.empresaCert)) {
    var prefix = (typeof getUrlPrefix === 'function') ? getUrlPrefix() : '';
    formCert.action = (prefix || '') + '/empresa/Cert/';
  }
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
  document.getElementById('upd_chave_acesso').value = data.chave_acesso || '';
  document.getElementById('upd_cliente_id').value = data.cod_cliente || '';
    document.getElementById('upd_cert_codempresa').value = data.cod_empresa || '';

  var codE = (data && data.cod_empresa != null) ? String(data.cod_empresa).trim() : '';
  if (!codE) {
    var u = document.getElementById('upd_empresa_id');
    if (u && u.value) codE = String(u.value).trim();
  }
  og_estado_empresas.codEmpresaAtual = codE;
  const hidFilEmp = document.getElementById('modal_emp_tab_fil_empresa');
  if (hidFilEmp) hidFilEmp.value = codE;
  const tabFil = document.getElementById('tab-filiais-emp');
  if (tabFil && tabFil.classList.contains('active') && codE) {
    if (typeof fn_emp_tab_filiais_carregar === 'function') fn_emp_tab_filiais_carregar();
  }
  
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
  var senhaEl = document.getElementById('upd_senha_certificado');
  if (senhaEl) senhaEl.value = '';
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
  og_estado_empresas.codEmpresaAtual = '';
  if (typeof fn_emp_tab_filiais_resetForm === 'function') {
    fn_emp_tab_filiais_resetForm(true);
  }
  const tb = document.getElementById('empTabFiliaisTbody');
  if (tb) {
    tb.innerHTML = '<tr><td colspan="5" class="text-center text-muted py-3">Abra uma empresa e carregue a aba Filiais.</td></tr>';
  }
  const alF = document.getElementById('empTabFilialAlerts');
  if (alF) alF.innerHTML = '';
  const hidE = document.getElementById('modal_emp_tab_fil_empresa');
  if (hidE) hidE.value = '';
  if (typeof fn_emp_tab_filiais_fecharModal === 'function') {
    fn_emp_tab_filiais_fecharModal();
  }
  og_estado_empresas.filiaisCache = [];
  
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
    
    const errors = [];
    if (!cod_empresa) errors.push("Código da empresa é obrigatório");
    if (!cnpj) errors.push("CNPJ é obrigatório");
    if (!razao) errors.push("Razão Social é obrigatória");
    if (!fantasia) errors.push("Nome Fantasia é obrigatório");
    
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

/* ===============================
   ABA Filiais — lista na tab; criação/edição no modal #modalFilialEmpForm
================================ */

/** Sincroniza og_estado_empresas + hidden a partir do JSON do modal (upd_empresa_id como fallback). */
function fn_emp_tab_sincronizar_cod_empresa() {
  var c = (og_estado_empresas.codEmpresaAtual || "").trim();
  if (!c) {
    var u = document.getElementById("upd_empresa_id");
    if (u && u.value) c = String(u.value).trim();
  }
  if (!c) {
    var h = document.getElementById("modal_emp_tab_fil_empresa");
    if (h && h.value) c = String(h.value).trim();
  }
  if (c) {
    og_estado_empresas.codEmpresaAtual = c;
    var hid = document.getElementById("modal_emp_tab_fil_empresa");
    if (hid) hid.value = c;
  }
  return c;
}

function fn_emp_mover_modal_filial_para_body() {
  var el = document.getElementById("modalFilialEmpForm");
  if (!el || el.parentNode === document.body) return;
  try {
    document.body.appendChild(el);
  } catch (e) {}
}

function fn_emp_tab_filiais_fecharModal() {
  var el = document.getElementById('modalFilialEmpForm');
  if (!el || typeof bootstrap === 'undefined' || !bootstrap.Modal) return;
  var m = bootstrap.Modal.getInstance(el);
  if (m) m.hide();
}

function fn_emp_tab_filiais_urlFiliais(codEmp) {
  var c = (codEmp || fn_emp_tab_sincronizar_cod_empresa() || og_estado_empresas.codEmpresaAtual || '').trim();
  if (!c) return '';
  if (window.APP_URLS && window.APP_URLS.empresaFiliais) {
    return String(window.APP_URLS.empresaFiliais).split('__COD__').join(encodeURIComponent(c));
  }
  var p = (typeof getUrlPrefix === 'function' ? getUrlPrefix() : '') || '';
  return p + '/empresa/' + encodeURIComponent(c) + '/filiais/';
}

function fn_emp_tab_filiais_resetForm(silent) {
  var idH = document.getElementById('modal_emp_tab_fil_id');
  if (idH) idH.value = '';
  var c = document.getElementById('modal_emp_tab_fil_cod');
  if (c) c.value = '';
  var n = document.getElementById('modal_emp_tab_fil_nome');
  if (n) n.value = '';
  var cnpj = document.getElementById('modal_emp_tab_fil_cnpj');
  if (cnpj) cnpj.value = '';
  var a = document.getElementById('modal_emp_tab_fil_ativo');
  if (a) a.checked = true;
  var tl = document.getElementById('modalFilialEmpFormLabel');
  if (tl) tl.textContent = 'Nova filial';
  var btnS = document.getElementById('btn_modal_emp_tab_fil_salvar');
  if (btnS) btnS.textContent = 'Salvar';
  if (!silent) {
    var al = document.getElementById('empTabFilialAlerts');
    if (al) al.innerHTML = '';
  }
  var mAl = document.getElementById('modalFilialEmpFormAlerts');
  if (mAl) mAl.innerHTML = '';
}

function fn_emp_tab_filiais_abrirModalNova() {
  var al = document.getElementById('modalFilialEmpFormAlerts');
  if (al) al.innerHTML = '';
  var codE = fn_emp_tab_sincronizar_cod_empresa();
  if (!codE) {
    var tAl = document.getElementById('empTabFilialAlerts');
    if (tAl) tAl.innerHTML = '<div class="alert alert-warning py-2">Selecione e carregue uma empresa antes (clique em uma linha da lista de empresas).</div>';
    return;
  }
  fn_emp_tab_filiais_resetForm(true);
  var hidE = document.getElementById('modal_emp_tab_fil_empresa');
  if (hidE) hidE.value = codE;
  var tit = document.getElementById('modalFilialEmpFormLabel');
  if (tit) tit.textContent = 'Nova filial';
  var btnS = document.getElementById('btn_modal_emp_tab_fil_salvar');
  if (btnS) btnS.textContent = 'Cadastrar';
  var el = document.getElementById('modalFilialEmpForm');
  if (el && typeof bootstrap !== 'undefined' && bootstrap.Modal) {
    fn_emp_mover_modal_filial_para_body();
    var inst = bootstrap.Modal.getOrCreateInstance(el, { backdrop: 'static', keyboard: true, focus: true });
    inst.show();
  }
  setTimeout(function () {
    var c = document.getElementById('modal_emp_tab_fil_cod');
    if (c) c.focus();
  }, 500);
}

function fn_emp_tab_filiais_abrirModalEditar(it) {
  if (!it) return;
  var al = document.getElementById('modalFilialEmpFormAlerts');
  if (al) al.innerHTML = '';
  var codE = fn_emp_tab_sincronizar_cod_empresa();
  var hidE = document.getElementById('modal_emp_tab_fil_empresa');
  if (hidE) hidE.value = codE || '';
  var idH = document.getElementById('modal_emp_tab_fil_id');
  if (idH) idH.value = it.id != null ? String(it.id) : '';
  var c = document.getElementById('modal_emp_tab_fil_cod');
  if (c) c.value = it.cod_filial || '';
  var n = document.getElementById('modal_emp_tab_fil_nome');
  if (n) n.value = it.nome || '';
  var cnpj = document.getElementById('modal_emp_tab_fil_cnpj');
  if (cnpj) cnpj.value = it.cnpj || '';
  var atv = document.getElementById('modal_emp_tab_fil_ativo');
  if (atv) atv.checked = !!it.ativo;
  var tit = document.getElementById('modalFilialEmpFormLabel');
  if (tit) tit.textContent = 'Editar filial';
  var btnS = document.getElementById('btn_modal_emp_tab_fil_salvar');
  if (btnS) btnS.textContent = 'Salvar alterações';
  var el = document.getElementById('modalFilialEmpForm');
  if (el && typeof bootstrap !== 'undefined' && bootstrap.Modal) {
    fn_emp_mover_modal_filial_para_body();
    bootstrap.Modal.getOrCreateInstance(el, { backdrop: 'static', keyboard: true, focus: true }).show();
  }
}

function fn_emp_tab_filiais_carregar() {
  fn_emp_tab_sincronizar_cod_empresa();
  var al = document.getElementById('empTabFilialAlerts');
  var url = fn_emp_tab_filiais_urlFiliais('');
  if (!url) {
    if (al) {
      al.innerHTML = '<div class="alert alert-warning py-2">Selecione a empresa (carregue o modal) antes de gerenciar filiais.</div>';
    }
    return;
  }
  if (al) al.innerHTML = '<div class="text-muted small py-1">Carregando filiais…</div>';
  fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest', 'Accept': 'application/json' }, credentials: 'same-origin' })
    .then(function (r) { return r.json().then(function (d) { return { ok: r.ok, d: d, st: r.status }; }); })
    .then(function (o) {
      if (al) al.innerHTML = '';
      if (!o.ok || o.d.erro) {
        if (al) {
          al.innerHTML = '<div class="alert alert-danger py-2">' + (o.d.erro || 'Não foi possível carregar as filiais.') + '</div>';
        }
        return;
      }
      var list = o.d.filiais || [];
      og_estado_empresas.filiaisCache = list;
      var tb = document.getElementById('empTabFiliaisTbody');
      if (!tb) return;
      if (!list.length) {
        tb.innerHTML = '<tr><td colspan="5" class="text-center text-muted py-3">Nenhuma filial cadastrada para esta empresa.</td></tr>';
        return;
      }
      tb.innerHTML = list
        .map(function (f) {
          return (
            '<tr class="emp-tab-fil-tr" data-filial-id="' + fn_empresas_escAttr(f.id) + '">' +
            '<td><code>' + fn_empresas_escAttr(f.cod_filial) + '</code></td>' +
            '<td>' + fn_empresas_escAttr(f.nome || '—') + '</td>' +
            '<td>' + fn_empresas_escAttr(f.cnpj || '—') + '</td>' +
            '<td class="text-center">' + (f.ativo ? 'Sim' : 'Não') + '</td>' +
            '<td class="text-end text-nowrap">' +
            '<button type="button" class="btn btn-sm btn-outline-primary me-1 btn-emp-fil-edt" data-filial-id="' + fn_empresas_escAttr(f.id) + '">Editar</button>' +
            '<button type="button" class="btn btn-sm btn-outline-danger btn-emp-fil-excl" data-filial-id="' + fn_empresas_escAttr(f.id) + '">Excluir</button>' +
            '</td></tr>'
          );
        })
        .join('');
    })
    .catch(function () {
      if (al) {
        al.innerHTML = '<div class="alert alert-danger py-2">Erro de conexão ao listar filiais.</div>';
      }
    });
}

function fn_emp_tab_filiais_salvar(event) {
  event.preventDefault();
  var alM = document.getElementById('modalFilialEmpFormAlerts');
  if (alM) alM.innerHTML = '';
  var al = document.getElementById('empTabFilialAlerts');
  if (al) al.innerHTML = '';
  var codE = (document.getElementById('modal_emp_tab_fil_empresa') && document.getElementById('modal_emp_tab_fil_empresa').value) || og_estado_empresas.codEmpresaAtual;
  if (!codE) {
    if (alM) {
      alM.innerHTML = '<div class="alert alert-warning py-2">Código da empresa indisponível.</div>';
    }
    return false;
  }
  var cod = document.getElementById('modal_emp_tab_fil_cod');
  if (!cod || !String(cod.value).trim()) {
    if (alM) {
      alM.innerHTML = '<div class="alert alert-danger py-2">Código da filial é obrigatório.</div>';
    }
    return false;
  }
  var pk = (document.getElementById('modal_emp_tab_fil_id') && document.getElementById('modal_emp_tab_fil_id').value.trim()) || '';
  var form = document.getElementById('formModalFilialEmp');
  if (!form) return false;
  var formData = new FormData(form);
  formData.set('m_empresa', codE);
  if (!document.getElementById('modal_emp_tab_fil_ativo').checked) {
    formData.delete('m_ativo');
  }
  var h = { 'X-Requested-With': 'XMLHttpRequest' };
  if (typeof getCsrfToken === 'function') {
    var tok = getCsrfToken();
    if (tok) h['X-CSRFToken'] = tok;
  }
  var inserir = (window.APP_URLS && window.APP_URLS.filialInserir) ? window.APP_URLS.filialInserir : ((typeof getUrlPrefix === 'function' ? getUrlPrefix() : '') + '/filial/inserir/');
  var updT = (window.APP_URLS && window.APP_URLS.filialUpd) ? String(window.APP_URLS.filialUpd).split('__ID__').join(encodeURIComponent(pk)) : ((typeof getUrlPrefix === 'function' ? getUrlPrefix() : '') + '/filial/' + encodeURIComponent(pk) + '/atualizar/');
  var action = pk ? updT : inserir;
  fetch(action, { method: 'POST', body: formData, headers: h, credentials: 'same-origin' })
    .then(function (r) {
      return r.json().then(function (d) { return { ok: r.ok, d: d }; });
    })
    .then(function (o) {
      if (o.ok && o.d.success) {
        fn_emp_tab_filiais_resetForm(true);
        fn_emp_tab_filiais_fecharModal();
        if (al) {
          al.innerHTML = '<div class="alert alert-success py-2">' + (o.d.message || 'Operação concluída.') + '</div>';
        }
        fn_emp_tab_filiais_carregar();
        return;
      }
      if (alM) {
        alM.innerHTML = '<div class="alert alert-danger py-2">' + (o.d.erro || 'Falha ao salvar filial.') + '</div>';
      }
    })
    .catch(function () {
      if (alM) {
        alM.innerHTML = '<div class="alert alert-danger py-2">Erro de conexão.</div>';
      }
    });
  return false;
}

function fn_emp_tab_filiais_excluir(filialId) {
  if (!window.confirm('Excluir esta filial? A operação não poderá ser desfeita se houver vínculos fiscais/SAP.')) return;
  var al = document.getElementById('empTabFilialAlerts');
  if (al) al.innerHTML = '';
  var u =
    (window.APP_URLS && window.APP_URLS.filialDel) ?
      String(window.APP_URLS.filialDel).split('__ID__').join(encodeURIComponent(filialId)) :
      ((typeof getUrlPrefix === 'function' ? getUrlPrefix() : '') + '/filial/' + encodeURIComponent(filialId) + '/excluir/');
  var fd = new FormData();
  var csrfF = document.querySelector('#formModalFilialEmp [name=csrfmiddlewaretoken], #formEmpresaUpd [name=csrfmiddlewaretoken]');
  if (csrfF) {
    fd.append('csrfmiddlewaretoken', csrfF.value);
  }
  var h = { 'X-Requested-With': 'XMLHttpRequest' };
  if (typeof getCsrfToken === 'function') {
    var tok = getCsrfToken();
    if (tok) h['X-CSRFToken'] = tok;
  }
  fetch(u, { method: 'POST', body: fd, headers: h, credentials: 'same-origin' })
    .then(function (r) { return r.json().then(function (d) { return { ok: r.ok, d: d }; }); })
    .then(function (o) {
      if (o.ok && o.d.success) {
        if (al) {
          al.innerHTML = '<div class="alert alert-success py-2">' + (o.d.message || 'Excluída.') + '</div>';
        }
        fn_emp_tab_filiais_resetForm(true);
        fn_emp_tab_filiais_carregar();
        return;
      }
      if (al) {
        al.innerHTML = '<div class="alert alert-danger py-2">' + (o.d.erro || 'Não foi possível excluir.') + '</div>';
      }
    })
    .catch(function () {
      if (al) {
        al.innerHTML = '<div class="alert alert-danger py-2">Erro de conexão.</div>';
      }
    });
}

function fn_init_emp_tab_filiais() {
  // Não exigir #formModalFilialEmp: sem tabela+aba, não há nada a fazer; botão e lista ainda registo.
  var abaBtn = document.getElementById('tab-filiais-emp-btn');
  var abaFiliais = document.getElementById('empTabFiliaisTbody');
  var form = document.getElementById('formModalFilialEmp');
  if (!abaBtn && !abaFiliais) return;

  if (abaBtn) {
    abaBtn.addEventListener('click', function () {
      setTimeout(function () {
        fn_emp_tab_sincronizar_cod_empresa();
        if (og_estado_empresas.codEmpresaAtual) {
          fn_emp_tab_filiais_carregar();
        }
      }, 200);
    });
  }
  if (abaBtn) {
    abaBtn.addEventListener('shown.bs.tab', function () {
      fn_emp_tab_sincronizar_cod_empresa();
      if (og_estado_empresas.codEmpresaAtual) {
        fn_emp_tab_filiais_carregar();
      }
    });
  }
  var nav = document.getElementById('empresaTabs');
  if (nav) {
    nav.addEventListener('shown.bs.tab', function (e) {
      var trg = e.target;
      if (!trg) return;
      if (trg.getAttribute('data-bs-target') !== '#tab-filiais-emp' && trg.id !== 'tab-filiais-emp-btn') return;
      setTimeout(function () {
        fn_emp_tab_sincronizar_cod_empresa();
        if (og_estado_empresas.codEmpresaAtual) {
          fn_emp_tab_filiais_carregar();
        }
      }, 0);
    });
  }

  var btnA = document.getElementById('btn_emp_tab_fil_abrir_modal');
  if (btnA) {
    btnA.addEventListener('click', function (e) {
      e.preventDefault();
      e.stopPropagation();
      if (typeof fn_emp_tab_filiais_abrirModalNova === 'function') {
        fn_emp_tab_filiais_abrirModalNova();
      }
    });
  }
  if (form) {
    form.addEventListener('submit', function (e) {
      fn_emp_tab_filiais_salvar(e);
    });
  }
  var mEl = document.getElementById('modalFilialEmpForm');
  if (mEl) {
    mEl.addEventListener('hidden.bs.modal', function () {
      fn_emp_tab_filiais_resetForm(true);
    });
  }
  if (abaFiliais) {
    abaFiliais.addEventListener('click', function (e) {
      var edt = e.target.closest('.btn-emp-fil-edt');
      if (edt) {
        e.preventDefault();
        var fid = edt.getAttribute('data-filial-id');
        var it = (og_estado_empresas.filiaisCache || []).find(function (x) {
          return String(x.id) === String(fid);
        });
        if (!it) {
          var aw = document.getElementById('empTabFilialAlerts');
          if (aw) {
            aw.innerHTML = '<div class="alert alert-warning py-2">Dados indisponíveis. Mude de aba e reabra Filiais.</div>';
          }
          return;
        }
        fn_emp_tab_filiais_abrirModalEditar(it);
        return;
      }
      var ex = e.target.closest('.btn-emp-fil-excl');
      if (ex) {
        e.preventDefault();
        var idEx = ex.getAttribute('data-filial-id');
        if (idEx) {
          fn_emp_tab_filiais_excluir(idEx);
        }
      }
    });
  }
}

window.fn_emp_tab_filiais_salvar = fn_emp_tab_filiais_salvar;
