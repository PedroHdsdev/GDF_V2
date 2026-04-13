/**
 * NotificacoesPadrao.js
 * Padrão único do painel GDF: toasts Bootstrap 5 na pilha global (topo central da tela).
 *
 * Uso:
 *   Notificacoes.pagina('Mensagem', 'success');
 *   Notificacoes.modal('Erro ao salvar', 'danger', 'modalClienteUpdAlerts'); // mesmo stack global; containerId só para limparModal
 */

(function (global) {
  'use strict';

  const TIPOS_VALIDOS = ['success', 'danger', 'warning', 'info'];
  const CONTAINER_PAGINA_PADRAO = 'alertas-container';
  /** Pilha fixa topo central (id do elemento em index_Base.html). */
  const TOAST_STACK_ID = 'notificacoes-toast-stack';
  const CONTAINER_FIXO_ID = TOAST_STACK_ID;
  const AUTO_CLOSE_SUCESSO_MS = 5000;
  const AUTO_CLOSE_PAGINA_MS = 5000;

  function rotuloPorTipo(tipo) {
    const t = normalizarTipo(tipo);
    const rotulos = { success: 'Sucesso', danger: 'Erro', warning: 'Aviso', info: 'Informação' };
    return rotulos[t] || 'Informação';
  }

  function normalizarTipo(tipo) {
    if (!tipo || typeof tipo !== 'string') return 'info';
    const t = tipo.toLowerCase();
    if (t === 'error') return 'danger';
    return TIPOS_VALIDOS.includes(t) ? t : 'info';
  }

  function iconePorTipo(tipo) {
    const t = normalizarTipo(tipo);
    const icones = {
      success: 'fa-check-circle',
      danger: 'fa-exclamation-circle',
      warning: 'fa-exclamation-triangle',
      info: 'fa-info-circle'
    };
    return icones[t] || icones.info;
  }

  function prepararMensagem(mensagem) {
    if (mensagem == null) return '';
    var s = typeof mensagem === 'string' ? mensagem : String(mensagem);
    return s
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/\n/g, '<br>');
  }

  /** Variante visual suave (CSS em Style_Base — sem text-bg-* forte do Bootstrap). */
  function classesToastSkin(tipoNorm) {
    if (tipoNorm === 'success') return { skin: 'gdf-toast--success', btnClose: '' };
    if (tipoNorm === 'danger') return { skin: 'gdf-toast--danger', btnClose: '' };
    if (tipoNorm === 'warning') return { skin: 'gdf-toast--warning', btnClose: '' };
    return { skin: 'gdf-toast--info', btnClose: '' };
  }

  /**
   * Pilha global de toasts (cria no body se ainda não existir o nó do template).
   */
  function obterToastStack() {
    var el = document.getElementById(TOAST_STACK_ID);
    if (!el) {
      el = document.createElement('div');
      el.id = TOAST_STACK_ID;
      el.className = 'toast-container position-fixed top-0 start-50 translate-middle-x p-3 gdf-toast-stack';
      el.setAttribute('role', 'region');
      el.setAttribute('aria-live', 'polite');
      el.setAttribute('aria-label', 'Notificações');
      document.body.appendChild(el);
    }
    return el;
  }

  function prepararContainerComoToastStack(container) {
    if (!container) return;
    if (!container.classList.contains('toast-container')) {
      container.classList.add('toast-container');
    }
    if (container.id !== TOAST_STACK_ID && !container.classList.contains('position-fixed')) {
      container.classList.add('position-relative');
    }
  }

  /**
   * Alerta inline (fallback se Bootstrap Toast não existir).
   */
  function criarElementoAlerta(mensagem, tipo, opcoes) {
    const tipoNorm = normalizarTipo(tipo);
    const comIcone = opcoes.comIcone !== false;
    const textoEscapado = prepararMensagem(mensagem);
    const rotulo = rotuloPorTipo(tipoNorm);
    const icone = iconePorTipo(tipoNorm);

    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-padrao alert-' + tipoNorm + ' alert-dismissible fade show';
    alertDiv.setAttribute('role', 'alert');

    var html = '';
    if (comIcone) {
      html += '<i class="fas ' + icone + ' me-2" aria-hidden="true"></i>';
    }
    html += '<span class="alert-padrao-rotulo">' + prepararMensagem(rotulo) + ':</span>';
    html += '<span class="alert-padrao-texto">' + textoEscapado + '</span>';
    if (opcoes.acaoTexto && typeof opcoes.acaoCallback === 'function') {
      html += '<button type="button" class="btn btn-sm alert-padrao-acao ms-2" aria-label="' + prepararMensagem(opcoes.acaoTexto) + '">' + prepararMensagem(opcoes.acaoTexto) + '</button>';
    }
    html += '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Fechar"></button>';
    alertDiv.innerHTML = html;
    if (opcoes.acaoTexto && typeof opcoes.acaoCallback === 'function') {
      var btnAcao = alertDiv.querySelector('.alert-padrao-acao');
      if (btnAcao) {
        btnAcao.addEventListener('click', function () {
          opcoes.acaoCallback();
          try {
            var inst = global.bootstrap && global.bootstrap.Alert.getOrCreateInstance(alertDiv);
            if (inst) inst.close(); else alertDiv.remove();
          } catch (_) {
            alertDiv.remove();
          }
        });
      }
    }
    return alertDiv;
  }

  /**
   * Elemento .toast (Bootstrap 5).
   */
  function criarElementoToast(mensagem, tipo, opcoes) {
    const tipoNorm = normalizarTipo(tipo);
    const comIcone = opcoes.comIcone !== false;
    const textoEscapado = prepararMensagem(mensagem);
    const rotulo = prepararMensagem(rotuloPorTipo(tipoNorm).toUpperCase());
    const icone = iconePorTipo(tipoNorm);
    const pair = classesToastSkin(tipoNorm);
    const btnCloseClass = pair.btnClose ? 'btn-close ' + pair.btnClose : 'btn-close';

    const wrap = document.createElement('div');
    wrap.className = 'toast fade align-items-center border-0 mb-2 shadow-sm gdf-toast-item ' + pair.skin;
    wrap.setAttribute('role', 'alert');
    wrap.setAttribute('aria-live', tipoNorm === 'danger' ? 'assertive' : 'polite');
    wrap.setAttribute('aria-atomic', 'true');

    var bodyHtml = '';
    if (comIcone) {
      bodyHtml += '<i class="fas ' + icone + ' me-2" aria-hidden="true"></i>';
    }
    bodyHtml += '<strong>' + rotulo + '</strong><br><span class="gdf-toast-msg">' + textoEscapado + '</span>';
    if (opcoes.acaoTexto && typeof opcoes.acaoCallback === 'function') {
      var outline = 'btn-outline-secondary';
      if (tipoNorm === 'danger') outline = 'btn-outline-danger';
      else if (tipoNorm === 'success') outline = 'btn-outline-success';
      else if (tipoNorm === 'warning') outline = 'btn-outline-dark';
      else if (tipoNorm === 'info') outline = 'btn-outline-primary';
      bodyHtml += '<br><button type="button" class="btn btn-sm ' + outline + ' mt-2 gdf-toast-acao">' + prepararMensagem(opcoes.acaoTexto) + '</button>';
    }

    wrap.innerHTML =
      '<div class="d-flex w-100 align-items-start">' +
      '<div class="toast-body py-3 pe-1">' + bodyHtml + '</div>' +
      '<button type="button" class="' + btnCloseClass + ' me-2 m-auto" data-bs-dismiss="toast" aria-label="Fechar"></button>' +
      '</div>';

    if (opcoes.acaoTexto && typeof opcoes.acaoCallback === 'function') {
      var btn = wrap.querySelector('.gdf-toast-acao');
      if (btn) {
        btn.addEventListener('click', function () {
          opcoes.acaoCallback();
          try {
            var ti = global.bootstrap && global.bootstrap.Toast && global.bootstrap.Toast.getInstance(wrap);
            if (ti) ti.hide(); else wrap.remove();
          } catch (_) {
            wrap.remove();
          }
        });
      }
    }

    return wrap;
  }

  function anexarToastEExibir(container, mensagem, tipo, cfg) {
    const opcoes = {
      comIcone: cfg.comIcone !== false,
      acaoTexto: cfg.acaoTexto,
      acaoCallback: cfg.acaoCallback
    };

    const autoCloseMs = cfg.autoCloseMs !== undefined ? cfg.autoCloseMs : AUTO_CLOSE_PAGINA_MS;

    if (!global.bootstrap || !global.bootstrap.Toast) {
      var alertEl = criarElementoAlerta(mensagem, tipo, opcoes);
      container.appendChild(alertEl);
      if (autoCloseMs > 0) {
        setTimeout(function () {
          if (alertEl.parentNode) {
            try {
              var inst = global.bootstrap && global.bootstrap.Alert && global.bootstrap.Alert.getOrCreateInstance(alertEl);
              if (inst) inst.close(); else alertEl.remove();
            } catch (_) {
              alertEl.remove();
            }
          }
        }, autoCloseMs);
      }
      return;
    }

    const toastEl = criarElementoToast(mensagem, tipo, opcoes);
    container.appendChild(toastEl);

    const autohide = autoCloseMs > 0;
    const delay = autohide ? Math.max(autoCloseMs, 2000) : 5000;

    const inst = global.bootstrap.Toast.getOrCreateInstance(toastEl, {
      autohide: autohide,
      delay: delay
    });

    toastEl.addEventListener('hidden.bs.toast', function onHidden() {
      toastEl.removeEventListener('hidden.bs.toast', onHidden);
      try {
        inst.dispose();
      } catch (_) {}
      if (toastEl.parentNode) toastEl.remove();
    });

    inst.show();
  }

  /**
   * Toast na página (pilha fixa ou #alertas-container se existir e for o alvo).
   */
  function pagina(mensagem, tipo, opcoes) {
    const cfg = typeof opcoes === 'string'
      ? { containerId: opcoes }
      : (opcoes || {});

    var container = null;
    var containerId = cfg.containerId;

    if (containerId) {
      container = document.getElementById(containerId);
    }
    if (!container) {
      container = obterToastStack();
    }

    if (!container) {
      console.warn('[Notificacoes.pagina] Nenhum container de toast disponível.');
      if (typeof global.alert === 'function') {
        global.alert(mensagem);
      }
      return;
    }

    prepararContainerComoToastStack(container);
    anexarToastEExibir(container, mensagem, tipo, cfg);
  }

  /**
   * Mesmas notificações de pagina(): toast na pilha global (topo central), não dentro do modal.
   * containerId permanece na assinatura para compatibilidade com limparModal(containerId).
   */
  function modal(mensagem, tipo, containerId, opcoes) {
    const cfg = opcoes || {};
    var avisoDom = false;
    if (containerId && !document.getElementById(containerId)) {
      avisoDom = true;
    }

    if (cfg.limparAntes !== false && containerId) {
      var slotModal = document.getElementById(containerId);
      if (slotModal) slotModal.innerHTML = '';
    }

    const stack = obterToastStack();
    prepararContainerComoToastStack(stack);

    const tipoNorm = normalizarTipo(tipo);
    const autoCloseMs = cfg.autoCloseMs !== undefined
      ? cfg.autoCloseMs
      : (tipoNorm === 'success' ? AUTO_CLOSE_SUCESSO_MS : 0);

    if (avisoDom) {
      console.warn('[Notificacoes.modal] Container #' + containerId + ' não encontrado; toast exibido na pilha global.');
    }

    anexarToastEExibir(stack, mensagem, tipo, {
      comIcone: cfg.comIcone !== false,
      acaoTexto: cfg.acaoTexto,
      acaoCallback: cfg.acaoCallback,
      autoCloseMs: autoCloseMs
    });
  }

  function limparModal(containerId) {
    const container = containerId ? document.getElementById(containerId) : null;
    if (container) container.innerHTML = '';
  }

  function limparPagina(containerId) {
    var id = containerId || CONTAINER_PAGINA_PADRAO;
    if (id === CONTAINER_FIXO_ID || id === TOAST_STACK_ID) {
      var stack = document.getElementById(TOAST_STACK_ID);
      if (stack) {
        stack.querySelectorAll('.toast').forEach(function (t) {
          try {
            var ti = global.bootstrap && global.bootstrap.Toast && global.bootstrap.Toast.getInstance(t);
            if (ti) ti.dispose();
          } catch (_) {}
        });
        stack.innerHTML = '';
      }
      return;
    }
    var container = document.getElementById(id);
    if (container) container.innerHTML = '';
  }

  global.Notificacoes = {
    pagina: pagina,
    modal: modal,
    limparModal: limparModal,
    limparPagina: limparPagina,
    normalizarTipo: normalizarTipo,
    TIPOS: TIPOS_VALIDOS,
    CONTAINER_PAGINA_PADRAO: CONTAINER_PAGINA_PADRAO,
    CONTAINER_FIXO_ID: CONTAINER_FIXO_ID,
    TOAST_STACK_ID: TOAST_STACK_ID
  };
})(typeof window !== 'undefined' ? window : this);
