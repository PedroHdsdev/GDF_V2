(function () {
  function escHtml(s) {
    var d = document.createElement("div");
    d.textContent = s == null ? "" : String(s);
    return d.innerHTML;
  }

  function getApiUrl() {
    var page = document.querySelector(".cfm-page[data-api-url]");
    if (!page) return "";
    return page.getAttribute("data-api-url") || "";
  }

  function getSapApiUrl() {
    var page = document.querySelector(".cfm-page");
    if (!page) return "";
    return page.getAttribute("data-sap-api-url") || "";
  }

  function getDefaultPeriodo() {
    var page = document.querySelector(".cfm-page");
    if (!page) return { inicio: "", fim: "" };
    return {
      inicio: page.getAttribute("data-default-start") || "",
      fim: page.getAttribute("data-default-end") || ""
    };
  }

  function toNumber(v) {
    if (v === null || v === undefined || v === "") return null;
    var n = Number(String(v).replace(",", "."));
    return Number.isFinite(n) ? n : null;
  }

  function fmtAliquota(v) {
    var n = toNumber(v);
    if (n === null) return "-";
    return n.toFixed(2).replace(".", ",") + "%";
  }

  function getState() {
    return {
      buscou: false,
      loading: false,
      page: 1,
      pageSize: 30,
      totalPages: 1,
      total: 0,
      sortField: "material",
      sortDir: "asc",
      items: []
    };
  }

  var state = getState();
  var searchTimer = null;

  function limparMensagensErroCampos() {
    ["cfm-data-inicial", "cfm-data-final"].forEach(function (id) {
      var el = document.getElementById(id);
      if (el) el.classList.remove("is-invalid");
    });
  }

  function validarPeriodo(dataInicial, dataFinal) {
    limparMensagensErroCampos();
    if (!dataInicial || !dataFinal) {
      if (!dataInicial) {
        var di = document.getElementById("cfm-data-inicial");
        if (di) di.classList.add("is-invalid");
      }
      if (!dataFinal) {
        var df = document.getElementById("cfm-data-final");
        if (df) df.classList.add("is-invalid");
      }
      return "Informe o periodo (Data Inicial e Data Final).";
    }

    if (dataInicial > dataFinal) {
      var di2 = document.getElementById("cfm-data-inicial");
      var df2 = document.getElementById("cfm-data-final");
      if (di2) di2.classList.add("is-invalid");
      if (df2) df2.classList.add("is-invalid");
      return "A Data Inicial nao pode ser maior que a Data Final.";
    }
    return "";
  }

  function lerFiltros() {
    return {
      chave_acesso: (document.getElementById("cfm-chave-acesso").value || "").trim(),
      cod_material: (document.getElementById("cfm-cod-material").value || "").trim(),
      fornecedor: (document.getElementById("cfm-fornecedor").value || "").trim(),
      data_inicio: (document.getElementById("cfm-data-inicial").value || "").trim(),
      data_fim: (document.getElementById("cfm-data-final").value || "").trim()
    };
  }

  function buildQueryParams(filtros) {
    var p = new URLSearchParams();
    Object.keys(filtros).forEach(function (k) {
      var v = filtros[k];
      if (v) p.set(k, v);
    });
    p.set("page", String(state.page));
    p.set("page_size", String(state.pageSize));
    p.set("order", state.sortField);
    p.set("dir", state.sortDir);
    return p;
  }

  function setResumo(msg) {
    var el = document.getElementById("cfm-resumo");
    if (el) el.textContent = msg;
  }

  function atualizarIndicadoresOrdenacao() {
    document.querySelectorAll("#cfm-tabela th.cfm-sort").forEach(function (th) {
      th.classList.remove("is-sorted-asc", "is-sorted-desc");
      var field = th.getAttribute("data-sort");
      if (field === state.sortField) {
        th.classList.add(state.sortDir === "asc" ? "is-sorted-asc" : "is-sorted-desc");
      }
    });
  }

  function renderRows(items, mensagemVazio) {
    var tbody = document.getElementById("cfm-tbody");
    if (!tbody) return;

    if (!items || !items.length) {
      tbody.innerHTML =
        '<tr><td colspan="9" class="text-center text-muted py-4">' +
        escHtml(mensagemVazio || "Nenhum registro encontrado.") +
        "</td></tr>";
      return;
    }

    var html = "";
    items.forEach(function (item) {
      html += "<tr>" +
        "<td>" + escHtml(item.material || "-") + "</td>" +
        "<td>" + escHtml(item.descricao_material || "-") + "</td>" +
        "<td>" + escHtml(item.fornecedor || "-") + "</td>" +
        '<td class="text-end">' + escHtml(fmtAliquota(item.aliquota_icms)) + "</td>" +
        '<td class="text-end">' + escHtml(fmtAliquota(item.aliquota_st)) + "</td>" +
        '<td class="text-end">' + escHtml(fmtAliquota(item.aliquota_cofins)) + "</td>" +
        '<td class="text-end">' + escHtml(fmtAliquota(item.aliquota_ipi)) + "</td>" +
        '<td class="text-end">' + escHtml(fmtAliquota(item.aliquota_pis)) + "</td>" +
        '<td class="text-end">' + escHtml(fmtAliquota(item.reducao_base)) + "</td>" +
      "</tr>";
    });
    tbody.innerHTML = html;
  }

  function renderPaginacao() {
    var nav = document.getElementById("cfm-paginacao");
    if (!nav) return;
    var ul = nav.querySelector("ul");
    if (!ul) return;

    if (!state.buscou || state.totalPages <= 1) {
      nav.classList.add("d-none");
      ul.innerHTML = "";
      return;
    }

    nav.classList.remove("d-none");
    var html = "";

    var prevDisabled = state.page <= 1 ? " disabled" : "";
    html += '<li class="page-item' + prevDisabled + '"><button class="page-link" data-page="' + (state.page - 1) + '">Anterior</button></li>';

    var start = Math.max(1, state.page - 2);
    var end = Math.min(state.totalPages, state.page + 2);
    for (var p = start; p <= end; p += 1) {
      var active = p === state.page ? " active" : "";
      html += '<li class="page-item' + active + '"><button class="page-link" data-page="' + p + '">' + p + "</button></li>";
    }

    var nextDisabled = state.page >= state.totalPages ? " disabled" : "";
    html += '<li class="page-item' + nextDisabled + '"><button class="page-link" data-page="' + (state.page + 1) + '">Proxima</button></li>';

    ul.innerHTML = html;
  }

  function renderResumo(mensagem) {
    if (!state.buscou) {
      setResumo("Aguarde o carregamento inicial da consulta.");
      return;
    }
    if (state.loading) {
      setResumo("Consultando banco de dados...");
      return;
    }
    if (mensagem) {
      setResumo(mensagem);
      return;
    }
    if (!state.total) {
      setResumo("Nenhum registro encontrado para os filtros informados.");
      return;
    }
    setResumo("Total de " + state.total + " registro(s). Pagina " + state.page + " de " + state.totalPages + ".");
  }

  function showError(msg) {
    if (typeof Notificacoes !== "undefined" && Notificacoes.pagina) {
      Notificacoes.pagina(msg, "danger");
    }
  }

  function showWarning(msg) {
    if (typeof Notificacoes !== "undefined" && Notificacoes.pagina) {
      Notificacoes.pagina(msg, "warning");
    }
  }

  function buscar() {
    var apiUrl = getApiUrl();
    if (!apiUrl) return;

    var filtros = lerFiltros();
    var erroPeriodo = validarPeriodo(filtros.data_inicio, filtros.data_fim);
    if (erroPeriodo) {
      showWarning(erroPeriodo);
      renderResumo(erroPeriodo);
      return;
    }

    state.buscou = true;
    state.loading = true;
    renderResumo("");
    renderRows([], "Consultando banco de dados...");

    var query = buildQueryParams(filtros);
    var finalUrl = apiUrl + "?" + query.toString();

    fetch(finalUrl, {
      method: "GET",
      headers: {
        "Accept": "application/json",
        "X-Requested-With": "XMLHttpRequest"
      },
      credentials: "same-origin"
    })
      .then(function (resp) {
        return resp.text().then(function (text) {
          var data;
          try {
            data = text ? JSON.parse(text) : {};
          } catch (e) {
            throw new Error("Resposta invalida da API.");
          }
          if (!resp.ok) {
            var msg = data.mensagem || data.erro || ("Falha na consulta (HTTP " + resp.status + ").");
            throw new Error(msg);
          }
          return data;
        });
      })
      .then(function (data) {
        state.loading = false;
        state.items = data.items || [];
        state.total = Number(data.total || 0);
        state.totalPages = Number(data.total_pages || 1);
        state.page = Number(data.page || state.page);

        var mensagem = data.mensagem || "";
        if (!state.total && !mensagem) {
          mensagem = "Nenhum registro encontrado para os filtros informados.";
        }

        renderRows(state.items, mensagem);
        renderPaginacao();
        renderResumo(mensagem);
      })
      .catch(function (err) {
        state.loading = false;
        state.items = [];
        state.total = 0;
        state.totalPages = 1;
        renderRows([], err.message || "Erro ao consultar a origem de dados.");
        renderPaginacao();
        renderResumo(err.message || "Erro ao consultar a origem de dados.");
        showError(err.message || "Erro ao consultar a origem de dados.");
      });
  }

  function agendarBusca() {
    if (searchTimer) {
      window.clearTimeout(searchTimer);
    }
    searchTimer = window.setTimeout(function () {
      state.page = 1;
      buscar();
    }, 300);
  }

  function consultarSap() {
    var apiUrl = getSapApiUrl();
    if (!apiUrl) return;

    var filtros = lerFiltros();
    state.buscou = true;
    state.loading = true;
    renderResumo("");
    renderRows([], "Consultando SAP...");

    var params = new URLSearchParams();
    if (filtros.chave_acesso) params.set("chave_acesso", filtros.chave_acesso);
    if (filtros.cod_material) params.set("cod_material", filtros.cod_material);
    if (filtros.fornecedor) params.set("fornecedor", filtros.fornecedor);

    fetch(apiUrl + "?" + params.toString(), {
      method: "GET",
      headers: {
        "Accept": "application/json",
        "X-Requested-With": "XMLHttpRequest"
      },
      credentials: "same-origin"
    })
      .then(function (resp) {
        return resp.text().then(function (text) {
          var data;
          try {
            data = text ? JSON.parse(text) : {};
          } catch (e) {
            throw new Error("Resposta invalida da API do SAP.");
          }
          if (!resp.ok) {
            var msg = data.mensagem || data.erro || ("Falha na consulta SAP (HTTP " + resp.status + ").");
            throw new Error(msg);
          }
          return data;
        });
      })
      .then(function (data) {
        state.loading = false;
        state.items = data.items || [];
        state.total = Number(state.items.length || 0);
        state.totalPages = 1;
        state.page = 1;

        var mensagem = data.mensagem || "Consulta SAP realizada com sucesso.";
        renderRows(state.items, mensagem);
        renderPaginacao();
        renderResumo(mensagem);
      })
      .catch(function (err) {
        state.loading = false;
        state.items = [];
        state.total = 0;
        state.totalPages = 1;
        renderRows([], err.message || "Erro ao consultar o SAP.");
        renderPaginacao();
        renderResumo(err.message || "Erro ao consultar o SAP.");
        showError(err.message || "Erro ao consultar o SAP.");
      });
  }

  function limpar() {
    var defaults = getDefaultPeriodo();
    ["cfm-chave-acesso", "cfm-cod-material", "cfm-fornecedor"].forEach(function (id) {
      var el = document.getElementById(id);
      if (el) el.value = "";
    });
    var di = document.getElementById("cfm-data-inicial");
    var df = document.getElementById("cfm-data-final");
    if (di) di.value = defaults.inicio;
    if (df) df.value = defaults.fim;
    limparMensagensErroCampos();
    state = getState();
    atualizarIndicadoresOrdenacao();
    renderRows([], "Aguarde o carregamento inicial da consulta.");
    renderPaginacao();
    renderResumo("");
    buscar();
  }

  function bindBuscaAutomatica() {
    ["cfm-chave-acesso", "cfm-cod-material", "cfm-fornecedor"].forEach(function (id) {
      var el = document.getElementById(id);
      if (!el) return;
      el.addEventListener("input", function () {
        agendarBusca();
      });
    });

    ["cfm-data-inicial", "cfm-data-final"].forEach(function (id) {
      var el = document.getElementById(id);
      if (!el) return;
      el.addEventListener("change", function () {
        limparMensagensErroCampos();
        agendarBusca();
      });
    });
  }

  function bindEventos() {
    var btnLimpar = document.getElementById("cfm-btn-limpar");
    if (btnLimpar) {
      btnLimpar.addEventListener("click", limpar);
    }

    var btnConsultaSap = document.getElementById("cfm-btn-consulta-sap");
    if (btnConsultaSap) {
      btnConsultaSap.addEventListener("click", consultarSap);
    }

    var pag = document.getElementById("cfm-paginacao");
    if (pag) {
      pag.addEventListener("click", function (evt) {
        var btn = evt.target.closest("button[data-page]");
        if (!btn) return;
        var targetPage = Number(btn.getAttribute("data-page") || 1);
        if (!Number.isFinite(targetPage)) return;
        if (targetPage < 1 || targetPage > state.totalPages || targetPage === state.page) return;
        state.page = targetPage;
        buscar();
      });
    }

    document.querySelectorAll("#cfm-tabela th.cfm-sort").forEach(function (th) {
      th.addEventListener("click", function () {
        var field = th.getAttribute("data-sort");
        if (!field) return;
        if (state.sortField === field) {
          state.sortDir = state.sortDir === "asc" ? "desc" : "asc";
        } else {
          state.sortField = field;
          state.sortDir = "asc";
        }
        state.page = 1;
        atualizarIndicadoresOrdenacao();
        if (state.buscou) buscar();
      });
    });
  }

  function initDatasPadraoMesAtual() {
    var defaults = getDefaultPeriodo();
    var now = new Date();
    var primeiro = defaults.inicio || new Date(now.getFullYear(), now.getMonth(), 1);
    var ultimo = defaults.fim || new Date(now.getFullYear(), now.getMonth() + 1, 0);

    function fmt(d) {
      if (typeof d === "string") return d;
      var m = String(d.getMonth() + 1).padStart(2, "0");
      var day = String(d.getDate()).padStart(2, "0");
      return d.getFullYear() + "-" + m + "-" + day;
    }

    var di = document.getElementById("cfm-data-inicial");
    var df = document.getElementById("cfm-data-final");
    if (di && !di.value) di.value = fmt(primeiro);
    if (df && !df.value) df.value = fmt(ultimo);
  }

  document.addEventListener("DOMContentLoaded", function () {
    if (!document.querySelector(".cfm-page")) return;
    bindEventos();
    bindBuscaAutomatica();
    initDatasPadraoMesAtual();
    atualizarIndicadoresOrdenacao();
    buscar();
  });
})();
