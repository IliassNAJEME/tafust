import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { Play, Shield, Loader2, AlertCircle, Wifi, ShieldCheck, Activity, Cpu, CheckCircle2 } from "lucide-react";
import { useSettings } from "../hooks/useSettings";
import { useHistory } from "../hooks/useHistory";
import { Button } from "../components/ui/button";

const API_BASE = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/$/, "");

const SCAN_STEPS = [
  { icon: Wifi,         label: "Analyse des interfaces réseau..." },
  { icon: Cpu,          label: "Inspection des processus actifs..." },
  { icon: Activity,     label: "Évaluation des ports en écoute..." },
  { icon: Shield,       label: "Vérification des signatures..." },
  { icon: ShieldCheck,  label: "Génération du rapport de sécurité..." },
];

export default function Dashboard() {
  const { settings, setSettings } = useSettings();
  const { addEntry } = useHistory();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [stepIndex, setStepIndex] = useState(0);
  const [health, setHealth] = useState<any>(undefined);

  useEffect(() => {
    fetch(`${API_BASE}/api/health`)
      .then((r) => r.json())
      .then(setHealth)
      .catch(() => setHealth(null));
  }, []);

  // Cycle through scan steps during loading
  useEffect(() => {
    if (!loading) { setStepIndex(0); return; }
    const id = setInterval(() => {
      setStepIndex((i) => (i + 1) % SCAN_STEPS.length);
    }, 1400);
    return () => clearInterval(id);
  }, [loading]);

  const apiOnline = health !== null && health !== undefined;
  const CurrentStepIcon = SCAN_STEPS[stepIndex]?.icon || Shield;

  const launchScan = async () => {
    setLoading(true);
    setError("");
    try {
      const response = await fetch(`${API_BASE}/api/scan`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ exclude_local: settings.exclude_local }),
      });
      if (!response.ok) throw new Error(`API error ${response.status}`);
      const data = await response.json();
      localStorage.setItem("tafust_last_report", JSON.stringify(data));
      const report = data.report || {};
      const summary = report.summary || {};
      addEntry({
        excludeLocal: settings.exclude_local,
        summary: {
          nb_alertes:   summary.nb_alertes   || 0,
          nb_surveiller:summary.nb_surveiller || 0,
          nb_legitimes: summary.nb_legitimes  || 0,
          total:        summary.total         || 0,
          verdict:      summary.verdict,
        },
      });
      navigate("/results");
    } catch {
      setError("Impossible de joindre l'API Tafust. L'agent local est-il démarré ?");
    } finally {
      setLoading(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -16 }}
      transition={{ duration: 0.4 }}
      className="flex flex-col items-center justify-center py-10 min-h-[75vh]"
    >
      {/* ── HERO SECTION ── */}
      <div className="w-full max-w-2xl space-y-6">

        {/* Title block */}
        <div className="text-center space-y-2 animate-fade-in">
          <div className="inline-flex items-center gap-2 rounded-full border border-signal/20 bg-signal/5 px-4 py-1.5 text-xs font-semibold text-signal uppercase tracking-widest mb-4">
            <span className="h-1.5 w-1.5 rounded-full bg-signal animate-pulse" />
            Network Security Audit
          </div>
          <h2 className="text-4xl font-black text-mist tracking-tight">
            Analysez votre{" "}
            <span className="text-gradient-signal">réseau local</span>
          </h2>
          <p className="text-subtle text-base max-w-md mx-auto leading-relaxed">
            Détection des processus suspects, analyse des ports exposés et évaluation
            complète des risques réseau sur votre machine.
          </p>
        </div>

        {/* Main card */}
        <div className="relative rounded-2xl border border-signal/20 glass-card shadow-glow overflow-hidden animate-slide-up delay-100">
          {/* Animated top bar */}
          <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-signal/60 to-transparent" />

          {/* Scan overlay when loading */}
          {loading && <div className="scan-overlay z-10" />}

          <div className="relative z-20 p-8 flex flex-col items-center gap-6">
            {/* Icon orb */}
            <div className="relative">
              {/* Outer ring */}
              <div className={`absolute inset-0 rounded-full border-2 border-signal/20 scale-[1.6] ${loading ? "animate-ping-slow" : ""}`} />
              <div className={`absolute inset-0 rounded-full border border-signal/10 scale-[1.3]`} />
              {/* Main icon */}
              <div className={`relative flex h-24 w-24 items-center justify-center rounded-full border-2 border-signal/40 bg-signal/10 transition-all duration-500 ${loading ? "animate-glow-pulse shadow-glow-lg" : "shadow-glow"}`}>
                {loading ? (
                  <CurrentStepIcon className="h-10 w-10 text-signal animate-fade-in-fast" key={stepIndex} />
                ) : (
                  <Shield className="h-10 w-10 text-signal" />
                )}
              </div>
            </div>

            {/* Status text */}
            <div className="text-center space-y-1">
              {loading ? (
                <div key={stepIndex} className="animate-fade-in-fast">
                  <div className="text-lg font-bold text-mist">Audit en cours...</div>
                  <div className="text-sm text-signal font-medium mt-1">{SCAN_STEPS[stepIndex]?.label}</div>
                  {/* Progress dots */}
                  <div className="flex justify-center gap-1.5 mt-3">
                    {SCAN_STEPS.map((_, i) => (
                      <div
                        key={i}
                        className={`h-1.5 rounded-full transition-all duration-300 ${
                          i < stepIndex ? "w-6 bg-signal" :
                          i === stepIndex ? "w-3 bg-signal animate-pulse" :
                          "w-1.5 bg-border"
                        }`}
                      />
                    ))}
                  </div>
                </div>
              ) : (
                <>
                  <div className="text-lg font-bold text-mist">Prêt pour l'audit</div>
                  <div className="text-sm text-subtle">Cliquez pour lancer une analyse complète de votre système</div>
                </>
              )}
            </div>

            {/* Launch button */}
            <Button
              size="lg"
              onClick={launchScan}
              disabled={loading}
              className="w-full sm:w-auto min-w-[220px] gap-3 text-base font-bold h-14 bg-signal hover:bg-signal-dim text-ink rounded-xl shadow-glow transition-all duration-200 hover:scale-[1.02] active:scale-95 disabled:scale-100"
            >
              {loading ? (
                <>
                  <Loader2 className="h-5 w-5 animate-spin" />
                  Analyse en cours...
                </>
              ) : (
                <>
                  <Play className="h-5 w-5 fill-current" />
                  Lancer l'Audit
                </>
              )}
            </Button>

            {/* Options */}
            <label className="flex items-center gap-3 cursor-pointer group">
              <div className="relative">
                <input
                  type="checkbox"
                  checked={settings.exclude_local}
                  onChange={(e) => setSettings({ ...settings, exclude_local: e.target.checked })}
                  className="peer sr-only"
                />
                <div className="h-5 w-9 rounded-full border border-border bg-ink transition-colors peer-checked:border-signal/50 peer-checked:bg-signal/20" />
                <div className="absolute top-0.5 left-0.5 h-4 w-4 rounded-full bg-subtle transition-all peer-checked:left-4 peer-checked:bg-signal" />
              </div>
              <span className="text-sm text-subtle group-hover:text-mist transition-colors">
                Exclure les listeners <code className="font-mono text-xs bg-ink/60 px-1.5 py-0.5 rounded border border-border text-mist">loopback</code>
              </span>
            </label>

            {error && (
              <div className="w-full flex items-start gap-3 rounded-xl border border-danger/30 bg-danger/8 p-4 text-sm text-danger/90 animate-fade-in">
                <AlertCircle className="h-5 w-5 flex-shrink-0 mt-0.5" />
                <p>{error}</p>
              </div>
            )}
          </div>

          {/* Bottom decorative bar */}
          <div className="absolute inset-x-0 bottom-0 h-px bg-gradient-to-r from-transparent via-signal/30 to-transparent" />
        </div>

        {/* ── System info cards ── */}
        <div className="grid grid-cols-3 gap-3 animate-slide-up delay-200">
          {[
            {
              icon: <Wifi className="h-4 w-4" />,
              label: "Agent Local",
              value: health === undefined ? "..." : (apiOnline ? "Connecté" : "Hors ligne"),
              color: health === undefined ? "text-subtle" : (apiOnline ? "text-signal" : "text-danger"),
              dot: health === undefined ? "bg-subtle" : (apiOnline ? "bg-signal animate-pulse" : "bg-danger"),
            },
            {
              icon: <Cpu className="h-4 w-4" />,
              label: "Système",
              value: health?.os ? health.os.charAt(0).toUpperCase() + health.os.slice(1) : "—",
              color: "text-mist",
              dot: null,
            },
            {
              icon: <CheckCircle2 className="h-4 w-4" />,
              label: "VirusTotal",
              value: health?.has_virustotal_key ? "Actif" : "Non configuré",
              color: health?.has_virustotal_key ? "text-signal" : "text-subtle",
              dot: null,
            },
          ].map((card, i) => (
            <div key={i} className="glass-card-lighter rounded-xl p-3 text-center border border-border/50">
              <div className={`flex justify-center mb-1 ${card.color} opacity-70`}>{card.icon}</div>
              <div className="text-xs text-subtle mb-1">{card.label}</div>
              <div className={`flex items-center justify-center gap-1.5 text-sm font-bold ${card.color}`}>
                {card.dot && <span className={`h-1.5 w-1.5 rounded-full ${card.dot}`} />}
                {card.value}
              </div>
            </div>
          ))}
        </div>

        {/* Feature pills */}
        <div className="flex flex-wrap justify-center gap-2 animate-slide-up delay-300">
          {[
            "🔍 Analyse des ports",
            "🛡️ Réputation Cloud",
            "⚡ Détection temps réel",
            "📋 Rapport détaillé",
          ].map((f) => (
            <span key={f} className="rounded-full border border-border/60 bg-ink/50 px-3 py-1.5 text-xs text-subtle">
              {f}
            </span>
          ))}
        </div>
      </div>
    </motion.div>
  );
}
