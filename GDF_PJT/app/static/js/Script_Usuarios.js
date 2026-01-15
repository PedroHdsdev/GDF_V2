// ================================
// Dados vindos do Django
// ================================
const USERS = JSON.parse(
  document.getElementById("user-data").textContent
);

// ================================
// Bootstrap Modals
// ================================
const modalInsEl = document.getElementById("modalUsuarioIns");
const modalUpdEl = document.getElementById("modalUsuarioUpd");

const modalIns = modalInsEl ? new bootstrap.Modal(modalInsEl) : null;
const modalUpd = modalUpdEl ? new bootstrap.Modal(modalUpdEl) : null;

// ================================
// Abrir modal INS
// ================================
function openModal_ins() {
  if (modalIns) modalIns.show();
}

// ================================
// Clique na linha da tabela
// ================================
function handleUserClick(userId) {
  const user = USERS.find(u => String(u.id) === String(userId));
  if (!user) {
    alert("Usuário não encontrado.");
    return;
  }
  fillUserModal(user);
  modalUpd.show();
}

// ================================
// Preencher modal de edição
// ================================
function fillUserModal(user) {

  // Campos hidden
  document.getElementById("m_user_id").value = user.id;
  document.getElementById("m_grpUserid").value = user.id;

  // Dados principais
  setValue("m_username", user.username);
  setValue("m_first_name", user.first_name);
  setValue("m_last_name", user.last_name);
  setValue("m_email_upd", user.email);

  // Ativo
  document.getElementById("m_active").checked = !!user.is_active;

  // Limpa senha
  setValue("m_senhanew", "");
  setValue("m_confsenhanew", "");

  // Grupos
  renderUserGroups(user.groups || []);
}

// ================================
// Renderizar grupos do usuário
// ================================
function renderUserGroups(groups) {
  const tbody = document.getElementById("grupo-usuario-tbody");
  tbody.innerHTML = "";

  if (!groups.length) {
    tbody.innerHTML = `
      <tr>
        <td class="text-muted">Nenhum grupo atribuído</td>
      </tr>
    `;
    return;
  }

  groups.forEach(grp => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td class="d-flex justify-content-between align-items-center">
        ${grp}
        <form method="POST" action="/userGroup_dlt/">
          <input type="hidden" name="csrfmiddlewaretoken" value="${csrfToken}">
          <input type="hidden" name="m_grpUser_id" value="${document.getElementById("m_user_id").value}">
          <input type="hidden" name="m_name_grp" value="${grp}">
          <button class="btn btn-sm btn-outline-danger">
            Remover
          </button>
        </form>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

// ================================
// Helpers
// ================================
function setValue(id, value) {
  const el = document.getElementById(id);
  if (el) el.value = value ?? "";
}

// ================================
// Reabrir modal via messages (Django)
// ================================
document.addEventListener("DOMContentLoaded", () => {
  if (!modalUpdId) return;

  const user = USERS.find(u => String(u.id) === String(modalUpdId));
  if (user) {
    fillUserModal(user);
    modalUpd.show();
  }
});
