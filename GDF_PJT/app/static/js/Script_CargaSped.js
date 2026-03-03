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

function carregarParametrosPrincipais() {
    const tbody = document.querySelector('#tabela-parametros-main tbody');
    if (!tbody) return;
    fetch('/api/cargasped/parametros/')
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
        const s = (p.diretorio + ' ' + p.tipo_sped + ' ' + p.horario + ' ' + p.empresa_nome).toLowerCase();
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
        tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted py-4">Nenhum parâmetro cadastrado</td></tr>';
        document.getElementById('paginacao-cargas').innerHTML = '';
        return;
    }

    tbody.innerHTML = page.map(p => `
        <tr class="align-middle">
            <td>${p.horario}</td>
            <td>${p.tipo_sped}</td>
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
    fetch('/api/cargasped/parametros/')
        .then(r => r.json())
        .then(data => {
            const items = data.items || [];
            if (items.length === 0) {
                tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted">Nenhum parâmetro</td></tr>';
                return;
            }
            tbody.innerHTML = items.map(p => `
                <tr>
                    <td>${p.horario || ''}</td>
                    <td>${p.tipo_sped || ''}</td>
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
        alert('Selecione ao menos um arquivo .txt');
        return;
    }
    const fd = new FormData();
    estadoSped.arquivosManuais.forEach(f => fd.append('arquivo', f));
    fd.append('tipo_sped', document.getElementById('select-tipo-sped-manual').value);
    fd.append('csrfmiddlewaretoken', obterCsrfToken());
    const btn = document.getElementById('btn-enviar-sped');
    btn.disabled = true;
    fetch('/api/processar-sped/', { method: 'POST', body: fd })
        .then(r => r.json())
        .then(data => {
            btn.disabled = false;
            alert(data.mensagem || (data.sucesso ? 'Enviado.' : 'Erro.'));
            if (data.sucesso) {
                estadoSped.arquivosManuais = [];
                document.getElementById('contador-sped').textContent = '0';
                document.getElementById('file-input-sped').value = '';
                bootstrap.Modal.getInstance(document.getElementById('modalCargaSped')).hide();
                carregarParametrosPrincipais();
            }
        })
        .catch(() => { btn.disabled = false; alert('Erro na requisição.'); });
}

document.addEventListener('DOMContentLoaded', function () {
    carregarParametrosPrincipais();

    const filtroBusca = document.getElementById('filtro-param-busca');
    if (filtroBusca) filtroBusca.addEventListener('keyup', function () { estadoSped.filtros.busca = this.value.toLowerCase(); aplicarFiltrosSped(); renderizarTabelaParametrosSped(); });

    const chkAtivos = document.getElementById('filtro-param-ativos');
    const chkInativos = document.getElementById('filtro-param-inativos');
    if (chkAtivos) chkAtivos.addEventListener('change', function () { estadoSped.filtros.mostrarAtivos = this.checked; aplicarFiltrosSped(); renderizarTabelaParametrosSped(); });
    if (chkInativos) chkInativos.addEventListener('change', function () { estadoSped.filtros.mostrarInativos = this.checked; aplicarFiltrosSped(); renderizarTabelaParametrosSped(); });

    const dropZone = document.getElementById('drop-zone-sped');
    const fileInput = document.getElementById('file-input-sped');
    if (dropZone && fileInput) {
        dropZone.addEventListener('click', () => fileInput.click());
        fileInput.addEventListener('change', function () {
            const files = Array.from(this.files || []).filter(f => (f.name || '').toLowerCase().endsWith('.txt'));
            estadoSped.arquivosManuais = files;
            document.getElementById('contador-sped').textContent = files.length;
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
            tipo_sped: document.getElementById('param-sped-tipo').value,
            diretorio: document.getElementById('param-sped-diretorio').value.trim(),
            empresa_id: document.getElementById('param-sped-empresa').value,
            ativo: document.getElementById('param-sped-ativo').checked
        };
        if (!payload.horario || !payload.diretorio || !payload.empresa_id) { alert('Preencha horário, diretório e empresa.'); return; }
        fetch('/api/cargasped/parametros/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': obterCsrfToken() },
            body: JSON.stringify(payload)
        })
            .then(r => r.json())
            .then(data => {
                if (data.sucesso) { carregarParametrosModal(); carregarParametrosPrincipais(); this.reset(); }
                else alert(data.mensagem || 'Erro');
            })
            .catch(() => alert('Erro na requisição.'));
    });

    document.getElementById('tab-automatico-sped').addEventListener('shown.bs.tab', carregarParametrosModal);

    document.getElementById('btn-confirmar-upload-zip-sped').addEventListener('click', function () {
        const paramId = document.getElementById('upload-zip-sped-param-id').value;
        const fileInput = document.getElementById('upload-zip-sped-file');
        if (!paramId || !fileInput.files || !fileInput.files[0]) { alert('Selecione um arquivo ZIP.'); return; }
        const fd = new FormData();
        fd.append('arquivo_zip', fileInput.files[0]);
        fd.append('csrfmiddlewaretoken', obterCsrfToken());
        fetch(`/api/cargasped/parametros/${paramId}/upload-zip/`, { method: 'POST', body: fd })
            .then(r => r.json())
            .then(data => {
                alert(data.mensagem || (data.sucesso ? 'OK' : 'Erro'));
                if (data.sucesso) { fileInput.value = ''; bootstrap.Modal.getInstance(document.getElementById('modalUploadZipSped')).hide(); carregarParametrosPrincipais(); carregarParametrosModal(); }
            })
            .catch(() => alert('Erro na requisição.'));
    });
});
