/* Carga SPED - mesma linha de raciocínio da Carga XML */
const estadoSped = {
    todos: [],
    filtrados: [],
    filtros: { busca: '', mostrarAtivos: true, mostrarInativos: true },
    currentPage: 1,
    itemsPerPage: 10,
    arquivosManuais: []
};

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
                }, 3000);
            } else if (data.em_andamento === 0 && intervaloResumoSped) {
                clearInterval(intervaloResumoSped);
                intervaloResumoSped = null;
            }
        })
        .catch(function () {});
}

function carregarAvisosCargaSped(preencherModal) {
    fetch(getApiBase() + '/api/cargasped/avisos/', {
        method: 'GET',
        headers: { 'X-CSRFToken': obterCsrfToken() },
    })
        .then(function (r) { return r.json(); })
        .then(function (data) {
            var total = (data.sucesso && data.total_erros) ? data.total_erros : 0;
            var badge = document.getElementById('avisos-badge-cargasped');
            if (badge) {
                if (total > 0) {
                    badge.textContent = total > 99 ? '99+' : total;
                    badge.style.display = 'inline-block';
                } else {
                    badge.style.display = 'none';
                }
            }
            if (preencherModal) {
                preencherModalAvisosCargaSped(data.items || []);
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
    if (items.length === 0) {
        emptyEl.style.display = 'block';
        listEl.style.display = 'none';
        listEl.innerHTML = '';
        return;
    }
    emptyEl.style.display = 'none';
    listEl.style.display = 'block';
    function formatDt(iso) {
        if (!iso) return '-';
        try {
            var d = new Date(iso);
            return d.toLocaleString('pt-BR', { dateStyle: 'short', timeStyle: 'short' });
        } catch (e) { return iso; }
    }
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
        html += '    <span class="aviso-item-info"><strong>Job #' + job.id + '</strong> &middot; ' + formatDt(job.started_at) + ' <span class="text-muted small ms-1">(clique para ' + (bodyVisible ? 'recolher' : 'expandir') + ')</span></span>';
        html += '    <span class="d-flex align-items-center gap-2">';
        if (totalOk > 0) html += '<span class="badge aviso-badge-ok">' + totalOk + ' OK</span>';
        html += '<span class="badge aviso-badge-erro">' + totalErro + ' erro(s)</span> <i class="fas fa-chevron-' + (bodyVisible ? 'down' : 'right') + ' aviso-chevron small"></i></span>';
        html += '  </div>';
        html += '  <div class="aviso-item-body ' + (bodyVisible ? '' : 'd-none') + '">' + logHtml + '</div>';
        html += '</div>';
    });
    listEl.innerHTML = html;
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

function carregarParametrosPrincipais() {
    const tbody = document.querySelector('#tabela-parametros-main tbody');
    if (!tbody) return;
    fetch(getApiBase() + '/api/cargasped/parametros/')
        .then(r => r.json())
        .then(data => {
            estadoSped.todos = (data.items || []).map(item => ({
                id: item.id,
                horario: item.horario || '',
                tipo_sped: item.tipo_sped || '',
                diretorio: item.diretorio || '',
                empresa_nome: item.empresa_nome || '',
                ativo: !!item.ativo
            }));
            aplicarFiltrosSped();
            renderizarTabelaParametrosSped();
        })
        .catch(() => {
            estadoSped.todos = [];
            estadoSped.filtrados = [];
            renderizarTabelaParametrosSped();
        });
}

function aplicarFiltrosSped() {
    let list = estadoSped.todos.filter(p => {
        const ativoOk = (p.ativo && estadoSped.filtros.mostrarAtivos) || (!p.ativo && estadoSped.filtros.mostrarInativos);
        const busca = estadoSped.filtros.busca;
        if (!ativoOk) return false;
        if (!busca) return true;
        const s = (p.diretorio + ' ' + p.horario + ' ' + p.empresa_nome).toLowerCase();
        return s.indexOf(busca) !== -1;
    });
    estadoSped.filtrados = list;
    estadoSped.currentPage = 1;
}

function renderizarTabelaParametrosSped() {
    const tbody = document.querySelector('#tabela-parametros-main tbody');
    if (!tbody) return;
    const total = estadoSped.filtrados.length;
    const start = (estadoSped.currentPage - 1) * estadoSped.itemsPerPage;
    const page = estadoSped.filtrados.slice(start, start + estadoSped.itemsPerPage);

    if (page.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" class="text-center text-muted py-4">Nenhum parâmetro cadastrado</td></tr>';
        document.getElementById('paginacao-cargas').innerHTML = '';
        return;
    }

    tbody.innerHTML = page.map(p => `
        <tr class="align-middle">
            <td>${p.horario}</td>
            <td class="text-truncate" style="max-width:200px" title="${(p.diretorio || '').replace(/"/g, '&quot;')}">${p.diretorio || '-'}</td>
            <td>${p.empresa_nome || '-'}</td>
            <td><span class="badge ${p.ativo ? 'bg-success' : 'bg-secondary'}">${p.ativo ? 'Ativo' : 'Inativo'}</span></td>
        </tr>
    `).join('');

    const totalPages = Math.max(1, Math.ceil(total / estadoSped.itemsPerPage));
    let pagHtml = '';
    for (let i = 1; i <= totalPages; i++) {
        pagHtml += `<li class="page-item ${i === estadoSped.currentPage ? 'active' : ''}"><a class="page-link" href="#" data-page="${i}">${i}</a></li>`;
    }
    const pagEl = document.getElementById('paginacao-cargas');
    pagEl.innerHTML = pagHtml;
    pagEl.querySelectorAll('.page-link').forEach(link => {
        link.addEventListener('click', e => { e.preventDefault(); estadoSped.currentPage = parseInt(link.dataset.page, 10); renderizarTabelaParametrosSped(); });
    });
}

function carregarParametrosModal() {
    const tbody = document.querySelector('#tabela-parametros-sped tbody');
    if (!tbody) return;
    fetch(getApiBase() + '/api/cargasped/parametros/')
        .then(r => r.json())
        .then(data => {
            const items = data.items || [];
            if (items.length === 0) {
                tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">Nenhum parâmetro</td></tr>';
                return;
            }
            tbody.innerHTML = items.map(p => `
                <tr>
                    <td>${p.horario || ''}</td>
                    <td class="text-truncate" style="max-width:120px">${p.diretorio || '-'}</td>
                    <td>${p.empresa_nome || '-'}</td>
                    <td><span class="badge ${p.ativo ? 'bg-success' : 'bg-secondary'}">${p.ativo ? 'Ativo' : 'Inativo'}</span></td>
                    <td><button type="button" class="btn btn-sm btn-outline-primary upload-zip-sped" data-param-id="${p.id}">ZIP</button></td>
                </tr>
            `).join('');
            tbody.querySelectorAll('.upload-zip-sped').forEach(btn => {
                btn.addEventListener('click', () => {
                    document.getElementById('upload-zip-sped-param-id').value = btn.dataset.paramId;
                    new bootstrap.Modal(document.getElementById('modalUploadZipSped')).show();
                });
            });
        });
}

function enviarArquivosManuais() {
    if (estadoSped.arquivosManuais.length === 0) {
        Notificacoes.modal('Selecione ao menos um arquivo .txt', 'warning', 'modalCargaSpedAlerts');
        return;
    }
    const fd = new FormData();
    estadoSped.arquivosManuais.forEach(f => fd.append('arquivo', f));
    fd.append('csrfmiddlewaretoken', obterCsrfToken());
    const btn = document.getElementById('btn-enviar-sped');
    btn.disabled = true;
    fetch(getApiBase() + '/api/processar-sped/', { method: 'POST', body: fd })
        .then(r => r.json())
        .then(data => {
            btn.disabled = false;
            Notificacoes.modal(data.mensagem || (data.sucesso ? 'Job em execução.' : 'Erro.'), data.sucesso ? 'success' : 'danger', 'modalCargaSpedAlerts');
            if (data.sucesso) {
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
                carregarParametrosPrincipais();
                carregarResumoCargaSped();
                carregarAvisosCargaSped();
            }
        })
        .catch(() => { btn.disabled = false; Notificacoes.modal('Erro na requisição.', 'danger', 'modalCargaSpedAlerts'); });
}

document.addEventListener('DOMContentLoaded', function () {
    carregarParametrosPrincipais();
    carregarResumoCargaSped();
    carregarAvisosCargaSped();

    var btnAtualizarResumo = document.getElementById('btn-atualizar-resumo-sped');
    if (btnAtualizarResumo) btnAtualizarResumo.addEventListener('click', function () { carregarResumoCargaSped(); });

    var modalAvisos = document.getElementById('modalAvisosCargaSped');
    if (modalAvisos) {
        modalAvisos.addEventListener('show.bs.modal', function () {
            carregarAvisosCargaSped(true);
        });
    }

    const filtroBusca = document.getElementById('filtro-param-busca');
    if (filtroBusca) filtroBusca.addEventListener('keyup', function () { estadoSped.filtros.busca = this.value.toLowerCase(); aplicarFiltrosSped(); renderizarTabelaParametrosSped(); });

    const chkAtivos = document.getElementById('filtro-param-ativos');
    const chkInativos = document.getElementById('filtro-param-inativos');
    if (chkAtivos) chkAtivos.addEventListener('change', function () { estadoSped.filtros.mostrarAtivos = this.checked; aplicarFiltrosSped(); renderizarTabelaParametrosSped(); });
    if (chkInativos) chkInativos.addEventListener('change', function () { estadoSped.filtros.mostrarInativos = this.checked; aplicarFiltrosSped(); renderizarTabelaParametrosSped(); });

    const dropZoneArquivo = document.getElementById('drop-zone-sped-arquivo');
    const dropZonePasta = document.getElementById('drop-zone-sped-pasta');
    const fileInput = document.getElementById('file-input-sped');
    const fileInputPasta = document.getElementById('file-input-sped-pasta');
    if (dropZoneArquivo && fileInput) {
        dropZoneArquivo.addEventListener('click', function () { fileInput.value = ''; fileInput.click(); });
        dropZoneArquivo.addEventListener('keydown', function (e) { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); fileInput.click(); } });
    }
    if (dropZonePasta && fileInputPasta) {
        dropZonePasta.addEventListener('click', function () { fileInputPasta.value = ''; fileInputPasta.click(); });
        dropZonePasta.addEventListener('keydown', function (e) { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); fileInputPasta.click(); } });
    }
    if (fileInput) {
        fileInput.addEventListener('change', function () {
            const files = Array.from(this.files || []).filter(f => (f.name || '').toLowerCase().endsWith('.txt'));
            estadoSped.arquivosManuais = files;
            document.getElementById('contador-sped').textContent = files.length;
        });
    }
    if (fileInputPasta) {
        fileInputPasta.addEventListener('change', function () {
            const files = Array.from(this.files || []).filter(f => (f.name || '').toLowerCase().endsWith('.txt'));
            estadoSped.arquivosManuais = files;
            document.getElementById('contador-sped').textContent = files.length;
            this.value = '';
        });
    }

    document.getElementById('btn-enviar-sped').addEventListener('click', function () {
        const tabManual = document.getElementById('manual-sped');
        if (tabManual && tabManual.classList.contains('show')) {
            enviarArquivosManuais();
        }
    });

    document.getElementById('form-parametros-sped').addEventListener('submit', function (e) {
        e.preventDefault();
        const payload = {
            horario: document.getElementById('param-sped-horario').value,
            diretorio: document.getElementById('param-sped-diretorio').value.trim(),
            empresa_id: document.getElementById('param-sped-empresa').value,
            ativo: document.getElementById('param-sped-ativo').checked
        };
        if (!payload.horario || !payload.diretorio) { Notificacoes.modal('Preencha horário e diretório.', 'warning', 'modalCargaSpedAlerts'); return; }
        fetch(getApiBase() + '/api/cargasped/parametros/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': obterCsrfToken() },
            body: JSON.stringify(payload)
        })
            .then(r => r.json())
            .then(data => {
                if (data.sucesso) { carregarParametrosModal(); carregarParametrosPrincipais(); this.reset(); }
                else Notificacoes.modal(data.mensagem || 'Erro', 'danger', 'modalCargaSpedAlerts');
            })
            .catch(() => Notificacoes.modal('Erro na requisição.', 'danger', 'modalCargaSpedAlerts'));
    });

    document.getElementById('tab-automatico-sped').addEventListener('shown.bs.tab', carregarParametrosModal);

    document.getElementById('btn-confirmar-upload-zip-sped').addEventListener('click', function () {
        const paramId = document.getElementById('upload-zip-sped-param-id').value;
        const fileInput = document.getElementById('upload-zip-sped-file');
        if (!paramId || !fileInput.files || !fileInput.files[0]) { Notificacoes.modal('Selecione um arquivo ZIP.', 'warning', 'modalUploadZipSpedAlerts'); return; }
        const fd = new FormData();
        fd.append('arquivo_zip', fileInput.files[0]);
        fd.append('csrfmiddlewaretoken', obterCsrfToken());
        fetch(getApiBase() + `/api/cargasped/parametros/${paramId}/upload-zip/`, { method: 'POST', body: fd })
            .then(r => r.json())
            .then(data => {
                Notificacoes.modal(data.mensagem || (data.sucesso ? 'OK' : 'Erro'), data.sucesso ? 'success' : 'danger', 'modalUploadZipSpedAlerts');
                if (data.sucesso) { fileInput.value = ''; bootstrap.Modal.getInstance(document.getElementById('modalUploadZipSped')).hide(); carregarParametrosPrincipais(); carregarParametrosModal(); }
            })
            .catch(() => Notificacoes.modal('Erro na requisição.', 'danger', 'modalUploadZipSpedAlerts'));
    });

    // Limpar alertas ao abrir cada modal
    ['modalCargaSped', 'modalUploadZipSped'].forEach(function (modalId) {
        var el = document.getElementById(modalId);
        if (el) {
            el.addEventListener('show.bs.modal', function () {
                var alertsId = modalId + 'Alerts';
                if (typeof Notificacoes !== 'undefined') Notificacoes.limparModal(alertsId);
            });
        }
    });
});
