const Clientes_ = JSON.parse(
  document.getElementById("Clientes-data").textContent
);

// Abrir modal cliente Solução
function openModal_upd(clienteId) {
  const clie = Clientes_.find((e) => e.cod_cliente === clienteId);
  document.getElementById("m_cliente_id").value = clie.cod_cliente;
  document.getElementById("m_razao").value = clie.razao;
  document.getElementById("m_cnpj").value = clie.cnpj;

  // Converte string ou valor numérico para booleano real
  const isActive =
    clie.is_active === true ||
    clie.is_active === 1 ||
    clie.is_active === "1" ||
    (typeof clie.is_active === "string" && clie.is_active.toLowerCase() === "true");
  document.getElementById("m_active").checked = isActive;


  for (const sol of clie.solucoes_acesso) {
    const checkbox = document.getElementById(sol.solucoes_id);
    if (checkbox) {
      checkbox.checked = sol.is_active; 
    }
  }

  document.querySelectorAll("#myModal_upd .modal_field2").forEach((div) => {
    if (div.dataset.cliente === clienteId) {
      div.style.display = "flex";
    } else {
      div.style.display = "none";
    }
  });

  const modal = document.getElementById("myModal_upd");
  modal.style.display = "flex";
}

// Abrir modal Cadastro
function openModal_ins() {
  document.getElementById("myModal_ins").style.display = "flex";
}

// Fecha o modal
function closeModal() {
  const Modal_upd = document.getElementById("myModal_upd");
  Modal_upd.style.display = "none";
  const modal_ins = document.getElementById("myModal_ins");
  modal_ins.style.display = "none";
}

// Fecha o modal clicando fora da área
window.onclick = function (event) {
  const Modal_upd = document.getElementById("myModal_upd");
  const Modal_ins = document.getElementById("myModal_ins");

  if (event.target === Modal_upd) {
    Modal_upd.style.display = "none";
  }
  if (event.target === Modal_ins) {
    Modal_ins.style.display = "none";
  }
};

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
        const clieObj = Clientes_.find(u => u.id == modalUpdId);
        if (clieObj) openModal_upd(clieObj);
      }
    });
  }
};