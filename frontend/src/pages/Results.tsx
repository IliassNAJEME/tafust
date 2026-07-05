import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { ShieldAlert, ShieldCheck, Download, AlertTriangle, Eye, Shield, Info, Filter, ChevronRight } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "../components/ui/card";
import { Button } from "../components/ui/button";
import RiskDistribution from "../components/charts/RiskDistribution";
import AnalysisCard from "../components/AnalysisCard";

/* ──────────────── helpers ──────────────── */
type FilterKey = "all" | "alertes" | "surveiller" | "legitimes";

const FILTER_OPTIONS: { key: FilterKey; label: string; color: string; dot: string }[] = [
  { key: "all",       label: "Tout",          color: "text-mist",    dot: "bg-mist" },
  { key: "alertes",   label: "Alertes",       color: "text-danger",  dot: "bg-danger" },
  { key: "surveiller",label: "À Surveiller",  color: "text-warning", dot: "bg-warning" },
  { key: "legitimes", label: "Légitimes",     color: "text-signal",  dot: "bg-signal" },
];

/* animated counter */
function AnimatedCount({ value, className }: { value: number; className: string }) {
  return (
    <span key={value} className={`text-3xl font-black font-mono animate-counter-up ${className}`}>
      {value}
    </span>
  );
}

/* global score badge */
function SecurityScore({ nb_alertes, nb_surveiller, total }: { nb_alertes: number; nb_surveiller: number; total: number }) {
  const score = total === 0 ? 100 : Math.max(0, Math.round(100 - (nb_alertes * 25 + nb_surveiller * 8)));
  const color = score >= 80 ? "text-signal" : score >= 50 ? "text-warning" : "text-danger";
  const ring  = score >= 80 ? "stroke-signal" : score >= 50 ? "stroke-warning" : "stroke-danger";
  const r = 36;
  const circ = 2 * Math.PI * r;
  const dash = circ * (score / 100);

  return (
    <div className="flex flex-col items-center gap-2">
      <div className="relative h-24 w-24">
        <svg className="absolute inset-0 -rotate-90" viewBox="0 0 88 88" fill="none">
          <circle cx="44" cy="44" r={r} stroke="#1a2d4a" strokeWidth="8" />
          <circle
            cx="44" cy="44" r={r}
            className={`${ring} transition-all duration-1000`}
            strokeWidth="8"
            strokeDasharray={`${dash} ${circ}`}
            strokeLinecap="round"
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className={`text-xl font-black font-mono ${color}`}>{score}</span>
          <span className="text-[9px] text-subtle font-semibold uppercase tracking-wider">Score</span>
        </div>
      </div>
      <span className={`text-xs font-bold ${color}`}>
        {score >= 80 ? "Sécurisé" : score >= 50 ? "Attention" : "Critique"}
      </span>
    </div>
  );
}

/* ──────────────── main component ──────────────── */
export default function Results() {
  const [reportData, setReportData] = useState<any>(null);
  const [filter, setFilter] = useState<FilterKey>("all");

  useEffect(() => {
    try {
      const stored = localStorage.getItem("tafust_last_report");
      if (stored) setReportData(JSON.parse(stored));
    } catch (e) { console.error(e); }
  }, []);

  if (!reportData) {
    return (
      <div className="flex flex-col items-center justify-center py-24 text-center">
        <div className="h-20 w-20 rounded-full border border-signal/20 bg-signal/5 flex items-center justify-center mb-6">
          <Shield className="h-9 w-9 text-signal opacity-60" />
        </div>
        <h2 className="text-xl font-bold text-mist">Aucun résultat récent</h2>
        <p className="mt-2 text-sm text-subtle max-w-sm">
          Lancez un audit depuis le Dashboard pour voir les résultats ici.
        </p>
      </div>
    );
  }

  const { report, raw_results } = reportData;
  const summary  = report?.summary  || {};
  const alertes  = report?.alertes  || [];
  const surveiller = report?.surveiller || [];
  const legitimes  = report?.legitimes  || [];
  const hardenings = report?.hardenings || [];

  const filteredItems: any[] =
    filter === "alertes"    ? alertes :
    filter === "surveiller" ? surveiller :
    filter === "legitimes"  ? legitimes :
    [...alertes, ...surveiller, ...legitimes];

  const counts: Record<FilterKey, number> = {
    all: alertes.length + surveiller.length + legitimes.length,
    alertes: alertes.length,
    surveiller: surveiller.length,
    legitimes: legitimes.length,
  };

  const isHealthy = !summary.verdict?.toLowerCase().includes("attention");

  const handleExport = () => {
    const blob = new Blob([JSON.stringify(reportData, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `tafust_report_${new Date().toISOString().replace(/[:.]/g, "-")}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -12 }}
      transition={{ duration: 0.35 }}
      className="space-y-6 pb-20"
    >
      {/* ── Header ── */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-black text-mist tracking-tight">Rapport d'Audit</h2>
          <p className="text-sm text-subtle mt-0.5">
            Généré le <span className="text-mist font-medium">{report?.meta?.date || "—"}</span>
            {report?.meta?.total_unique && (
              <> · <span className="text-mist font-medium">{report.meta.total_unique}</span> processus uniques analysés</>
            )}
          </p>
        </div>
        <Button
          onClick={handleExport}
          variant="outline"
          className="border-signal/25 text-signal hover:bg-signal/10 hover:border-signal/50 gap-2 shrink-0"
        >
          <Download className="h-4 w-4" />
          Exporter JSON
        </Button>
      </div>

      {/* ── Summary cards ── */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">

        {/* Verdict card */}
        <div className={`col-span-full lg:col-span-2 rounded-2xl border p-5 glass-card relative overflow-hidden
          ${isHealthy ? "border-signal/25" : "border-danger/25"}`}>
          <div className={`absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent ${isHealthy ? "via-signal/50" : "via-danger/50"} to-transparent`} />
          <div className="flex items-start gap-4">
            <div className={`flex h-12 w-12 items-center justify-center rounded-xl border ${isHealthy ? "border-signal/30 bg-signal/10 text-signal" : "border-danger/30 bg-danger/10 text-danger"}`}>
              {isHealthy ? <ShieldCheck className="h-6 w-6" /> : <ShieldAlert className="h-6 w-6" />}
            </div>
            <div className="flex-1">
              <div className={`text-sm font-bold ${isHealthy ? "text-signal" : "text-danger"}`}>
                {summary.verdict}
              </div>
              <p className="mt-1 text-xs text-subtle leading-relaxed">{summary.verdict_detail}</p>
            </div>
            <SecurityScore
              nb_alertes={summary.nb_alertes || 0}
              nb_surveiller={summary.nb_surveiller || 0}
              total={summary.total || 0}
            />
          </div>
        </div>

        {/* Stat cards */}
        {[
          { label: "Alertes",       value: summary.nb_alertes   || 0, color: "text-danger",  border: "border-danger/25",  bg: "bg-danger/5",  icon: <AlertTriangle className="h-5 w-5" /> },
          { label: "À Surveiller",  value: summary.nb_surveiller|| 0, color: "text-warning", border: "border-warning/25", bg: "bg-warning/5", icon: <Eye className="h-5 w-5" /> },
          { label: "Légitimes",     value: summary.nb_legitimes || 0, color: "text-signal",  border: "border-signal/25",  bg: "bg-signal/5",  icon: <ShieldCheck className="h-5 w-5" /> },
          { label: "Total Analysé", value: summary.total        || 0, color: "text-mist",    border: "border-border",     bg: "bg-ink/60",    icon: <Info className="h-5 w-5" /> },
        ].map((s, i) => (
          <div key={i} className={`rounded-2xl border p-4 ${s.border} ${s.bg} glass-card`}>
            <div className={`flex items-center justify-between mb-3 ${s.color} opacity-70`}>
              {s.icon}
              <span className="text-xs font-bold uppercase tracking-wider text-subtle">{s.label}</span>
            </div>
            <AnimatedCount value={s.value} className={s.color} />
          </div>
        ))}
      </div>

      {/* ── Chart + Hardenings row ── */}
      <div className="grid gap-4 lg:grid-cols-3">
        {/* Risk distribution */}
        <Card className="border-border/60 bg-card/40 backdrop-blur-xl">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-bold text-subtle uppercase tracking-wider">Distribution des Risques</CardTitle>
          </CardHeader>
          <CardContent>
            <RiskDistribution summary={summary} />
          </CardContent>
        </Card>

        {/* Hardenings summary */}
        <Card className="lg:col-span-2 border-border/60 bg-card/40 backdrop-blur-xl">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-bold text-subtle uppercase tracking-wider flex items-center gap-2">
              <Shield className="h-4 w-4 text-warning" />
              Points de Hardening ({hardenings.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            {hardenings.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-6 text-center">
                <ShieldCheck className="h-8 w-8 text-signal mb-2 opacity-60" />
                <p className="text-sm text-subtle">Aucune action de hardening recommandée.</p>
              </div>
            ) : (
              <div className="space-y-2 max-h-52 overflow-y-auto pr-1">
                {hardenings.map((h: any, i: number) => (
                  <div key={i} className="flex items-start gap-3 rounded-xl border border-border/40 bg-ink/50 p-3">
                    <span className="text-sm shrink-0">{h.risk_icon}</span>
                    <div className="flex-1 min-w-0">
                      <div className="text-xs font-semibold text-mist truncate">{h.label || h.proc}</div>
                      <div className="text-xs text-subtle mt-0.5 line-clamp-2">{h.justification}</div>
                    </div>
                    <ChevronRight className="h-4 w-4 text-border shrink-0 mt-0.5" />
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* ── Filter tabs + Analysis cards ── */}
      <div className="space-y-4">
        {/* Filter bar */}
        <div className="flex items-center gap-2 flex-wrap">
          <Filter className="h-4 w-4 text-subtle shrink-0" />
          {FILTER_OPTIONS.map((opt) => (
            <button
              key={opt.key}
              onClick={() => setFilter(opt.key)}
              className={`flex items-center gap-2 rounded-xl border px-4 py-2 text-sm font-semibold transition-all duration-200 ${
                filter === opt.key
                  ? `${opt.color} border-current bg-current/10 shadow-sm`
                  : "text-subtle border-border/50 hover:border-border hover:text-mist bg-ink/40"
              }`}
            >
              {filter === opt.key && <span className={`h-1.5 w-1.5 rounded-full ${opt.dot}`} />}
              {opt.label}
              <span className={`rounded-full px-1.5 py-0.5 text-xs font-bold ${
                filter === opt.key ? "bg-current/20" : "bg-border/50 text-subtle"
              }`}>
                {counts[opt.key]}
              </span>
            </button>
          ))}
        </div>

        {/* Section label */}
        <div className="flex items-center gap-3">
          <div className="cyber-divider flex-1" />
          <span className="text-xs font-bold uppercase tracking-widest text-subtle px-2">
            {filteredItems.length} entrée{filteredItems.length !== 1 ? "s" : ""}
          </span>
          <div className="cyber-divider flex-1" />
        </div>

        {/* Cards */}
        {filteredItems.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 text-center rounded-2xl border border-border/40 bg-ink/30">
            <ShieldCheck className="h-10 w-10 text-signal mb-3 opacity-50" />
            <p className="text-sm font-semibold text-mist">Aucun élément dans cette catégorie</p>
          </div>
        ) : (
          <div className="space-y-3">
            {filteredItems.map((item, idx) => (
              <AnalysisCard key={`${item.proc}-${item.port}-${idx}`} item={item} index={idx} />
            ))}
          </div>
        )}
      </div>
    </motion.div>
  );
}
