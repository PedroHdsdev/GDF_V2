/**
 * NotificacoesPadrao.js
 * Padrão único do painel GDF para exibição de erros, avisos e mensagens de sucesso.
 * Use em toda a aplicação: página (alertas no conteúdo) e modais.
 *
 * Uso:
 *   Notificacoes.pagina('Mensagem', 'success');
 *   Notificacoes.modal('Erro ao salvar', 'danger', 'modalClienteUpdAlerts');
 */

(function (global) {
  'use strict';

  const TIPOS_VALIDOS = ['success', 'danger', 'warning', 'info'];
  const CONTAINER_PAGINA_PADRAO = 'alertas-container';
  const CONTAINER_FIXO_ID = 'notificacoes-global';
  const AUTO_CLOSE_SUCESSO_MS = 5000;
  const AUTO_CLOSE_PAGINA_MS = 5000;

  /**
   * Rótulo em português por tipo (exibido em destaque no alerta)
   */
  function rotuloPorTipo(tipo) {
    const t = normalizarTipo(tipo);
    const rotulos = { success: 'Sucesso', danger: 'Erro', warning: 'Aviso', info: 'Informação' };
    return rotulos[t] || 'Informação';
  }

  /**
   * Normaliza tipo para Bootstrap: 'error' -> 'danger'
   */
  function normalizarTipo(tipo) {
    if (!tipo || typeof tipo !== 'string') return 'info';
    const t = tipo.toLowerCase();
    if (t === 'error') return 'danger';
    return TIPOS_VALIDOS.includes(t) ? t : 'info';
  }

  /**
   * Retorna ícone opcional por tipo (para uso consistente)
   */
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

  /**
   * Escapa HTML e converte \n em <br> para exibição segura com quebras de linha
   */
  function prepararMensagem(mensagem) {
    if (typeof mensagem !== 'string') return '';
    return mensagem
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/\n/g, '<br>');
  }

  /**
   * Cria o elemento DOM do alerta (rótulo + texto + botão fechar)
   * @param {string} mensagem - Texto da mensagem (pode conter \n para quebras de linha)
   * @param {string} tipo - success | danger | warning | info
   * @param {Object} opcoes - { dismissible: boolean, comIcone: boolean, acaoTexto: string, acaoCallback: function }
   */
  function criarElementoAlerta(mensagem, tipo, opcoes) {
    const tipoNorm = normalizarTipo(tipo);
    const dismissible = opcoes.dismissible !== false;
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
    if (dismissible) {
      html += '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Fechar"></button>';
    }
    alertDiv.innerHTML = html;
    if (opcoes.acaoTexto && typeof opcoes.acaoCallback === 'function') {
      var btnAcao = alertDiv.querySelector('.alert-padrao-acao');
      if (btnAcao) {
        btnAcao.addEventListener('click', function () {
          opcoes.acaoCallback();
          try {
            var inst = global.bootstrap && bootstrap.Alert.getOrCreateInstance(alertDiv);
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
   * Exibe alerta na PÁGINA (acima do conteúdo, dentro do container da própria tela).
   * Container padrão: #alertas-container (a página deve ter esse id no bloco de alertas).
   *
   * @param {string} mensagem - Texto da mensagem
   * @param {string} tipo - 'success' | 'danger' | 'warning' | 'info' (ou 'error' como alias de danger)
   * @param {Object|string} opcoes - Se string, é o containerId. Objeto: { containerId, autoCloseMs, dismissible, comIcone, acaoTexto, acaoCallback }
   */
  function pagina(mensagem, tipo, opcoes) {
    const cfg = typeof opcoes === 'string'
      ? { containerId: opcoes }
      : (opcoes || {});

    var containerId = cfg.containerId;
    if (!containerId) {
      containerId = document.getElementById(CONTAINER_FIXO_ID) ? CONTAINER_FIXO_ID : CONTAINER_PAGINA_PADRAO;
    }
    var container = document.getElementById(containerId);
    if (containerId === CONTAINER_FIXO_ID) {
      var inner = container && container.querySelector && container.querySelector('.notificacoes-fixa-inner');
      if (inner) container = inner;
    }

    if (!container) {
      console.warn('[Notificacoes.pagina] Container #' + containerId + ' não encontrado. Use um elemento com id="alertas-container" (ou informe containerId).');
      if (typeof global.alert === 'function') {
        global.alert(mensagem);
      }
      return;
    }

    const alertEl = criarElementoAlerta(mensagem, tipo, {
      dismissible: true,
      comIcone: cfg.comIcone !== false,
      acaoTexto: cfg.acaoTexto,
      acaoCallback: cfg.acaoCallback
    });
    container.appendChild(alertEl);

    const autoCloseMs = cfg.autoCloseMs !== undefined ? cfg.autoCloseMs : AUTO_CLOSE_PAGINA_MS;
    if (autoCloseMs > 0) {
      setTimeout(function () {
        if (alertEl.parentNode) {
          alertEl.style.transition = 'opacity 0.3s ease';
          alertEl.style.opacity = '0';
          setTimeout(function () {
            if (alertEl.parentNode) {
              try {
                const inst = global.bootstrap && bootstrap.Alert.getOrCreateInstance(alertEl);
                if (inst) inst.close(); else alertEl.remove();
              } catch (_) {
                alertEl.remove();
              }
            }
          }, 300);
        }
      }, autoCloseMs);
    }
  }

  /**
   * Exibe alerta dentro de um MODAL (no topo do body do modal).
   * O container deve existir dentro do modal (ex: modalClienteUpdAlerts).
   *
   * @param {string} mensagem - Texto da mensagem
   * @param {string} tipo - 'success' | 'danger' | 'warning' | 'info'
   * @param {string} containerId - ID do elemento container (ex: 'modalClienteUpdAlerts')
   * @param {Object} opcoes - { limparAntes: boolean, autoCloseMs (só success), dismissible, comIcone }
   */
  function modal(mensagem, tipo, containerId, opcoes) {
    const cfg = opcoes || {};
    const container = containerId ? document.getElementById(containerId) : null;

    if (!container) {
      console.warn('[Notificacoes.modal] Container #' + (containerId || '') + ' não encontrado.');
      if (typeof global.alert === 'function') {
        global.alert(mensagem);
      }
      return;
    }

    if (cfg.limparAntes !== false) {
      container.innerHTML = '';
    }

    const alertEl = criarElementoAlerta(mensagem, tipo, {
      dismissible: true,
      comIcone: cfg.comIcone !== false
    });
    container.appendChild(alertEl);

    const tipoNorm = normalizarTipo(tipo);
    const autoCloseMs = cfg.autoCloseMs !== undefined
      ? cfg.autoCloseMs
      : (tipoNorm === 'success' ? AUTO_CLOSE_SUCESSO_MS : 0);

    if (autoCloseMs > 0) {
      setTimeout(function () {
        if (alertEl.parentNode) {
          try {
            const inst = global.bootstrap && bootstrap.Alert.getOrCreateInstance(alertEl);
            if (inst) inst.close(); else alertEl.remove();
          } catch (_) {
            alertEl.remove();
          }
        }
      }, autoCloseMs);
    }
  }

  /**
   * Limpa todos os alertas de um container (útil ao abrir o modal).
   * @param {string} containerId - ID do container (ex: 'modalClienteUpdAlerts')
   */
  function limparModal(containerId) {
    const container = containerId ? document.getElementById(containerId) : null;
    if (container) container.innerHTML = '';
  }

  /**
   * Limpa o container de alertas da página.
   * @param {string} containerId - ID do container (default: alertas-container). Use CONTAINER_FIXO_ID para a área fixa.
   */
  function limparPagina(containerId) {
    var id = containerId || CONTAINER_PAGINA_PADRAO;
    if (id === CONTAINER_FIXO_ID) {
      var outer = document.getElementById(CONTAINER_FIXO_ID);
      var inner = outer && outer.querySelector('.notificacoes-fixa-inner');
      if (inner) inner.innerHTML = '';
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
    CONTAINER_FIXO_ID: CONTAINER_FIXO_ID
  };
})(typeof window !== 'undefined' ? window : this);
