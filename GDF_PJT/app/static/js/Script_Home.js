/**
 * Script específico da página Home.
 * Esconde alertas de carga XML/SPED que o usuário já marcou como "já lido" (localStorage).
 */
(function() {
  'use strict';

  var VISTOS_KEYS = {
    cargaxml: 'gdf_cargaxml_avisos_vistos',
    cargasped: 'gdf_cargasped_avisos_vistos'
  };

  function getVistos(fonte) {
    var key = VISTOS_KEYS[fonte];
    if (!key) return new Set();
    try {
      var raw = localStorage.getItem(key);
      var arr = raw ? JSON.parse(raw) : [];
      return new Set((arr || []).map(Number).filter(Boolean));
    } catch (e) { return new Set(); }
  }

  function esconderAlertasJaLidos() {
    var itens = document.querySelectorAll('.home-alert[data-job-ids][data-fonte]');
    itens.forEach(function (li) {
      var idsStr = li.getAttribute('data-job-ids');
      var fonte = li.getAttribute('data-fonte');
      if (!idsStr || !fonte) return;
      var ids = idsStr.split(',').map(Number).filter(Boolean);
      if (ids.length === 0) return;
      var vistos = getVistos(fonte);
      var todosVistos = ids.every(function (id) { return vistos.has(id); });
      if (todosVistos) {
        li.style.display = 'none';
      }
    });
  }

  document.addEventListener('DOMContentLoaded', esconderAlertasJaLidos);
})();
