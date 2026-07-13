// ─────────────────────────────────────────────────────────────────────────────
// Global State
// ─────────────────────────────────────────────────────────────────────────────
let currentReport = null;
let networkNetwork = null;
let activeTab = 'alertes';

// Safe item store: avoids JSON escaping hell in onclick attributes
const _itemStore = {};
let _itemStoreIndex = 0;

function storeItem(item) {
    const key = `item_${_itemStoreIndex++}`;
    _itemStore[key] = item;
    return key;
}

function getItem(key) {
    return _itemStore[key] || null;
}

// ─────────────────────────────────────────────────────────────────────────────
// Init – wait for PyWebview bridge
// ─────────────────────────────────────────────────────────────────────────────
window.addEventListener('pywebviewready', function () {
    console.log('[Tafust] PyWebview ready.');

    document.getElementById('btn-scan').addEventListener('click', startScan);
    document.getElementById('btn-export').addEventListener('click', exportJson);
    document.getElementById('btn-close-drawer').addEventListener('click', closeDrawer);
    document.getElementById('drawer-overlay').addEventListener('click', closeDrawer);
    document.getElementById('vt-container').addEventListener('click', handleVtClick);

    document.addEventListener('keydown', (e) => { if (e.key === 'Escape') closeDrawer(); });

    updateSystemInfo();
    setInterval(updateSystemInfo, 5000);
});

// ─────────────────────────────────────────────────────────────────────────────
// System Info
// ─────────────────────────────────────────────────────────────────────────────
async function updateSystemInfo() {
    try {
        const info = await window.pywebview.api.get_system_info();
        if (info.error) return;

        document.getElementById('sys-os').innerText = info.os;
        document.getElementById('sys-res').innerText = `CPU: ${info.cpu}% | RAM: ${info.ram}%`;

        const vtEl = document.getElementById('sys-vt');
        if (info.vt_active) {
            vtEl.innerText = 'VirusTotal Actif';
            vtEl.className = 'text-safe';
        } else {
            vtEl.innerText = 'VirusTotal Inactif';
            vtEl.className = 'text-warning';
        }
    } catch (e) {
        console.error('[Tafust] get_system_info failed', e);
    }
}

function handleVtClick() {
    const text = document.getElementById('sys-vt').innerText;
    if (text.includes('Inactif')) {
        alert('VirusTotal Inactif.\nPour l\'activer, ajoutez VIRUSTOTAL_API_KEY=votre_cle dans le fichier .env à la racine de l\'application.');
    } else {
        alert('VirusTotal est Actif !');
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// State helpers — show/hide with animation
// ─────────────────────────────────────────────────────────────────────────────
function showState(id) {
    const el = document.getElementById(id);
    el.style.display = 'flex';
    el.classList.remove('hidden');
    gsap.fromTo(el, { opacity: 0, y: 12 }, { opacity: 1, y: 0, duration: 0.4, ease: 'power2.out' });
}

function hideState(id) {
    const el = document.getElementById(id);
    gsap.to(el, {
        opacity: 0, y: -8, duration: 0.25, ease: 'power2.in', onComplete: () => {
            el.style.display = 'none';
            el.classList.add('hidden');
        }
    });
}

// ─────────────────────────────────────────────────────────────────────────────
// Scan
// ─────────────────────────────────────────────────────────────────────────────
async function startScan() {
    const btn = document.getElementById('btn-scan');
    const excludeLocal = document.getElementById('exclude-local').checked;

    btn.disabled = true;
    btn.innerHTML = `<i class="ph-bold ph-spinner animate-spin text-xl"></i> Analyse en cours...`;
    btn.classList.add('opacity-50', 'cursor-not-allowed');

    networkNetwork = null;

    // Hide both states that might be visible
    ['empty-state', 'results-view'].forEach(id => {
        const el = document.getElementById(id);
        el.style.display = 'none';
        el.classList.add('hidden');
    });

    showState('loading-state');

    try {
        await window.pywebview.api.start_scan(excludeLocal);
    } catch (e) {
        showToast('Erreur de lancement: ' + e, 'danger');
        resetScanBtn();
    }
}

async function exportJson() {
    try {
        const res = await window.pywebview.api.export_json();
        if (res.success) {
            showToast('Rapport exporté avec succès', 'safe');
        } else if (res.error) {
            showToast("Erreur d'exportation: " + res.error, 'danger');
        }
    } catch (e) {
        showToast('Erreur système: ' + e, 'danger');
    }
}

function resetScanBtn() {
    const btn = document.getElementById('btn-scan');
    btn.disabled = false;
    btn.innerHTML = `<i class="ph-bold ph-lightning text-xl"></i> Relancer l'audit`;
    btn.classList.remove('opacity-50', 'cursor-not-allowed');
}

// ─────────────────────────────────────────────────────────────────────────────
// Callbacks from Python
// ─────────────────────────────────────────────────────────────────────────────
window.updateProgress = function (step, detail) {
    const el = document.getElementById('loading-step');
    if (el) {
        el.innerText = detail;
        gsap.fromTo(el, { opacity: 0, y: 10 }, { opacity: 1, y: 0, duration: 0.3 });
    }
};

window.onScanComplete = function (report) {
    console.log('[Tafust] Scan complete', report);
    currentReport = report;

    hideState('loading-state');

    setTimeout(() => {
        renderSummaryCards(report.summary);
        buildTabs(report);
        switchTab('alertes');
        showState('results-view');
        resetScanBtn();
        showToast('Audit terminé avec succès', 'safe');
        // Smooth scroll to results
        setTimeout(() => {
            document.getElementById('results-view').scrollIntoView({ behavior: 'smooth', block: 'start' });
        }, 300);
    }, 350);
};

window.onScanError = function (error) {
    console.error('[Tafust] Scan error', error);
    hideState('loading-state');
    setTimeout(() => {
        showState('empty-state');
        resetScanBtn();
        showToast("Erreur d'audit: " + error, 'danger');
    }, 350);
};

// ─────────────────────────────────────────────────────────────────────────────
// Summary Cards
// ─────────────────────────────────────────────────────────────────────────────
function renderSummaryCards(summary) {
    if (!summary) return;

    const score = Math.max(0, Math.min(100, 100 - (summary.nb_alertes || 0) * 25 - (summary.nb_surveiller || 0) * 8));
    let scoreColor = 'text-safe';
    if (score < 80) scoreColor = 'text-warning';
    if (score < 50) scoreColor = 'text-danger';

    const html = `
        <div class="glass-panel p-4 border-l-4 border-l-accent flex flex-col justify-center">
            <div class="text-gray-400 text-xs font-semibold uppercase tracking-wider mb-1">Score Sécurité</div>
            <div class="text-3xl font-bold ${scoreColor}">${score}/100</div>
        </div>
        <div class="glass-panel p-4 border-l-4 border-l-danger flex flex-col justify-center cursor-pointer hover:opacity-80 transition-opacity" onclick="switchTab('alertes')">
            <div class="text-gray-400 text-xs font-semibold uppercase tracking-wider mb-1">Alertes</div>
            <div class="text-3xl font-bold text-white">${summary.nb_alertes || 0}</div>
        </div>
        <div class="glass-panel p-4 border-l-4 border-l-warning flex flex-col justify-center cursor-pointer hover:opacity-80 transition-opacity" onclick="switchTab('surveiller')">
            <div class="text-gray-400 text-xs font-semibold uppercase tracking-wider mb-1">À Surveiller</div>
            <div class="text-3xl font-bold text-white">${summary.nb_surveiller || 0}</div>
        </div>
        <div class="glass-panel p-4 border-l-4 border-l-safe flex flex-col justify-center cursor-pointer hover:opacity-80 transition-opacity" onclick="switchTab('legitimes')">
            <div class="text-gray-400 text-xs font-semibold uppercase tracking-wider mb-1">Légitimes</div>
            <div class="text-3xl font-bold text-white">${summary.nb_legitimes || 0}</div>
        </div>
    `;
    document.getElementById('summary-cards').innerHTML = html;

    gsap.from('#summary-cards > div', {
        y: 20, opacity: 0, duration: 0.5, stagger: 0.1, ease: 'back.out(1.7)'
    });
}

// ─────────────────────────────────────────────────────────────────────────────
// Tabs
// ─────────────────────────────────────────────────────────────────────────────
function buildTabs(report) {
    const allForTopology = [
        ...(report.alertes || []),
        ...(report.surveiller || []),
        ...(report.legitimes || [])
    ];

    const tabs = [
        { id: 'alertes',    label: 'Alertes',     icon: 'ph-warning-circle', color: 'text-danger',  count: (report.alertes || []).length },
        { id: 'surveiller', label: 'Surveillance', icon: 'ph-eye',            color: 'text-warning', count: (report.surveiller || []).length },
        { id: 'legitimes',  label: 'Légitimes',    icon: 'ph-check-circle',   color: 'text-safe',    count: (report.legitimes || []).length },
        { id: 'topology',   label: 'Topologie',    icon: 'ph-graph',          color: 'text-accent',  count: allForTopology.length },
    ];

    let html = '';
    tabs.forEach(t => {
        const countHtml = t.count > 0
            ? `<span class="ml-2 bg-surface px-2 py-0.5 rounded-full text-xs text-gray-400">${t.count}</span>`
            : '';
        html += `
            <button onclick="switchTab('${t.id}')" id="tab-${t.id}"
                class="tab-btn px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200
                       text-gray-400 hover:text-white flex items-center gap-1.5">
                <i class="ph-fill ${t.icon} ${t.color}"></i>
                ${t.label}${countHtml}
            </button>`;
    });
    document.getElementById('tabs-container').innerHTML = html;
}

window.switchTab = function (tabId) {
    activeTab = tabId;

    document.querySelectorAll('.tab-btn').forEach(btn => {
        if (btn.id === `tab-${tabId}`) {
            btn.classList.add('bg-surface-light', 'text-white', 'border', 'border-border');
            btn.classList.remove('text-gray-400');
        } else {
            btn.classList.remove('bg-surface-light', 'text-white', 'border', 'border-border');
            btn.classList.add('text-gray-400');
        }
    });

    const listContainer  = document.getElementById('results-list');
    const graphContainer = document.getElementById('network-graph-container');

    if (tabId === 'topology') {
        listContainer.style.display  = 'none';
        graphContainer.style.display = 'block';
        graphContainer.classList.remove('hidden');
        if (!networkNetwork) renderTopology();
    } else {
        graphContainer.style.display = 'none';
        graphContainer.classList.add('hidden');
        listContainer.style.display  = 'block';
        renderList(tabId);
    }
};

// ─────────────────────────────────────────────────────────────────────────────
// Risk helpers
// ─────────────────────────────────────────────────────────────────────────────
function getRiskClass(level) {
    const l = (level || '').toUpperCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');
    if (l === 'CRITIQUE') return 'critique';
    if (l === 'ELEVE')    return 'eleve';
    if (l === 'MODERE')   return 'modere';
    return 'faible';
}

function getRiskColorHex(level) {
    const c = getRiskClass(level);
    if (c === 'critique') return '#ff2a5f';
    if (c === 'eleve')    return '#ff6b35';
    if (c === 'modere')   return '#ffb800';
    return '#00ffa3';
}

function getTabBorderColor(tabId) {
    if (tabId === 'alertes')    return '#ff2a5f';
    if (tabId === 'surveiller') return '#ffb800';
    if (tabId === 'legitimes')  return '#00ffa3';
    return '#00f0ff';
}

function getTabIcon(tabId) {
    if (tabId === 'alertes')    return 'ph-warning-circle text-danger';
    if (tabId === 'surveiller') return 'ph-eye text-warning';
    if (tabId === 'legitimes')  return 'ph-check-circle text-safe';
    return 'ph-graph text-accent';
}

// ─────────────────────────────────────────────────────────────────────────────
// List rendering — ALL items shown, no scroll limit
// Légitimes & Surveillance → 2-column grid (compact)
// Alertes → full-width (needs full attention)
// ─────────────────────────────────────────────────────────────────────────────
function renderList(tabId) {
    const container = document.getElementById('results-list');
    if (!currentReport) return;

    const data = currentReport[tabId] || [];

    if (data.length === 0) {
        container.innerHTML = `
            <div class="flex flex-col items-center justify-center py-16 text-center text-gray-500">
                <i class="ph ph-check-fat text-4xl mb-3 text-safe opacity-40"></i>
                <p>Aucun résultat dans cette catégorie.</p>
            </div>`;
        return;
    }

    const borderColor = getTabBorderColor(tabId);
    const icon        = getTabIcon(tabId);

    // Use 2-col grid for tabs with many items (surveillance + légitimes)
    const useGrid = (tabId === 'legitimes' || tabId === 'surveiller') && data.length > 3;

    // Count header
    const countBadgeColor = tabId === 'alertes' ? 'text-danger border-danger/30 bg-danger/10'
                          : tabId === 'surveiller' ? 'text-warning border-warning/30 bg-warning/10'
                          : tabId === 'legitimes'  ? 'text-safe border-safe/30 bg-safe/10'
                          : 'text-accent border-accent/30 bg-accent/10';

    let html = `
        <div class="flex items-center gap-3 mb-4">
            <span class="text-xs font-bold uppercase tracking-wider px-3 py-1 rounded-full border ${countBadgeColor}">
                ${data.length} entrée${data.length > 1 ? 's' : ''}
            </span>
            <div class="flex-1 h-px bg-border"></div>
            ${useGrid ? '<span class="text-xs text-gray-600 italic">vue compacte</span>' : ''}
        </div>
        <div class="${useGrid ? 'grid grid-cols-2 gap-3' : 'flex flex-col gap-3'}">
    `;

    data.forEach((item) => {
        const riskClass = getRiskClass(item.risk_level);
        const isGrouped = Array.isArray(item.ports_list);

        const portDisplay = isGrouped
            ? item.ports_list.slice(0, 4).join(', ') + (item.ports_list.length > 4 ? ` +${item.ports_list.length - 4}` : '')
            : `${item.port}`;
        const portLabel = isGrouped
            ? `<span><i class="ph ph-stack"></i> ${item.ports_list.length} port(s): ${portDisplay}</span>`
            : `<span><i class="ph ph-plugs"></i> Port ${item.port} (${item.proto})</span>`;

        const vtBadge = item.vt_positives && item.vt_positives > 0
            ? `<span class="text-danger flex items-center gap-1"><i class="ph-fill ph-virus"></i> ${item.vt_positives}/${item.vt_total} VT</span>`
            : '';

        const pidLabel = item.pid
            ? `<span class="text-xs font-mono text-gray-400 bg-surface px-2 py-0.5 rounded">PID: ${item.pid}</span>`
            : '';

        const countBadge = isGrouped && item.count > 1
            ? `<span class="text-xs bg-accent/10 text-accent border border-accent/20 px-2 py-0.5 rounded-full">${item.count}x</span>`
            : '';

        const key = storeItem(item);

        if (useGrid) {
            // Compact grid card
            html += `
                <div class="result-card glass-panel p-3 cursor-pointer flex items-center justify-between gap-2 min-w-0"
                     style="border-left:3px solid ${borderColor}"
                     onclick="openDrawer(getItem('${key}'))">
                    <div class="flex items-center gap-3 min-w-0">
                        <div class="w-8 h-8 flex-shrink-0 rounded-full bg-surface-light border border-border flex items-center justify-center">
                            <i class="ph-fill ${icon} text-base"></i>
                        </div>
                        <div class="min-w-0">
                            <div class="font-semibold text-white text-sm truncate flex items-center gap-1.5">
                                ${item.proc || 'Inconnu'} ${countBadge}
                            </div>
                            <div class="text-xs font-mono text-gray-500 mt-0.5 truncate flex items-center gap-2">
                                ${portLabel} ${vtBadge}
                            </div>
                            ${pidLabel ? `<div class="mt-1">${pidLabel}</div>` : ''}
                        </div>
                    </div>
                    <div class="flex items-center gap-2 flex-shrink-0">
                        <div class="badge ${riskClass} text-xs">${item.risk_level || 'INFO'}</div>
                        <i class="ph ph-caret-right text-gray-600 text-xs"></i>
                    </div>
                </div>`;
        } else {
            // Full-width card
            html += `
                <div class="result-card glass-panel p-4 cursor-pointer flex items-center justify-between"
                     style="border-left:3px solid ${borderColor}"
                     onclick="openDrawer(getItem('${key}'))">
                    <div class="flex items-center gap-4 min-w-0">
                        <div class="w-10 h-10 flex-shrink-0 rounded-full bg-surface-light border border-border flex items-center justify-center">
                            <i class="ph-fill ${icon} text-xl"></i>
                        </div>
                        <div class="min-w-0">
                            <div class="font-bold text-white flex items-center gap-2 flex-wrap">
                                ${item.proc || 'Inconnu'}
                                ${pidLabel}
                                ${countBadge}
                            </div>
                            <div class="text-sm font-mono text-gray-400 mt-1 flex items-center gap-3 flex-wrap">
                                ${portLabel}
                                ${vtBadge}
                            </div>
                        </div>
                    </div>
                    <div class="flex items-center gap-3 flex-shrink-0 ml-4">
                        <div class="badge ${riskClass}">${item.risk_level || 'INFO'}</div>
                        <i class="ph ph-caret-right text-gray-500"></i>
                    </div>
                </div>`;
        }
    });

    html += '</div>';
    container.innerHTML = html;

    gsap.from('.result-card', {
        y: 14, opacity: 0, duration: 0.35, stagger: 0.03, ease: 'power2.out'
    });
}

// ─────────────────────────────────────────────────────────────────────────────
// Side Drawer (Detail Panel)
// ─────────────────────────────────────────────────────────────────────────────
window.openDrawer = function (item) {
    const content   = document.getElementById('drawer-content');
    const riskClass = getRiskClass(item.risk_level);
    const riskColor = getRiskColorHex(item.risk_level);

    const isGrouped  = Array.isArray(item.ports_list);
    const portDisplay = isGrouped ? item.ports_list.join(', ') : `${item.port}`;
    const ipDisplay   = isGrouped ? (item.ips_list || []).join(', ') : item.ip;

    const vtPositives = parseInt(item.vt_positives) || 0;
    const vtTotal     = parseInt(item.vt_total) || 0;
    const vtColor     = vtPositives > 0 ? 'text-danger' : 'text-safe';
    const vtLabel     = vtPositives > 0 ? `${vtPositives} / ${vtTotal} détections` : 'Aucune détection';

    const exposureHtml = item.exposure
        ? `<div class="flex items-start gap-2 text-sm text-gray-400 mt-2">
               <i class="ph ph-broadcast text-accent mt-0.5"></i>
               <span>${item.exposure}</span>
           </div>`
        : '';

    const sigHtml = item.signature_status && item.signature_status !== 'Unavailable'
        ? `<div class="mt-2 text-xs font-mono text-gray-500">
               <i class="ph ph-seal-check text-safe"></i> ${item.signature_status}
               ${item.publisher ? `— ${item.publisher}` : ''}
           </div>`
        : '';

    let psBlock = '';
    if (item.powershell && item.powershell.length > 0) {
        const lines = item.powershell.map(c =>
            c.startsWith('#')
                ? `<span class="text-gray-500">${c}</span>`
                : `PS&gt; <span class="text-accent">${c}</span>`
        ).join('\n');
        const psRaw = item.powershell.filter(c => !c.startsWith('#')).join('; ');
        psBlock = `
            <div>
                <h4 class="text-sm font-bold text-white mb-2 flex items-center gap-2">
                    <i class="ph-fill ph-terminal-window text-accent"></i>
                    Remédiation PowerShell
                </h4>
                <div class="bg-[#05080f] border border-border rounded-xl p-4 font-mono text-xs overflow-x-auto relative group">
                    <button onclick="copyToClipboard(this)"
                            data-text="${psRaw.replace(/"/g, '&quot;')}"
                            class="absolute top-2 right-2 p-1.5 bg-surface rounded text-gray-400 hover:text-white opacity-0 group-hover:opacity-100 transition-opacity">
                        <i class="ph ph-copy"></i>
                    </button>
                    <pre class="whitespace-pre-wrap leading-relaxed">${lines}</pre>
                </div>
            </div>`;
    }

    content.innerHTML = `
        <div class="flex items-start justify-between gap-4">
            <div class="min-w-0">
                <h3 class="text-2xl font-bold text-white mb-1 truncate">${item.proc || 'Inconnu'}</h3>
                <p class="text-sm text-gray-400 font-mono break-all">${item.path || 'Chemin indisponible'}</p>
                ${sigHtml}
            </div>
            <div class="badge ${riskClass} text-sm flex-shrink-0"
                 style="border-color:${riskColor}33;background:${riskColor}15;color:${riskColor}">
                ${item.risk_level || 'INFO'}
            </div>
        </div>

        <div class="grid grid-cols-2 gap-3">
            <div class="glass-panel p-4 rounded-xl">
                <div class="text-xs text-gray-500 uppercase tracking-wider mb-1 flex items-center gap-1">
                    <i class="ph ph-plugs text-accent"></i> Réseau
                </div>
                <div class="font-mono text-white text-sm"><span class="text-accent">${ipDisplay || '—'}</span></div>
                <div class="text-xs text-gray-400 mt-1">Port(s): ${portDisplay || '—'} · ${item.proto || '—'}</div>
                ${exposureHtml}
            </div>

            <div class="glass-panel p-4 rounded-xl">
                <div class="text-xs text-gray-500 uppercase tracking-wider mb-1 flex items-center gap-1">
                    <i class="ph ph-virus text-accent"></i> VirusTotal
                </div>
                <div class="font-mono ${vtColor} text-sm">${vtLabel}</div>
                <div class="text-xs text-gray-400 mt-1 truncate">${item.vt_vendor || item.reputation_summary || 'Non analysé'}</div>
            </div>

            <div class="glass-panel p-4 rounded-xl">
                <div class="text-xs text-gray-500 uppercase tracking-wider mb-1 flex items-center gap-1">
                    <i class="ph ph-identification-badge text-accent"></i> PID
                </div>
                <div class="font-mono text-white text-sm">${item.pid || '—'}</div>
            </div>

            <div class="glass-panel p-4 rounded-xl">
                <div class="text-xs text-gray-500 uppercase tracking-wider mb-1 flex items-center gap-1">
                    <i class="ph ph-link text-accent"></i> État connexion
                </div>
                <div class="font-mono text-white text-sm">${item.state || 'LISTENING'}</div>
            </div>
        </div>

        <div>
            <h4 class="text-sm font-bold text-white mb-2 flex items-center gap-2">
                <i class="ph-fill ph-magnifying-glass text-accent"></i> Analyse
            </h4>
            <div class="bg-surface-light border border-border rounded-xl p-4 text-sm text-gray-300 leading-relaxed">
                ${item.justification || 'Aucune justification détaillée.'}
            </div>
        </div>

        ${psBlock}
    `;

    const overlay = document.getElementById('drawer-overlay');
    const drawer  = document.getElementById('side-drawer');

    overlay.classList.remove('pointer-events-none');
    gsap.to(overlay, { opacity: 1, duration: 0.3 });
    gsap.to(drawer,  { x: 0, duration: 0.4, ease: 'power3.out' });
};

function closeDrawer() {
    const overlay = document.getElementById('drawer-overlay');
    const drawer  = document.getElementById('side-drawer');

    overlay.classList.add('pointer-events-none');
    gsap.to(overlay, { opacity: 0, duration: 0.3 });
    gsap.to(drawer,  { x: '100%', duration: 0.3, ease: 'power3.in' });
}

window.copyToClipboard = async function (btn) {
    const text = btn.getAttribute('data-text');
    try {
        await window.pywebview.api.copy_to_clipboard(text);
        const icon = btn.querySelector('i');
        icon.className = 'ph-fill ph-check text-safe';
        setTimeout(() => { icon.className = 'ph ph-copy'; }, 2000);
        showToast('Copié dans le presse-papier', 'safe');
    } catch (e) {
        showToast('Erreur de copie', 'danger');
    }
};

// ─────────────────────────────────────────────────────────────────────────────
// Topology Graph (Vis.js)
// ─────────────────────────────────────────────────────────────────────────────
function renderTopology() {
    if (!currentReport) return;

    const container = document.getElementById('network-graph');
    const nodes = new vis.DataSet();
    const edges = new vis.DataSet();

    nodes.add({
        id: 'localhost',
        label: 'Système Local',
        shape: 'dot',
        size: 25,
        color: { background: '#00f0ff', border: '#ffffff33' },
        font: { color: 'white', size: 13 }
    });

    const allData = [
        ...(currentReport.alertes    || []),
        ...(currentReport.surveiller || []),
        ...(currentReport.legitimes  || [])
    ];

    const addedNodes = new Set();

    allData.forEach((item, i) => {
        const nodeId = `proc_${i}`;
        if (!addedNodes.has(nodeId)) {
            const color = getRiskColorHex(item.risk_level);
            const port  = Array.isArray(item.ports_list) ? item.ports_list[0] : item.port;

            nodes.add({
                id: nodeId,
                label: item.proc || 'Unknown',
                title: `Processus : ${item.proc}\nPort : ${port}\nIP : ${item.ip || '—'}\nRisque : ${item.risk_level}`,
                shape: 'dot',
                size: 14,
                color: { background: color, border: 'rgba(255,255,255,0.15)' },
                font: { color: '#94a3b8', size: 11 }
            });

            edges.add({
                from: 'localhost',
                to: nodeId,
                label: `${port}`,
                font: { color: '#475569', size: 10, background: 'transparent' },
                color: { color: '#2a3441', highlight: '#00f0ff' }
            });

            addedNodes.add(nodeId);
        }
    });

    const data    = { nodes, edges };
    const options = {
        nodes: { borderWidth: 2 },
        edges: { smooth: { type: 'continuous' } },
        physics: {
            solver: 'forceAtlas2Based',
            forceAtlas2Based: {
                gravitationalConstant: -50,
                centralGravity: 0.01,
                springLength: 110,
                springConstant: 0.08
            }
        },
        interaction: { hover: true, tooltipDelay: 150 }
    };

    networkNetwork = new vis.Network(container, data, options);

    networkNetwork.on('click', (params) => {
        if (params.nodes.length === 0 || params.nodes[0] === 'localhost') return;
        const idx = parseInt(params.nodes[0].replace('proc_', ''), 10);
        if (!isNaN(idx) && allData[idx]) openDrawer(allData[idx]);
    });
}

// ─────────────────────────────────────────────────────────────────────────────
// Toasts
// ─────────────────────────────────────────────────────────────────────────────
function showToast(message, type = 'accent') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');

    const borderCol = type === 'safe' ? 'border-safe' : type === 'danger' ? 'border-danger' : 'border-accent';
    const iconCol   = type === 'safe' ? 'text-safe'   : type === 'danger' ? 'text-danger'   : 'text-accent';
    const icon      = type === 'safe' ? 'ph-check-circle' : type === 'danger' ? 'ph-warning-circle' : 'ph-info';

    toast.className = `glass-panel px-4 py-3 border-l-4 ${borderCol} flex items-center gap-3 toast-enter shadow-lg`;
    toast.innerHTML = `
        <i class="ph-fill ${icon} ${iconCol} text-xl"></i>
        <span class="text-sm text-white font-medium">${message}</span>`;

    container.appendChild(toast);

    setTimeout(() => {
        toast.classList.replace('toast-enter', 'toast-exit');
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}
