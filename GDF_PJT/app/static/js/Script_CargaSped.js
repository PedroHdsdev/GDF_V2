/* Carga SPED - mesma linha de raciocínio da Carga XML */
const estadoSped = {
    todosJobs: [],
    arquivosManuais: [],
    avisosAtuaisIds: []
};

function formatJobDateTimeLocal(iso, detailed) {
    if (!iso) return '-';
    try {
        var d = new Date(iso);
        if (isNaN(d.getTime())) return iso;
        return d.toLocaleString('pt-BR', detailed
            ? { dateStyle: 'short', timeStyle: 'medium' }
            : { dateStyle: 'short', timeStyle: 'short' });
    } catch (e) {
        return iso;
    }
}

function cargaSpedEscHtml(s) {
    const d = document.createElement('div');
    d.textContent = s == null ? '' : String(s);
    return d.innerHTML;
}

function cargaSpedEscAttr(s) {
    return String(s == null ? '' : s)
        .replace(/&/g, '&amp;')
        .replace(/"/g, '&quot;')
        .replace(/</g, '&lt;');
}

function obterCsrfToken() {
    const t = document.querySelector('[name=csrfmiddlewaretoken]');
    return t ? t.value : '';
}

function getApiBase() {
    var el = document.querySelector('.layout-page[data-url-prefix], [data-url-prefix]');
    var prefix = (el && el.getAttribute('data-url-prefix')) || '';
    if (!prefix && typeof getUrlPrefix === 'function') prefix = getUrlPrefix();
    return prefix || '';
}

var intervaloResumoSped = null;

function carregarResumoCargaSped() {
    fetch(getApiBase() + '/api/cargasped/resumo/', { method: 'GET', headers: { 'X-CSRFToken': obterCsrfToken() } })
        .then(function (r) { return r.json(); })
        .then(function (data) {
            if (!data.sucesso) return;
            var elTotal = document.getElementById('resumo-sped-total');
            var elConcluidos = document.getElementById('resumo-sped-concluidos');
            var elErros = document.getElementById('resumo-sped-com-erros');
            var elAndamento = document.getElementById('resumo-sped-em-andamento');
            if (elTotal) elTotal.textContent = data.total || 0;
            if (elConcluidos) elConcluidos.textContent = data.concluidos || 0;
            if (elErros) elErros.textContent = data.com_erros || 0;
            if (elAndamento) elAndamento.textContent = data.em_andamento || 0;
            if (data.em_andamento > 0 && !intervaloResumoSped) {
                intervaloResumoSped = setInterval(function () {
                    carregarResumoCargaSped();
                    carregarJobsCargaSped();
                }, 3000);
            } else if (data.em_andamento === 0 && intervaloResumoSped) {
                clearInterval(intervaloResumoSped);
                intervaloResumoSped = null;
            }
        })
        .catch(function () {});
}

/* Avisos CargaSped – badge só para avisos não vistos */
var AVISOS_CARGASPED_VISTOS_KEY = 'gdf_cargasped_avisos_vistos';
var AVISOS_CARGASPED_VISTOS_MAX = 500;

function getAvisosCargaSpedVistos() {
    try {
        var raw = localStorage.getItem(AVISOS_CARGASPED_VISTOS_KEY);
        var arr = raw ? JSON.parse(raw) : [];
        return new Set((arr || []).map(Number).filter(Boolean));
    } catch (e) { return new Set(); }
}

function marcarAvisosCargaSpedComoVistos(ids) {
    if (!ids || ids.length === 0) return;
    try {
        var arr = [];
        try {
            var raw = localStorage.getItem(AVISOS_CARGASPED_VISTOS_KEY);
            if (raw) arr = JSON.parse(raw);
        } catch (e) {}
        ids.forEach(function (id) { arr.push(Number(id)); });
        arr = Array.from(new Set(arr)).slice(-AVISOS_CARGASPED_VISTOS_MAX);
        localStorage.setItem(AVISOS_CARGASPED_VISTOS_KEY, JSON.stringify(arr));
    } catch (e) {}
}

function carregarAvisosCargaSped(preencherModal) {
    fetch(getApiBase() + '/api/cargasped/avisos/', {
        method: 'GET',
        headers: { 'X-CSRFToken': obterCsrfToken() },
    })
        .then(function (r) { return r.json(); })
        .then(function (data) {
            var items = (data.sucesso && data.items) ? data.items : [];
            var vistos = getAvisosCargaSpedVistos();
            var naoVistos = items.filter(function (j) { return !vistos.has(Number(j.id)); });
            var totalNaoVistos = naoVistos.length;

            var badge = document.getElementById('avisos-badge-cargasped');
            if (badge) {
                if (totalNaoVistos > 0) {
                    badge.textContent = totalNaoVistos > 99 ? '99+' : totalNaoVistos;
                    badge.style.display = 'inline-block';
                } else {
                    badge.style.display = 'none';
                }
            }
            if (preencherModal) {
                preencherModalAvisosCargaSped(items);
                marcarAvisosCargaSpedComoVistos(items.map(function (j) { return j.id; }));
            }
            if (items.length > 0) {
                renderizarLogsResumoSped(items);
            } else {
                renderizarLogsResumoSped([]);
            }
        })
        .catch(function () {
            var badge = document.getElementById('avisos-badge-cargasped');
            if (badge) badge.style.display = 'none';
        });
}

function preencherModalAvisosCargaSped(items) {
    var emptyEl = document.getElementById('modal-avisos-cargasped-empty');
    var listEl = document.getElementById('modal-avisos-cargasped-list');
    if (!emptyEl || !listEl) return;
    estadoSped.avisosAtuaisIds = items.map(function (j) { return j.id; });
    if (items.length === 0) {
        emptyEl.style.display = 'block';
        listEl.style.display = 'none';
        listEl.innerHTML = '';
        var btnJaLido = document.getElementById('btn-avisos-ja-lido-sped');
        if (btnJaLido) { btnJaLido.disabled = true; btnJaLido.style.visibility = 'hidden'; }
        return;
    }
    emptyEl.style.display = 'none';
    listEl.style.display = 'block';
    function escapeHtml(s) {
        return (s || '').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    }
    function classForLogLine(line) {
        var t = (line || '').trim();
        if (t.indexOf('ERRO:') === 0) return 'aviso-log-erro';
        if (t.indexOf('PENDENTES') === 0) return 'aviso-log-pendente';
        if (t.indexOf('OK:') === 0) return 'aviso-log-ok';
        return 'aviso-log-outro';
    }
    var html = '';
    items.forEach(function (job, index) {
        var totalErro = job.total_erro || 0;
        var totalOk = job.total_sucesso || 0;
        var logLines = (job.log && job.log.length) ? job.log : [];
        if (logLines.length === 0 && (job.mensagem || '').trim()) {
            logLines = (job.mensagem || '').trim().split(/\r?\n/).map(function (l) { return l.trim(); }).filter(Boolean);
        }
        // Nos detalhes do aviso mostrar só erros e pendentes (não mostrar OK)
        logLines = logLines.filter(function (l) {
            var t = (l || '').trim();
            return t.indexOf('OK:') !== 0;
        });
        var logHtml = '';
        if (logLines.length) {
            logHtml = '<div class="aviso-dados-adicionais">';
            logHtml += '<div class="aviso-dados-titulo small fw-600 text-uppercase text-muted mb-2">Erros e pendentes</div>';
            logHtml += '<div class="aviso-log-lines">';
            logLines.forEach(function (l) {
                var cssClass = classForLogLine(l);
                logHtml += '<div class="aviso-log-line ' + cssClass + '">' + escapeHtml(l) + '</div>';
            });
            logHtml += '</div></div>';
        } else {
            logHtml = '<div class="aviso-dados-adicionais"><div class="text-muted small">Sem log</div></div>';
        }
        var bodyVisible = index === 0;
        html += '<div class="aviso-item layout-subcard">';
        html += '  <div class="aviso-item-header d-flex justify-content-between align-items-center" role="button" tabindex="0">';
        html += '    <span class="aviso-item-info"><strong>Job #' + job.id + '</strong> &middot; ' + formatJobDateTimeLocal(job.started_at, false) + ' <span class="text-muted small ms-1">(clique para ' + (bodyVisible ? 'recolher' : 'expandir') + ')</span></span>';
        html += '    <span class="d-flex align-items-center gap-2">';
        if (totalOk > 0) html += '<span class="badge aviso-badge-ok">' + totalOk + ' OK</span>';
        html += '<span class="badge aviso-badge-erro">' + totalErro + ' erro(s)</span> <i class="fas fa-chevron-' + (bodyVisible ? 'down' : 'right') + ' aviso-chevron small"></i></span>';
        html += '  </div>';
        html += '  <div class="aviso-item-body ' + (bodyVisible ? '' : 'd-none') + '">' + logHtml + '</div>';
        html += '</div>';
    });
    listEl.innerHTML = html;
    var btnJaLido = document.getElementById('btn-avisos-ja-lido-sped');
    if (btnJaLido) {
        btnJaLido.disabled = false;
        btnJaLido.style.visibility = 'visible';
    }
    listEl.querySelectorAll('.aviso-item-header').forEach(function (header) {
        header.addEventListener('click', function () {
            var card = header.closest('.aviso-item');
            var body = card.querySelector('.aviso-item-body');
            var chevron = header.querySelector('.aviso-chevron');
            if (!body || !chevron) return;
            body.classList.toggle('d-none');
            chevron.classList.toggle('fa-chevron-right');
            chevron.classList.toggle('fa-chevron-down');
            var spanHint = header.querySelector('.aviso-item-info .text-muted');
            if (spanHint) spanHint.textContent = body.classList.contains('d-none') ? ' (clique para expandir)' : ' (clique para recolher)';
        });
        header.addEventListener('keydown', function (e) {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                header.click();
            }
        });
        });
}

/* ===============================
   JOBS – Em execução / Já executado (containers tipo Home)
================================ */
function carregarJobsCargaSped() {
    fetch(getApiBase() + '/api/cargasped/jobs/', { method: 'GET', headers: { 'X-CSRFToken': obterCsrfToken() } })
        .then(function (r) {
            return r.json().then(function (data) { return { status: r.status, data: data }; });
        })
        .then(function (out) {
            var data = out.data;
            if (out.status === 403) {
                estadoSped.todosJobs = [];
            } else if (data.sucesso && data.items && data.items.length > 0) {
                estadoSped.todosJobs = data.items.map(function (j) {
                    var totalArq = j.total_arquivos || 0;
                    var sucesso = j.total_sucesso || 0;
                    var erro = j.total_erro || 0;
                    var resumo = totalArq > 0 ? sucesso + '\u2713/' + erro + '\u2717' : '-';
                    return {
                        id: j.id,
                        status: j.status,
                        resumo: totalArq + ' arquivo(s) - ' + resumo,
                        tipo: 'Manual',
                        started_at: j.started_at
                    };
                });
            } else {
                estadoSped.todosJobs = [];
            }
            renderizarEmExecucaoSped();
            renderizarJaExecutadoSped();
        })
        .catch(function () {
            estadoSped.todosJobs = [];
            renderizarEmExecucaoSped();
            renderizarJaExecutadoSped();
        });
}

function renderizarEmExecucaoSped() {
    var lista = document.getElementById('lista-em-execucao-sped');
    if (!lista) return;
    var emExecucao = estadoSped.todosJobs.filter(function (c) {
        var s = (c.status || '').toUpperCase();
        return s === 'RUNNING' || s === 'PENDING';
    });
    lista.innerHTML = '';
    if (emExecucao.length === 0) {
        lista.innerHTML = '<li class="cargaxml-lista-empty text-muted py-3 text-center"><i class="fas fa-check-circle fa-2x mb-2 d-block opacity-50"></i>Nenhum job em execução no momento.</li>';
        return;
    }
    emExecucao.forEach(function (carga) {
        var li = document.createElement('li');
        li.className = 'home-activity-item cargaxml-job-item';
        li.style.cursor = 'pointer';
        li.setAttribute('data-job-id', carga.id);
        var dataStr = carga.started_at ? formatJobDateTimeLocal(carga.started_at, false) : '-';
        li.innerHTML = '<span class="home-activity-type home-activity-type-xml">' + cargaSpedEscHtml(carga.tipo || 'SPED') + '</span>' +
            '<div class="home-activity-detail">' +
            '<span class="home-activity-status home-activity-status-running">Em execução</span>' +
            '<span class="home-activity-meta">' + cargaSpedEscHtml(carga.resumo || '') + '</span></div>' +
            '<div class="home-activity-time">' + cargaSpedEscHtml(dataStr) + '</div>' +
            '<a href="#" class="home-activity-link" data-job-id="' + cargaSpedEscAttr(carga.id) + '" title="Ver detalhes">\u2192</a>';
        li.addEventListener('click', function (e) {
            e.preventDefault();
            abrirModalJobSped(carga.id);
        });
        var link = li.querySelector('a.home-activity-link');
        if (link) link.addEventListener('click', function (e) { e.preventDefault(); abrirModalJobSped(carga.id); });
        lista.appendChild(li);
    });
}

function renderizarJaExecutadoSped() {
    var lista = document.getElementById('lista-ja-executado-sped');
    if (!lista) return;
    var jaExecutado = estadoSped.todosJobs.filter(function (c) {
        var s = (c.status || '').toUpperCase();
        return s === 'SUCCESS' || s === 'ERROR';
    }).slice(0, 25);
    lista.innerHTML = '';
    if (jaExecutado.length === 0) {
        lista.innerHTML = '<li class="cargaxml-lista-empty text-muted py-3 text-center"><i class="fas fa-inbox fa-2x mb-2 d-block opacity-50"></i>Nenhuma execução recente.</li>';
        return;
    }
    jaExecutado.forEach(function (carga) {
        var li = document.createElement('li');
        li.className = 'home-activity-item cargaxml-job-item';
        li.style.cursor = 'pointer';
        var statusClass = (carga.status || '').toUpperCase() === 'ERROR' ? 'home-activity-status-error' : 'home-activity-status-success';
        var dataStr = carga.started_at ? formatJobDateTimeLocal(carga.started_at, false) : '-';
        li.innerHTML = '<span class="home-activity-type home-activity-type-xml">' + cargaSpedEscHtml(carga.tipo || 'SPED') + '</span>' +
            '<div class="home-activity-detail">' +
            '<span class="home-activity-status ' + statusClass + '">' + (carga.status === 'SUCCESS' ? 'Concluído' : 'Erro') + '</span>' +
            '<span class="home-activity-meta">' + cargaSpedEscHtml(carga.resumo || '') + '</span></div>' +
            '<div class="home-activity-time">' + cargaSpedEscHtml(dataStr) + '</div>' +
            '<a href="#" class="home-activity-link" data-job-id="' + cargaSpedEscAttr(carga.id) + '" title="Ver log">\u2192</a>';
        li.addEventListener('click', function (e) {
            e.preventDefault();
            abrirModalJobSped(carga.id);
        });
        var linkJa = li.querySelector('a.home-activity-link');
        if (linkJa) linkJa.addEventListener('click', function (e) { e.preventDefault(); abrirModalJobSped(carga.id); });
        lista.appendChild(li);
    });
}

function renderizarLogsResumoSped(items) {
    var emptyEl = document.getElementById('logs-resumo-empty-sped');
    var contentEl = document.getElementById('logs-resumo-content-sped');
    if (!emptyEl || !contentEl) return;
    if (!items || items.length === 0) {
        emptyEl.style.display = 'block';
        contentEl.style.display = 'none';
        contentEl.innerHTML = '';
        return;
    }
    emptyEl.style.display = 'none';
    contentEl.style.display = 'block';
    function classLog(line) {
        var t = (line || '').trim();
        if (t.indexOf('ERRO:') === 0) return 'aviso-log-erro';
        if (t.indexOf('PENDENTES') === 0) return 'aviso-log-pendente';
        if (t.indexOf('OK:') === 0) return 'aviso-log-ok';
        return 'aviso-log-outro';
    }
    var html = '';
    items.slice(0, 3).forEach(function (job) {
        var logLines = (job.log && job.log.length) ? job.log.filter(function (l) {
            var t = (l || '').trim();
            return t.indexOf('ERRO:') === 0 || t.indexOf('PENDENTES') === 0;
        }).slice(0, 5) : [];
        html += '<div class="cargaxml-log-job mb-3">';
        html += '<div class="small fw-600 text-secondary mb-1">Job #' + job.id + ' \u00b7 ' + formatJobDateTimeLocal(job.started_at, false) + '</div>';
        if (logLines.length === 0) {
            html += '<div class="small text-muted">Sem linhas de log</div>';
        } else {
            logLines.forEach(function (l) {
                html += '<div class="cargaxml-log-line ' + classLog(l) + '">' + cargaSpedEscHtml(l) + '</div>';
            });
        }
        html += '</div>';
    });
    contentEl.innerHTML = html;
}

function abrirModalJobSped(jobId) {
    if (!jobId) return;
    var expectedId = Number(jobId);
    fetch(getApiBase() + '/api/cargasped/jobs/' + jobId + '/', { method: 'GET', headers: { 'X-CSRFToken': obterCsrfToken() } })
        .then(function (r) { return r.json(); })
        .then(function (data) {
            if (!data.sucesso || !data.job) return;
            if (Number(data.job.id) !== expectedId) return;
            var job = data.job;
            var logLines = data.log || [];
            document.getElementById('modal-sped-job-id').textContent = job.id;
            document.getElementById('modal-sped-job-status').textContent = job.status || '-';
            var elS = document.getElementById('modal-sped-job-started');
            var elF = document.getElementById('modal-sped-job-finished');
            if (elS) {
                elS.textContent = formatJobDateTimeLocal(job.started_at, true);
                elS.title = job.started_at ? ('Registro em UTC (API): ' + job.started_at) : '';
            }
            if (elF) {
                elF.textContent = formatJobDateTimeLocal(job.finished_at, true);
                elF.title = job.finished_at ? ('Registro em UTC (API): ' + job.finished_at) : '';
            }
            document.getElementById('modal-sped-job-log').textContent = logLines.length ? logLines.join('\n') : 'Sem log.';
            var modal = document.getElementById('modalJobDetailsSped');
            if (modal && typeof bootstrap !== 'undefined' && bootstrap.Modal) {
                var inst = bootstrap.Modal.getOrCreateInstance(modal);
                inst.show();
            }
        })
        .catch(function () {});
}

var TAMANHO_LOTE_CARGA_SPED = 100;

function enviarUmLoteSped(arquivosLote, apiUrl, csrfToken, jobId, ultimoLote) {
    var fd = new FormData();
    arquivosLote.forEach(function (f) { fd.append('arquivo', f); });
    if (jobId) fd.append('job_id', String(jobId));
    if (ultimoLote) fd.append('ultimo_lote', '1');
    return fetch(apiUrl, {
        method: 'POST',
        headers: { 'X-CSRFToken': csrfToken },
        body: fd
    }).then(function (r) {
        return r.text().then(function (text) {
            var data;
            try { data = text ? JSON.parse(text) : {}; } catch (e) { data = {}; }
            return { status: r.status, data: data };
        });
    });
}

function fecharModalELimparArquivosSped() {
    estadoSped.arquivosManuais = [];
    var contador = document.getElementById('contador-sped');
    if (contador) contador.textContent = '0';
    var fileInput = document.getElementById('file-input-sped');
    var fileInputPasta = document.getElementById('file-input-sped-pasta');
    if (fileInput) fileInput.value = '';
    if (fileInputPasta) fileInputPasta.value = '';
    var modal = document.getElementById('modalCargaSped');
    if (modal && typeof bootstrap !== 'undefined' && bootstrap.Modal) {
        var inst = bootstrap.Modal.getInstance(modal);
        if (inst) inst.hide();
    }
    carregarResumoCargaSped();
    carregarJobsCargaSped();
    carregarAvisosCargaSped();
}

function enviarArquivosManuais() {
    if (estadoSped.arquivosManuais.length === 0) {
        Notificacoes.modal('Selecione ao menos um arquivo .txt', 'warning', 'modalCargaSpedAlerts');
        return;
    }
    var arquivos = estadoSped.arquivosManuais;
    var total = arquivos.length;
    var usarLotes = total > TAMANHO_LOTE_CARGA_SPED;
    var apiUrl = getApiBase() + '/api/processar-sped/';
    var csrfToken = obterCsrfToken();
    if (typeof window.getCsrfToken === 'function') csrfToken = csrfToken || window.getCsrfToken();
    var btn = document.getElementById('btn-enviar-sped');
    btn.disabled = true;

    if (usarLotes) {
        var lotes = [];
        for (var i = 0; i < total; i += TAMANHO_LOTE_CARGA_SPED) {
            lotes.push(arquivos.slice(i, i + TAMANHO_LOTE_CARGA_SPED));
        }
        var numLotes = lotes.length;
        var loteAtual = 0;
        var jobIdUnico = null;
        function enviarProximoLote() {
            if (loteAtual >= numLotes) {
                btn.disabled = false;
                Notificacoes.modal('Job #' + (jobIdUnico || '') + ' criado com ' + total + ' arquivo(s). Atualize o painel.', 'success', 'modalCargaSpedAlerts');
                fecharModalELimparArquivosSped();
                return;
            }
            var ehUltimoLote = (loteAtual === numLotes - 1);
            enviarUmLoteSped(lotes[loteAtual], apiUrl, csrfToken, jobIdUnico || null, ehUltimoLote)
                .then(function (result) {
                    if (result.status === 413) {
                        btn.disabled = false;
                        Notificacoes.modal(result.data.mensagem || 'Arquivo(s) muito grande (413). Configure Nginx.', 'danger', 'modalCargaSpedAlerts');
                        return;
                    }
                    if (result.status === 400) {
                        btn.disabled = false;
                        Notificacoes.modal((result.data && result.data.mensagem) ? result.data.mensagem : 'Erro 400.', 'danger', 'modalCargaSpedAlerts');
                        return;
                    }
                    if (result.status !== 200 && result.status !== 202) {
                        btn.disabled = false;
                        Notificacoes.modal((result.data && result.data.mensagem) ? result.data.mensagem : 'Erro no lote.', 'danger', 'modalCargaSpedAlerts');
                        return;
                    }
                    if (result.data && result.data.job_id) jobIdUnico = result.data.job_id;
                    loteAtual++;
                    enviarProximoLote();
                })
                .catch(function (err) {
                    btn.disabled = false;
                    Notificacoes.modal('Erro ao enviar lote: ' + (err.message || 'Falha na rede.'), 'danger', 'modalCargaSpedAlerts');
                });
        }
        enviarProximoLote();
        return;
    }

    enviarUmLoteSped(arquivos, apiUrl, csrfToken, null, true)
        .then(function (result) {
            btn.disabled = false;
            if (result.status === 413) {
                Notificacoes.modal(result.data.mensagem || 'Arquivo(s) muito grande (413).', 'danger', 'modalCargaSpedAlerts');
                return;
            }
            if (result.status === 400) {
                Notificacoes.modal((result.data && result.data.mensagem) ? result.data.mensagem : 'Requisição inválida.', 'danger', 'modalCargaSpedAlerts');
                return;
            }
            var data = result.data;
            Notificacoes.modal(data.mensagem || (data.sucesso ? 'Job em execução.' : 'Erro.'), data.sucesso ? 'success' : 'danger', 'modalCargaSpedAlerts');
            if (data.sucesso) fecharModalELimparArquivosSped();
        })
        .catch(function () {
            btn.disabled = false;
            Notificacoes.modal('Erro na requisição.', 'danger', 'modalCargaSpedAlerts');
        });
}

document.addEventListener('DOMContentLoaded', function () {
    carregarResumoCargaSped();
    carregarJobsCargaSped();
    carregarAvisosCargaSped();

    var btnAtualizarResumo = document.getElementById('btn-atualizar-resumo-sped');
    if (btnAtualizarResumo) btnAtualizarResumo.addEventListener('click', function () {
        carregarResumoCargaSped();
        carregarJobsCargaSped();
        carregarAvisosCargaSped();
    });

    var modalAvisos = document.getElementById('modalAvisosCargaSped');
    if (modalAvisos) {
        modalAvisos.addEventListener('show.bs.modal', function () {
            carregarAvisosCargaSped(true);
        });
    }
    var btnAvisosJaLidoSped = document.getElementById('btn-avisos-ja-lido-sped');
    if (btnAvisosJaLidoSped) {
        btnAvisosJaLidoSped.addEventListener('click', function () {
            var ids = estadoSped.avisosAtuaisIds || [];
            if (ids.length === 0) return;
            marcarAvisosCargaSpedComoVistos(ids);
            var badge = document.getElementById('avisos-badge-cargasped');
            if (badge) {
                badge.style.display = 'none';
                badge.textContent = '0';
            }
            if (typeof Notificacoes !== 'undefined' && Notificacoes.pagina) {
                Notificacoes.pagina('Avisos marcados como lidos.', 'success');
            }
        });
    }

    var fileInput = document.getElementById('file-input-sped');
    var fileInputPasta = document.getElementById('file-input-sped-pasta');
    if (fileInput) {
        fileInput.addEventListener('click', function () { this.value = ''; });
        fileInput.addEventListener('change', function () {
            var files = Array.from(this.files || []).filter(function (f) { return (f.name || '').toLowerCase().endsWith('.txt'); });
            estadoSped.arquivosManuais = files;
            var cont = document.getElementById('contador-sped');
            if (cont) cont.textContent = files.length;
        });
    }
    if (fileInputPasta) {
        fileInputPasta.addEventListener('click', function () { this.value = ''; });
        fileInputPasta.addEventListener('change', function () {
            var files = Array.from(this.files || []).filter(function (f) { return (f.name || '').toLowerCase().endsWith('.txt'); });
            estadoSped.arquivosManuais = files;
            var cont = document.getElementById('contador-sped');
            if (cont) cont.textContent = files.length;
        });
    }

    var btnEnviarSped = document.getElementById('btn-enviar-sped');
    if (btnEnviarSped) {
        btnEnviarSped.addEventListener('click', function () {
            enviarArquivosManuais();
        });
    }

    var modalCargaSpedEl = document.getElementById('modalCargaSped');
    if (modalCargaSpedEl) {
        modalCargaSpedEl.addEventListener('show.bs.modal', function () {
            if (typeof Notificacoes !== 'undefined') Notificacoes.limparModal('modalCargaSpedAlerts');
        });
    }
});
