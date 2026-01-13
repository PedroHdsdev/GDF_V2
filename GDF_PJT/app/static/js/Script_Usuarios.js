const User_ = JSON.parse(
  document.getElementById("user-data").textContent
);

function handleUserClick(user_id) {
  const v_user = User_.find((e) => e.id.toString() === user_id.toString());
  if (v_user) {
    openModal_upd(v_user);
  } else {
    alert("informaçao do USsuario não econtrado.");
  }
}

function openModal_ins() {
  document.getElementById("myModal_ins").style.display = "flex";
}

function openModal_upd(v_user) {
  //const v_user = Users.find(u => u.id === id);

  document.getElementById("m_user_id").value = v_user.id;
  document.getElementById("m_grpUserid").value = v_user.id;
  document.getElementById("m_username").value = v_user.username;
  document.getElementById("m_first_name").value = v_user.first_name;
  document.getElementById("m_last_name").value = v_user.last_name;
  document.getElementById("m_email_upd").value = v_user.email;

  const v_active =
    v_user.is_active === true ||
    v_user.is_active === 1 ||
    v_user.is_active === "1" ||
    (typeof v_user.is_active === "string" &&
      v_user.is_active.toLowerCase() === "true");
  document.getElementById("m_active").checked = v_active;

    // Renderizar grupos do usuário na tabela da aba Grupo de Acesso
  const grupoTableBody = document.querySelector("#tab-Grupoacesso tbody");
  grupoTableBody.innerHTML = ""; // limpa tabela

  if (v_user.groups && v_user.groups.length > 0) {
    v_user.groups.forEach(grp => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>
          <form method="POST" action="/userGroup_dlt/">
            <input type="hidden" name="m_grpUser_id" value="${v_user.id}" />
            <input type="hidden" name="csrfmiddlewaretoken" value="${csrfToken}" />
            ${grp}
            <input type="hidden" name="m_name_grp" value="${grp}">
            <button type="submit" class="btn-table"></button>
          </form>
        </td>
      `;
      grupoTableBody.appendChild(tr);
    });
  } else {
    grupoTableBody.innerHTML = `<tr><td>Nenhum grupo atribuído.</td></tr>`;
  }

  document.getElementById("myModal_upd").style.display = "flex";
  const tabUserBtn = document.querySelector(".tab-btn:nth-child(1)");
  openTab(tabUserBtn, "tab-User");
}

// fechar modal
function closeModal() {
  document.getElementById("myModal_ins").style.display = "none";
  document.getElementById("myModal_upd").style.display = "none";
}

// Fechar modal ao clicar fora
window.onclick = function (event) {
  const modal_ins = document.getElementById("myModal_ins");
  const Modal_upd = document.getElementById("myModal_upd");

  if (event.target === modal_ins) {
    modal_ins.style.display = "none";
  }
  if (event.target === Modal_upd) {
    Modal_upd.style.display = "none";
  }
};

function toggleEditable(editable) {

  const fields = [
    "m_senhanew",
    "m_confsenhanew",
    "m_first_name",
    "m_last_name",
    "m_email_upd",
  ];

  fields.forEach((id) => {
    const field = document.getElementById(id);
    if (editable) {
      field.removeAttribute("readonly");
      field.classList.remove("modal_txt_edit");
      field.classList.add("modal_txt");
    } else {
      field.setAttribute("readonly", true);
      field.classList.remove("modal_txt");
      field.classList.add("modal_txt_edit");
    }
  });

  const v_active = document.getElementById("m_active");
  if (editable) {
    v_active.removeAttribute("disabled");
  } else {
    v_active.setAttribute("disabled", true);
  }

  // Alterna visibilidade dos botões
  document.getElementById("edit-btn").style.display = editable
    ? "none"
    : "inline-block";
  document.getElementById("save-btn").style.display = editable
    ? "inline-block"
    : "none";
  document.getElementById("cancel-btn").style.display = editable
    ? "inline-block"
    : "none";
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
      if (msg.tags.startsWith("MODAL_UPD ")  && modalUpdId && msg.tags.startsWith("MODAL_DEL ") ) {
        const userObj = User_.find(u => u.id == modalUpdId);
        if (userObj) openModal_upd(userObj);
      }
    });
  }
};