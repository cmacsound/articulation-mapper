/**
 * Articulation Mapper - Client-side application logic
 */

// ── State ─────────────────────────────────────────────────────────

let banks = [];
let previewCache = { midnam: '', middev: '' };

// ── DOM refs ──────────────────────────────────────────────────────

const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);

const dom = {
    manufacturer: $('#manufacturer'),
    model: $('#model'),
    author: $('#author'),
    templateSelect: $('#template-select'),
    tbody: $('#bank-tbody'),
    emptyState: $('#empty-state'),
    bankCount: $('.bank-count'),
    bankSearch: $('#bank-search'),
    overlay: $('#modal-overlay'),
    selectAll: $('#select-all'),
};

// ── Init ──────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
    loadTemplateList();
    bindEvents();
    renderTable();
});

// ── Event binding ─────────────────────────────────────────────────

function bindEvents() {
    // Header actions
    $('#btn-new').addEventListener('click', newProject);
    $('#btn-open').addEventListener('click', openProjectModal);
    $('#btn-save').addEventListener('click', saveProject);
    $('#btn-import-midnam').addEventListener('click', () => showModal('modal-import-midnam'));
    $('#btn-import-text').addEventListener('click', () => showModal('modal-import-text'));
    $('#btn-preview').addEventListener('click', previewXML);
    $('#btn-export').addEventListener('click', exportFiles);
    $('#btn-install').addEventListener('click', installToProTools);

    // Bank toolbar
    $('#btn-add-bank').addEventListener('click', addBank);
    $('#btn-add-bulk').addEventListener('click', () => showModal('modal-bulk-add'));
    $('#btn-delete-selected').addEventListener('click', deleteSelected);
    $('#btn-duplicate').addEventListener('click', duplicateSelected);

    // Template
    $('#btn-load-template').addEventListener('click', loadTemplate);

    // Search filter
    dom.bankSearch.addEventListener('input', renderTable);

    // Select all
    dom.selectAll.addEventListener('change', (e) => {
        $$('#bank-tbody input[type="checkbox"]').forEach(cb => {
            cb.checked = e.target.checked;
        });
    });

    // Modal close buttons
    $$('.modal-close').forEach(btn => {
        btn.addEventListener('click', hideAllModals);
    });

    // Overlay click to close
    dom.overlay.addEventListener('click', (e) => {
        if (e.target === dom.overlay) hideAllModals();
    });

    // Preview tabs
    $$('.preview-tabs .tab').forEach(tab => {
        tab.addEventListener('click', (e) => {
            $$('.preview-tabs .tab').forEach(t => t.classList.remove('active'));
            e.target.classList.add('active');
            const type = e.target.dataset.tab;
            $('#preview-content').textContent = previewCache[type] || '';
        });
    });

    // Import text action
    $('#btn-do-import-text').addEventListener('click', doImportText);

    // Import midnam file
    $('#midnam-file-input').addEventListener('change', doImportMidnam);

    // Bulk add action
    $('#btn-do-bulk-add').addEventListener('click', doBulkAdd);

    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        if (e.metaKey && e.key === 's') {
            e.preventDefault();
            saveProject();
        }
        if (e.key === 'Escape') {
            hideAllModals();
        }
    });
}

// ── Table rendering ───────────────────────────────────────────────

function renderTable() {
    const filter = dom.bankSearch.value.toLowerCase();
    dom.tbody.innerHTML = '';

    const filtered = banks.map((bank, idx) => ({ bank, idx }))
        .filter(({ bank }) => !filter || bank.name.toLowerCase().includes(filter));

    if (filtered.length === 0 && banks.length === 0) {
        dom.emptyState.classList.add('visible');
        $('.table-wrapper').style.display = 'none';
    } else {
        dom.emptyState.classList.remove('visible');
        $('.table-wrapper').style.display = '';
    }

    filtered.forEach(({ bank, idx }) => {
        const tr = document.createElement('tr');
        tr.dataset.index = idx;
        tr.draggable = true;

        // Checkbox
        const tdCheck = document.createElement('td');
        tdCheck.className = 'col-check';
        const cb = document.createElement('input');
        cb.type = 'checkbox';
        cb.dataset.index = idx;
        tdCheck.appendChild(cb);
        tr.appendChild(tdCheck);

        // Name
        const tdName = document.createElement('td');
        tdName.className = 'col-name';
        const nameInput = document.createElement('input');
        nameInput.type = 'text';
        nameInput.value = bank.name;
        nameInput.addEventListener('change', (e) => {
            banks[idx].name = e.target.value;
            // Also update the patch name to match
            if (banks[idx].patches && banks[idx].patches.length > 0) {
                banks[idx].patches[0].name = e.target.value;
            }
        });
        tdName.appendChild(nameInput);
        tr.appendChild(tdName);

        // CC0
        const tdCC0 = document.createElement('td');
        tdCC0.className = 'col-cc0';
        const cc0Input = document.createElement('input');
        cc0Input.type = 'number';
        cc0Input.min = '0';
        cc0Input.max = '127';
        cc0Input.value = bank.cc0 !== null && bank.cc0 !== undefined ? bank.cc0 : '';
        cc0Input.placeholder = '-';
        cc0Input.addEventListener('change', (e) => {
            banks[idx].cc0 = e.target.value !== '' ? parseInt(e.target.value) : null;
        });
        tdCC0.appendChild(cc0Input);
        tr.appendChild(tdCC0);

        // CC32
        const tdCC32 = document.createElement('td');
        tdCC32.className = 'col-cc32';
        const cc32Input = document.createElement('input');
        cc32Input.type = 'number';
        cc32Input.min = '0';
        cc32Input.max = '127';
        cc32Input.value = bank.cc32 !== null && bank.cc32 !== undefined ? bank.cc32 : '';
        cc32Input.placeholder = '-';
        cc32Input.addEventListener('change', (e) => {
            banks[idx].cc32 = e.target.value !== '' ? parseInt(e.target.value) : null;
        });
        tdCC32.appendChild(cc32Input);
        tr.appendChild(tdCC32);

        // Program Change
        const tdPC = document.createElement('td');
        tdPC.className = 'col-pc';
        const pcInput = document.createElement('input');
        pcInput.type = 'number';
        pcInput.min = '0';
        pcInput.max = '127';
        const pc = bank.patches && bank.patches.length > 0 ? bank.patches[0].program_change : '';
        pcInput.value = pc;
        pcInput.addEventListener('change', (e) => {
            const val = parseInt(e.target.value) || 0;
            if (!banks[idx].patches || banks[idx].patches.length === 0) {
                banks[idx].patches = [{ number: '001', name: banks[idx].name, program_change: val }];
            } else {
                banks[idx].patches[0].program_change = val;
            }
        });
        tdPC.appendChild(pcInput);
        tr.appendChild(tdPC);

        // Delete button
        const tdAct = document.createElement('td');
        tdAct.className = 'col-actions';
        const delBtn = document.createElement('button');
        delBtn.className = 'btn-row-delete';
        delBtn.textContent = '\u00d7';
        delBtn.title = 'Delete this row';
        delBtn.addEventListener('click', () => {
            banks.splice(idx, 1);
            renderTable();
        });
        tdAct.appendChild(delBtn);
        tr.appendChild(tdAct);

        // Drag events
        tr.addEventListener('dragstart', handleDragStart);
        tr.addEventListener('dragover', handleDragOver);
        tr.addEventListener('drop', handleDrop);
        tr.addEventListener('dragend', handleDragEnd);
        tr.addEventListener('dragleave', handleDragLeave);

        dom.tbody.appendChild(tr);
    });

    updateBankCount();
}

function updateBankCount() {
    dom.bankCount.textContent = `${banks.length} articulation${banks.length !== 1 ? 's' : ''}`;
}

// ── Drag and drop ─────────────────────────────────────────────────

let dragSrcIndex = null;

function handleDragStart(e) {
    dragSrcIndex = parseInt(this.dataset.index);
    this.classList.add('dragging');
    e.dataTransfer.effectAllowed = 'move';
}

function handleDragOver(e) {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    this.classList.add('drag-over');
}

function handleDragLeave() {
    this.classList.remove('drag-over');
}

function handleDrop(e) {
    e.preventDefault();
    this.classList.remove('drag-over');
    const dropIndex = parseInt(this.dataset.index);
    if (dragSrcIndex !== null && dragSrcIndex !== dropIndex) {
        const [moved] = banks.splice(dragSrcIndex, 1);
        banks.splice(dropIndex, 0, moved);
        renderTable();
    }
}

function handleDragEnd() {
    this.classList.remove('dragging');
    $$('tr.drag-over').forEach(tr => tr.classList.remove('drag-over'));
}

// ── Bank actions ──────────────────────────────────────────────────

function addBank() {
    const nextCC32 = banks.length > 0
        ? Math.max(...banks.map(b => b.cc32 || 0)) + 1
        : 1;
    const name = 'New Articulation';
    banks.push({
        name: name,
        cc0: null,
        cc32: nextCC32,
        patches: [{ number: String(banks.length + 1).padStart(3, '0'), name: name, program_change: nextCC32 }]
    });
    renderTable();

    // Focus the new row's name input
    requestAnimationFrame(() => {
        const rows = dom.tbody.querySelectorAll('tr');
        const lastRow = rows[rows.length - 1];
        if (lastRow) {
            const nameInput = lastRow.querySelector('.col-name input');
            if (nameInput) {
                nameInput.focus();
                nameInput.select();
            }
        }
    });
}

function deleteSelected() {
    const checked = [...$$('#bank-tbody input[type="checkbox"]:checked')];
    if (checked.length === 0) {
        toast('Select rows to delete first', 'info');
        return;
    }
    const indices = checked.map(cb => parseInt(cb.dataset.index)).sort((a, b) => b - a);
    indices.forEach(i => banks.splice(i, 1));
    dom.selectAll.checked = false;
    renderTable();
    toast(`Deleted ${indices.length} articulation(s)`, 'success');
}

function duplicateSelected() {
    const checked = [...$$('#bank-tbody input[type="checkbox"]:checked')];
    if (checked.length === 0) {
        toast('Select a row to duplicate first', 'info');
        return;
    }
    checked.forEach(cb => {
        const idx = parseInt(cb.dataset.index);
        const copy = JSON.parse(JSON.stringify(banks[idx]));
        copy.name += ' (copy)';
        if (copy.patches && copy.patches.length > 0) {
            copy.patches[0].name = copy.name;
        }
        banks.push(copy);
    });
    dom.selectAll.checked = false;
    renderTable();
    toast(`Duplicated ${checked.length} articulation(s)`, 'success');
}

// ── Project management ────────────────────────────────────────────

function getProjectData() {
    return {
        manufacturer: dom.manufacturer.value,
        model: dom.model.value,
        author: dom.author.value,
        banks: banks
    };
}

function loadProjectData(data) {
    dom.manufacturer.value = data.manufacturer || '';
    dom.model.value = data.model || '';
    dom.author.value = data.author || 'Articulation Mapper';
    banks = data.banks || [];
    renderTable();
}

function newProject() {
    if (banks.length > 0 && !confirm('Discard current project?')) return;
    dom.manufacturer.value = '';
    dom.model.value = '';
    dom.author.value = 'Articulation Mapper';
    banks = [];
    renderTable();
    toast('New project created', 'info');
}

async function saveProject() {
    const data = getProjectData();
    if (!data.manufacturer || !data.model) {
        toast('Set Manufacturer and Model before saving', 'error');
        return;
    }
    try {
        const res = await fetch('/api/projects', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        const result = await res.json();
        toast(`Saved: ${result.filename}`, 'success');
    } catch (err) {
        toast('Save failed: ' + err.message, 'error');
    }
}

async function openProjectModal() {
    try {
        const res = await fetch('/api/projects');
        const projects = await res.json();
        const list = $('#project-list');
        list.innerHTML = '';

        if (projects.length === 0) {
            list.innerHTML = '<p style="color: var(--text-dim); padding: 20px; text-align: center;">No saved projects yet.</p>';
        } else {
            projects.forEach(p => {
                const item = document.createElement('div');
                item.className = 'project-item';
                item.innerHTML = `
                    <div class="project-item-info">
                        <span class="project-item-name">${p.manufacturer} ${p.model}</span>
                        <span class="project-item-meta">${p.bank_count} banks - ${p.filename}</span>
                    </div>
                    <div class="project-item-actions">
                        <button class="small danger btn-proj-delete" data-file="${p.filename}">Delete</button>
                    </div>
                `;
                item.addEventListener('click', async (e) => {
                    if (e.target.classList.contains('btn-proj-delete')) {
                        e.stopPropagation();
                        if (confirm(`Delete "${p.manufacturer} ${p.model}"?`)) {
                            await fetch(`/api/projects/${encodeURIComponent(p.filename)}`, { method: 'DELETE' });
                            openProjectModal();
                        }
                        return;
                    }
                    const res2 = await fetch(`/api/projects/${encodeURIComponent(p.filename)}`);
                    const data = await res2.json();
                    loadProjectData(data);
                    hideAllModals();
                    toast(`Loaded: ${p.manufacturer} ${p.model}`, 'success');
                });
                list.appendChild(item);
            });
        }
        showModal('modal-open');
    } catch (err) {
        toast('Failed to load projects: ' + err.message, 'error');
    }
}

// ── Templates ─────────────────────────────────────────────────────

async function loadTemplateList() {
    try {
        const res = await fetch('/api/templates');
        const templates = await res.json();
        const select = dom.templateSelect;
        templates.forEach(t => {
            const opt = document.createElement('option');
            opt.value = t.filename;
            opt.textContent = `${t.name} (${t.bank_count} banks)`;
            select.appendChild(opt);
        });
    } catch (err) {
        console.error('Failed to load templates:', err);
    }
}

async function loadTemplate() {
    const filename = dom.templateSelect.value;
    if (!filename) {
        toast('Select a template first', 'info');
        return;
    }
    if (banks.length > 0 && !confirm('Replace current banks with template?')) return;

    try {
        const res = await fetch(`/api/templates/${encodeURIComponent(filename)}`);
        const data = await res.json();
        dom.manufacturer.value = data.manufacturer || '';
        dom.model.value = data.model || '';
        banks = data.banks || [];
        renderTable();
        toast(`Loaded template: ${data.name || filename}`, 'success');
    } catch (err) {
        toast('Failed to load template: ' + err.message, 'error');
    }
}

// ── Preview ───────────────────────────────────────────────────────

async function previewXML() {
    const data = getProjectData();
    if (!data.manufacturer || !data.model) {
        toast('Set Manufacturer and Model first', 'error');
        return;
    }

    try {
        const [midnamRes, middevRes] = await Promise.all([
            fetch('/api/preview/midnam', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            }),
            fetch('/api/preview/middev', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            })
        ]);

        const midnam = await midnamRes.json();
        const middev = await middevRes.json();
        previewCache.midnam = midnam.xml;
        previewCache.middev = middev.xml;

        // Show the active tab's content
        const activeTab = $('.preview-tabs .tab.active');
        const type = activeTab ? activeTab.dataset.tab : 'midnam';
        $('#preview-content').textContent = previewCache[type];

        showModal('modal-preview');
    } catch (err) {
        toast('Preview failed: ' + err.message, 'error');
    }
}

// ── Export ─────────────────────────────────────────────────────────

async function exportFiles() {
    const data = getProjectData();
    if (!data.manufacturer || !data.model) {
        toast('Set Manufacturer and Model first', 'error');
        return;
    }
    if (banks.length === 0) {
        toast('Add some articulations first', 'error');
        return;
    }

    try {
        // Export midnam
        const midnamRes = await fetch('/api/export/midnam', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        const midnamBlob = await midnamRes.blob();
        downloadBlob(midnamBlob, `${data.manufacturer} ${data.model}.midnam`);

        // Export middev
        const middevRes = await fetch('/api/export/middev', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        const middevBlob = await middevRes.blob();
        downloadBlob(middevBlob, `${data.manufacturer}.middev`);

        toast('Exported midnam + middev files', 'success');
    } catch (err) {
        toast('Export failed: ' + err.message, 'error');
    }
}

function downloadBlob(blob, filename) {
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

// ── Install to Pro Tools ──────────────────────────────────────────

async function installToProTools() {
    const data = getProjectData();
    if (!data.manufacturer || !data.model) {
        toast('Set Manufacturer and Model first', 'error');
        return;
    }
    if (banks.length === 0) {
        toast('Add some articulations first', 'error');
        return;
    }

    if (!confirm(`Install "${data.manufacturer} ${data.model}" to Pro Tools?\n\nFiles will be written to:\n/Library/Audio/MIDI Patch Names/${data.manufacturer}/`)) {
        return;
    }

    try {
        const res = await fetch('/api/install', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        const result = await res.json();

        const content = $('#install-result-content');
        if (res.ok) {
            content.innerHTML = `
                <p style="color: var(--success); font-weight: 600; margin-bottom: 12px;">Installed successfully!</p>
                <p style="margin-bottom: 6px;"><strong>Midnam:</strong><br><code style="font-size: 11px; color: var(--text-dim);">${result.midnam_path}</code></p>
                <p><strong>Middev:</strong><br><code style="font-size: 11px; color: var(--text-dim);">${result.middev_path}</code></p>
                <p style="margin-top: 12px; color: var(--text-dim); font-size: 12px;">Restart Pro Tools to see the new patch names.</p>
            `;
        } else {
            content.innerHTML = `<p style="color: var(--danger);">${result.error}</p>`;
        }
        showModal('modal-install-result');
    } catch (err) {
        toast('Install failed: ' + err.message, 'error');
    }
}

// ── Import ────────────────────────────────────────────────────────

async function doImportText() {
    const text = $('#import-text-area').value.trim();
    if (!text) {
        toast('Enter some articulation names', 'error');
        return;
    }

    const startCC32 = parseInt($('#import-start-cc32').value) || 1;
    const replace = $('#import-replace').checked;

    try {
        const res = await fetch('/api/import/text', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text, start_cc32: startCC32 })
        });
        const result = await res.json();

        if (replace) {
            banks = result.banks;
        } else {
            banks = banks.concat(result.banks);
        }
        renderTable();
        hideAllModals();
        toast(`Imported ${result.banks.length} articulations`, 'success');
    } catch (err) {
        toast('Import failed: ' + err.message, 'error');
    }
}

async function doImportMidnam(e) {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    try {
        const res = await fetch('/api/import/midnam', {
            method: 'POST',
            body: formData
        });
        const data = await res.json();

        if (data.error) {
            toast('Import error: ' + data.error, 'error');
            return;
        }

        loadProjectData(data);
        hideAllModals();
        toast(`Imported: ${data.manufacturer} ${data.model} (${data.banks.length} banks)`, 'success');
    } catch (err) {
        toast('Import failed: ' + err.message, 'error');
    }

    // Reset file input
    e.target.value = '';
}

async function doBulkAdd() {
    const text = $('#bulk-add-area').value.trim();
    if (!text) {
        toast('Enter some articulation names', 'error');
        return;
    }

    const startCC32 = parseInt($('#bulk-start-cc32').value) || 1;

    try {
        const res = await fetch('/api/import/text', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text, start_cc32: startCC32 })
        });
        const result = await res.json();
        banks = banks.concat(result.banks);
        renderTable();
        hideAllModals();
        toast(`Added ${result.banks.length} articulations`, 'success');
    } catch (err) {
        toast('Bulk add failed: ' + err.message, 'error');
    }
}

// ── Modal management ──────────────────────────────────────────────

function showModal(id) {
    dom.overlay.classList.add('active');
    $$('.modal').forEach(m => m.classList.remove('active'));
    const modal = $(`#${id}`);
    if (modal) modal.classList.add('active');
}

function hideAllModals() {
    dom.overlay.classList.remove('active');
    $$('.modal').forEach(m => m.classList.remove('active'));
}

// ── Toast notifications ───────────────────────────────────────────

function toast(message, type = 'info') {
    const container = $('#toast-container');
    const el = document.createElement('div');
    el.className = `toast ${type}`;
    el.textContent = message;
    container.appendChild(el);

    setTimeout(() => {
        el.style.opacity = '0';
        el.style.transition = 'opacity 0.3s';
        setTimeout(() => el.remove(), 300);
    }, 3000);
}
