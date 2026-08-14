/**
 * Painel "Registros no período" — agregação por mês via /api/cargaxml|sped/registros-mensais/.
 * Depende de relatorio_fiscal.js (relatorioGetPrefix, relatorioBuildUrl).
 */
(function () {
    'use strict';

    function rootEl() {
        return document.getElementById('reg-periodo-root');
    }

    function modoPainel() {
        var r = rootEl();
        return r ? (r.getAttribute('data-reg-panel-modo') || 'xml') : 'xml';
    }

    function pad(n) {
        return n < 10 ? '0' + n : String(n);
    }

    function initDatasMes() {
        var now = new Date();
        var primeiro = new Date(now.getFullYear(), now.getMonth(), 1);
        var ultimo = new Date(now.getFullYear(), now.getMonth() + 1, 0);
        var ini = primeiro.getFullYear() + '-' + pad(primeiro.getMonth() + 1) + '-' + pad(primeiro.getDate());
        var fim = ultimo.getFullYear() + '-' + pad(ultimo.getMonth() + 1) + '-' + pad(ultimo.getDate());
        var pairs = [
            ['reg-periodo-data-inicio', ini],
            ['reg-periodo-data-fim', fim],
            ['reg-periodo-sped-data-inicio', ini],
            ['reg-periodo-sped-data-fim', fim]
        ];
        pairs.forEach(function (p) {
            var el = document.getElementById(p[0]);
            if (el && !el.value) el.value = p[1];
        });
    }

    function filialPorEmpresaXml() {
        var emp = document.getElementById('reg-periodo-empresa');
        var sel = document.getElementById('reg-periodo-filial');
        if (!emp || !sel) return;
        var cod = emp.value.trim();
        var cur = sel.value;
        Array.from(sel.options).forEach(function (opt, i) {
            if (i === 0) {
                opt.disabled = false;
                return;
            }
            var oe = opt.getAttribute('data-cod-empresa') || '';
            opt.disabled = !!(cod && oe !== cod);
        });
        if (cur) {
            var idx = sel.selectedIndex;
            var selected = sel.options[idx];
            if (selected && selected.disabled) sel.value = '';
        }
    }

    function atualizarVisibilidadeStatusNfe() {
        var tipo = document.getElementById('reg-periodo-tipo-doc');
        var wrap = document.querySelector('#reg-periodo-root .reg-periodo-wrap-status');
        if (!wrap || !tipo) return;
        wrap.classList.toggle('d-none', tipo.value !== 'nfe');
    }

    function paramsXml(tipoDoc) {
        var statusEl = document.getElementById('reg-periodo-status-nfe');
        var tsap = document.getElementById('reg-periodo-tem-sap');
        var p = {
            empresa_id: (document.getElementById('reg-periodo-empresa') && document.getElementById('reg-periodo-empresa').value.trim()) || '',
            filial_id: (document.getElementById('reg-periodo-filial') && document.getElementById('reg-periodo-filial').value.trim()) || '',
            data_inicio: (document.getElementById('reg-periodo-data-inicio') && document.getElementById('reg-periodo-data-inicio').value.trim()) || '',
            data_fim: (document.getElementById('reg-periodo-data-fim') && document.getElementById('reg-periodo-data-fim').value.trim()) || '',
            busca: (document.getElementById('reg-periodo-busca') && document.getElementById('reg-periodo-busca').value.trim()) || '',
            tipo: tipoDoc
        };
        if (tipoDoc === 'nfe' && statusEl && statusEl.value.trim()) {
            p.status = statusEl.value.trim();
        }
        var vsap = tsap && tsap.value.trim();
        if (vsap) p.tem_sap = vsap;
        return p;
    }

    function paramsSped() {
        return {
            empresa_id: (document.getElementById('reg-periodo-sped-empresa') && document.getElementById('reg-periodo-sped-empresa').value.trim()) || '',
            filial_id: '',
            data_inicio: (document.getElementById('reg-periodo-sped-data-inicio') && document.getElementById('reg-periodo-sped-data-inicio').value.trim()) || '',
            data_fim: (document.getElementById('reg-periodo-sped-data-fim') && document.getElementById('reg-periodo-sped-data-fim').value.trim()) || '',
            busca: (document.getElementById('reg-periodo-sped-busca') && document.getElementById('reg-periodo-sped-busca').value.trim()) || '',
            tipo_sped: (document.getElementById('reg-periodo-sped-tipo') && document.getElementById('reg-periodo-sped-tipo').value.trim()) || ''
        };
    }

    function theadMensal() {
        return '<tr><th scope="col">Mês</th><th scope="col" class="text-end">Quantidade</th></tr>';
    }

    function atualizarContador(items, labelUnit) {
        var el = document.getElementById('reg-periodo-contador-num');
        if (!el) return;
        if (!items || !items.length) {
            el.textContent = 'Nenhum ' + labelUnit + ' no período';
            return;
        }
        var total = items.reduce(function (a, x) {
            return a + (Number(x.quantidade) || 0);
        }, 0);
        el.textContent = total + ' ' + labelUnit + ' em ' + items.length + ' mês(es)';
    }

    function escapeHtml(s) {
        if (s == null || s === '') return '';
        var d = document.createElement('div');
        d.textContent = s;
        return d.innerHTML;
    }

    function renderLinhasMensais(items) {
        return items.map(function (x) {
            var lbl = x.mes_label || x.mes || '—';
            var q = x.quantidade != null ? x.quantidade : '—';
            return '<tr><td>' + escapeHtml(String(lbl)) + '</td><td class="text-end">' + escapeHtml(String(q)) + '</td></tr>';
        }).join('');
    }

    function carregarXml() {
        var tipo = (document.getElementById('reg-periodo-tipo-doc') && document.getElementById('reg-periodo-tipo-doc').value) || 'nfe';
        var thead = document.getElementById('reg-periodo-thead');
        var tbody = document.getElementById('reg-periodo-tbody');
        if (!thead || !tbody) return;

        thead.innerHTML = theadMensal();
        tbody.innerHTML = '<tr><td colspan="2" class="text-center py-3">Carregando…</td></tr>';

        var prefix = typeof relatorioGetPrefix === 'function' ? relatorioGetPrefix() : '';
        var url = prefix + relatorioBuildUrl('/api/cargaxml/registros-mensais/', paramsXml(tipo));

        fetch(url, { credentials: 'same-origin' })
            .then(function (r) { return r.json(); })
            .then(function (data) {
                if (data.erro) {
                    tbody.innerHTML = '<tr><td colspan="2" class="text-center text-danger py-4">' + escapeHtml(String(data.erro)) + '</td></tr>';
                    atualizarContador([], 'registro');
                    return;
                }
                var items = data.items || [];
                atualizarContador(items, 'registro(s)');
                if (!items.length) {
                    tbody.innerHTML = '<tr><td colspan="2" class="text-center text-muted py-4">Nenhum registro</td></tr>';
                    return;
                }
                tbody.innerHTML = renderLinhasMensais(items);
            })
            .catch(function () {
                tbody.innerHTML = '<tr><td colspan="2" class="text-center text-danger py-4">Erro ao carregar</td></tr>';
                atualizarContador([], 'registro');
            });
    }

    function carregarSped() {
        var thead = document.getElementById('reg-periodo-thead');
        var tbody = document.getElementById('reg-periodo-tbody');
        if (!thead || !tbody) return;
        thead.innerHTML = theadMensal();
        tbody.innerHTML = '<tr><td colspan="2" class="text-center py-3">Carregando…</td></tr>';

        var prefix = typeof relatorioGetPrefix === 'function' ? relatorioGetPrefix() : '';
        var url = prefix + relatorioBuildUrl('/api/cargasped/registros-mensais/', paramsSped());

        fetch(url, { credentials: 'same-origin' })
            .then(function (r) { return r.json(); })
            .then(function (data) {
                if (data.erro) {
                    tbody.innerHTML = '<tr><td colspan="2" class="text-center text-danger py-4">' + escapeHtml(String(data.erro)) + '</td></tr>';
                    atualizarContador([], 'arquivo');
                    return;
                }
                var items = data.items || [];
                atualizarContador(items, 'arquivo(s)');
                if (!items.length) {
                    tbody.innerHTML = '<tr><td colspan="2" class="text-center text-muted py-4">Nenhum arquivo</td></tr>';
                    return;
                }
                tbody.innerHTML = renderLinhasMensais(items);
            })
            .catch(function () {
                tbody.innerHTML = '<tr><td colspan="2" class="text-center text-danger py-4">Erro ao carregar</td></tr>';
                atualizarContador([], 'arquivo');
            });
    }

    function carregar() {
        if (!rootEl()) return;
        if (modoPainel() === 'sped') {
            carregarSped();
        } else {
            carregarXml();
        }
    }

    function init() {
        if (!rootEl()) return;
        initDatasMes();

        var btnXml = document.getElementById('reg-periodo-btn-consultar');
        if (btnXml) {
            btnXml.addEventListener('click', function () {
                carregarXml();
            });
        }
        var emp = document.getElementById('reg-periodo-empresa');
        if (emp) emp.addEventListener('change', filialPorEmpresaXml);
        filialPorEmpresaXml();

        var tipoSel = document.getElementById('reg-periodo-tipo-doc');
        if (tipoSel) {
            tipoSel.addEventListener('change', function () {
                atualizarVisibilidadeStatusNfe();
            });
            atualizarVisibilidadeStatusNfe();
        }

        var btnSped = document.getElementById('reg-periodo-sped-btn-consultar');
        if (btnSped) {
            btnSped.addEventListener('click', function () {
                carregarSped();
            });
        }
    }

    document.addEventListener('DOMContentLoaded', init);
})();
