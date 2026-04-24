/**
 * Filiais: busca na tabela, modais inserir/editar (AJAX).
 * Depende de: Bootstrap, getUrlPrefix (Script_Base.js, carregado no index_Base).
 */

function fn_filial_url_prefix() {
  if (typeof getUrlPrefix === "function") return getUrlPrefix() || "";
  var el = document.querySelector(".layout-page[data-url-prefix]");
  return (el && el.getAttribute("data-url-prefix")) || "";
}

function fn_filial_escHtml(s) {
  var d = document.createElement("div");
  d.textContent = s == null ? "" : String(s);
  return d.innerHTML;
}

function fn_abrir_editar_filial(filialId) {
  var urlPrefix = fn_filial_url_prefix();
  var alertEl = document.getElementById("modalFilialEditarAlerts");
  if (alertEl) alertEl.innerHTML = "";
  var action = urlPrefix + "/filial/" + filialId + "/atualizar/";
  var form = document.getElementById("formFilialEditar");
  if (form) form.action = action;
  var hid = document.getElementById("edt_filial_id");
  if (hid) hid.value = filialId;
  fetch(action, { method: "GET", headers: { "X-Requested-With": "XMLHttpRequest" } })
    .then(function (r) {
      return r.json();
    })
    .then(function (data) {
      var disp = document.getElementById("edt_filial_empresa_display");
      if (disp) disp.textContent = (data.empresa_cod || "") + " – " + (data.empresa_nome || "");
      var c = document.getElementById("edt_filial_cod");
      if (c) c.value = data.cod_filial || "";
      var n = document.getElementById("edt_filial_nome");
      if (n) n.value = data.nome || "";
      var cnpj = document.getElementById("edt_filial_cnpj");
      if (cnpj) cnpj.value = data.cnpj || "";
      var atv = document.getElementById("edt_filial_ativo");
      if (atv) atv.checked = !!data.ativo;
      var modal = document.getElementById("modalFilialEditar");
      if (modal && typeof bootstrap !== "undefined" && bootstrap.Modal) {
        new bootstrap.Modal(modal).show();
      }
    })
    .catch(function () {
      if (alertEl) alertEl.innerHTML = '<div class="alert alert-danger py-2">Erro ao carregar dados da filial.</div>';
    });
}

function fn_submit_editar_filial(event) {
  event.preventDefault();
  var form = document.getElementById("formFilialEditar");
  var alertEl = document.getElementById("modalFilialEditarAlerts");
  var cod = document.getElementById("edt_filial_cod");
  if (!cod || !cod.value.trim()) {
    if (alertEl) alertEl.innerHTML = '<div class="alert alert-danger py-2">Código da filial é obrigatório.</div>';
    return false;
  }
  var formData = new FormData(form);
  var headers = { "X-Requested-With": "XMLHttpRequest" };
  if (typeof getCsrfToken === "function") {
    var t = getCsrfToken();
    if (t) headers["X-CSRFToken"] = t;
  }
  fetch(form.action, {
    method: "POST",
    body: formData,
    headers: headers,
    credentials: "same-origin"
  })
    .then(function (r) {
      return r
        .json()
        .then(function (data) {
          return { ok: r.ok, data: data };
        })
        .catch(function () {
          return { ok: r.ok, data: {} };
        });
    })
    .then(function (result) {
      if (result.ok && result.data.success) {
        if (alertEl) {
          alertEl.innerHTML =
            '<div class="alert alert-success py-2">' + fn_filial_escHtml(result.data.message || "Filial atualizada.") + "</div>";
        }
        setTimeout(function () {
          window.location.reload();
        }, 1000);
      } else {
        if (alertEl) {
          alertEl.innerHTML =
            '<div class="alert alert-danger py-2">' + fn_filial_escHtml(result.data.erro || "Erro ao atualizar.") + "</div>";
        }
      }
    })
    .catch(function () {
      if (alertEl) alertEl.innerHTML = '<div class="alert alert-danger py-2">Erro de conexão.</div>';
    });
  return false;
}

function fn_validar_formulario_filial_ins(event) {
  event.preventDefault();
  var form = document.getElementById("formFilialIns");
  var empresa = document.getElementById("ins_filial_empresa");
  var cod = document.getElementById("ins_filial_cod");
  var alertEl = document.getElementById("modalFilialInsAlerts");
  if (!empresa || !empresa.value) {
    if (alertEl) alertEl.innerHTML = '<div class="alert alert-danger py-2">Selecione a empresa.</div>';
    return false;
  }
  if (!cod || !cod.value.trim()) {
    if (alertEl) alertEl.innerHTML = '<div class="alert alert-danger py-2">Código da filial é obrigatório.</div>';
    return false;
  }
  var formData = new FormData(form);
  var h = { "X-Requested-With": "XMLHttpRequest" };
  if (typeof getCsrfToken === "function") {
    var tok = getCsrfToken();
    if (tok) h["X-CSRFToken"] = tok;
  }
  fetch(form.action, {
    method: "POST",
    body: formData,
    headers: h,
    credentials: "same-origin"
  })
    .then(function (r) {
      return r
        .json()
        .then(function (data) {
          return { ok: r.ok, data: data };
        })
        .catch(function () {
          return { ok: r.ok, data: {} };
        });
    })
    .then(function (result) {
      var al = document.getElementById("modalFilialInsAlerts");
      if (result.ok && result.data.success) {
        if (al) {
          al.innerHTML =
            '<div class="alert alert-success py-2">' + fn_filial_escHtml(result.data.message || "Filial cadastrada.") + "</div>";
        }
        setTimeout(function () {
          window.location.reload();
        }, 1000);
      } else {
        if (al) {
          al.innerHTML =
            '<div class="alert alert-danger py-2">' + fn_filial_escHtml(result.data.erro || "Erro ao cadastrar.") + "</div>";
        }
      }
    })
    .catch(function () {
      var al = document.getElementById("modalFilialInsAlerts");
      if (al) al.innerHTML = '<div class="alert alert-danger py-2">Erro de conexão.</div>';
    });
  return false;
}

function initFiliaisPage() {
  var searchBox = document.getElementById("searchBox");
  var rows = document.querySelectorAll(".filial-row");
  if (searchBox && rows.length) {
    searchBox.addEventListener("input", function () {
      var q = this.value.trim().toLowerCase();
      rows.forEach(function (tr) {
        var text = tr.textContent.toLowerCase();
        tr.classList.toggle("d-none", q !== "" && text.indexOf(q) === -1);
      });
    });
  }

  document.querySelectorAll(".btn-editar-filial").forEach(function (btn) {
    btn.addEventListener("click", function (e) {
      e.stopPropagation();
      var id = this.getAttribute("data-filial-id");
      if (id) fn_abrir_editar_filial(id);
    });
  });
}

document.addEventListener("DOMContentLoaded", function () {
  window.fn_submit_editar_filial = fn_submit_editar_filial;
  window.fn_validar_formulario_filial_ins = fn_validar_formulario_filial_ins;
  initFiliaisPage();
});
