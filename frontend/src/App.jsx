import { useCallback, useEffect, useState } from "react";
import Header from "./components/Header";
import ScanPanel from "./components/ScanPanel";
import SummaryBar from "./components/SummaryBar";
import Section from "./components/Section";
import HardeningPanel from "./components/HardeningPanel";
import Loader from "./components/Loader";
import { ToastContainer } from "./components/Toast";

const API_BASE = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/$/, "");
const DEMO_MODE = (import.meta.env.VITE_DEMO_MODE || "").toLowerCase() === "true";
const DEMO_REPORT_URL = `${import.meta.env.BASE_URL}demo-report.json`;

const SEVERITY_ORDER = ["CRITIQUE", "Ã‰LEVÃ‰", "MODÃ‰RÃ‰", "FAIBLE", "TRÃˆS FAIBLE"];

const TABS = [
  { id: "dashboard", label: "Dashboard" },
  { id: "alertes", label: "Alertes" },
  { id: "surveiller", label: "Surveillance" },
  { id: "legitimes", label: "LÃ©gitimes" },
  { id: "hardenings", label: "Durcissement" },
  { id: "raw", label: "Donnees brutes" },
];

let toastCounter = 0;

export default function App() {
  const [excludeLocal, setExcludeLocal] = useState(false);
  const [health, setHealth] = useState(undefined);
  const [payload, setPayload] = useState(null);
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

  useEffect(() => {
    if (DEMO_MODE) {
      fetch(DEMO_REPORT_URL)
        .then((r) => r.json())
        .then((data) => {
          setPayload(data);
          setHealth({
            status: "ok",
            os: "Demo",
            exclude_local: false,
            has_virustotal_key: true,
            https_required: true,
          });
        })
        .catch(() => {
          setHealth(null);
          setError("Impossible de charger le rapport de demo.");
        });
      return;
    }

    fetch(`${API_BASE}/api/health`)
      .then((r) => r.json())
      .then(setHealth)
      .catch(() => setHealth(null));
  }, []);

  async function launchScan() {
    if (DEMO_MODE) {
      setLoading(true);
      setError("");
      try {
        const response = await fetch(DEMO_REPORT_URL);
        if (!response.ok) throw new Error(`Demo error ${response.status}`);
        const data = await response.json();
        setPayload(data);
        setActiveTab("dashboard");
        addToast("Mode demo recharge - rapport d'exemple affiche.", "success");
      } catch {
        const msg = "Impossible de recharger le rapport de demo.";
        setError(msg);
        addToast(msg, "error");
      } finally {
        setLoading(false);
      }
      return;
    }

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
        /* storage full - ignore */
      }

      const nb = data.report?.summary?.nb_alertes ?? 0;
      if (nb > 0) {
        addToast(`Scan termine - ${nb} alerte(s) detectee(s).`, "error");
      } else {
        addToast("Scan termine - aucune alerte critique.", "success");
      }
      setActiveTab("dashboard");
    } catch {
      const msg = "Impossible de joindre l'API Tafust. Demarrez le serveur Python puis reessayez.";
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
    addToast("Rapport exporte en JSON.", "success");
  }

  const report = payload?.report;
  const summary = report?.summary;
  const meta = report?.meta;

  const alertItems = [...(report?.alertes || []), ...(report?.surveiller || [])].sort(
    (a, b) => SEVERITY_ORDER.indexOf(a.risk_level) - SEVERITY_ORDER.indexOf(b.risk_level)
  );

  const tabCounts = {
    alertes: report?.alertes?.length ?? 0,
    surveiller: report?.surveiller?.length ?? 0,
    legitimes: report?.legitimes?.length ?? 0,
    hardenings: report?.hardenings?.length ?? 0,
  };

  return (
    <div className="relative min-h-screen bg-ink bg-grid bg-grid-sm">
      <div className="pointer-events-none fixed inset-x-0 top-0 h-96 bg-gradient-radial-signal opacity-40" />

      <div className="relative mx-auto max-w-7xl space-y-6 px-4 py-6 md:px-6 xl:px-8">
        <Header health={health} />

        <ScanPanel
          excludeLocal={excludeLocal}
          setExcludeLocal={setExcludeLocal}
          onScan={launchScan}
          loading={loading}
          error={error}
          demoMode={DEMO_MODE}
        />

        {loading && <Loader />}

        {!loading && report && (
          <>
            <SummaryBar summary={summary} meta={meta} />

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

            <div className="pb-10">
              {activeTab === "dashboard" && (
                <div className="space-y-8 animate-fade-in">
                  <Section
                    title="File de priorite"
                    subtitle="Alertes et services a examiner en premier."
                    items={alertItems}
                  />
                  <Section
                    title="Services legitimes"
                    subtitle="Processus connus, groupes par application."
                    items={report?.legitimes || []}
                    compact
                  />
                </div>
              )}

              {activeTab === "alertes" && (
                <div className="animate-fade-in">
                  <Section
                    title="Alertes"
                    subtitle="Processus suspects ou exposes sur le reseau sans preuve de confiance."
                    items={report?.alertes || []}
                  />
                </div>
              )}

              {activeTab === "surveiller" && (
                <div className="animate-fade-in">
                  <Section
                    title="A surveiller"
                    subtitle="Services watchlist et outils d'acces distant."
                    items={report?.surveiller || []}
                  />
                </div>
              )}

              {activeTab === "legitimes" && (
                <div className="animate-fade-in">
                  <Section
                    title="Services legitimes"
                    subtitle="Processus classes comme surs, groupes par application."
                    items={report?.legitimes || []}
                    compact
                  />
                </div>
              )}

              {activeTab === "hardenings" && (
                <div className="space-y-4 animate-fade-in">
                  <div>
                    <h2 className="text-xl font-bold text-mist">Recommandations de durcissement</h2>
                    <p className="mt-1 text-sm text-subtle">
                      Commandes PowerShell et Bash pour reduire la surface d'attaque.
                    </p>
                  </div>
                  <HardeningPanel hardenings={report?.hardenings} />
                </div>
              )}

              {activeTab === "raw" && (
                <div className="space-y-4 animate-fade-in">
                  <div className="flex items-center justify-between">
                    <div>
                      <h2 className="text-xl font-bold text-mist">Donnees brutes</h2>
                      <p className="mt-1 text-sm text-subtle">
                        Resultats JSON complets retournes par l'application.
                      </p>
                    </div>
                    <button onClick={exportJSON} className="btn-signal text-sm">
                      <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                      </svg>
                      Telecharger JSON
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

        {!loading && !report && (
          <div className="flex flex-col items-center justify-center gap-4 rounded-2xl border border-border py-20 text-center animate-fade-in glass-card">
            <div className="flex h-16 w-16 items-center justify-center rounded-2xl border border-border bg-card">
              <svg className="h-8 w-8 text-subtle" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
              </svg>
            </div>
            <div>
              <p className="font-semibold text-mist">Aucun rapport disponible</p>
              <p className="mt-1 text-sm text-subtle">
                Lance un audit depuis le panneau ci-dessus pour afficher les resultats.
              </p>
            </div>
          </div>
        )}
      </div>

      <ToastContainer toasts={toasts} removeToast={removeToast} />
    </div>
  );
}
