const manifestoState = {
    notas: [],
    filter: 'ALL',
    search: '',
    currentPage: 1,
    itemsPerPage: 50
};

function fn_manifesto_escHtml(s) {
    const d = document.createElement('div');
    d.textContent = s == null ? '' : String(s);
    return d.innerHTML;
}

function fn_manifesto_escAttr(s) {
    return String(s == null ? '' : s)
        .replace(/&/g, '&amp;')
        .replace(/"/g, '&quot;')
        .replace(/</g, '&lt;');
}

function fn_manifesto_status_class(status) {
    const normalized = (status || '').toLowerCase();
    if (normalized.includes('autorizada')) return 'autorizada';
    if (normalized.includes('analise')) return 'em_analise';
    return 'pendente';
}

function fn_manifesto_format_currency(value) {
    const parsed = Number(value);
    if (Number.isNaN(parsed)) {
        return fn_manifesto_escHtml(String(value == null ? '' : value));
    }
    return parsed.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function fn_manifesto_apply_filters() {
    return manifestoState.notas.filter((nota) => {
        const matchesFilter = manifestoState.filter === 'ALL' || nota.tipo === manifestoState.filter;
        if (!matchesFilter) return false;

        if (!manifestoState.search) return true;
        const query = manifestoState.search.toLowerCase();
        return [
            nota.numero,
            nota.emitente,
            nota.destinatario,
            nota.tipo
        ].some((field) => (field || '').toLowerCase().includes(query));
    });
}

function fn_manifesto_calculate_pagination(notasFiltradas) {
    const total = notasFiltradas.length;
    const totalPages = Math.ceil(total / manifestoState.itemsPerPage);
    
    if (manifestoState.currentPage > totalPages) {
        manifestoState.currentPage = Math.max(1, totalPages);
    }
    
    const start = (manifestoState.currentPage - 1) * manifestoState.itemsPerPage;
    const end = start + manifestoState.itemsPerPage;
    
    return {
        itemsNoInterval: notasFiltradas.slice(start, end),
        totalPages,
        currentPage: manifestoState.currentPage,
        total
    };
}

function fn_manifesto_update_pagination(paginacao) {
    const container = document.getElementById('manifesto-pagination');
    if (!container) return;
    
    if (paginacao.totalPages <= 1) {
        container.innerHTML = '';
        return;
    }
    
    let html = '<ul class="pagination manifesto-pagination">';
    
    // Botão Anterior
    if (paginacao.currentPage > 1) {
        html += `
            <li class="page-item">
                <a class="page-link" href="#" data-page="${paginacao.currentPage - 1}">Anterior</a>
            </li>
        `;
    }
    
    // Números de página
    const start = Math.max(1, paginacao.currentPage - 2);
    const end = Math.min(paginacao.totalPages, paginacao.currentPage + 2);
    
    for (let i = start; i <= end; i++) {
        if (i === paginacao.currentPage) {
            html += `<li class="page-item active"><span class="page-link">${i}</span></li>`;
        } else {
            html += `
                <li class="page-item">
                    <a class="page-link" href="#" data-page="${i}">${i}</a>
                </li>
            `;
        }
    }
    
    // Botão Próxima
    if (paginacao.currentPage < paginacao.totalPages) {
        html += `
            <li class="page-item">
                <a class="page-link" href="#" data-page="${paginacao.currentPage + 1}">Próxima</a>
            </li>
        `;
    }
    
    html += '</ul>';
    container.innerHTML = html;
    
    // Adicionar event listeners
    container.querySelectorAll('a.page-link').forEach((link) => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const page = parseInt(link.dataset.page);
            manifestoState.currentPage = page;
            fn_manifesto_render_notas();
            window.scrollTo(0, 0);
        });
    });
}

function fn_manifesto_render_notas() {
    const tbody = document.getElementById('manifesto-notas-body');
    if (!tbody) return;

    const notasFiltradas = fn_manifesto_apply_filters();
    const paginacao = fn_manifesto_calculate_pagination(notasFiltradas);

    if (!paginacao.itemsNoInterval.length) {
        tbody.innerHTML = `
            <tr>
                <td colspan="8" class="text-center py-4">Nenhuma nota encontrada</td>
            </tr>
        `;
        fn_manifesto_update_pagination({ totalPages: 0 });
        return;
    }

    tbody.innerHTML = paginacao.itemsNoInterval.map((nota) => {
        const badgeClass = fn_manifesto_status_class(nota.status);
        const stLabel = String((nota.status || '').replace('_', ' '));
        return `
            <tr data-nota-id="${fn_manifesto_escAttr(nota.id)}">
                <td>${fn_manifesto_escHtml(nota.tipo)}</td>
                <td>${fn_manifesto_escHtml(nota.numero)}</td>
                <td>${fn_manifesto_escHtml(nota.serie)}</td>
                <td>${fn_manifesto_escHtml(nota.emissao)}</td>
                <td>${fn_manifesto_escHtml(nota.emitente)}</td>
                <td>${fn_manifesto_escHtml(nota.destinatario)}</td>
                <td class="text-end">${fn_manifesto_format_currency(nota.valor)}</td>
                <td><span class="manifesto-badge ${badgeClass}">${fn_manifesto_escHtml(stLabel)}</span></td>
            </tr>
        `;
    }).join('');
    
    fn_manifesto_update_pagination(paginacao);
}

function fn_manifesto_render_documentos(documentos) {
    const container = document.getElementById('manifesto-docs');
    if (!container) return;

    if (!documentos || !documentos.length) {
        container.innerHTML = '<p class="manifesto-empty">Nenhum documento vinculado</p>';
        return;
    }

    container.innerHTML = documentos.map((doc, index) => {
        const docId = `manifesto-doc-${index}`;
        const itensHtml = (doc.itens || []).map((item) => {
            return `
                <tr>
                    <td>${fn_manifesto_escHtml(item.seq)}</td>
                    <td>${fn_manifesto_escHtml(item.material)}</td>
                    <td>${fn_manifesto_escHtml(item.descricao)}</td>
                    <td class="text-end">${fn_manifesto_escHtml(item.qtd)}</td>
                    <td>${fn_manifesto_escHtml(item.un)}</td>
                    <td class="text-end">${fn_manifesto_format_currency(item.valor)}</td>
                </tr>
            `;
        }).join('');

        return `
            <div class="manifesto-doc-card">
                <div class="manifesto-doc-header manifesto-doc-toggle" data-doc-id="${fn_manifesto_escAttr(docId)}">
                    <div class="manifesto-doc-header-content">
                        <span class="manifesto-doc-toggle-icon">▶</span>
                        <div>
                            <div class="manifesto-doc-title">${fn_manifesto_escHtml(doc.tipo)} ${fn_manifesto_escHtml(doc.numero)}</div>
                            <div class="manifesto-doc-meta">Data ${fn_manifesto_escHtml(doc.data)} • Status ${fn_manifesto_escHtml(doc.status)}</div>
                        </div>
                    </div>
                    <span class="manifesto-badge ${fn_manifesto_status_class(doc.status)}">${fn_manifesto_escHtml(doc.status)}</span>
                </div>
                <div class="manifesto-doc-content" id="${docId}" style="display: none;">
                    <div class="table-responsive">
                        <table class="table manifesto-table">
                            <thead>
                                <tr>
                                    <th>Seq</th>
                                    <th>Material</th>
                                    <th>Descricao</th>
                                    <th class="text-end">Qtd</th>
                                    <th>Un</th>
                                    <th class="text-end">Valor</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${itensHtml || '<tr><td colspan="6" class="text-center">Sem itens</td></tr>'}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        `;
    }).join('');

    // Adicionar event listeners para toggle
    document.querySelectorAll('.manifesto-doc-toggle').forEach((toggle) => {
        toggle.addEventListener('click', () => {
            const docId = toggle.dataset.docId;
            const content = document.getElementById(docId);
            const icon = toggle.querySelector('.manifesto-doc-toggle-icon');
            
            if (content) {
                const isHidden = content.style.display === 'none';
                content.style.display = isHidden ? 'block' : 'none';
                icon.textContent = isHidden ? '▼' : '▶';
                toggle.classList.toggle('is-expanded', isHidden);
            }
        });
    });
}

function fn_manifesto_get_linked_item_seqs(documentos) {
    const linked = new Set();
    if (!documentos || !documentos.length) return linked;
    
    documentos.forEach((doc) => {
        if (doc.itens && doc.itens.length) {
            doc.itens.forEach((item) => {
                if (item.nfe_item_seq) {
                    linked.add(String(item.nfe_item_seq));
                }
            });
        }
    });
    return linked;
}

function fn_manifesto_render_itens(itens, documentos = []) {
    const tbody = document.getElementById('manifesto-itens-body');
    if (!tbody) return;

    if (!itens || !itens.length) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center">Sem itens</td></tr>';
        return;
    }

    const linkedSeqs = fn_manifesto_get_linked_item_seqs(documentos);

    tbody.innerHTML = itens.map((item) => {
        const isLinked = linkedSeqs.has(String(item.seq));
        const rowClass = isLinked ? 'manifesto-item-linked' : '';
        return `
            <tr class="${rowClass}" data-item-seq="${fn_manifesto_escAttr(item.seq)}">
                <td>${fn_manifesto_escHtml(item.seq)}</td>
                <td>${fn_manifesto_escHtml(item.codigo)}</td>
                <td>${fn_manifesto_escHtml(item.descricao)}</td>
                <td class="text-end">${fn_manifesto_escHtml(item.qtd)}</td>
                <td>${fn_manifesto_escHtml(item.un)}</td>
                <td class="text-end">${fn_manifesto_format_currency(item.valor)}</td>
            </tr>
        `;
    }).join('');
}

function fn_manifesto_open_modal(notaId) {
    const nota = manifestoState.notas.find((item) => item.id === notaId);
    if (!nota) return;

    manifestoState.currentNota = nota; // save for item modal handlers

    const title = document.getElementById('manifesto-modal-title');
    const meta = document.getElementById('manifesto-modal-meta');

    if (title) {
        title.textContent = `${nota.tipo} ${nota.numero}/${nota.serie}`;
    }

    if (meta) {
        meta.textContent = `${nota.emissao} • ${nota.emitente} -> ${nota.destinatario}`;
    }

    fn_manifesto_render_documentos(nota.documentos);
    fn_manifesto_render_itens(nota.itens, nota.documentos);

    const modalElement = document.getElementById('manifestoModal');
    if (modalElement) {
        const modal = bootstrap.Modal.getOrCreateInstance(modalElement);
        modal.show();
    }
}

function fn_manifesto_init_filters() {
    const chips = document.querySelectorAll('.manifesto-chip');
    chips.forEach((chip) => {
        chip.addEventListener('click', () => {
            chips.forEach((item) => item.classList.remove('is-active'));
            chip.classList.add('is-active');
            manifestoState.filter = chip.dataset.filter || 'ALL';
            manifestoState.currentPage = 1;
            fn_manifesto_render_notas();
        });
    });

    const searchInput = document.getElementById('manifesto-search');
    if (searchInput) {
        searchInput.addEventListener('input', (event) => {
            manifestoState.search = event.target.value.trim();
            manifestoState.currentPage = 1;
            fn_manifesto_render_notas();
        });
    }
}

/* ------------------------------------------------------------------ */
/* Item modal helpers */
function fn_manifesto_render_item_details(item) {
    const container = document.getElementById('manifesto-item-details');
    if (!container) return;
    container.innerHTML = `
        <p><strong>Sequência:</strong> ${fn_manifesto_escHtml(item.seq)}</p>
        <p><strong>Código:</strong> ${fn_manifesto_escHtml(item.codigo)}</p>
        <p><strong>Descrição:</strong> ${fn_manifesto_escHtml(item.descricao)}</p>
        <p><strong>Quantidade:</strong> ${fn_manifesto_escHtml(item.qtd)}</p>
        <p><strong>Unidade:</strong> ${fn_manifesto_escHtml(item.un)}</p>
        <p><strong>Valor:</strong> ${fn_manifesto_format_currency(item.valor)}</p>
    `;
}

function fn_manifesto_open_item_modal(seq) {
    if (!manifestoState.currentNota) return;
    const item = manifestoState.currentNota.itens.find((i) => String(i.seq) === String(seq));
    if (!item) return;

    fn_manifesto_render_item_details(item);

    const modalEl = document.getElementById('manifestoItemModal');
    if (modalEl) {
        const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
        modal.show();
    }
}

/* bind item row click after notas rendered */
function fn_manifesto_bind_item_events() {
    const body = document.getElementById('manifesto-itens-body');
    if (!body) return;
    body.addEventListener('click', (ev) => {
        const row = ev.target.closest('tr[data-item-seq]');
        if (!row) return;
        fn_manifesto_open_item_modal(row.dataset.itemSeq);
    });
}


document.addEventListener('DOMContentLoaded', () => {
    const dataScript = document.getElementById('manifesto-data');
    if (!dataScript) return;

    const data = JSON.parse(dataScript.textContent);
    manifestoState.notas = data.notas || [];

    fn_manifesto_render_notas();
    fn_manifesto_init_filters();
    fn_manifesto_bind_item_events();

    // rateio button inside item modal
    const rateioBtn = document.getElementById('btn-rateio-item');
    if (rateioBtn) {
        rateioBtn.addEventListener('click', () => {
            // placeholder: abrir outro modal ou realizar ação de rateio
            alert('Abrir modal de rateio (a implementar)');
        });
    }

    const tbody = document.getElementById('manifesto-notas-body');
    if (tbody) {
        tbody.addEventListener('click', (event) => {
            const row = event.target.closest('tr[data-nota-id]');
            if (!row) return;
            fn_manifesto_open_modal(row.dataset.notaId);
        });
    }
});
