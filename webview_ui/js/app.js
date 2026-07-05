// Global State
let currentReport = null;
let networkNetwork = null;
let activeTab = 'alertes';

// Initialize when pywebview is ready
window.addEventListener('pywebviewready', function() {
    console.log("PyWebview is ready.");
    console.log("window.pywebview: ", window.pywebview);
    
    // Setup event listeners ONLY after ready
    document.getElementById('btn-scan').addEventListener('click', startScan);
    document.getElementById('btn-export').addEventListener('click', exportJson);
    document.getElementById('btn-close-drawer').addEventListener('click', closeDrawer);
    document.getElementById('drawer-overlay').addEventListener('click', closeDrawer);
    document.getElementById('vt-container').addEventListener('click', handleVtClick);
    
    // Fetch initial system info
    updateSystemInfo();
    setInterval(updateSystemInfo, 5000);
});

// --- API Calls ---

async function updateSystemInfo() {
    try {
        const info = await window.pywebview.api.get_system_info();
        if (info.error) return;
        
        document.getElementById('sys-os').innerText = info.os;
        document.getElementById('sys-res').innerText = `CPU: ${info.cpu}% | RAM: ${info.ram}%`;
        
        const vtEl = document.getElementById('sys-vt');
        if (info.vt_active) {
            vtEl.innerText = "VirusTotal Actif";
            vtEl.className = "text-safe";
        } else {
            vtEl.innerText = "VirusTotal Inactif";
            vtEl.className = "text-warning";
        }
    } catch (e) {
        console.error("Failed to get sys info", e);
    }
}

function handleVtClick() {
    const text = document.getElementById('sys-vt').innerText;
    if (text.includes("Inactif")) {
        alert("VirusTotal Inactif.\nPour l'activer, ajoutez VIRUSTOTAL_API_KEY=votre_cle dans le fichier .env à la racine de l'application.");
    } else {
        alert("VirusTotal est Actif !");
    }
}

async function startScan() {
    const btn = document.getElementById('btn-scan');
    const excludeLocal = document.getElementById('exclude-local').checked;
    
    // UI Updates
    btn.disabled = true;
    btn.innerHTML = `<i class="ph-bold ph-spinner animate-spin text-xl"></i> Initialisation...`;
    btn.classList.add('opacity-50', 'cursor-not-allowed');
    
    gsap.to('#empty-state, #results-view', { opacity: 0, duration: 0.3, onComplete: () => {
        document.getElementById('empty-state').style.display = 'none';
        document.getElementById('results-view').style.display = 'none';
        
        const loading = document.getElementById('loading-state');
        loading.style.display = 'flex';
        gsap.to(loading, { opacity: 1, duration: 0.3 });
    }});

    try {
        await window.pywebview.api.start_scan(excludeLocal);
    } catch (e) {
        showToast("Erreur de lancement: " + e, "danger");
        resetScanBtn();
    }
}

async function exportJson() {
    try {
        const res = await window.pywebview.api.export_json();
        if (res.success) {
            showToast("Rapport exporté avec succès", "safe");
        } else if (res.error) {
            showToast("Erreur d'exportation: " + res.error, "danger");
        }
    } catch (e) {
        showToast("Erreur système: " + e, "danger");
    }
}

// --- Callbacks from Python ---

window.updateProgress = function(step, detail) {
    const el = document.getElementById('loading-step');
    if (el) {
        el.innerText = detail;
        gsap.fromTo(el, { opacity: 0, y: 10 }, { opacity: 1, y: 0, duration: 0.3 });
    }
};

window.onScanComplete = function(report) {
    console.log("Scan complete", report);
    currentReport = report;
    
    // Hide loading, show results
    gsap.to('#loading-state', { opacity: 0, duration: 0.3, onComplete: () => {
        document.getElementById('loading-state').style.display = 'none';
        
        const resultsView = document.getElementById('results-view');
        resultsView.style.display = 'flex';
        gsap.to(resultsView, { opacity: 1, duration: 0.5 });
        
        renderSummaryCards(report.summary);
        buildTabs(report);
        switchTab('alertes');
        
        resetScanBtn();
        showToast("Audit terminé avec succès", "safe");
    }});
};

window.onScanError = function(error) {
    console.error("Scan error", error);
    gsap.to('#loading-state', { opacity: 0, duration: 0.3, onComplete: () => {
        document.getElementById('loading-state').style.display = 'none';
        document.getElementById('empty-state').style.display = 'flex';
        gsap.to('#empty-state', { opacity: 1, duration: 0.3 });
        
        resetScanBtn();
        showToast("Erreur d'audit: " + error, "danger");
    }});
};

function resetScanBtn() {
    const btn = document.getElementById('btn-scan');
    btn.disabled = false;
    btn.innerHTML = `<i class="ph-bold ph-lightning text-xl"></i> Relancer l'audit`;
    btn.classList.remove('opacity-50', 'cursor-not-allowed');
}

// --- UI Rendering ---

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
        <div class="glass-panel p-4 border-l-4 border-l-danger flex flex-col justify-center">
            <div class="text-gray-400 text-xs font-semibold uppercase tracking-wider mb-1">Alertes</div>
            <div class="text-3xl font-bold text-white">${summary.nb_alertes || 0}</div>
        </div>
        <div class="glass-panel p-4 border-l-4 border-l-warning flex flex-col justify-center">
            <div class="text-gray-400 text-xs font-semibold uppercase tracking-wider mb-1">À Surveiller</div>
            <div class="text-3xl font-bold text-white">${summary.nb_surveiller || 0}</div>
        </div>
        <div class="glass-panel p-4 border-l-4 border-l-safe flex flex-col justify-center">
            <div class="text-gray-400 text-xs font-semibold uppercase tracking-wider mb-1">Légitimes</div>
            <div class="text-3xl font-bold text-white">${summary.nb_legitimes || 0}</div>
        </div>
    `;
    document.getElementById('summary-cards').innerHTML = html;
    
    gsap.from('#summary-cards > div', {
        y: 20, opacity: 0, duration: 0.5, stagger: 0.1, ease: "back.out(1.7)"
    });
}

function buildTabs(report) {
    const tabs = [
        { id: 'alertes', label: '🔴 Alertes', count: (report.alertes || []).length },
        { id: 'surveiller', label: '🟡 Surveillance', count: (report.surveiller || []).length },
        { id: 'legitimes', label: '✅ Légitimes', count: (report.legitimes || []).length },
        { id: 'topology', label: '🕸 Topologie', count: 0 },
    ];
    
    let html = '';
    tabs.forEach(t => {
        const countHtml = t.count > 0 ? `<span class="ml-2 bg-surface-light px-2 py-0.5 rounded-full text-xs">${t.count}</span>` : '';
        html += `<button onclick="switchTab('${t.id}')" id="tab-${t.id}" class="tab-btn px-4 py-2 rounded-lg text-sm font-medium transition-colors text-gray-400 hover:text-white flex items-center">
                    ${t.label} ${countHtml}
                 </button>`;
    });
    document.getElementById('tabs-container').innerHTML = html;
}

window.switchTab = function(tabId) {
    activeTab = tabId;
    
    // Update active state
    document.querySelectorAll('.tab-btn').forEach(btn => {
        if (btn.id === `tab-${tabId}`) {
            btn.classList.add('bg-surface-light', 'text-white', 'border', 'border-border');
            btn.classList.remove('text-gray-400', 'border-transparent');
        } else {
            btn.classList.remove('bg-surface-light', 'text-white', 'border', 'border-border');
            btn.classList.add('text-gray-400', 'border-transparent');
        }
    });
    
    const listContainer = document.getElementById('results-list');
    const graphContainer = document.getElementById('network-graph-container');
    
    if (tabId === 'topology') {
        listContainer.style.display = 'none';
        graphContainer.style.display = 'block';
        if (!networkNetwork) renderTopology();
    } else {
        graphContainer.style.display = 'none';
        listContainer.style.display = 'block';
        renderList(tabId);
    }
}

function getRiskClass(level) {
    const l = (level || '').toUpperCase();
    if(l === 'CRITIQUE') return 'critique';
    if(l === 'ÉLEVÉ' || l === 'ELEVE') return 'eleve';
    if(l === 'MODÉRÉ' || l === 'MODERE') return 'modere';
    return 'faible';
}

function getRiskColorHex(level) {
    const c = getRiskClass(level);
    if(c === 'critique') return '#ff2a5f';
    if(c === 'eleve') return '#ff6b35';
    if(c === 'modere') return '#ffb800';
    return '#00ffa3';
}

function renderList(tabId) {
    const container = document.getElementById('results-list');
    if (!currentReport) return;
    
    const data = currentReport[tabId] || [];
    if (data.length === 0) {
        container.innerHTML = `<div class="text-center text-gray-500 py-10">Aucun résultat dans cette catégorie.</div>`;
        return;
    }
    
    let html = '';
    data.forEach((item, index) => {
        const riskClass = getRiskClass(item.risk_level);
        const icon = tabId === 'alertes' ? 'ph-warning-circle text-danger' : 
                     tabId === 'surveiller' ? 'ph-info text-warning' : 'ph-check-circle text-safe';
                     
        html += `
            <div class="result-card glass-panel p-4 mb-3 cursor-pointer flex items-center justify-between border-l-2" 
                 style="border-left-color: ${getRiskColorHex(item.risk_level)}"
                 onclick='openDrawer(${JSON.stringify(item).replace(/'/g, "&#39;")})'>
                <div class="flex items-center gap-4">
                    <div class="w-10 h-10 rounded-full bg-surface-light border border-border flex items-center justify-center">
                        <i class="ph-fill ${icon} text-xl"></i>
                    </div>
                    <div>
                        <div class="font-bold text-white flex items-center gap-2">
                            ${item.proc || 'Inconnu'} 
                            <span class="text-xs font-mono text-gray-400 bg-surface px-2 py-0.5 rounded">PID: ${item.pid || '-'}</span>
                        </div>
                        <div class="text-sm font-mono text-gray-400 mt-1 flex items-center gap-3">
                            <span><i class="ph ph-plugs"></i> Port ${item.port} (${item.proto})</span>
                            ${item.vt_positives && item.vt_positives > 0 ? `<span class="text-danger flex items-center gap-1"><i class="ph-fill ph-virus"></i> ${item.vt_positives}/${item.vt_total} VT</span>` : ''}
                        </div>
                    </div>
                </div>
                <div class="flex items-center gap-3">
                    <div class="badge ${riskClass}">${item.risk_level || 'INFO'}</div>
                    <i class="ph ph-caret-right text-gray-500"></i>
                </div>
            </div>
        `;
    });
    
    container.innerHTML = html;
    
    // Animate list items
    gsap.from('.result-card', {
        y: 20, opacity: 0, duration: 0.4, stagger: 0.05, ease: "power2.out"
    });
}

// --- Side Drawer ---

window.openDrawer = function(item) {
    const content = document.getElementById('drawer-content');
    const riskClass = getRiskClass(item.risk_level);
    
    // Build Powershell block
    let psBlock = '';
    if (item.powershell && item.powershell.length > 0) {
        const lines = item.powershell.map(c => c.startsWith('#') ? `<span class="text-gray-500">${c}</span>` : `PS> <span class="text-accent">${c}</span>`).join('\n');
        psBlock = `
            <div class="mt-6">
                <h4 class="text-sm font-bold text-white mb-2 flex items-center gap-2"><i class="ph-fill ph-terminal-window"></i> Remédiation PowerShell</h4>
                <div class="bg-[#05080f] border border-border rounded-xl p-4 font-mono text-xs overflow-x-auto relative group">
                    <button onclick="copyToClipboard(this)" data-text="${item.powershell.filter(c => !c.startsWith('#')).join('; ')}" class="absolute top-2 right-2 p-1.5 bg-surface rounded text-gray-400 hover:text-white opacity-0 group-hover:opacity-100 transition-opacity">
                        <i class="ph ph-copy"></i>
                    </button>
                    <pre class="whitespace-pre-wrap leading-relaxed">${lines}</pre>
                </div>
            </div>
        `;
    }

    // Build Details
    content.innerHTML = `
        <div class="flex items-start justify-between">
            <div>
                <h3 class="text-2xl font-bold text-white mb-1">${item.proc || 'Inconnu'}</h3>
                <p class="text-sm text-gray-400 font-mono">${item.path || 'Chemin indisponible'}</p>
            </div>
            <div class="badge ${riskClass} text-sm">${item.risk_level || 'INFO'}</div>
        </div>
        
        <div class="grid grid-cols-2 gap-4 mt-6">
            <div class="glass-panel p-4 rounded-xl border border-border">
                <div class="text-xs text-gray-500 uppercase tracking-wider mb-1">Réseau</div>
                <div class="font-mono text-white text-sm"><span class="text-accent">${item.ip}</span>:${item.port}</div>
                <div class="text-xs text-gray-400 mt-1">${item.proto}</div>
            </div>
            <div class="glass-panel p-4 rounded-xl border border-border">
                <div class="text-xs text-gray-500 uppercase tracking-wider mb-1">VirusTotal</div>
                <div class="font-mono ${item.vt_positives > 0 ? 'text-danger' : 'text-safe'} text-sm">${item.vt_positives || 0} / ${item.vt_total || 0} detections</div>
                <div class="text-xs text-gray-400 mt-1 truncate">${item.vt_vendor || 'Non analysé'}</div>
            </div>
        </div>

        <div class="mt-6">
            <h4 class="text-sm font-bold text-white mb-2 flex items-center gap-2"><i class="ph-fill ph-magnifying-glass"></i> Analyse</h4>
            <div class="bg-surface-light border border-border rounded-xl p-4 text-sm text-gray-300 leading-relaxed">
                ${item.justification || 'Aucune justification détaillée.'}
            </div>
        </div>
        
        ${psBlock}
    `;

    // Show overlay and drawer
    const overlay = document.getElementById('drawer-overlay');
    const drawer = document.getElementById('side-drawer');
    
    overlay.classList.remove('pointer-events-none');
    gsap.to(overlay, { opacity: 1, duration: 0.3 });
    gsap.to(drawer, { x: 0, duration: 0.4, ease: "power3.out" });
}

function closeDrawer() {
    const overlay = document.getElementById('drawer-overlay');
    const drawer = document.getElementById('side-drawer');
    
    overlay.classList.add('pointer-events-none');
    gsap.to(overlay, { opacity: 0, duration: 0.3 });
    gsap.to(drawer, { x: '100%', duration: 0.3, ease: "power3.in" });
}

window.copyToClipboard = async function(btn) {
    const text = btn.getAttribute('data-text');
    try {
        await window.pywebview.api.copy_to_clipboard(text);
        
        const icon = btn.querySelector('i');
        icon.className = "ph-fill ph-check text-safe";
        setTimeout(() => { icon.className = "ph ph-copy text-gray-400"; }, 2000);
        
        showToast("Copié dans le presse-papier", "safe");
    } catch(e) {
        showToast("Erreur de copie", "danger");
    }
}

// --- Topology Graph (Vis.js) ---

function renderTopology() {
    if (!currentReport) return;
    
    const container = document.getElementById('network-graph');
    
    // Extract unique nodes
    const nodes = new vis.DataSet();
    const edges = new vis.DataSet();
    
    // Central Node (Localhost)
    nodes.add({ id: 'localhost', label: 'Local System', shape: 'image', image: 'https://api.iconify.design/ph/desktop-fill.svg?color=%23ffffff', size: 30, font: { color: 'white' } });
    
    const allData = [...(currentReport.alertes||[]), ...(currentReport.surveiller||[]), ...(currentReport.legitimes||[])];
    const addedNodes = new Set();
    
    allData.forEach((item, i) => {
        const nodeId = `proc_${i}`;
        if (!addedNodes.has(nodeId)) {
            const color = getRiskColorHex(item.risk_level);
            
            nodes.add({
                id: nodeId,
                label: item.proc || 'Unknown',
                title: `Port: ${item.port}\nIP: ${item.ip}\nRisk: ${item.risk_level}`,
                shape: 'dot',
                size: 15,
                color: { background: color, border: 'rgba(255,255,255,0.2)' },
                font: { color: '#94a3b8', size: 12 }
            });
            
            edges.add({
                from: 'localhost',
                to: nodeId,
                label: `${item.port}`,
                font: { color: '#475569', size: 10, background: 'transparent' },
                color: { color: '#2a3441', highlight: '#00f0ff' }
            });
            
            addedNodes.add(nodeId);
        }
    });
    
    const data = { nodes: nodes, edges: edges };
    const options = {
        nodes: { borderWidth: 2 },
        edges: { smooth: { type: 'continuous' } },
        physics: {
            solver: 'forceAtlas2Based',
            forceAtlas2Based: { gravitationalConstant: -50, centralGravity: 0.01, springLength: 100, springConstant: 0.08 }
        },
        interaction: { hover: true, tooltipDelay: 200 }
    };
    
    networkNetwork = new vis.Network(container, data, options);
}

// --- Toasts ---

function showToast(message, type = "accent") {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    
    let borderCol = type === 'safe' ? 'border-safe' : type === 'danger' ? 'border-danger' : 'border-accent';
    let iconCol = type === 'safe' ? 'text-safe' : type === 'danger' ? 'text-danger' : 'text-accent';
    let icon = type === 'safe' ? 'ph-check-circle' : type === 'danger' ? 'ph-warning-circle' : 'ph-info';
    
    toast.className = `glass-panel px-4 py-3 border-l-4 ${borderCol} flex items-center gap-3 toast-enter shadow-lg`;
    toast.innerHTML = `
        <i class="ph-fill ${icon} ${iconCol} text-xl"></i>
        <span class="text-sm text-white font-medium">${message}</span>
    `;
    
    container.appendChild(toast);
    
    setTimeout(() => {
        toast.classList.replace('toast-enter', 'toast-exit');
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}
