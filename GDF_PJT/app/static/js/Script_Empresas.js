const Empresas_ = JSON.parse(
  document.getElementById("empresas-data").textContent
);

function handleEmpresaClick(cod_empresa) {
  const v_empresa = Empresas_.find((e) => e.cod_empresa === cod_empresa);
  if (v_empresa) {
    openModal_upd(v_empresa);
  } else {
    alert("Empresa não encontrada.");
  }
}

function openModal_upd(v_empresa) {
  // Dados de Empresa
  document.getElementById("m_empresa_id").value = v_empresa.cod_empresa;
  document.getElementById("m_emp_cnpj").value = v_empresa.cnpj;
  document.getElementById("m_razao").value = v_empresa.razao;
  document.getElementById("m_fantasia").value = v_empresa.fantasia;
  document.getElementById("m_ie").value = v_empresa.ie;
  document.getElementById("m_im").value = v_empresa.im;
  document.getElementById("m_tipo").value = v_empresa.tipo;
  document.getElementById("m_crt").value = v_empresa.crt;
  document.getElementById("m_cnae").value = v_empresa.cnae;
  document.getElementById("m_iest").value = v_empresa.iest;
  document.getElementById("m_suframa").value = v_empresa.suframa;
  document.getElementById("m_grpEmpresa_id").value = v_empresa.grp_empresa;
  document.getElementById("m_chave_acesso").value = v_empresa.chave_acesso;
  document.getElementById("m_cliente_id").value = v_empresa.cliente;

  const v_matriz =
    v_empresa.matriz === true ||
    v_empresa.matriz === 1 ||
    v_empresa.matriz === "1" ||
    (typeof v_empresa.matriz === "string" &&
      v_empresa.matriz.toLowerCase() === "true");
  document.getElementById("m_matriz").checked = v_matriz;

  // Dados de Certificado
  const cert = v_empresa.cert_emp[0];
  document.getElementById("m_raiz").value        = cert.raiz || "";
  document.getElementById("m_file").value        = "";
  document.getElementById("m_emissor").value     = cert.emissor || "";
  document.getElementById("m_cnpj").value        = cert.cpf_cnpj || "";
  document.getElementById("m_dt_inicial").value  = cert.ini_validade || "";
  document.getElementById("m_dt_fim").value      = cert.fim_validade || "";

  document.getElementById("myModal_upd").style.display = "flex";
  const tabEmpresaBtn = document.querySelector(".tab-btn:nth-child(1)");
  openTab(tabEmpresaBtn, "tab-Empresa");
}

function openModal_ins() {
  document.getElementById("myModal_ins").style.display = "flex";
}

// fechar modal
function closeModal() {
  document.getElementById("myModal_upd").style.display = "none";
  document.getElementById("myModal_ins").style.display = "none";
}

// Fechar modal ao clicar fora
window.onclick = function (event) {
  const modal_upd = document.getElementById("myModal_upd");
  if (event.target === modal_upd) {
    modal_upd.style.display = "none";
  }
  const modal_ins = document.getElementById("myModal_ins");
  if (event.target === modal_ins) {
    modal_ins.style.display = "none";
  }
};

function toggleEditable(editable) {
  const activeTab = document.querySelector(".tab-content.active-tab");
  // Define os campos de cada aba
  const camposEmpresa = [
    "m_emp_cnpj",
    "m_razao",
    "m_fantasia",
    "m_ie",
    "m_im",
    "m_tipo",
    "m_crt",
    "m_cnae", 
    "m_iest",
    "m_suframa",
    "m_grpEmpresa_id",
    "m_chave_acesso",
  ];

  const camposCertificado = [
    "m_file",
    "m_emissor",
    "m_cnpj",
    "m_dt_inicial",
    "m_dt_fim",
  ];

  const fields = activeTab.id === "tab-Empresa" ? camposEmpresa : camposCertificado;

  fields.forEach((id) => {
    const field = document.getElementById(id);
    if (editable) {
      field.removeAttribute("readonly");
      field.removeAttribute("disabled");
      field.classList.remove("modal_txt_edit");
      field.classList.add("modal_txt");
    } else {
      field.setAttribute("readonly", true);
      field.setAttribute("disabled", true);
      field.classList.remove("modal_txt");
      field.classList.add("modal_txt_edit");
    }
  });

  const v_matriz = document.getElementById("m_matriz");
  const v_file = document.getElementById("m_file");
  if (editable) {
    v_matriz.removeAttribute("disabled");
    v_file.removeAttribute("disabled");
  } else {
    v_matriz.setAttribute("disabled", true);
    v_file.setAttribute("disabled", true);
  }

  const saveBtn = activeTab.querySelector("#save-btn");
  const cancelBtn = activeTab.querySelector("#cancel-btn");
  const editBtn = activeTab.querySelector("#edit-btn");

  if (editable) {
    if (saveBtn) saveBtn.style.display = "inline-block";
    if (cancelBtn) cancelBtn.style.display = "inline-block";
    if (editBtn) editBtn.style.display = "none";
  } else {
    if (saveBtn) saveBtn.style.display = "none";
    if (cancelBtn) cancelBtn.style.display = "none";
    if (editBtn) editBtn.style.display = "inline-block";
  }
}

function makeEditable() {
  toggleEditable(true);
}

function cancelChanges() {
  toggleEditable(false);
}

function openTab(button, tabId) {
  // Remove active de todos os botões
  const allButtons = document.querySelectorAll(".tab-btn");
  allButtons.forEach((btn) => btn.classList.remove("active"));

  // Oculta todas as tab-content
  const allTabs = document.querySelectorAll(".tab-content");
  allTabs.forEach((tab) => tab.classList.remove("active-tab"));

  // Adiciona active ao botão clicado e à tab correspondente
  button.classList.add("active");
  document.getElementById(tabId).classList.add("active-tab");

  toggleEditable(false);
}

window.onload = function () {
  const raw = document.getElementById("dj-messages");
  if (raw) {
    const messages = JSON.parse(raw.textContent);

    messages.forEach(msg => {
      if (msg.tags.includes("MODAL_INS")) {
        openModal_ins();
      }
      if (msg.tags.startsWith("MODAL_UPD ")  && modalUpdId) {
        const EmpObj = Empresas_.find(u => u.id == modalUpdId);
        if (EmpObj) openModal_upd(EmpObj);
      }
    });
  }
};