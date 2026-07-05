import { useState } from "react";
import { ChevronDown, ChevronUp, Copy, Check, Terminal, Shield, AlertTriangle, Eye, Info, Cpu, Network, Lock } from "lucide-react";

/* ─── helpers ─── */
const RISK_META: Record<string, { label: string; color: string; bg: string; border: string; icon: React.ReactNode; desc: string }> = {
  "CRITIQUE": {
    label: "CRITIQUE",
    color: "text-danger",
    bg: "bg-danger/10",
    border: "border-danger/40",
    icon: <AlertTriangle className="h-4 w-4" />,
    desc: "Menace active détectée — intervention immédiate requise",
  },
  "ÉLEVÉ": {
    label: "ÉLEVÉ",
    color: "text-ember",
    bg: "bg-ember/10",
    border: "border-ember/40",
    icon: <Shield className="h-4 w-4" />,
    desc: "Risque significatif — vérification urgente recommandée",
  },
  "MODÉRÉ": {
    label: "MODÉRÉ",
    color: "text-warning",
    bg: "bg-warning/10",
    border: "border-warning/40",
    icon: <Eye className="h-4 w-4" />,
    desc: "Service connu mais nécessite une surveillance active",
  },
  "FAIBLE": {
    label: "FAIBLE",
    color: "text-safe",
    bg: "bg-safe/10",
    border: "border-safe/40",
    icon: <Info className="h-4 w-4" />,
    desc: "Risque mineur — service reconnu, surveiller occasionnellement",
  },
  "TRÈS FAIBLE": {
    label: "TRÈS FAIBLE",
    color: "text-signal",
    bg: "bg-signal/8",
    border: "border-signal/30",
    icon: <Shield className="h-4 w-4" />,
    desc: "Processus système légitime et de confiance",
  },
};

const getRiskMeta = (level: string) => RISK_META[level] || RISK_META["FAIBLE"];

/* ─── Analyse narrative par catégorie ─── */
function buildAnalysisParagraph(item: any): string {
  const risk = item.risk_level || "FAIBLE";
  const proc = item.label || item.proc || "Inconnu";
  const port = item.ports_list ? item.ports_list.join(", ") : item.port;
  const ip = item.ip || "?";
  const proto = item.proto || "TCP";
  const reputationVerdict = item.reputation_verdict || "unknown";

  if (risk === "CRITIQUE") {
    return `⚠️ Le processus **${proc}** a été signalé comme **malveillant** par les bases de données de réputation cloud (VirusTotal / sources tierces). Ce type de détection indique une forte probabilité de comportement malveillant — logiciel espion, trojan, C2 (Command & Control) ou exfiltration de données. Ce service doit être **arrêté et isolé immédiatement**, et le système doit faire l'objet d'une analyse forensic complète.`;
  }

  if (risk === "ÉLEVÉ") {
    if (item.reputation_verdict === "suspicious") {
      return `🔶 Le processus **${proc}** a reçu un signal de suspicion de la part des moteurs d'analyse cloud. Sans preuve locale de confiance (signature numérique valide, publisher reconnu), ce comportement ne peut pas être exclu comme potentiellement malveillant. Il écoute sur le port **${port}/${proto}** depuis l'adresse **${ip}**, ce qui le rend accessible sur le réseau. Il est recommandé de vérifier manuellement l'origine de ce processus, son chemin d'installation, et son comportement réseau.`;
    }
    return `🔶 Le service **${proc}** écoute sur le port **${port}/${proto}**, un port classé comme sensible. ${item.justification || ""} Ce type d'exposition réseau représente un vecteur d'attaque courant (brute-force, exploitation de vulnérabilités connues). Aucune preuve de confiance suffisante n'a été trouvée pour ce processus.`;
  }

  if (risk === "MODÉRÉ") {
    return `🟡 **${proc}** est un service connu qui écoute sur le port **${port}/${proto}**. ${item.justification || ""} Bien qu'il s'agisse généralement d'un service légitime, sa présence active sur le réseau mérite une attention particulière. Vérifiez que son utilisation est intentionnelle et que son exposition est nécessaire dans votre contexte.`;
  }

  if (risk === "FAIBLE") {
    return `🟢 **${proc}** est un processus reconnu avec un risque résiduel faible. ${item.justification || ""} Il écoute sur le port **${port}/${proto}**. Son exposition est considérée comme contrôlée, mais une surveillance périodique reste conseillée pour s'assurer que son comportement ne change pas.`;
  }

  // TRÈS FAIBLE / LÉGITIME
  return `✅ **${proc}** est un processus système ou une application de confiance. ${item.justification || "Ses signatures numériques et/ou son publisher ont été vérifiés."} Il écoute sur le port **${port}/${proto}** depuis **${ip}**. Aucune action requise — ce service est classé comme légitime.`;
}

/* ─── Copy button ─── */
function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  const handleCopy = () => {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };
  return (
    <button
      onClick={handleCopy}
      className="flex items-center gap-1.5 rounded-md border border-signal/20 bg-signal/5 px-2.5 py-1.5 text-xs font-medium text-signal transition-all hover:bg-signal/15 active:scale-95"
      title="Copier dans le presse-papier"
    >
      {copied ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
      {copied ? "Copié !" : "Copier"}
    </button>
  );
}

/* ─── Metadata row ─── */
function MetaRow({ label, value, mono }: { label: string; value?: string | number | null; mono?: boolean }) {
  if (!value && value !== 0) return null;
  return (
    <div className="flex items-start gap-3 py-2 border-b border-border/40 last:border-0">
      <span className="min-w-[110px] text-xs font-semibold uppercase tracking-wide text-subtle">{label}</span>
      <span className={`text-xs text-mist break-all ${mono ? "font-mono text-signal/80" : ""}`}>{String(value)}</span>
    </div>
  );
}

/* ─── Main component ─── */
interface AnalysisCardProps {
  item: any;
  index: number;
}

export default function AnalysisCard({ item, index }: AnalysisCardProps) {
  const [expanded, setExpanded] = useState(false);
  const [activeTab, setActiveTab] = useState<"analyse" | "remediation" | "meta">("analyse");

  const meta = getRiskMeta(item.risk_level);
  const analysis = buildAnalysisParagraph(item);
  const hasPowershell = item.powershell && item.powershell.length > 0;
  const hasHardening = item.hardening_note && item.hardening_note.trim().length > 0;
  const hasRemediation = hasPowershell || hasHardening;
  const psCode = (item.powershell || []).join("\n");
  const portsDisplay = item.ports_list ? item.ports_list.join(", ") : item.port;

  const delay = Math.min(index * 60, 400);

  return (
    <div
      className={`rounded-2xl border overflow-hidden transition-all duration-300 animate-slide-up ${meta.bg} ${meta.border} hover:shadow-card-hover group`}
      style={{ animationDelay: `${delay}ms`, opacity: 0 }}
    >
      {/* ── Header ── */}
      <button
        className="w-full flex items-center gap-4 p-4 text-left focus:outline-none"
        onClick={() => setExpanded(!expanded)}
        aria-expanded={expanded}
      >
        {/* Risk icon */}
        <div className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border ${meta.bg} ${meta.border} ${meta.color}`}>
          {meta.icon}
        </div>

        {/* Process info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className={`text-sm font-bold ${meta.color}`}>{item.label || item.proc}</span>
            {item.company_name && (
              <span className="text-xs text-subtle font-normal">— {item.company_name}</span>
            )}
          </div>
          <div className="mt-0.5 flex items-center gap-2 text-xs text-subtle font-mono">
            <span>:{portsDisplay}</span>
            <span className="opacity-50">|</span>
            <span>{item.proto || "TCP"}</span>
            <span className="opacity-50">|</span>
            <span>{item.ip}</span>
          </div>
        </div>

        {/* Risk badge */}
        <div className="flex items-center gap-3 shrink-0">
          <span className={`hidden sm:flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-bold ${meta.color} ${meta.bg} ${meta.border}`}>
            {meta.label}
          </span>
          <span className={`transition-transform duration-200 ${meta.color} ${expanded ? "rotate-180" : ""}`}>
            <ChevronDown className="h-4 w-4" />
          </span>
        </div>
      </button>

      {/* Brief justification visible when collapsed */}
      {!expanded && item.justification && (
        <div className="px-4 pb-3 text-xs text-subtle leading-relaxed line-clamp-1 border-t border-border/20 pt-2">
          {item.justification}
        </div>
      )}

      {/* ── Expanded content ── */}
      {expanded && (
        <div className="border-t border-border/40 animate-fade-in">
          {/* Tab bar */}
          <div className="flex gap-1 p-3 border-b border-border/40 bg-ink/30">
            {(["analyse", "remediation", "meta"] as const).map((tab) => {
              const tabLabels = {
                analyse: { icon: <Shield className="h-3.5 w-3.5" />, label: "Analyse" },
                remediation: { icon: <Terminal className="h-3.5 w-3.5" />, label: "Remédiation" },
                meta: { icon: <Cpu className="h-3.5 w-3.5" />, label: "Métadonnées" },
              };
              const t = tabLabels[tab];
              return (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-semibold transition-all duration-150 ${
                    activeTab === tab
                      ? `${meta.bg} ${meta.color} ${meta.border} border`
                      : "text-subtle hover:text-mist hover:bg-white/5 border border-transparent"
                  }`}
                >
                  {t.icon} {t.label}
                  {tab === "remediation" && hasRemediation && (
                    <span className={`ml-1 rounded-full px-1.5 py-0.5 text-[10px] font-bold bg-warning/20 text-warning`}>!</span>
                  )}
                </button>
              );
            })}
          </div>

          {/* Tab contents */}
          <div className="p-4">

            {/* ── ANALYSE TAB ── */}
            {activeTab === "analyse" && (
              <div className="space-y-4">
                {/* Risk header */}
                <div className={`flex items-start gap-3 rounded-xl border p-4 ${meta.bg} ${meta.border}`}>
                  <span className={`text-2xl shrink-0`}>{item.risk_icon || "🔵"}</span>
                  <div>
                    <div className={`text-sm font-bold ${meta.color} mb-1`}>Niveau de risque : {item.risk_level}</div>
                    <div className="text-xs text-subtle">{meta.desc}</div>
                  </div>
                </div>

                {/* Analysis paragraph */}
                <div className="rounded-xl border border-border/40 bg-ink/50 p-4">
                  <div className="flex items-center gap-2 mb-3">
                    <Network className="h-4 w-4 text-signal" />
                    <span className="text-xs font-bold uppercase tracking-wider text-signal">Analyse détaillée</span>
                  </div>
                  <p className="text-sm text-mist/90 leading-relaxed whitespace-pre-line">
                    {analysis.replace(/\*\*(.*?)\*\*/g, "$1")}
                  </p>
                </div>

                {/* Exposure */}
                {item.exposure && (
                  <div className="rounded-xl border border-border/40 bg-ink/50 p-4">
                    <div className="flex items-center gap-2 mb-3">
                      <Network className="h-4 w-4 text-subtle" />
                      <span className="text-xs font-bold uppercase tracking-wider text-subtle">Exposition réseau</span>
                    </div>
                    <p className="text-sm text-subtle leading-relaxed">{item.exposure}</p>
                  </div>
                )}

                {/* Reputation */}
                {item.reputation_verdict && item.reputation_verdict !== "unknown" && (
                  <div className="rounded-xl border border-border/40 bg-ink/50 p-4">
                    <div className="flex items-center gap-2 mb-2">
                      <Lock className="h-4 w-4 text-subtle" />
                      <span className="text-xs font-bold uppercase tracking-wider text-subtle">Réputation Cloud</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className={`rounded-full px-2.5 py-0.5 text-xs font-bold border ${
                        item.reputation_verdict === "malicious" ? "bg-danger/15 text-danger border-danger/40" :
                        item.reputation_verdict === "suspicious" ? "bg-warning/15 text-warning border-warning/40" :
                        item.reputation_verdict === "benign" ? "bg-signal/10 text-signal border-signal/30" :
                        "bg-border text-subtle border-border"
                      }`}>
                        {item.reputation_verdict.toUpperCase()}
                      </span>
                      {item.reputation_source && (
                        <span className="text-xs text-subtle">via {item.reputation_source}</span>
                      )}
                    </div>
                    {item.reputation_summary && (
                      <p className="mt-2 text-xs text-subtle">{item.reputation_summary}</p>
                    )}
                  </div>
                )}
              </div>
            )}

            {/* ── REMEDIATION TAB ── */}
            {activeTab === "remediation" && (
              <div className="space-y-4">
                {hasHardening && (
                  <div className="rounded-xl border border-warning/20 bg-warning/5 p-4">
                    <div className="flex items-center gap-2 mb-2">
                      <Shield className="h-4 w-4 text-warning" />
                      <span className="text-xs font-bold uppercase tracking-wider text-warning">Note de Hardening</span>
                    </div>
                    <p className="text-sm text-mist/85 leading-relaxed">{item.hardening_note}</p>
                  </div>
                )}

                {hasPowershell ? (
                  <div>
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-2">
                        <Terminal className="h-4 w-4 text-signal" />
                        <span className="text-xs font-bold uppercase tracking-wider text-signal">Commandes PowerShell</span>
                      </div>
                      <CopyButton text={psCode} />
                    </div>
                    <div className="terminal-card p-4 overflow-x-auto">
                      {(item.powershell as string[]).map((line, i) => (
                        <div key={i} className={`font-mono text-xs leading-relaxed ${line.startsWith("#") ? "text-signal/50 italic" : "text-signal"}`}>
                          {!line.startsWith("#") && <span className="text-subtle mr-2">PS&gt;</span>}
                          {line}
                        </div>
                      ))}
                    </div>
                  </div>
                ) : (
                  <div className="flex flex-col items-center justify-center py-8 text-center rounded-xl border border-border/40 bg-ink/40">
                    <Shield className="h-8 w-8 text-signal mb-3 opacity-60" />
                    <p className="text-sm font-semibold text-mist">Aucune remédiation requise</p>
                    <p className="mt-1 text-xs text-subtle">Ce service est considéré comme légitime ou sûr dans son contexte actuel.</p>
                  </div>
                )}

                {item.bash && item.bash.length > 0 && (
                  <div>
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-2">
                        <Terminal className="h-4 w-4 text-safe" />
                        <span className="text-xs font-bold uppercase tracking-wider text-safe">Commandes Bash / Linux</span>
                      </div>
                      <CopyButton text={(item.bash as string[]).join("\n")} />
                    </div>
                    <div className="terminal-card p-4">
                      {(item.bash as string[]).map((line, i) => (
                        <div key={i} className="font-mono text-xs text-safe leading-relaxed">
                          <span className="text-subtle mr-2">$</span>{line}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* ── METADATA TAB ── */}
            {activeTab === "meta" && (
              <div className="rounded-xl border border-border/40 bg-ink/50 overflow-hidden">
                <div className="p-3 border-b border-border/40 bg-ink/30">
                  <div className="flex items-center gap-2">
                    <Cpu className="h-4 w-4 text-subtle" />
                    <span className="text-xs font-bold uppercase tracking-wider text-subtle">Données Techniques</span>
                  </div>
                </div>
                <div className="divide-y divide-border/30 px-4 py-2">
                  <MetaRow label="Processus" value={item.proc} />
                  <MetaRow label="PID" value={item.pid} mono />
                  <MetaRow label="Port(s)" value={item.ports_list ? item.ports_list.join(", ") : item.port} mono />
                  <MetaRow label="Protocole" value={item.proto} mono />
                  <MetaRow label="IP" value={item.ip} mono />
                  <MetaRow label="Chemin" value={item.path} mono />
                  <MetaRow label="Publisher" value={item.publisher} />
                  <MetaRow label="Éditeur" value={item.company_name} />
                  <MetaRow label="Signature" value={item.signature_status} />
                  <MetaRow label="SHA-256" value={item.sha256 ? `${item.sha256.slice(0, 24)}...` : null} mono />
                  <MetaRow label="Réputation" value={item.reputation_verdict} />
                  <MetaRow label="Source" value={item.reputation_source} />
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
