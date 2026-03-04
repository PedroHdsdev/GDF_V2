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
        fetch('/api/reprocessamento/lotes/' + (qs ? '?' + qs : ''), { method: 'GET', credentials: 'same-origin' })
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
                    const empresaExibir = formatarEmpresaLote(l.escopo_empresas, l.cod_empresa);
                    tr.innerHTML =
                        '<td class="text-center">' + l.id_lote + '</td>' +
                        '<td class="col-empresa">' + empresaExibir + '</td>' +
                        '<td class="text-center">' + competenciaExibir + '</td>' +
                        '<td class="text-end tab-num">' + (l.total_nfe_esperado ?? '-') + '</td>' +
                        '<td class="text-end tab-num">' + (l.total_nfe_encontrado ?? '-') + '</td>' +
                        '<td class="text-end tab-num">' + (divNum > 0 ? '<span class="badge bg-warning text-dark">' + divNum + '</span>' : divNum) + '</td>' +
                        '<td class="text-center">' + statusBadge + '</td>' +
                        '<td class="text-secondary small">' + dataCriacaoStr + '</td>' +
                        '<td class="text-center"><button type="button" class="btn btn-sm btn-outline-primary btn-ver-divergencias" data-id="' + l.id_lote + '" title="Ver divergências"><i class="fas fa-list-ul me-1"></i>Ver</button></td>';
                    tbody.appendChild(tr);
                });
                tbody.querySelectorAll('.btn-ver-divergencias').forEach(btn => {
                    btn.addEventListener('click', function () {
                        abrirModalDivergencias(parseInt(this.getAttribute('data-id'), 10));
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

    /** Exibe empresa conforme escopo: Todas as empresas, Várias empresas ou código da empresa. */
    function formatarEmpresaLote(escopo, codEmpresa) {
        const cod = escapeHtml(codEmpresa || '-');
        if (escopo === 'TODAS') {
            return '<span class="badge bg-primary me-1">Todas as empresas</span><br><span class="small text-muted">' + cod + '</span>';
        }
        if (escopo === 'VARIAS') {
            return '<span class="badge bg-info text-dark me-1">Várias empresas</span><br><span class="small text-muted">' + cod + '</span>';
        }
        return '<span class="cod-empresa">' + cod + '</span>';
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
        const lista = document.getElementById('divergencias-lista');
        const vazio = document.getElementById('divergencias-vazio');
        const tbody = document.getElementById('tbody-divergencias');
        if (titulo) titulo.textContent = '#' + idLote;
        if (modal) modal.style.display = 'block';
        if (carregando) carregando.classList.remove('d-none');
        if (lista) lista.classList.add('d-none');
        if (vazio) vazio.classList.add('d-none');
        if (tbody) tbody.innerHTML = '';

        fetch('/api/reprocessamento/lotes/' + idLote + '/divergencias/', { method: 'GET', credentials: 'same-origin' })
            .then(res => res.json())
            .then(data => {
                if (carregando) carregando.classList.add('d-none');
                if (!data.sucesso || !data.divergencias || data.divergencias.length === 0) {
                    if (vazio) vazio.classList.remove('d-none');
                    return;
                }
                if (lista) lista.classList.remove('d-none');
                data.divergencias.forEach(d => {
                    const tr = document.createElement('tr');
                    const btnResolver = d.status === 'ABERTA'
                        ? '<button type="button" class="btn btn-sm btn-success btn-resolver-div" data-id="' + d.id_divergencia + '"><i class="fas fa-check me-1"></i>Resolver</button>'
                        : '<span class="badge bg-secondary">' + (d.status === 'RESOLVIDA' ? 'Resolvida' : d.status) + '</span>';
                    const tipoLabel = tipoDivergenciaLabel(d.tipo);
                    const desc = (d.descricao || '-');
                    const descShort = desc.length > 80 ? desc.substring(0, 80) + '…' : desc;
                    tr.innerHTML =
                        '<td><span class="badge bg-light text-dark border">' + escapeHtml(tipoLabel) + '</span></td>' +
                        '<td><code class="small">' + escapeHtml(d.chave_nfe || d.numero_nfe || '-') + '</code></td>' +
                        '<td class="small">' + escapeHtml(descShort) + '</td>' +
                        '<td class="text-center">' + btnResolver + '</td>';
                    tbody.appendChild(tr);
                });
                tbody.querySelectorAll('.btn-resolver-div').forEach(btn => {
                    btn.addEventListener('click', function () {
                        reprocessarDivergencia(parseInt(this.getAttribute('data-id'), 10));
                    });
                });
            })
            .catch(() => {
                if (carregando) carregando.classList.add('d-none');
                if (vazio) vazio.classList.remove('d-none');
            });
    }

    function reprocessarDivergencia(idDiv) {
        const csrf = getCsrfToken();
        fetch('/api/reprocessamento/divergencias/' + idDiv + '/reprocessar/', {
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

        const todasCheck = document.getElementById('confronto-todas-empresas');
        const listaEmpresas = document.getElementById('confronto-lista-empresas');
        if (todasCheck && listaEmpresas) {
            if (todasCheck.checked) {
                listaEmpresas.style.display = 'none';
            } else {
                listaEmpresas.style.display = 'block';
            }
        }
        if (modal) modal.style.display = 'block';
    }

    function fecharModalNovoConfronto() {
        const modal = document.getElementById('modal-novo-confronto');
        if (modal) modal.style.display = 'none';
    }

    function executarConfronto() {
        const todasCheck = document.getElementById('confronto-todas-empresas');
        const selMes = document.getElementById('confronto-mes');
        const selAno = document.getElementById('confronto-ano');
        if (!selMes || !selAno) return;
        const competencia = selAno.value + '-' + selMes.value;

        let payload;
        if (todasCheck && todasCheck.checked) {
            payload = { todas_empresas: true, competencia: competencia };
        } else {
            const checkboxes = document.querySelectorAll('.confronto-empresa-cb:checked');
            const cod_empresas = Array.from(checkboxes).map(cb => cb.value);
            if (cod_empresas.length === 0) {
                if (typeof Notificacoes !== 'undefined') Notificacoes.pagina('Marque "Todas as empresas" ou selecione ao menos uma empresa.', 'warning');
                return;
            }
            payload = { cod_empresas: cod_empresas, competencia: competencia };
        }

        const csrf = getCsrfToken();
        const btn = document.getElementById('btn-executar-confronto');
        if (btn) btn.disabled = true;
        fetch('/api/reprocessamento/confronto/', {
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
                    if (typeof Notificacoes !== 'undefined') Notificacoes.pagina(data.mensagem || 'Confronto iniciado.', 'success');
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

        const todasCheck = document.getElementById('confronto-todas-empresas');
        const listaEmpresas = document.getElementById('confronto-lista-empresas');
        if (todasCheck && listaEmpresas) {
            todasCheck.addEventListener('change', function () {
                listaEmpresas.style.display = this.checked ? 'none' : 'block';
            });
        }
        const selTodas = document.getElementById('confronto-sel-todas');
        if (selTodas) {
            selTodas.addEventListener('change', function () {
                document.querySelectorAll('.confronto-empresa-cb').forEach(cb => { cb.checked = selTodas.checked; });
            });
        }
    });
})();
