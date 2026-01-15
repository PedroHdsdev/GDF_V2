/* ===============================
   UTIL
================================ */
async function fetchJSON(url) {
  const resp = await fetch(url, {
    headers: { "X-Requested-With": "XMLHttpRequest" }
  });
  if (!resp.ok) throw new Error("Erro ao buscar dados");
  return await resp.json();
}

/* ===============================
   MODAIS
================================ */
let modalIns, modalUpd;

document.addEventListener("DOMContentLoaded", () => {
  const insEl = document.getElementById("modalUsuarioIns");
  const updEl = document.getElementById("modalUsuarioUpd");

  if (insEl) modalIns = new bootstrap.Modal(insEl);
  if (updEl) modalUpd = new bootstrap.Modal(updEl);

  if (modalUpdId) {
    carregarUsuario(modalUpdId);
  }
});

/* ===============================
   ABRIR MODAL INS
================================ */
async function openModal_ins() {
  try {
    const data = await fetchJSON("/usuario_ins/?ajax=1");

    preencherEmpresas("empresaSelectIns", data.empresas);
    preencherGrupos("grupoSelectIns", data.grupos);

    modalIns.show();
  } catch (e) {
    alert("Erro ao carregar dados do formulário");
  }
}

/* ===============================
   CLICK NA LINHA DA TABELA
================================ */
async function handleUserClick(userId) {
  try {
    const data = await fetchJSON(`/usuario_upd/?user_id=${userId}&ajax=1`);

    document.getElementById("upd_user_id").value = data.id;
    document.getElementById("upd_username").value = data.username;
    document.getElementById("upd_email").value = data.email;
    document.getElementById("upd_active").checked = data.is_active;

    preencherEmpresas("empresaSelectUpd", data.empresas, data.empresa_id);
    preencherGrupos("grupoSelectUpd", data.grupos, data.grupos_usuario);

    modalUpd.show();
  } catch (e) {
    alert("Erro ao carregar usuário");
  }
}

/* ===============================
   PREENCHER SELECTS
================================ */
function preencherEmpresas(selectId, empresas, selected = null) {
  const sel = document.getElementById(selectId);
  sel.innerHTML = "";

  empresas.forEach(e => {
    const opt = document.createElement("option");
    opt.value = e.cod_empresa;
    opt.textContent = e.nome;
    if (selected && selected === e.cod_empresa) opt.selected = true;
    sel.appendChild(opt);
  });
}

function preencherGrupos(selectId, grupos, selecionados = []) {
  const sel = document.getElementById(selectId);
  sel.innerHTML = "";

  grupos.forEach(g => {
    const opt = document.createElement("option");
    opt.value = g.id;
    opt.textContent = g.nome;
    if (selecionados.includes(g.id)) opt.selected = true;
    sel.appendChild(opt);
  });
}

/* ===============================
   SUBMIT CADASTRO
================================ */
document.getElementById("formUsuarioIns")?.addEventListener("submit", async e => {
  e.preventDefault();

  const form = e.target;
  const resp = await fetch("/usuario_ins/", {
    method: "POST",
    headers: {
      "X-CSRFToken": csrfToken
    },
    body: new FormData(form)
  });

  if (resp.ok) location.reload();
  else alert("Erro ao cadastrar usuário");
});

/* ===============================
   SUBMIT UPDATE
================================ */
document.getElementById("formUsuarioUpd")?.addEventListener("submit", async e => {
  e.preventDefault();

  const form = e.target;
  const userId = document.getElementById("upd_user_id").value;

  const resp = await fetch(`/usuario_upd/?user_id=${userId}`, {
    method: "POST",
    headers: {
      "X-CSRFToken": csrfToken
    },
    body: new FormData(form)
  });

  if (resp.ok) location.reload();
  else alert("Erro ao atualizar usuário");
});
