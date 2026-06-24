const VERDICT_STYLES = {
  "Audit needs attention": {
    border: "border-danger/30",
    bg: "bg-danger/5",
    icon: "⚠️",
    color: "text-danger",
  },
  "System looks healthy": {
    border: "border-signal/30",
    bg: "bg-signal/5",
    icon: "✅",
    color: "text-signal",
  },
};

function StatCard({ label, value, hint, accent = false }) {
  return (
    <div
      className={`rounded-2xl border p-5 glass-card shadow-card animate-fade-in ${
        accent ? "border-signal/25 bg-signal/5" : "border-border"
      }`}
    >
      <p className="text-xs font-semibold uppercase tracking-[0.2em] text-subtle">{label}</p>
      <p
        className={`mt-3 font-mono text-4xl font-bold tabular-nums ${
          accent ? "text-signal" : "text-mist"
        }`}
      >
        {value}
      </p>
      <p className="mt-2 text-xs leading-5 text-subtle">{hint}</p>
    </div>
  );
}

function RiskDistribution({ alertes = 0, surveiller = 0, legitimes = 0 }) {
  const total = alertes + surveiller + legitimes;
  if (total === 0) return null;

  const pctA = Math.round((alertes / total) * 100);
  const pctS = Math.round((surveiller / total) * 100);
  const pctL = 100 - pctA - pctS;

  return (
    <div className="rounded-2xl border border-border glass-card p-5 shadow-card animate-fade-in">
      <p className="text-xs font-semibold uppercase tracking-[0.2em] text-subtle">Distribution</p>
      <div className="mt-3 flex h-2.5 overflow-hidden rounded-full bg-ink/60">
        {alertes > 0 && <div className="bg-danger transition-all duration-700" style={{ width: `${pctA}%` }} />}
        {surveiller > 0 && <div className="bg-warning transition-all duration-700" style={{ width: `${pctS}%` }} />}
        {legitimes > 0 && <div className="bg-signal/60 transition-all duration-700" style={{ width: `${pctL}%` }} />}
      </div>
      <div className="mt-3 flex gap-4">
        {[
          { label: "Alertes", value: alertes, color: "bg-danger" },
          { label: "Surveillance", value: surveiller, color: "bg-warning" },
          { label: "Légitimes", value: legitimes, color: "bg-signal/60" },
        ].map(({ label, value, color }) => (
          <div key={label} className="flex items-center gap-1.5">
            <span className={`h-2 w-2 rounded-full ${color}`} />
            <span className="text-xs text-subtle">
              {label} <span className="font-medium text-mist">{value}</span>
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function SummaryBar({ summary, meta }) {
  if (!summary) {
    return (
      <div className="grid gap-4 md:grid-cols-3">
        {["Verdict", "À traiter", "Légitimes"].map((label) => (
          <StatCard key={label} label={label} value="—" hint="Aucun scan lancé." />
        ))}
      </div>
    );
  }

  const verdictStyle = VERDICT_STYLES[summary.verdict] || VERDICT_STYLES["Audit needs attention"];

  return (
    <div className="space-y-4">
      <div className={`rounded-2xl border p-4 glass-card animate-fade-in ${verdictStyle.border} ${verdictStyle.bg}`}>
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-3">
            <span className="text-2xl">{verdictStyle.icon}</span>
            <div>
              <p className={`font-semibold ${verdictStyle.color}`}>{summary.verdict}</p>
              <p className="mt-0.5 text-xs text-subtle">{summary.verdict_detail}</p>
            </div>
          </div>
          {meta?.date && (
            <span className="rounded-lg border border-border bg-ink/40 px-3 py-1.5 font-mono text-xs text-subtle">
              {meta.date}
            </span>
          )}
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          label="Entrées totales"
          value={summary.total ?? 0}
          hint={`${meta?.total_raw ?? 0} connexions brutes analysées`}
        />
        <StatCard
          label="Alertes"
          value={summary.nb_alertes ?? 0}
          hint="Processus suspects ou exposés sur le réseau"
        />
        <StatCard
          label="À surveiller"
          value={summary.nb_surveiller ?? 0}
          hint="Services watchlist ou accès distants"
        />
        <StatCard
          label="Légitimes"
          value={summary.nb_legitimes ?? 0}
          hint="Services Windows connus et validés"
          accent
        />
      </div>

      <RiskDistribution
        alertes={summary.nb_alertes}
        surveiller={summary.nb_surveiller}
        legitimes={summary.nb_legitimes}
      />
    </div>
  );
}
