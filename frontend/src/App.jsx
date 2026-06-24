import { useEffect, useState } from "react";

const API_BASE = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/$/, "");
const LOGO_SRC = "/logo.png";

const riskTone = {
  CRITIQUE: "border-red-500/40 bg-red-500/10 text-red-100",
  "ÉLEVÉ": "border-orange-500/40 bg-orange-500/10 text-orange-100",
  "MODÉRÉ": "border-amber-500/40 bg-amber-500/10 text-amber-100",
  FAIBLE: "border-lime-500/40 bg-lime-500/10 text-lime-100",
  "TRÈS FAIBLE": "border-emerald-500/40 bg-emerald-500/10 text-emerald-100",
};

const severityOrder = ["CRITIQUE", "ÉLEVÉ", "MODÉRÉ", "FAIBLE", "TRÈS FAIBLE"];

function StatCard({ label, value, hint }) {
  return (
    <div className="rounded-3xl border border-white/10 bg-white/5 p-5 shadow-glow backdrop-blur">
      <p className="text-xs uppercase tracking-[0.25em] text-mist/70">{label}</p>
      <p className="mt-3 text-3xl font-semibold text-white">{value}</p>
      <p className="mt-2 text-sm text-mist/70">{hint}</p>
    </div>
  );
}

function EntryCard({ entry, compact }) {
  const ports = compact ? entry.ports_list?.join(", ") || entry.port : `${entry.port}/${entry.proto}`;
  const ips = compact ? entry.ips_list?.join(", ") || entry.ip : entry.ip;
  const tone = riskTone[entry.risk_level] || "border-white/10 bg-white/5 text-white";

  return (
    <article className={`rounded-3xl border p-5 ${tone}`}>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 className="text-lg font-semibold">{entry.label || entry.proc}</h3>
          <p className="mt-1 text-sm text-white/70">{entry.proc}</p>
        </div>
        <span className="rounded-full border border-current/20 px-3 py-1 text-xs font-semibold tracking-wide">
          {entry.risk_level}
        </span>
      </div>
      <div className="mt-4 grid gap-3 text-sm text-white/80 md:grid-cols-2">
        <p><span className="text-white/50">Ports</span><br />{ports}</p>
        <p><span className="text-white/50">Exposure</span><br />{ips}</p>
        {entry.company_name ? <p><span className="text-white/50">Company</span><br />{entry.company_name}</p> : null}
        {entry.signature_status ? <p><span className="text-white/50">Signature</span><br />{entry.signature_status}</p> : null}
      </div>
      <p className="mt-4 text-sm leading-6 text-white/85">{entry.justification}</p>
      {entry.path ? <p className="mt-3 break-all text-xs text-white/55">{entry.path}</p> : null}
    </article>
  );
}

function Section({ title, subtitle, items, compact = false }) {
  if (!items.length) {
    return null;
  }

  return (
    <section className="space-y-4">
      <div className="flex items-end justify-between gap-4">
        <div>
          <h2 className="text-2xl font-semibold text-white">{title}</h2>
          <p className="mt-1 text-sm text-mist/70">{subtitle}</p>
        </div>
        <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-sm text-white/80">
          {items.length}
        </span>
      </div>
      <div className="grid gap-4 xl:grid-cols-2">
        {items.map((entry, index) => (
          <EntryCard
            key={`${entry.proc}-${entry.port || "group"}-${index}`}
            entry={entry}
            compact={compact}
          />
        ))}
      </div>
    </section>
  );
}

export default function App() {
  const [excludeLocal, setExcludeLocal] = useState(false);
  const [health, setHealth] = useState(null);
  const [payload, setPayload] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    fetch(`${API_BASE}/api/health`)
      .then((response) => response.json())
      .then(setHealth)
      .catch(() => {
        setHealth(null);
      });
  }, []);

  async function launchScan() {
    setLoading(true);
    setError("");
    try {
      const response = await fetch(`${API_BASE}/api/scan`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ exclude_local: excludeLocal }),
      });

      if (!response.ok) {
        throw new Error(`API error ${response.status}`);
      }

      const data = await response.json();
      setPayload(data);
    } catch (err) {
      setError("Unable to reach the Tafust API. Start the Python server and try again.");
    } finally {
      setLoading(false);
    }
  }

  const report = payload?.report;
  const summary = report?.summary;
  const itemsToReview = [
    ...(report?.alertes || []),
    ...(report?.surveiller || []),
  ].sort((a, b) => severityOrder.indexOf(a.risk_level) - severityOrder.indexOf(b.risk_level));

  return (
    <main className="min-h-screen px-5 py-8 text-white md:px-8 xl:px-12">
      <div className="mx-auto max-w-7xl space-y-8">
        <header className="overflow-hidden rounded-[2rem] border border-white/10 bg-panel/80 p-8 shadow-glow backdrop-blur">
          <div className="grid gap-8 lg:grid-cols-[1.35fr_0.65fr]">
            <div>
              <div className="flex items-center gap-4">
                <img
                  src={LOGO_SRC}
                  alt="Tafust logo"
                  className="h-16 w-16 rounded-2xl border border-white/10 bg-white/5 p-2 shadow-glow"
                />
                <p className="text-sm uppercase tracking-[0.4em] text-signal">Tafust Command Center</p>
              </div>
              <h1 className="mt-4 max-w-3xl text-4xl font-semibold leading-tight md:text-5xl">
                React + Tailwind architecture for a cleaner security audit workflow.
              </h1>
              <p className="mt-4 max-w-2xl text-base leading-7 text-mist/75">
                The Python engine stays responsible for process inspection and risk analysis. This web layer
                focuses on clarity, triage speed, and a more modern presentation of the scan output.
              </p>
            </div>
            <div className="rounded-[1.75rem] border border-white/10 bg-white/5 p-6">
              <p className="text-xs uppercase tracking-[0.25em] text-mist/70">Runtime</p>
              <div className="mt-4 space-y-4 text-sm text-white/80">
                <p>API: <span className="text-white">{API_BASE || "Same origin (/api via proxy or reverse proxy)"}</span></p>
                <p>Backend OS: <span className="text-white">{health?.os || "Unavailable"}</span></p>
                <p>VirusTotal key: <span className="text-white">{health?.has_virustotal_key ? "Configured" : "Not configured"}</span></p>
                <p>HTTPS policy: <span className="text-white">{health?.https_required ? "Enforced" : "Optional"}</span></p>
              </div>
              <label className="mt-6 flex items-center gap-3 rounded-2xl border border-white/10 bg-ink/40 px-4 py-3 text-sm">
                <input
                  type="checkbox"
                  checked={excludeLocal}
                  onChange={(event) => setExcludeLocal(event.target.checked)}
                  className="h-4 w-4 rounded border-white/20 bg-transparent accent-signal"
                />
                Exclude local-only listeners
              </label>
              <button
                type="button"
                onClick={launchScan}
                disabled={loading}
                className="mt-6 inline-flex w-full items-center justify-center rounded-2xl bg-signal px-4 py-3 font-semibold text-ink transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-70"
              >
                {loading ? "Scanning..." : "Launch audit"}
              </button>
              {error ? <p className="mt-3 text-sm text-red-300">{error}</p> : null}
            </div>
          </div>
        </header>

        <section className="grid gap-4 md:grid-cols-3">
          <StatCard
            label="Verdict"
            value={summary?.verdict || "No scan yet"}
            hint={summary?.verdict_detail || "Run an audit from the panel above."}
          />
          <StatCard
            label="Entries To Review"
            value={summary ? summary.nb_alertes + summary.nb_surveiller : 0}
            hint="Critical and watchlist findings grouped for faster triage."
          />
          <StatCard
            label="Legitimate Entries"
            value={summary?.nb_legitimes || 0}
            hint={report?.meta?.date ? `Last scan: ${report.meta.date}` : "No report generated yet."}
          />
        </section>

        <Section
          title="Priority Queue"
          subtitle="Findings that deserve a human check first."
          items={itemsToReview}
        />

        <Section
          title="Trusted Services"
          subtitle="Grouped legitimate processes and local services."
          items={report?.legitimes || []}
          compact
        />

        <section className="rounded-[2rem] border border-white/10 bg-white/5 p-6">
          <h2 className="text-2xl font-semibold text-white">Suggested architecture</h2>
          <div className="mt-4 grid gap-4 md:grid-cols-3">
            <div className="rounded-3xl border border-white/10 bg-ink/40 p-5">
              <p className="text-sm font-semibold text-signal">Backend</p>
              <p className="mt-2 text-sm leading-6 text-mist/75">
                FastAPI wraps the existing Python engine and exposes `/api/health`, `/api/report`, and `/api/scan`.
              </p>
            </div>
            <div className="rounded-3xl border border-white/10 bg-ink/40 p-5">
              <p className="text-sm font-semibold text-signal">Frontend</p>
              <p className="mt-2 text-sm leading-6 text-mist/75">
                React renders dashboard views, while Tailwind handles layout, color system, spacing, and responsive cards.
              </p>
            </div>
            <div className="rounded-3xl border border-white/10 bg-ink/40 p-5">
              <p className="text-sm font-semibold text-signal">Evolution path</p>
              <p className="mt-2 text-sm leading-6 text-mist/75">
                Later we can add scan history, filtering, auth, or package it as a desktop shell with Tauri or pywebview.
              </p>
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}
