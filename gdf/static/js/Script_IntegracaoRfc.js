/**
 * Integração SAP — execução de RFCs (API_RfcExecutar), filiais por empresa, modal de consulta.
 * Requer: Bootstrap, csrf_protection.js (getCsrfToken) ou cookie csrftoken.
 */
(function () {
  function getCookie(name) {
    var m = document.cookie.match("(?:^|; )" + name.replace(/[-[\]{}()*+?.,\\^$|#\s]/g, "\\$&") + "=([^;]*)");
    return m ? decodeURIComponent(m[1]) : "";
  }

  function getCsrf() {
    if (typeof getCsrfToken === "function") {
      var t = getCsrfToken();
      if (t) return t;
    }
    var csrfEl = document.querySelector("[name=csrfmiddlewaretoken]");
    if (csrfEl && csrfEl.value) return csrfEl.value;
    return getCookie("csrftoken") || "";
  }

  function escHtml(s) {
    var d = document.createElement("div");
    d.textContent = s == null ? "" : String(s);
    return d.innerHTML;
  }

  function preencherModalConsultaSap(linhas) {
    var tb = document.querySelector("#modalRfcConsultaSapTable tbody");
    var titleEl = document.getElementById("modalRfcConsultaSapLabel");
    if (!tb) return;
    var n = linhas && linhas.length ? linhas.length : 0;
    if (titleEl) titleEl.textContent = "Resultado da consulta SAP — " + n + " chave(s)";
    var html = "";
    (linhas || []).forEach(function (l) {
      var ts = l.tem_sap
        ? '<span class="text-success fw-semibold">Sim</span>'
        : '<span class="text-secondary">Não</span>';
      var ag =
        l.atualizado_gdf && Number(l.atualizado_gdf) > 0
          ? '<span class="text-success fw-semibold">' + escHtml(l.atualizado_gdf) + "</span>"
          : '<span class="text-muted">0</span>';
      html +=
        '<tr><td class="font-monospace text-break">' +
        escHtml(l.chave) +
        "</td><td>" +
        escHtml(l.tipos) +
        "</td><td class=\"text-center\">" +
        escHtml(l.qtd_docs) +
        "</td><td>" +
        ts +
        "</td><td>" +
        escHtml(l.status) +
        '</td><td class="text-break font-monospace">' +
        escHtml(l.name_table) +
        "</td><td class=\"text-center\">" +
        ag +
        "</td></tr>";
    });
    tb.innerHTML = html;
  }

  function abrirModalConsultaSap(linhas) {
    var el = document.getElementById("modalRfcConsultaSap");
    if (!el || typeof bootstrap === "undefined" || !bootstrap.Modal) return;
    preencherModalConsultaSap(linhas);
    bootstrap.Modal.getOrCreateInstance(el).show();
  }

  var lastConsultaSapLinhas = null;

  document.addEventListener("DOMContentLoaded", function () {
    var pageEl = document.querySelector("[data-api-rfc-executar]");
    var apiUrl = pageEl ? pageEl.getAttribute("data-api-rfc-executar") || pageEl.dataset.apiRfcExecutar : "";
    if (!apiUrl) return;

    if (pageEl) {
      pageEl.addEventListener("click", function (ev) {
        var t = ev.target && ev.target.closest ? ev.target.closest("#btnRfcReabrirModalConsulta") : null;
        if (t && lastConsultaSapLinhas && lastConsultaSapLinhas.length) {
          abrirModalConsultaSap(lastConsultaSapLinhas);
        }
      });
    }

    document.querySelectorAll(".rfc-form").forEach(function (form) {
      form.addEventListener("submit", function (e) {
        e.preventDefault();
        var codRfc = form.getAttribute("data-cod-rfc") || form.dataset.codRfc || "";
        var params = {};
        form.querySelectorAll("input, select, textarea").forEach(function (el) {
          if (!el.name) return;
          if (el.type === "checkbox") {
            params[el.name] = el.checked;
          } else {
            var v = el.tagName === "TEXTAREA" ? el.value || "" : (el.value || "").trim();
            if (v || el.tagName === "TEXTAREA") params[el.name] = v;
          }
        });
        var card = form.closest(".rfc-sap-card");
        var resultEl = card ? card.querySelector(".rfc-result") : null;
        var btn = form.querySelector('button[type="submit"]');
        if (!resultEl) return;
        if (btn) btn.disabled = true;
        resultEl.classList.remove("d-none");
        resultEl.innerHTML = '<span class="text-muted"><i class="fas fa-spinner fa-spin"></i> Executando...</span>';

        fetch(apiUrl, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCsrf(),
            "X-Requested-With": "XMLHttpRequest"
          },
          body: JSON.stringify({ cod_rfc: codRfc, params: params }),
          credentials: "same-origin"
        })
          .then(function (r) {
            return r.text().then(function (text) {
              var data = null;
              try {
                data = text ? JSON.parse(text) : {};
              } catch (parseErr) {
                var head = (text || "").replace(/^\s+/, "").slice(0, 1);
                var hint;
                if (r.status === 502 || r.status === 503 || r.status === 504) {
                  hint =
                    "Gateway ou tempo esgotado: a RFC pode demorar muito e o proxy ou o Gunicorn encerrou a conexão. " +
                    "Aumente GUNICORN_TIMEOUT (ex.: 600) e no Nginx proxy_read_timeout para /api/; confira logs do Gunicorn. " +
                    "Se não for timeout, pode ser página HTML de erro do proxy.";
                } else if (head === "<") {
                  hint =
                    "O servidor devolveu HTML (login, CSRF ou erro), não JSON. Atualize a página, faça login de novo; " +
                    "se persistir, confira se o cookie csrftoken está sendo enviado.";
                } else {
                  hint = (text || "").replace(/\s+/g, " ").trim().slice(0, 180);
                }
                throw new Error("Resposta não é JSON (HTTP " + r.status + "). " + hint);
              }
              return { ok: r.ok, status: r.status, data: data };
            });
          })
          .then(function (resp) {
            var data = resp.data;
            if (!resp.ok) {
              var errRaw = data && (data.mensagem || data.erro || data.detail);
              var errMsg = errRaw != null && errRaw !== "" ? (typeof errRaw === "string" || typeof errRaw === "number" || typeof errRaw === "boolean" ? errRaw : JSON.stringify(errRaw)) : "HTTP " + resp.status;
              resultEl.innerHTML = '<div class="alert alert-danger small mb-0">' + escHtml(String(errMsg)) + "</div>";
              return;
            }
            if (data.sucesso) {
              var baseM = data.mensagem != null && String(data.mensagem) !== "" ? data.mensagem : "OK";
              var msgHtml = escHtml(String(baseM)).replace(/\n/g, "<br>");
              if (data.total_pendentes !== undefined) {
                msgHtml +=
                  ' <br><span class="d-inline-block mt-1">Documentos pendentes: ' +
                  escHtml(String(data.total_pendentes)) +
                  "</span>";
              }
              if (data.total_chaves_unicas !== undefined) {
                msgHtml += " | Chaves únicas consultadas: " + escHtml(String(data.total_chaves_unicas));
              }
              if (data.total_atualizados !== undefined) {
                msgHtml += " | Atualizados no GDF: " + escHtml(String(data.total_atualizados));
              }
              if (data.total_linhas !== undefined && data.total_atualizados === undefined) {
                msgHtml += " Linhas: " + escHtml(String(data.total_linhas));
              }
              if (data.total_gravados !== undefined) {
                msgHtml += " | Gravados: " + escHtml(String(data.total_gravados));
              }
              var html = '<div class="alert alert-success small mb-2">' + msgHtml + "</div>";
              lastConsultaSapLinhas = null;
              if (data.linhas_consulta_sap && data.linhas_consulta_sap.length) {
                lastConsultaSapLinhas = data.linhas_consulta_sap;
                html +=
                  '<p class="small mb-2 rfc-sap-hint">A tabela completa foi aberta em um modal. Use o botão abaixo para abrir novamente.</p>' +
                  '<button type="button" class="btn btn-sm btn-outline-primary" id="btnRfcReabrirModalConsulta">' +
                  '<i class="fas fa-table me-1"></i>Ver resultados completos (' +
                  data.linhas_consulta_sap.length +
                  " chave(s))</button>";
                abrirModalConsultaSap(data.linhas_consulta_sap);
              } else if (data.linhas && data.linhas.length) {
                var hasTipo = data.linhas.some(function (l) {
                  return l.tipo;
                });
                html +=
                  '<div class="table-responsive"><table class="table table-sm table-bordered mb-0 small"><thead><tr>' +
                  (hasTipo ? "<th>Tipo</th>" : "") +
                  "<th>Chave</th><th>No SAP</th><th>STATUS</th><th>NAME_TABLE</th></tr></thead><tbody>";
                data.linhas.forEach(function (l) {
                  var ts = l.tem_sap
                    ? '<span class="text-success">Sim</span>'
                    : '<span class="text-muted">Não</span>';
                  var ch = l.chave != null ? String(l.chave) : "";
                  var st = l.status != null ? String(l.status) : "";
                  var nt = l.name_table != null ? String(l.name_table) : "";
                  var tipoTd = hasTipo
                    ? "<td>" + escHtml(l.tipo != null ? String(l.tipo) : "") + "</td>"
                    : "";
                  html +=
                    "<tr>" +
                    tipoTd +
                    '<td class="font-monospace text-break">' +
                    escHtml(ch) +
                    "</td><td>" +
                    ts +
                    "</td><td>" +
                    escHtml(st) +
                    '</td><td class="text-break">' +
                    escHtml(nt) +
                    "</td></tr>";
                });
                html += "</tbody></table></div>";
              }
              resultEl.innerHTML = html;
            } else {
              var fr = data.mensagem != null && data.mensagem !== "" ? data.mensagem : data.erro;
              var failMsg = fr != null && fr !== "" ? (typeof fr === "string" || typeof fr === "number" || typeof fr === "boolean" ? fr : JSON.stringify(fr)) : "Erro";
              resultEl.innerHTML = '<div class="alert alert-danger small mb-0">' + escHtml(String(failMsg)) + "</div>";
            }
          })
          .catch(function (err) {
            resultEl.innerHTML =
              '<div class="alert alert-danger small mb-0">' + escHtml(err.message || "Erro na requisição") + "</div>";
          })
          .finally(function () {
            if (btn) btn.disabled = false;
          });
      });
    });

    var filiaisEl = document.getElementById("filiais-por-empresa-data");
    var filiaisData = {};
    try {
      if (filiaisEl && filiaisEl.textContent) filiaisData = JSON.parse(filiaisEl.textContent);
    } catch (e) {}
    document.querySelectorAll("select[name=bukrs]").forEach(function (selEmp) {
      var card = selEmp.closest(".rfc-sap-card");
      var selFilial = card ? card.querySelector("select[name=branch].rfc-branch-select") : null;
      if (!selFilial) return;
      selEmp.addEventListener("change", function () {
        var cod = this.value;
        selFilial.innerHTML = '<option value="">Todas as filiais</option>';
        if (cod && filiaisData[cod]) {
          filiaisData[cod].forEach(function (f) {
            var opt = document.createElement("option");
            opt.value = f.cod_filial;
            opt.textContent = f.cod_filial + (f.nome ? " – " + f.nome : "");
            selFilial.appendChild(opt);
          });
        }
      });
    });
  });
})();
