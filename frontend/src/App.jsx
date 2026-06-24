import { useEffect, useState, useCallback } from "react";
import Header from "./components/Header";
import ScanPanel from "./components/ScanPanel";
import SummaryBar from "./components/SummaryBar";
import Section from "./components/Section";
import HardeningPanel from "./components/HardeningPanel";
import Loader from "./components/Loader";
import { ToastContainer } from "./components/Toast";

const API_BASE = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/$/, "");

const SEVERITY_ORDER = ["CRITIQUE", "ÉLEVÉ", "MODÉRÉ", "FAIBLE", "TRÈS FAIBLE"];

const TABS = [
  { id: "dashboard", label: "Dashboard" },
  { id: "alertes", label: "Alertes" },
  { id: "surveiller", label: "Surveillance" },
  { id: "legitimes", label: "Légitimes" },
  { id: "hardenings", label: "Durcissement" },
  { id: "raw", label: "Données brutes" },
];

let toastCounter = 0;

export default function App() {
  const [excludeLocal, setExcludeLocal] = useState(false);
  const [health, setHealth] = useState(undefined);
  const [payload, setPayload] = useState(() => {
    try {
      const saved = localStorage.getItem("tafust_last_report");
      return saved ? JSON.parse(saved) : null;
    } catch {
      return null;
    }
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [activeTab, setActiveTab] = useState("dashboard");
  const [toasts, setToasts] = useState([]);

  const addToast = useCallback((message, type = "info") => {
    const id = ++toastCounter;
    setToasts((prev) => [...prev, { id, message, type }]);
  }, []);

  const removeToast = useCallback((id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  // Health check
  useEffect(() => {
    fetch(`${API_BASE}/api/health`)
      .then((r) => r.json())
      .then(setHealth)
      .catch(() => setHealth(null));
  }, []);

  async function launchScan() {
    setLoading(true);
    setError("");
    try {
      const response = await fetch(`${API_BASE}/api/scan`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ exclude_local: excludeLocal }),
      });

      if (!response.ok) throw new Error(`API error ${response.status}`);

      const data = await response.json();
      setPayload(data);
      try {
        localStorage.setItem("tafust_last_report", JSON.stringify(data));
      } catch {
        /* storage full – ignore */
      }

      const nb = (data.report?.summary?.nb_alertes ?? 0);
      if (nb > 0) {
        addToast(`Scan terminé — ${nb} alerte(s) détectée(s).`, "error");
      } else {
        addToast("Scan terminé — aucune alerte critique.", "success");
      }
      setActiveTab("dashboard");
    } catch {
      const msg = "Impossible de joindre l'API Tafust. Démarrez le serveur Python puis réessayez.";
      setError(msg);
      addToast(msg, "error");
    } finally {
      setLoading(false);
    }
  }

  function exportJSON() {
    if (!payload) return;
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `tafust_report_${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
    addToast("Rapport exporté en JSON.", "success");
  }

  const report = payload?.report;
  const summary = report?.summary;
  const meta = report?.meta;

  const alertItems = [...(report?.alertes || []), ...(report?.surveiller || [])].sort(
    (a, b) => SEVERITY_ORDER.indexOf(a.risk_level) - SEVERITY_ORDER.indexOf(b.risk_level)
  );

  // Tab badge counts
  const tabCounts = {
    alertes: report?.alertes?.length ?? 0,
    surveiller: report?.surveiller?.length ?? 0,
    legitimes: report?.legitimes?.length ?? 0,
    hardenings: report?.hardenings?.length ?? 0,
  };

  return (
    <div className="relative min-h-screen bg-ink bg-grid bg-grid-sm">
      {/* Radial glow top */}
      <div className="pointer-events-none fixed inset-x-0 top-0 h-96 bg-gradient-radial-signal opacity-40" />

      <div className="relative mx-auto max-w-7xl space-y-6 px-4 py-6 md:px-6 xl:px-8">
        {/* ── Header ── */}
        <Header health={health} />

        {/* ── Scan panel ── */}
        <ScanPanel
          excludeLocal={excludeLocal}
          setExcludeLocal={setExcludeLocal}
          onScan={launchScan}
          loading={loading}
          error={error}
        />

        {/* ── Loading state ── */}
        {loading && <Loader />}

        {/* ── Results ── */}
        {!loading && report && (
          <>
            {/* Summary */}
            <SummaryBar summary={summary} meta={meta} />

            {/* Tab bar + export */}
            <div className="flex items-center justify-between gap-4 border-b border-border">
              <nav className="flex overflow-x-auto" aria-label="Sections du rapport">
                {TABS.map(({ id, label }) => {
                  const count = tabCounts[id];
                  return (
                    <button
                      key={id}
                      onClick={() => setActiveTab(id)}
                      className={`tab-btn whitespace-nowrap ${activeTab === id ? "active" : ""}`}
                      aria-current={activeTab === id ? "page" : undefined}
                      id={`tab-${id}`}
                    >
                      {label}
                      {count > 0 && (
                        <span className="ml-1.5 rounded-full bg-white/10 px-1.5 py-0.5 font-mono text-[10px] text-subtle">
                          {count}
                        </span>
                      )}
                    </button>
                  );
                })}
              </nav>

              {/* Export JSON button */}
              <button
                onClick={exportJSON}
                className="flex flex-shrink-0 items-center gap-1.5 rounded-xl border border-border bg-card px-3 py-2 text-xs font-medium text-subtle transition-all hover:border-signal/30 hover:text-mist"
                title="Exporter le rapport en JSON"
              >
                <svg className="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                </svg>
                Export JSON
              </button>
            </div>

            {/* ── Tab Content ── */}
            <div className="pb-10">
              {/* Dashboard */}
              {activeTab === "dashboard" && (
                <div className="space-y-8 animate-fade-in">
                  <Section
                    title="🔴 File de priorité"
                    subtitle="Alertes et services à examiner en premier."
                    items={alertItems}
                  />
                  <Section
                    title="🟢 Services légitimes"
                    subtitle="Processus Windows connus — groupés par application."
                    items={report?.legitimes || []}
                    compact
                  />
                </div>
              )}

              {/* Alertes */}
              {activeTab === "alertes" && (
                <div className="animate-fade-in">
                  <Section
                    title="Alertes"
                    subtitle="Processus suspects ou exposés sur le réseau sans preuve de confiance."
                    items={report?.alertes || []}
                  />
                </div>
              )}

              {/* Surveiller */}
              {activeTab === "surveiller" && (
                <div className="animate-fade-in">
                  <Section
                    title="À surveiller"
                    subtitle="Services watchlist et outils d'accès distant."
                    items={report?.surveiller || []}
                  />
                </div>
              )}

              {/* Légitimes */}
              {activeTab === "legitimes" && (
                <div className="animate-fade-in">
                  <Section
                    title="Services légitimes"
                    subtitle="Processus classifiés comme sûrs, groupés par application."
                    items={report?.legitimes || []}
                    compact
                  />
                </div>
              )}

              {/* Hardenings */}
              {activeTab === "hardenings" && (
                <div className="space-y-4 animate-fade-in">
                  <div>
                    <h2 className="text-xl font-bold text-mist">Recommandations de durcissement</h2>
                    <p className="mt-1 text-sm text-subtle">
                      Commandes PowerShell et Bash pour réduire la surface d'attaque.
                    </p>
                  </div>
                  <HardeningPanel hardenings={report?.hardenings} />
                </div>
              )}

              {/* Raw JSON */}
              {activeTab === "raw" && (
                <div className="space-y-4 animate-fade-in">
                  <div className="flex items-center justify-between">
                    <div>
                      <h2 className="text-xl font-bold text-mist">Données brutes</h2>
                      <p className="mt-1 text-sm text-subtle">
                        Résultats JSON complets retournés par l'API.
                      </p>
                    </div>
                    <button onClick={exportJSON} className="btn-signal text-sm">
                      <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                      </svg>
                      Télécharger JSON
                    </button>
                  </div>
                  <pre className="code-block max-h-[600px] overflow-auto rounded-2xl p-5 text-xs leading-5 text-signal/80">
                    {JSON.stringify(payload, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          </>
        )}

        {/* ── Empty state ── */}
        {!loading && !report && (
          <div className="flex flex-col items-center justify-center gap-4 rounded-2xl border border-border py-20 glass-card text-center animate-fade-in">
            <div className="flex h-16 w-16 items-center justify-center rounded-2xl border border-border bg-card">
              <svg className="h-8 w-8 text-subtle" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
              </svg>
            </div>
            <div>
              <p className="font-semibold text-mist">Aucun rapport disponible</p>
              <p className="mt-1 text-sm text-subtle">
                Lancez un audit depuis le panneau ci-dessus pour afficher les résultats.
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Toast notifications */}
      <ToastContainer toasts={toasts} removeToast={removeToast} />
    </div>
  );
}
