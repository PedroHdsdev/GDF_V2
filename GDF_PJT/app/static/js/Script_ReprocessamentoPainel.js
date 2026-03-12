/**
 * Painel de Reprocessamento: confronto SPED x NFe, lotes e divergências.
 * APIs: /api/reprocessamento/lotes/, .../lotes/<id>/divergencias/, .../confronto/, .../divergencias/<id>/reprocessar/
 */
(function () {
    'use strict';

    const estado = {
        lotes: [],
        loteSelecionadoId: null,
        empresasMap: {},
        divergenciasLista: [],
        divergenciaSelecionada: null,
        condicoesLoteId: null,
        condicoesLista: [],
    };

    function getCsrfToken() {
        const name = 'csrftoken';
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const c = cookies[i].trim();
            if (c.indexOf(name + '=') === 0) return c.substring(name.length + 1);
        }
        return '';
    }

    function apiUrl(path) {
        var prefix = (typeof getUrlPrefix === 'function') ? getUrlPrefix() : '';
        return (prefix || '') + (path.charAt(0) === '/' ? path : '/' + path);
    }

    function parametrosFiltros() {
        const params = new URLSearchParams();
        const empresa = document.getElementById('filtro-empresa');
        const mes = document.getElementById('filtro-mes');
        const ano = document.getElementById('filtro-ano');
        const status = document.getElementById('filtro-status');
        const criadoDe = document.getElementById('filtro-criado-de');
        const criadoAte = document.getElementById('filtro-criado-ate');
        if (empresa && empresa.value) params.set('empresa', empresa.value);
        if (mes && ano && mes.value && ano.value) params.set('competencia', ano.value + '-' + mes.value);
        if (status && status.value) params.set('status', status.value);
        if (criadoDe && criadoDe.value) params.set('criado_de', criadoDe.value);
        if (criadoAte && criadoAte.value) params.set('criado_ate', criadoAte.value);
        return params.toString();
    }

    function limparFiltros() {
        const empresa = document.getElementById('filtro-empresa');
        const mes = document.getElementById('filtro-mes');
        const ano = document.getElementById('filtro-ano');
        const status = document.getElementById('filtro-status');
        const criadoDe = document.getElementById('filtro-criado-de');
        const criadoAte = document.getElementById('filtro-criado-ate');
        if (empresa) empresa.value = '';
        if (mes) mes.value = '';
        if (ano) ano.value = '';
        if (status) status.value = '';
        if (criadoDe) criadoDe.value = '';
        if (criadoAte) criadoAte.value = '';
        carregarLotes();
    }

    function preencherAnosFiltro() {
        const sel = document.getElementById('filtro-ano');
        if (!sel) return;
        const anoAtual = new Date().getFullYear();
        if (sel.options.length > 1) return; // já preenchido
        for (let a = anoAtual + 1; a >= anoAtual - 5; a--) {
            const opt = document.createElement('option');
            opt.value = a;
            opt.textContent = a;
            sel.appendChild(opt);
        }
    }

    function carregarLotes() {
        const tbody = document.querySelector('#tabela-lotes tbody');
        const trCarregando = document.getElementById('tr-carregando');
        const trVazio = document.getElementById('tr-vazio');
        if (!tbody) return;

        if (trCarregando) trCarregando.classList.remove('d-none');
        if (trVazio) trVazio.classList.add('d-none');
        tbody.querySelectorAll('tr.dados-lote').forEach(el => el.remove());

        const qs = parametrosFiltros();
        fetch(apiUrl('api/reprocessamento/lotes/') + (qs ? '?' + qs : ''), { method: 'GET', credentials: 'same-origin' })
            .then(res => res.json())
            .then(data => {
                if (trCarregando) trCarregando.classList.add('d-none');
                if (!data.sucesso) {
                    if (typeof Notificacoes !== 'undefined') Notificacoes.pagina(data.mensagem || 'Erro ao carregar lotes', 'danger');
                    return;
                }
                estado.lotes = data.lotes || [];
                atualizarResumo(estado.lotes);
                const textoExibindo = document.getElementById('texto-exibindo');
                const countExibindo = document.getElementById('count-exibindo');
                if (countExibindo) countExibindo.textContent = estado.lotes.length;
                if (textoExibindo) textoExibindo.classList.toggle('d-none', estado.lotes.length === 0);

                if (estado.lotes.length === 0) {
                    if (trVazio) trVazio.classList.remove('d-none');
                    return;
                }
                estado.lotes.forEach(l => {
                    const tr = document.createElement('tr');
                    tr.className = 'dados-lote' + (l.total_divergencias > 0 ? ' tem-divergencia' : '');
                    const statusBadge = statusParaBadge(l.status);
                    const competenciaExibir = formatarCompetenciaMes(l.competencia_mes || l.competencia);
                    const dataCriacaoStr = formatarDataHora(l.data_criacao);
                    const divNum = (l.total_divergencias ?? 0);
                    const empresaExibir = formatarEmpresaLote(l.cod_empresa, l.empresa_fantasia || l.empresa_razao);
                    tr.innerHTML =
                        '<td class="text-center">' + l.id_lote + '</td>' +
                        '<td class="col-empresa">' + empresaExibir + '</td>' +
                        '<td class="text-center">' + competenciaExibir + '</td>' +
                        '<td class="text-end tab-num">' + (l.total_nfe_esperado ?? '-') + '</td>' +
                        '<td class="text-end tab-num">' + (l.total_nfe_encontrado ?? '-') + '</td>' +
                        '<td class="text-end tab-num">' + (divNum > 0 ? '<span class="badge bg-warning text-dark">' + divNum + '</span>' : divNum) + '</td>' +
                        '<td class="text-center">' + statusBadge + '</td>' +
                        '<td class="text-secondary small">' + dataCriacaoStr + '</td>' +
                        '<td class="text-center"><button type="button" class="btn btn-sm btn-outline-primary btn-ver-divergencias" data-id="' + l.id_lote + '" title="Ver divergências"><i class="fas fa-list-ul me-1"></i>Ver</button> <button type="button" class="btn btn-sm btn-outline-secondary btn-cond-pagamento ms-1" data-id="' + l.id_lote + '" title="Condições de pagamento (SAP)"><i class="fas fa-file-invoice-dollar me-1"></i>Cond.</button></td>';
                    tbody.appendChild(tr);
                });
                tbody.querySelectorAll('.btn-ver-divergencias').forEach(btn => {
                    btn.addEventListener('click', function () {
                        abrirModalDivergencias(parseInt(this.getAttribute('data-id'), 10));
                    });
                });
                tbody.querySelectorAll('.btn-cond-pagamento').forEach(btn => {
                    btn.addEventListener('click', function () {
                        abrirModalCondicoes(parseInt(this.getAttribute('data-id'), 10));
                    });
                });
            })
            .catch(err => {
                if (trCarregando) trCarregando.classList.add('d-none');
                if (trVazio) trVazio.classList.remove('d-none');
                if (typeof Notificacoes !== 'undefined') Notificacoes.pagina('Erro ao carregar lotes', 'danger');
            });
    }

    /** Exibe competência como MM/YYYY (confronto é por mês). */
    function formatarCompetenciaMes(competencia) {
        if (!competencia) return '-';
        const s = String(competencia);
        if (s.length >= 7 && s[4] === '-') return s.substring(5, 7) + '/' + s.substring(0, 4);  // YYYY-MM
        if (s.length >= 10) return s.substring(5, 7) + '/' + s.substring(0, 4);               // YYYY-MM-DD
        return s;
    }

    function formatarDataHora(iso) {
        if (!iso) return '-';
        const d = new Date(iso);
        if (isNaN(d.getTime())) return '-';
        const dd = String(d.getDate()).padStart(2, '0');
        const mm = String(d.getMonth() + 1).padStart(2, '0');
        const yyyy = d.getFullYear();
        const h = String(d.getHours()).padStart(2, '0');
        const min = String(d.getMinutes()).padStart(2, '0');
        return dd + '/' + mm + '/' + yyyy + ' ' + h + ':' + min;
    }

    function escapeHtml(s) {
        if (s == null) return '';
        const div = document.createElement('div');
        div.textContent = s;
        return div.innerHTML;
    }

    function tipoDivergenciaLabel(tipo) {
        const labels = {
            NFE_AUSENTE_SPED: 'NF-e ausente no SPED',
            SPED_AUSENTE_NFE: 'SPED sem NF-e',
            VALOR_DIFERENTE: 'Valor divergente',
            CFOP_DIFERENTE: 'CFOP divergente',
            DATA_EMISSAO_DIFERENTE: 'Data divergente',
            CANCELAMENTO: 'Cancelamento',
            OUTRO: 'Outra',
        };
        return labels[tipo] || tipo || '-';
    }

    function tipoDivergenciaBadgeClass(tipo) {
        if (tipo === 'NFE_AUSENTE_SPED') return 'badge bg-warning text-dark';
        if (tipo === 'SPED_AUSENTE_NFE') return 'badge bg-info text-dark';
        return 'badge bg-secondary';
    }

    function ativarAbaDivergencias(tabId) {
        document.querySelectorAll('#divergencias-tabs .nav-link').forEach(function (el) {
            el.classList.remove('active');
        });
        document.querySelectorAll('#divergencias-tab-content .tab-pane').forEach(function (el) {
            el.classList.remove('show', 'active');
        });
        const btn = document.getElementById(tabId + '-btn');
        const pane = document.getElementById(tabId);
        if (btn) btn.classList.add('active');
        if (pane) pane.classList.add('show', 'active');
    }

    function renderizarPorTipo(lista) {
        const tbody = document.getElementById('lista-divergencias-todas');
        const vazio = document.getElementById('lista-divergencias-vazio');
        const wrap = document.getElementById('wrap-lista-divergencias');
        if (!tbody) return;
        tbody.innerHTML = '';
        const items = lista || [];
        if (vazio) vazio.classList.toggle('d-none', items.length > 0);
        if (wrap) wrap.classList.toggle('d-none', items.length === 0);
        items.forEach(function (d) {
            const chave = d.chave_nfe || '-';
            const doc = (d.numero_nfe || d.serie_nfe) ? 'Nº ' + (d.numero_nfe || '-') + '/' + (d.serie_nfe || '-') : '-';
            const statusLabel = d.status === 'ABERTA' ? 'Aberta' : (d.status === 'RESOLVIDA' ? 'Resolvida' : d.status);
            const statusBadge = d.status === 'ABERTA' ? 'bg-warning text-dark' : 'bg-success';
            const btnResolver = d.status === 'ABERTA'
                ? '<button type="button" class="btn btn-sm btn-success btn-resolver-lista" data-id="' + d.id_divergencia + '" title="Marcar como resolvida"><i class="fas fa-check"></i></button>'
                : '<span class="badge bg-success">Resolvida</span>';
            const tr = document.createElement('tr');
            tr.className = 'por-tipo-row';
            tr.setAttribute('data-id-div', d.id_divergencia);
            tr.innerHTML =
                '<td><code class="por-tipo-chave" title="' + escapeHtml(d.chave_nfe || '-') + '">' + escapeHtml(chave) + '</code></td>' +
                '<td>' + escapeHtml(doc) + '</td>' +
                '<td><span class="badge ' + statusBadge + '">' + escapeHtml(statusLabel) + '</span></td>' +
                '<td class="text-end"><button type="button" class="btn btn-sm btn-outline-primary btn-detalhe-lista me-1" data-id="' + d.id_divergencia + '" title="Ver detalhe"><i class="fas fa-search"></i></button>' + btnResolver + '</td>';
            tr.style.cursor = 'pointer';
            tr.addEventListener('click', function (e) {
                if (e.target.closest('button')) return;
                mostrarDetalheDivergencia(d);
            });
            tbody.appendChild(tr);
        });
        tbody.querySelectorAll('.btn-detalhe-lista').forEach(function (btn) {
            btn.addEventListener('click', function (e) {
                e.stopPropagation();
                const id = parseInt(btn.getAttribute('data-id'), 10);
                const item = estado.divergenciasLista.find(function (d) { return d.id_divergencia === id; });
                if (item) mostrarDetalheDivergencia(item);
            });
        });
        tbody.querySelectorAll('.btn-resolver-lista').forEach(function (btn) {
            btn.addEventListener('click', function (e) {
                e.stopPropagation();
                reprocessarDivergencia(parseInt(btn.getAttribute('data-id'), 10));
            });
        });
    }

    function formatarDataHoraDetalhe(iso) {
        if (!iso) return '—';
        try {
            const d = new Date(iso);
            return d.toLocaleString('pt-BR');
        } catch (e) { return iso; }
    }

    function formatarValorMonetario(v) {
        if (v == null || v === '' || v === undefined) return '—';
        const n = parseFloat(v);
        return isNaN(n) ? v : 'R$ ' + n.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    }

    function preencherSubAbasDetalhe(payload) {
        const d = payload.divergencia;
        const nfe = payload.nfe;
        const sped = payload.sped;
        const confrontos = payload.confrontos || [];

        // Resumo
        const campos = [
            { label: 'ID', value: d.id_divergencia },
            { label: 'Tipo', value: tipoDivergenciaLabel(d.tipo) },
            { label: 'Status', value: d.status === 'ABERTA' ? 'Aberta' : (d.status === 'RESOLVIDA' ? 'Resolvida' : d.status) },
            { label: 'Chave NF-e', value: d.chave_nfe || '—' },
            { label: 'Número', value: d.numero_nfe || '—' },
            { label: 'Série', value: d.serie_nfe || '—' },
            { label: 'Registro SPED', value: d.registro_sped || '—' },
            { label: 'Linha SPED', value: d.linha_sped != null ? d.linha_sped : '—' },
            { label: 'ID NF-e (sistema)', value: d.id_nfe != null ? d.id_nfe : '—' },
            { label: 'Valor esperado', value: d.valor_esperado != null ? d.valor_esperado : '—' },
            { label: 'Valor encontrado', value: d.valor_encontrado != null ? d.valor_encontrado : '—' },
            { label: 'Data criação', value: formatarDataHoraDetalhe(d.data_criacao) },
            { label: 'Data reprocessamento', value: formatarDataHoraDetalhe(d.data_reprocessamento) },
            { label: 'Usuário reprocessamento', value: d.usuario_reprocessamento || '—' },
        ];
        const tbody = document.getElementById('detalhe-campos');
        if (tbody) {
            tbody.innerHTML = campos.map(function (c) {
                return '<tr><td class="text-muted small pe-2">' + escapeHtml(c.label) + '</td><td class="small">' + escapeHtml(String(c.value)) + '</td></tr>';
            }).join('');
        }
        const descEl = document.getElementById('detalhe-descricao');
        if (descEl) descEl.textContent = d.descricao || '—';
        const jsonWrap = document.getElementById('detalhe-json-wrap');
        const jsonEl = document.getElementById('detalhe-json');
        if (d.detalhe_json && jsonWrap && jsonEl) {
            jsonEl.textContent = typeof d.detalhe_json === 'string' ? d.detalhe_json : JSON.stringify(d.detalhe_json, null, 2);
            jsonWrap.classList.remove('d-none');
        } else if (jsonWrap) jsonWrap.classList.add('d-none');

        // Cabeçalho
        const cabNfe = document.getElementById('detalhe-cabecalho-nfe');
        const cabSped = document.getElementById('detalhe-cabecalho-sped');
        if (cabNfe) {
            if (nfe && nfe['cabeçalho']) {
                const h = nfe['cabeçalho'];
                cabNfe.innerHTML = '<table class="table table-sm table-borderless mb-0"><tbody>' +
                    '<tr><td class="text-muted pe-2">Número/Série</td><td>' + escapeHtml((h.numero || '') + '/' + (h.serie || '')) + '</td></tr>' +
                    '<tr><td class="text-muted pe-2">Emissão</td><td>' + escapeHtml(h.emissao ? h.emissao.substring(0, 10) : '—') + '</td></tr>' +
                    '<tr><td class="text-muted pe-2">Natureza</td><td>' + escapeHtml(h.natureza_operacao || '—') + '</td></tr>' +
                    '<tr><td class="text-muted pe-2">Emitente</td><td>' + escapeHtml(h.emitente || '—') + '</td></tr>' +
                    '<tr><td class="text-muted pe-2">Destinatário</td><td>' + escapeHtml(h.destinatario || '—') + '</td></tr>' +
                    '</tbody></table>';
            } else {
                cabNfe.innerHTML = '<span class="text-muted">NF-e não disponível para esta divergência.</span>';
            }
        }
        if (cabSped) {
            if (sped && sped['cabeçalho']) {
                const h = sped['cabeçalho'];
                cabSped.innerHTML = '<table class="table table-sm table-borderless mb-0"><tbody>' +
                    '<tr><td class="text-muted pe-2">Número/Série</td><td>' + escapeHtml((h.num_doc || '') + '/' + (h.ser || '')) + '</td></tr>' +
                    '<tr><td class="text-muted pe-2">Data doc</td><td>' + escapeHtml(h.dt_doc || '—') + '</td></tr>' +
                    '<tr><td class="text-muted pe-2">Valor doc</td><td>' + formatarValorMonetario(h.vl_doc) + '</td></tr>' +
                    '</tbody></table>';
            } else {
                cabSped.innerHTML = '<span class="text-muted">SPED não disponível para esta divergência.</span>';
            }
        }

        // Itens
        const itensNfe = document.getElementById('detalhe-itens-nfe');
        const itensSped = document.getElementById('detalhe-itens-sped');
        if (itensNfe) {
            const lista = (nfe && nfe.itens) ? nfe.itens : [];
            itensNfe.innerHTML = lista.length ? lista.map(function (i) {
                const icms = (i.icms && i.icms.valor) ? formatarValorMonetario(i.icms.valor) : '—';
                const pis = (i.pis && i.pis.valor) ? formatarValorMonetario(i.pis.valor) : '—';
                const cofins = (i.cofins && i.cofins.valor) ? formatarValorMonetario(i.cofins.valor) : '—';
                return '<tr><td>' + escapeHtml(String(i.numero_item)) + '</td><td>' + escapeHtml((i.descricao || '').substring(0, 25)) + '</td><td>' + escapeHtml(i.cfop || '') + '</td><td>' + escapeHtml(i.unidade || '') + '</td><td>' + escapeHtml(String(i.quantidade || '')) + '</td><td>' + formatarValorMonetario(i.valor_total) + '</td><td>' + icms + '</td><td>' + pis + '</td><td>' + cofins + '</td></tr>';
            }).join('') : '<tr><td colspan="9" class="text-muted text-center">Nenhum item</td></tr>';
        }
        if (itensSped) {
            const lista = (sped && sped.itens) ? sped.itens : [];
            itensSped.innerHTML = lista.length ? lista.map(function (i) {
                const icms = formatarValorMonetario(i.vl_icms);
                const pis = formatarValorMonetario(i.vl_pis);
                const cofins = formatarValorMonetario(i.vl_cofins);
                return '<tr><td>' + escapeHtml(String(i.num_item || '')) + '</td><td>' + escapeHtml((i.descr_compl || i.cod_item || '').substring(0, 25)) + '</td><td>' + escapeHtml(i.cfop || '') + '</td><td>' + escapeHtml(i.unid || '') + '</td><td>' + escapeHtml(String(i.qtd || '')) + '</td><td>' + formatarValorMonetario(i.vl_item) + '</td><td>' + icms + '</td><td>' + pis + '</td><td>' + cofins + '</td></tr>';
            }).join('') : '<tr><td colspan="9" class="text-muted text-center">Nenhum item</td></tr>';
        }

        // Impostos
        const impNfe = document.getElementById('detalhe-impostos-nfe');
        const impSped = document.getElementById('detalhe-impostos-sped');
        if (impNfe) {
            const tot = (nfe && nfe.totalizacao) ? nfe.totalizacao : null;
            if (tot) {
                impNfe.innerHTML = '<table class="table table-sm table-borderless mb-0"><tbody>' +
                    '<tr><td class="text-muted pe-2">Base ICMS</td><td>' + formatarValorMonetario(tot.valor_base_icms) + '</td></tr>' +
                    '<tr><td class="text-muted pe-2">ICMS</td><td>' + formatarValorMonetario(tot.valor_icms) + '</td></tr>' +
                    '<tr><td class="text-muted pe-2">ICMS ST</td><td>' + formatarValorMonetario(tot.valor_icms_st) + '</td></tr>' +
                    '<tr><td class="text-muted pe-2">PIS</td><td>' + formatarValorMonetario(tot.valor_pis) + '</td></tr>' +
                    '<tr><td class="text-muted pe-2">COFINS</td><td>' + formatarValorMonetario(tot.valor_cofins) + '</td></tr>' +
                    '<tr><td class="text-muted pe-2">Total NF-e</td><td><strong>' + formatarValorMonetario(tot.valor_total_nfe) + '</strong></td></tr>' +
                    '</tbody></table>';
            } else {
                impNfe.innerHTML = '<span class="text-muted">Totalização não disponível.</span>';
            }
        }
        if (impSped) {
            const h = (sped && sped['cabeçalho']) ? sped['cabeçalho'] : null;
            if (h) {
                impSped.innerHTML = '<table class="table table-sm table-borderless mb-0"><tbody>' +
                    '<tr><td class="text-muted pe-2">Base ICMS</td><td>' + formatarValorMonetario(h.vl_bc_icms) + '</td></tr>' +
                    '<tr><td class="text-muted pe-2">ICMS</td><td>' + formatarValorMonetario(h.vl_icms) + '</td></tr>' +
                    '<tr><td class="text-muted pe-2">ICMS ST</td><td>' + formatarValorMonetario(h.vl_icms_st) + '</td></tr>' +
                    '<tr><td class="text-muted pe-2">PIS</td><td>' + formatarValorMonetario(h.vl_pis) + '</td></tr>' +
                    '<tr><td class="text-muted pe-2">COFINS</td><td>' + formatarValorMonetario(h.vl_cofins) + '</td></tr>' +
                    '<tr><td class="text-muted pe-2">Valor doc</td><td><strong>' + formatarValorMonetario(h.vl_doc) + '</strong></td></tr>' +
                    '</tbody></table>';
            } else {
                impSped.innerHTML = '<span class="text-muted">SPED não disponível.</span>';
            }
        }

        // Confrontos
        const tbodyConf = document.getElementById('detalhe-confrontos');
        if (tbodyConf) {
            tbodyConf.innerHTML = confrontos.map(function (c) {
                const statusClass = c.status === 'OK' ? 'success' : (c.status === 'DIVERGÊNCIA' ? 'danger' : 'secondary');
                return '<tr><td>' + escapeHtml(c.tipo) + '</td><td>' + escapeHtml(c.descricao || '') + '</td><td><span class="badge bg-' + statusClass + '">' + escapeHtml(c.status) + '</span></td><td class="small">' + escapeHtml(c.detalhe || '—') + '</td></tr>';
            }).join('');
        }
    }

    function mostrarDetalheDivergencia(d) {
        estado.divergenciaSelecionada = d;
        document.getElementById('tab-detalhe-btn')?.style.setProperty('display', '');
        ativarAbaDivergencias('tab-detalhe');
        document.getElementById('divergencia-detalhe-panel')?.classList.remove('d-none');

        // Mostrar loading nos sub-painéis
        ['detalhe-cabecalho-nfe', 'detalhe-cabecalho-sped', 'detalhe-impostos-nfe', 'detalhe-impostos-sped'].forEach(function (id) {
            const el = document.getElementById(id);
            if (el) el.innerHTML = '<span class="text-muted"><span class="spinner-reprocessamento" style="display:inline-block;width:1em;height:1em;"></span> Carregando...</span>';
        });
        document.getElementById('detalhe-itens-nfe') && (document.getElementById('detalhe-itens-nfe').innerHTML = '<tr><td colspan="5" class="text-muted text-center">Carregando...</td></tr>');
        document.getElementById('detalhe-itens-sped') && (document.getElementById('detalhe-itens-sped').innerHTML = '<tr><td colspan="5" class="text-muted text-center">Carregando...</td></tr>');
        document.getElementById('detalhe-confrontos') && (document.getElementById('detalhe-confrontos').innerHTML = '<tr><td colspan="4" class="text-muted text-center">Carregando...</td></tr>');

        // Resumo imediato com dados locais
        const campos = [
            { label: 'ID', value: d.id_divergencia },
            { label: 'Tipo', value: tipoDivergenciaLabel(d.tipo) },
            { label: 'Status', value: d.status === 'ABERTA' ? 'Aberta' : (d.status === 'RESOLVIDA' ? 'Resolvida' : d.status) },
            { label: 'Chave NF-e', value: d.chave_nfe || '—' },
            { label: 'Número', value: d.numero_nfe || '—' },
            { label: 'Série', value: d.serie_nfe || '—' },
            { label: 'Registro SPED', value: d.registro_sped || '—' },
            { label: 'Linha SPED', value: d.linha_sped != null ? d.linha_sped : '—' },
            { label: 'ID NF-e (sistema)', value: d.id_nfe != null ? d.id_nfe : '—' },
            { label: 'Valor esperado', value: d.valor_esperado != null ? d.valor_esperado : '—' },
            { label: 'Valor encontrado', value: d.valor_encontrado != null ? d.valor_encontrado : '—' },
            { label: 'Data criação', value: formatarDataHoraDetalhe(d.data_criacao) },
            { label: 'Data reprocessamento', value: formatarDataHoraDetalhe(d.data_reprocessamento) },
            { label: 'Usuário reprocessamento', value: d.usuario_reprocessamento || '—' },
        ];
        const tbody = document.getElementById('detalhe-campos');
        if (tbody) {
            tbody.innerHTML = campos.map(function (c) {
                return '<tr><td class="text-muted small pe-2">' + escapeHtml(c.label) + '</td><td class="small">' + escapeHtml(String(c.value)) + '</td></tr>';
            }).join('');
        }
        const descEl = document.getElementById('detalhe-descricao');
        if (descEl) descEl.textContent = d.descricao || '—';
        const jsonWrap = document.getElementById('detalhe-json-wrap');
        const jsonEl = document.getElementById('detalhe-json');
        if (d.detalhe_json && jsonWrap && jsonEl) {
            jsonEl.textContent = typeof d.detalhe_json === 'string' ? d.detalhe_json : JSON.stringify(d.detalhe_json, null, 2);
            jsonWrap.classList.remove('d-none');
        } else if (jsonWrap) jsonWrap.classList.add('d-none');

        const btnResolver = document.getElementById('btn-resolver-detalhe');
        if (btnResolver) {
            btnResolver.style.display = d.status === 'ABERTA' ? '' : 'none';
            btnResolver.onclick = function () { reprocessarDivergencia(d.id_divergencia); };
        }

        // Buscar detalhe completo via API
        fetch(apiUrl('api/reprocessamento/divergencias/' + d.id_divergencia + '/detalhe/'), { method: 'GET', credentials: 'same-origin' })
            .then(function (res) { return res.json(); })
            .then(function (data) {
                if (data.sucesso && data.detalhe) {
                    preencherSubAbasDetalhe(data.detalhe);
                } else {
                    ['detalhe-cabecalho-nfe', 'detalhe-cabecalho-sped'].forEach(function (id) {
                        const el = document.getElementById(id);
                        if (el) el.innerHTML = '<span class="text-danger">Erro ao carregar detalhes.</span>';
                    });
                }
            })
            .catch(function () {
                ['detalhe-cabecalho-nfe', 'detalhe-cabecalho-sped', 'detalhe-impostos-nfe', 'detalhe-impostos-sped'].forEach(function (id) {
                    const el = document.getElementById(id);
                    if (el) el.innerHTML = '<span class="text-danger">Erro ao carregar.</span>';
                });
                document.getElementById('detalhe-itens-nfe') && (document.getElementById('detalhe-itens-nfe').innerHTML = '<tr><td colspan="5" class="text-danger text-center">Erro</td></tr>');
                document.getElementById('detalhe-itens-sped') && (document.getElementById('detalhe-itens-sped').innerHTML = '<tr><td colspan="5" class="text-danger text-center">Erro</td></tr>');
                document.getElementById('detalhe-confrontos') && (document.getElementById('detalhe-confrontos').innerHTML = '<tr><td colspan="4" class="text-danger text-center">Erro</td></tr>');
            });

        // Ativar primeira sub-aba
        document.querySelectorAll('#detalhe-subtabs .nav-link').forEach(function (btn) { btn.classList.remove('active'); });
        document.querySelectorAll('#detalhe-subcontent .tab-pane').forEach(function (pane) { pane.classList.remove('show', 'active'); });
        const firstBtn = document.getElementById('subtab-resumo-btn');
        const firstPane = document.getElementById('subtab-resumo');
        if (firstBtn) firstBtn.classList.add('active');
        if (firstPane) firstPane.classList.add('show', 'active');
    }

    function voltarParaListaDivergencias() {
        document.getElementById('tab-detalhe-btn')?.style.setProperty('display', 'none');
        document.getElementById('divergencia-detalhe-panel')?.classList.add('d-none');
        ativarAbaDivergencias('tab-por-tipo');
    }

    /** Exibe empresa do lote (código e nome). */
    function formatarEmpresaLote(codEmpresa, nome) {
        const cod = escapeHtml(codEmpresa || '-');
        const desc = (nome || '').trim();
        if (desc) return '<span class="empresa-nome">' + escapeHtml(desc) + '</span><br><span class="small text-muted">' + cod + '</span>';
        return '<span class="empresa-cod">' + cod + '</span>';
    }

    function atualizarResumo(lotes) {
        const elResumo = document.getElementById('resumo-lotes');
        if (!elResumo) return;
        if (!lotes || lotes.length === 0) {
            elResumo.classList.add('d-none');
            return;
        }
        const total = lotes.length;
        const concluidos = lotes.filter(l => l.status === 'CONCLUIDO').length;
        const comDivergencias = lotes.filter(l => (l.total_divergencias || 0) > 0).length;
        const emAndamento = lotes.filter(l => l.status === 'EM_CONFRONTO' || l.status === 'PENDENTE').length;
        const rTotal = document.getElementById('resumo-total');
        const rConcluidos = document.getElementById('resumo-concluidos');
        const rDivergencias = document.getElementById('resumo-com-divergencias');
        const rAndamento = document.getElementById('resumo-em-andamento');
        if (rTotal) rTotal.textContent = total;
        if (rConcluidos) rConcluidos.textContent = concluidos;
        if (rDivergencias) rDivergencias.textContent = comDivergencias;
        if (rAndamento) rAndamento.textContent = emAndamento;
        elResumo.classList.remove('d-none');
    }

    function statusParaBadge(status) {
        const m = {
            PENDENTE: '<span class="badge bg-secondary">Pendente</span>',
            EM_CONFRONTO: '<span class="badge bg-info">Em confronto</span>',
            CONCLUIDO: '<span class="badge bg-success">Concluído</span>',
            ERRO: '<span class="badge bg-danger">Erro</span>',
            CANCELADO: '<span class="badge bg-dark">Cancelado</span>',
        };
        return m[status] || '<span class="badge bg-light text-dark">' + (status || '-') + '</span>';
    }

    function abrirModalDivergencias(idLote) {
        estado.loteSelecionadoId = idLote;
        const modal = document.getElementById('modal-divergencias');
        const titulo = document.getElementById('modal-divergencias-lote-id');
        const carregando = document.getElementById('divergencias-carregando');
        const porTipo = document.getElementById('divergencias-por-tipo');
        const vazio = document.getElementById('divergencias-vazio');
        if (titulo) titulo.textContent = '#' + idLote;
        if (modal) modal.style.display = 'block';
        if (carregando) carregando.classList.remove('d-none');
        if (porTipo) porTipo.classList.add('d-none');
        if (vazio) vazio.classList.add('d-none');
        fetch(apiUrl('api/reprocessamento/lotes/' + idLote + '/divergencias/'), { method: 'GET', credentials: 'same-origin' })
            .then(res => res.json())
            .then(data => {
                if (carregando) carregando.classList.add('d-none');
                if (!data.sucesso || !data.divergencias || data.divergencias.length === 0) {
                    if (vazio) vazio.classList.remove('d-none');
                    document.getElementById('divergencias-subtitulo')?.classList.add('d-none');
                    return;
                }
                const total = data.total != null ? data.total : data.divergencias.length;
                const subtitulo = document.getElementById('divergencias-subtitulo');
                const countEl = document.getElementById('divergencias-count');
                const totalEl = document.getElementById('divergencias-total');
                if (subtitulo && countEl && totalEl) {
                    countEl.textContent = data.divergencias.length;
                    totalEl.textContent = total;
                    subtitulo.classList.remove('d-none');
                }
                if (porTipo) porTipo.classList.remove('d-none');
                document.getElementById('divergencias-tabs')?.classList.remove('d-none');
                estado.divergenciasLista = data.divergencias;
                renderizarPorTipo(data.divergencias);
                ativarAbaDivergencias('tab-por-tipo');
                document.getElementById('tab-detalhe-btn')?.style.setProperty('display', 'none');
            })
            .catch(() => {
                if (carregando) carregando.classList.add('d-none');
                if (vazio) vazio.classList.remove('d-none');
            });
    }

    function reprocessarDivergencia(idDiv) {
        const csrf = getCsrfToken();
        fetch(apiUrl('api/reprocessamento/divergencias/' + idDiv + '/reprocessar/'), {
            method: 'POST',
            credentials: 'same-origin',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrf,
            },
            body: JSON.stringify({}),
        })
            .then(res => res.json())
            .then(data => {
                if (data.sucesso && typeof Notificacoes !== 'undefined') Notificacoes.pagina('Divergência marcada como resolvida.', 'success');
                if (estado.loteSelecionadoId) abrirModalDivergencias(estado.loteSelecionadoId);
            })
            .catch(() => {
                if (typeof Notificacoes !== 'undefined') Notificacoes.pagina('Erro ao reprocessar', 'danger');
            });
    }

    function abrirModalNovoConfronto() {
        const modal = document.getElementById('modal-novo-confronto');
        const d = new Date();
        const mesAtual = String(d.getMonth() + 1).padStart(2, '0');
        const anoAtual = d.getFullYear();

        const selMes = document.getElementById('confronto-mes');
        const selAno = document.getElementById('confronto-ano');
        if (selMes) selMes.value = mesAtual;
        if (selAno) {
            selAno.innerHTML = '';
            for (let a = anoAtual + 1; a >= anoAtual - 5; a--) {
                const opt = document.createElement('option');
                opt.value = a;
                opt.textContent = a;
                if (a === anoAtual) opt.selected = true;
                selAno.appendChild(opt);
            }
        }

        if (modal) modal.style.display = 'block';
    }

    function fecharModalNovoConfronto() {
        const modal = document.getElementById('modal-novo-confronto');
        if (modal) modal.style.display = 'none';
    }

    function executarConfronto() {
        const selEmpresa = document.getElementById('confronto-empresa');
        const selMes = document.getElementById('confronto-mes');
        const selAno = document.getElementById('confronto-ano');
        if (!selEmpresa || !selMes || !selAno) return;
        const cod_empresa = (selEmpresa.value || '').trim();
        const competencia = selAno.value + '-' + selMes.value;
        if (!cod_empresa) {
            if (typeof Notificacoes !== 'undefined') Notificacoes.pagina('Selecione a empresa.', 'warning');
            return;
        }
        const payload = { cod_empresa: cod_empresa, competencia: competencia };

        const csrf = getCsrfToken();
        const btn = document.getElementById('btn-executar-confronto');
        if (btn) btn.disabled = true;
        fetch(apiUrl('api/reprocessamento/confronto/'), {
            method: 'POST',
            credentials: 'same-origin',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrf,
            },
            body: JSON.stringify(payload),
        })
            .then(res => res.json())
            .then(data => {
                if (btn) btn.disabled = false;
                fecharModalNovoConfronto();
                if (data.sucesso) {
                    if (typeof Notificacoes !== 'undefined') {
                        Notificacoes.pagina(data.mensagem || 'Confronto iniciado.', 'success', {
                            acaoTexto: 'Atualizar painel',
                            acaoCallback: carregarLotes
                        });
                    }
                    carregarLotes();
                } else {
                    if (typeof Notificacoes !== 'undefined') Notificacoes.pagina(data.mensagem || 'Erro ao iniciar confronto', 'danger');
                }
            })
            .catch(() => {
                if (btn) btn.disabled = false;
                if (typeof Notificacoes !== 'undefined') Notificacoes.pagina('Erro ao iniciar confronto', 'danger');
            });
    }

    function fecharModalDivergencias() {
        const modal = document.getElementById('modal-divergencias');
        if (modal) modal.style.display = 'none';
    }

    function abrirModalCondicoes(idLote) {
        estado.condicoesLoteId = idLote;
        const modal = document.getElementById('modal-condicoes-pagamento');
        const titulo = document.getElementById('modal-condicoes-lote-id');
        if (titulo) titulo.textContent = '#' + idLote;
        if (modal) modal.style.display = 'block';
        carregarCondicoes(idLote);
    }

    function fecharModalCondicoes() {
        const modal = document.getElementById('modal-condicoes-pagamento');
        if (modal) modal.style.display = 'none';
        estado.condicoesLoteId = null;
    }

    function carregarCondicoes(idLote) {
        const carregando = document.getElementById('condicoes-carregando');
        const vazio = document.getElementById('condicoes-vazio');
        const wrap = document.getElementById('condicoes-tabela-wrap');
        const tbody = document.getElementById('tbody-condicoes-pagamento');
        const resumo = document.getElementById('condicoes-resumo');
        if (carregando) carregando.classList.remove('d-none');
        if (vazio) vazio.classList.add('d-none');
        if (wrap) wrap.classList.add('d-none');
        if (tbody) tbody.innerHTML = '';

        fetch(apiUrl('api/reprocessamento/lotes/' + idLote + '/condicoes-pagamento/'), { method: 'GET', credentials: 'same-origin' })
            .then(res => res.json())
            .then(data => {
                if (carregando) carregando.classList.add('d-none');
                if (!data.sucesso || !data.condicoes || data.condicoes.length === 0) {
                    if (vazio) vazio.classList.remove('d-none');
                    if (resumo) resumo.textContent = '';
                    return;
                }
                estado.condicoesLista = data.condicoes;
                if (resumo) resumo.textContent = data.condicoes.length + ' registro(s).';
                if (wrap) wrap.classList.remove('d-none');
                // Status: alinhado ao CondicaoPagamentoLote.STATUS_CHOICES (P, E, S, U, I, R) – cores distintas
                const statusCondicoesConfig = {
                    P: { cls: 'badge bg-secondary', lbl: 'Pendente', title: 'Aguardando envio ao SAP' },
                    E: { cls: 'badge bg-info', lbl: 'Enviado', title: 'Enviado ao SAP' },
                    S: { cls: 'badge bg-success', lbl: 'Processado', title: 'Processado no SAP' },
                    U: { cls: 'badge bg-primary', lbl: 'Atualizado (U)', title: 'Atualizado no SAP (U)' },
                    I: { cls: 'badge bg-success', lbl: 'Processado (I)', title: 'Processado no SAP (I)' },
                    R: { cls: 'badge bg-danger', lbl: 'Erro', title: 'Erro no processamento SAP' }
                };
                const statusBadge = function (s) {
                    var code = (s && String(s).trim().toUpperCase()) ? String(s).trim().toUpperCase().charAt(0) : 'P';
                    var cfg = statusCondicoesConfig[code] || { cls: 'badge bg-light text-dark', lbl: code || 'Pendente', title: code || 'Pendente' };
                    return '<span class="' + cfg.cls + '" title="' + escapeHtml(cfg.title) + '">' + escapeHtml(cfg.lbl) + '</span>';
                };
                const descTipo = function (cod) {
                    const m = window.TIPO_PAGAMENTO_DESC || {};
                    return (cod && m[String(cod)]) ? m[String(cod)] : (cod || '-');
                };
                data.condicoes.forEach(function (c) {
                    const tr = document.createElement('tr');
                    const chaveInteira = c.chave_nfe || '-';
                    const condSap = c.condicao_pagamento_sap || '-';
                    const tipoExibir = descTipo(c.tipo_pagamento);
                    tr.innerHTML =
                        '<td class="small font-monospace text-nowrap" title="' + escapeHtml(chaveInteira) + '">' + escapeHtml(chaveInteira) + '</td>' +
                        '<td class="small">' + escapeHtml(c.condicao_pagamento_nfe || '-') + '</td>' +
                        '<td class="small text-center" title="' + escapeHtml(c.tipo_pagamento || '') + '">' + escapeHtml(tipoExibir) + '</td>' +
                        '<td class="small">' + escapeHtml(condSap) + '</td>' +
                        '<td class="text-center">' + statusBadge(c.status) + '</td>';
                    tbody.appendChild(tr);
                });
            })
            .catch(function () {
                if (carregando) carregando.classList.add('d-none');
                if (vazio) vazio.classList.remove('d-none');
                if (typeof Notificacoes !== 'undefined') Notificacoes.pagina('Erro ao carregar condições', 'danger');
            });
    }

    function gerarCondicoes(idLote) {
        const btn = document.getElementById('btn-gerar-condicoes');
        if (btn) btn.disabled = true;
        const csrf = getCsrfToken();
        fetch(apiUrl('api/reprocessamento/lotes/' + idLote + '/condicoes-pagamento/gerar/'), {
            method: 'POST',
            credentials: 'same-origin',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf },
            body: JSON.stringify({}),
        })
            .then(res => res.json())
            .then(data => {
                if (btn) btn.disabled = false;
                if (data.sucesso) {
                    if (typeof Notificacoes !== 'undefined') Notificacoes.pagina(data.mensagem || 'Tabela gerada.', 'success');
                    carregarCondicoes(idLote);
                } else {
                    if (typeof Notificacoes !== 'undefined') Notificacoes.pagina(data.mensagem || 'Erro ao gerar', 'danger');
                }
            })
            .catch(function () {
                if (btn) btn.disabled = false;
                if (typeof Notificacoes !== 'undefined') Notificacoes.pagina('Erro ao gerar condições', 'danger');
            });
    }

    function abrirModalCondicaoParam() {
        const modal = document.getElementById('modal-condicao-param');
        const filtroTodos = document.getElementById('filtro-todos');
        const filtroTexto = document.getElementById('filtro-condicao-texto');
        const filtroTipo = document.getElementById('filtro-tipo-pagamento');
        if (modal) modal.style.display = 'block';
        if (filtroTodos) filtroTodos.checked = true;
        if (filtroTexto) filtroTexto.value = '';
        if (filtroTipo) filtroTipo.value = '';
        carregarCondicaoParam();
    }

    function fecharModalCondicaoParam() {
        const modal = document.getElementById('modal-condicao-param');
        if (modal) modal.style.display = 'none';
    }

    function carregarCondicaoParam() {
        const carregando = document.getElementById('condicao-param-carregando');
        const vazio = document.getElementById('condicao-param-vazio');
        const wrap = document.getElementById('condicao-param-tabela-wrap');
        const tbody = document.getElementById('tbody-condicao-param');
        if (carregando) carregando.classList.remove('d-none');
        if (vazio) vazio.classList.add('d-none');
        if (wrap) wrap.classList.add('d-none');
        if (tbody) tbody.innerHTML = '';

        fetch(apiUrl('api/reprocessamento/condicao-param/'), { method: 'GET', credentials: 'same-origin' })
            .then(res => res.json())
            .then(data => {
                if (carregando) carregando.classList.add('d-none');
                if (!data.sucesso || !data.condicoes || data.condicoes.length === 0) {
                    if (vazio) vazio.classList.remove('d-none');
                    return;
                }
                if (wrap) wrap.classList.remove('d-none');
                const descTipo = function (cod) {
                    const m = window.TIPO_PAGAMENTO_DESC || {};
                    return (cod && m[String(cod)]) ? m[String(cod)] : (cod || '-');
                };
                const tiposUnicos = {};
                data.condicoes.forEach(function (c) {
                    const tr = document.createElement('tr');
                    tr.setAttribute('data-id', c.id);
                    const sapVazio = !(c.condicao_pagamento_sap || '').trim();
                    tr.setAttribute('data-sap-vazio', sapVazio ? '1' : '0');
                    const valSap = String(c.condicao_pagamento_sap || '').replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
                    const tipoExibir = descTipo(c.tipo_pagamento);
                    const tipoCod = String(c.tipo_pagamento || '');
                    tiposUnicos[tipoCod] = tipoExibir;
                    tr.innerHTML =
                        '<td class="small text-center align-middle" title="' + escapeHtml(c.tipo_pagamento || '') + '" data-tipo="' + escapeHtml(tipoCod) + '">' + escapeHtml(tipoExibir) + '</td>' +
                        '<td class="small align-middle">' + escapeHtml(c.condicao_pagamento_nfe || '-') + '</td>' +
                        '<td><input type="text" class="form-control form-control-sm condicao-sap-input" data-id="' + c.id + '" value="' + valSap + '" maxlength="60" placeholder="Ex: Z001"></td>';
                    tbody.appendChild(tr);
                });
                const selTipo = document.getElementById('filtro-tipo-pagamento');
                if (selTipo) {
                    const opts = selTipo.querySelectorAll('option:not(:first-child)');
                    opts.forEach(function (o) { o.remove(); });
                    Object.keys(tiposUnicos).sort().forEach(function (cod) {
                        const opt = document.createElement('option');
                        opt.value = cod;
                        opt.textContent = tiposUnicos[cod] || cod || '-';
                        selTipo.appendChild(opt);
                    });
                }
                aplicarFiltroCondicaoParam();
                tbody.querySelectorAll('.condicao-sap-input').forEach(function (input) {
                    input.addEventListener('input', aplicarFiltroCondicaoParam);
                });
            })
            .catch(function () {
                if (carregando) carregando.classList.add('d-none');
                if (vazio) vazio.classList.remove('d-none');
                if (typeof Notificacoes !== 'undefined') Notificacoes.pagina('Erro ao carregar parâmetros', 'danger');
            });
    }

    function aplicarFiltroCondicaoParam() {
        const tipoFiltro = document.querySelector('input[name="filtro-condicao-tipo"]:checked');
        const texto = document.getElementById('filtro-condicao-texto');
        const selTipo = document.getElementById('filtro-tipo-pagamento');
        const tbody = document.getElementById('tbody-condicao-param');
        if (!tbody || !tipoFiltro) return;
        const valor = (tipoFiltro.value || '').trim();
        const termo = (texto && texto.value ? texto.value : '').trim().toLowerCase();
        const tipoPagSel = (selTipo && selTipo.value ? selTipo.value : '').trim();
        tbody.querySelectorAll('tr').forEach(function (tr) {
            const tdTipo = tr.querySelector('td:first-child');
            const tdNfe = tr.querySelector('td:nth-child(2)');
            const inputSap = tr.querySelector('.condicao-sap-input');
            const nfe = (tdNfe ? tdNfe.textContent : '').toLowerCase();
            const tipoTexto = (tdTipo ? tdTipo.textContent : '').toLowerCase();
            const tipoCod = (tdTipo && tdTipo.getAttribute('data-tipo')) ? tdTipo.getAttribute('data-tipo') : '';
            const sap = (inputSap ? (inputSap.value || '') : '').toLowerCase();
            const sapVazio = !inputSap || !(inputSap.value || '').trim();
            let show = true;
            if (valor === 'vazia') {
                show = sapVazio;
            } else if (valor === 'preenchida') {
                show = !sapVazio;
            }
            if (show && tipoPagSel && tipoCod !== tipoPagSel) {
                show = false;
            }
            if (show && termo) {
                show = nfe.indexOf(termo) >= 0 || tipoTexto.indexOf(termo) >= 0 || sap.indexOf(termo) >= 0;
            }
            tr.style.display = show ? '' : 'none';
        });
    }

    function salvarCondicaoParam() {
        const tbody = document.getElementById('tbody-condicao-param');
        if (!tbody) return;
        const itens = [];
        tbody.querySelectorAll('.condicao-sap-input').forEach(function (input) {
            const id = parseInt(input.getAttribute('data-id'), 10);
            if (!isNaN(id)) {
                itens.push({ id: id, condicao_pagamento_sap: (input.value || '').trim() });
            }
        });
        if (itens.length === 0) {
            if (typeof Notificacoes !== 'undefined') Notificacoes.pagina('Nenhum registro para salvar.', 'warning');
            return;
        }
        const btn = document.getElementById('btn-salvar-condicao-param');
        if (btn) btn.disabled = true;
        const csrf = getCsrfToken();
        fetch(apiUrl('api/reprocessamento/condicao-param/atualizar/'), {
            method: 'POST',
            credentials: 'same-origin',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf },
            body: JSON.stringify({ itens: itens }),
        })
            .then(res => res.json())
            .then(data => {
                if (btn) btn.disabled = false;
                if (data.sucesso) {
                    if (typeof Notificacoes !== 'undefined') Notificacoes.pagina(data.mensagem || 'Salvo com sucesso.', 'success');
                } else {
                    if (typeof Notificacoes !== 'undefined') Notificacoes.pagina(data.mensagem || 'Erro ao salvar', 'danger');
                }
            })
            .catch(function () {
                if (btn) btn.disabled = false;
                if (typeof Notificacoes !== 'undefined') Notificacoes.pagina('Erro ao salvar parâmetros', 'danger');
            });
    }

    function enviarCondicoesSap(idLote) {
        const btn = document.getElementById('btn-enviar-sap');
        if (btn) btn.disabled = true;
        const csrf = getCsrfToken();
        fetch(apiUrl('api/reprocessamento/lotes/' + idLote + '/condicoes-pagamento/enviar-sap/'), {
            method: 'POST',
            credentials: 'same-origin',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf },
            body: JSON.stringify({}),
        })
            .then(res => res.json())
            .then(data => {
                if (btn) btn.disabled = false;
                if (data.sucesso) {
                    if (typeof Notificacoes !== 'undefined') Notificacoes.pagina(data.mensagem || 'Enviado ao SAP.', 'success');
                    carregarCondicoes(idLote);
                } else {
                    if (typeof Notificacoes !== 'undefined') Notificacoes.pagina(data.mensagem || 'Erro ao enviar ao SAP', 'danger');
                }
            })
            .catch(function () {
                if (btn) btn.disabled = false;
                if (typeof Notificacoes !== 'undefined') Notificacoes.pagina('Erro ao enviar ao SAP', 'danger');
            });
    }

    document.addEventListener('DOMContentLoaded', function () {
        preencherAnosFiltro();
        carregarLotes();

        const btnNovo = document.getElementById('btn-novo-confronto');
        if (btnNovo) btnNovo.addEventListener('click', abrirModalNovoConfronto);
        const btnAtualizar = document.getElementById('btn-atualizar-lotes');
        if (btnAtualizar) btnAtualizar.addEventListener('click', carregarLotes);
        const btnAplicar = document.getElementById('btn-aplicar-filtros');
        if (btnAplicar) btnAplicar.addEventListener('click', carregarLotes);
        const btnLimpar = document.getElementById('btn-limpar-filtros');
        if (btnLimpar) btnLimpar.addEventListener('click', limparFiltros);

        document.querySelectorAll('.btn-atalho').forEach(function (btn) {
            btn.addEventListener('click', function () {
                const mes = this.getAttribute('data-mes');
                const ano = this.getAttribute('data-ano');
                const selMes = document.getElementById('filtro-mes');
                const selAno = document.getElementById('filtro-ano');
                const d = new Date();
                if (mes === '' || ano === '') {
                    if (selMes) selMes.value = '';
                    if (selAno) selAno.value = '';
                } else if (mes === 'este' && ano === 'este') {
                    if (selMes) selMes.value = String(d.getMonth() + 1).padStart(2, '0');
                    if (selAno) selAno.value = String(d.getFullYear());
                } else if (mes === 'passado' && ano === 'passado') {
                    d.setMonth(d.getMonth() - 1);
                    if (selMes) selMes.value = String(d.getMonth() + 1).padStart(2, '0');
                    if (selAno) selAno.value = String(d.getFullYear());
                }
                carregarLotes();
            });
        });

        document.getElementById('btn-fechar-modal-confronto')?.addEventListener('click', fecharModalNovoConfronto);
        document.getElementById('btn-cancelar-confronto')?.addEventListener('click', fecharModalNovoConfronto);
        document.getElementById('btn-executar-confronto')?.addEventListener('click', executarConfronto);
        document.getElementById('btn-fechar-modal-divergencias')?.addEventListener('click', fecharModalDivergencias);
        document.getElementById('btn-fechar-modal-condicoes')?.addEventListener('click', fecharModalCondicoes);
        document.getElementById('btn-gerar-condicoes')?.addEventListener('click', function () {
            if (estado.condicoesLoteId) gerarCondicoes(estado.condicoesLoteId);
        });
        document.getElementById('btn-abrir-condicao-param')?.addEventListener('click', abrirModalCondicaoParam);
        document.getElementById('btn-abrir-condicao-param-painel')?.addEventListener('click', abrirModalCondicaoParam);
        document.getElementById('btn-fechar-modal-condicao-param')?.addEventListener('click', fecharModalCondicaoParam);
        document.getElementById('btn-salvar-condicao-param')?.addEventListener('click', salvarCondicaoParam);
        document.getElementById('btn-enviar-sap')?.addEventListener('click', function () {
            if (estado.condicoesLoteId) enviarCondicoesSap(estado.condicoesLoteId);
        });
        const overlayCondicoes = document.getElementById('modal-condicoes-pagamento');
        if (overlayCondicoes) {
            overlayCondicoes.addEventListener('click', function (e) {
                if (e.target === overlayCondicoes) fecharModalCondicoes();
            });
        }
        const overlayCondicaoParam = document.getElementById('modal-condicao-param');
        if (overlayCondicaoParam) {
            overlayCondicaoParam.addEventListener('click', function (e) {
                if (e.target === overlayCondicaoParam) fecharModalCondicaoParam();
            });
        }
        document.querySelectorAll('input[name="filtro-condicao-tipo"]').forEach(function (r) {
            r.addEventListener('change', aplicarFiltroCondicaoParam);
        });
        document.getElementById('filtro-condicao-texto')?.addEventListener('input', aplicarFiltroCondicaoParam);
        document.getElementById('filtro-tipo-pagamento')?.addEventListener('change', aplicarFiltroCondicaoParam);
        document.getElementById('btn-voltar-lista')?.addEventListener('click', voltarParaListaDivergencias);
        document.getElementById('tab-por-tipo-btn')?.addEventListener('click', function () { ativarAbaDivergencias('tab-por-tipo'); });
        document.getElementById('tab-detalhe-btn')?.addEventListener('click', function () { ativarAbaDivergencias('tab-detalhe'); });
        function ativarSubAbaDetalhe(subtabId) {
            document.querySelectorAll('#detalhe-subtabs .nav-link').forEach(function (el) { el.classList.remove('active'); });
            document.querySelectorAll('#detalhe-subcontent .tab-pane').forEach(function (el) { el.classList.remove('show', 'active'); });
            const btn = document.getElementById(subtabId + '-btn');
            const pane = document.getElementById(subtabId);
            if (btn) btn.classList.add('active');
            if (pane) pane.classList.add('show', 'active');
        }
        document.getElementById('subtab-resumo-btn')?.addEventListener('click', function () { ativarSubAbaDetalhe('subtab-resumo'); });
        document.getElementById('subtab-cabecalho-btn')?.addEventListener('click', function () { ativarSubAbaDetalhe('subtab-cabecalho'); });
        document.getElementById('subtab-itens-btn')?.addEventListener('click', function () { ativarSubAbaDetalhe('subtab-itens'); });
        document.getElementById('subtab-impostos-btn')?.addEventListener('click', function () { ativarSubAbaDetalhe('subtab-impostos'); });
        document.getElementById('subtab-confrontos-btn')?.addEventListener('click', function () { ativarSubAbaDetalhe('subtab-confrontos'); });
        const overlayDivergencias = document.getElementById('modal-divergencias');
        if (overlayDivergencias) {
            overlayDivergencias.addEventListener('click', function (e) {
                if (e.target === overlayDivergencias) fecharModalDivergencias();
            });
        }
        const overlayConfronto = document.getElementById('modal-novo-confronto');
        if (overlayConfronto) {
            overlayConfronto.addEventListener('click', function (e) {
                if (e.target === overlayConfronto) fecharModalNovoConfronto();
            });
        }

    });
})();
