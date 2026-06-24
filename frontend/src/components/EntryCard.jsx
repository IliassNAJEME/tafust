import { useState } from "react";
import StatusBadge, { RISK_CONFIG } from "./StatusBadge";

function CopyButton({ text }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      /* fallback silent */
    }
  };

  return (
    <button
      onClick={handleCopy}
      className={`rounded-md border px-2 py-1 font-mono text-xs transition-all duration-200 ${
        copied
          ? "border-signal/40 bg-signal/10 text-signal"
          : "border-border text-subtle hover:border-signal/30 hover:text-mist"
      }`}
    >
      {copied ? "✓ Copié" : "Copier"}
    </button>
  );
}

function DetailRow({ label, value }) {
  if (!value) return null;
  return (
    <div className="flex flex-col gap-0.5">
      <span className="text-[10px] font-semibold uppercase tracking-wider text-subtle">{label}</span>
      <span className="break-all font-mono text-xs text-mist/80">{value}</span>
    </div>
  );
}

export default function EntryCard({ entry, compact = false, index = 0 }) {
  const [expanded, setExpanded] = useState(false);

  const ports = compact
    ? entry.ports_list?.join(", ") || String(entry.port)
    : `${entry.port}/${entry.proto}`;
  const ips = compact
    ? entry.ips_list?.join(", ") || entry.ip
    : entry.ip;

  const config = RISK_CONFIG[entry.risk_level] || {
    bg: "bg-subtle/5",
    border: "border-border",
    text: "text-subtle",
  };

  const hasDetails =
    entry.path || entry.sha256 || entry.signature_status || entry.publisher || entry.company_name;
  const hasPS = entry.powershell?.length > 0;

  return (
    <article
      className={`rounded-2xl border ${config.border} ${config.bg} shadow-card transition-all duration-200 animate-fade-in`}
      style={{ animationDelay: `${index * 0.05}s`, opacity: 0 }}
    >
      {/* Main content */}
      <div className="p-5">
        {/* Top row */}
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="min-w-0">
            <h3 className="truncate text-base font-semibold text-mist">
              {entry.label || entry.proc}
            </h3>
            {entry.label && entry.label !== entry.proc && (
              <p className="mt-0.5 font-mono text-xs text-subtle">{entry.proc}</p>
            )}
          </div>
          <StatusBadge level={entry.risk_level} />
        </div>

        {/* Info grid */}
        <div className="mt-4 grid grid-cols-2 gap-3 text-xs md:grid-cols-4">
          <div>
            <p className="text-subtle">Port(s)</p>
            <p className="mt-1 font-mono font-medium text-mist">{ports}</p>
          </div>
          <div>
            <p className="text-subtle">Interface</p>
            <p className="mt-1 font-mono font-medium text-mist">{ips}</p>
          </div>
          {entry.company_name && (
            <div>
              <p className="text-subtle">Éditeur</p>
              <p className="mt-1 font-medium text-mist truncate">{entry.company_name}</p>
            </div>
          )}
          {entry.signature_status && (
            <div>
              <p className="text-subtle">Signature</p>
              <p
                className={`mt-1 font-medium ${
                  entry.signature_status === "Valid"
                    ? "text-signal"
                    : entry.signature_status === "Unavailable"
                    ? "text-subtle"
                    : "text-warning"
                }`}
              >
                {entry.signature_status}
              </p>
            </div>
          )}
        </div>

        {/* Justification */}
        <p className="mt-4 text-sm leading-6 text-mist/75">{entry.justification}</p>

        {/* Exposure */}
        {entry.exposure && !compact && (
          <div className="mt-3 flex items-center gap-2 text-xs text-subtle">
            <svg className="h-3.5 w-3.5 flex-shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 21a9.004 9.004 0 008.716-6.747M12 21a9.004 9.004 0 01-8.716-6.747M12 21c2.485 0 4.5-4.03 4.5-9S14.485 3 12 3m0 18c-2.485 0-4.5-4.03-4.5-9S9.515 3 12 3m0 0a8.997 8.997 0 017.843 4.582M12 3a8.997 8.997 0 00-7.843 4.582m15.686 0A11.953 11.953 0 0112 10.5c-2.998 0-5.74-1.1-7.843-2.918m15.686 0A8.959 8.959 0 0121 12c0 .778-.099 1.533-.284 2.253m0 0A17.919 17.919 0 0112 16.5c-3.162 0-6.133-.815-8.716-2.247m0 0A9.015 9.015 0 013 12c0-1.605.42-3.113 1.157-4.418" />
            </svg>
            {entry.exposure}
          </div>
        )}

        {/* Expand / collapse toggle */}
        {(hasDetails || hasPS) && (
          <button
            onClick={() => setExpanded((v) => !v)}
            className="mt-4 flex items-center gap-1.5 text-xs font-medium text-subtle transition-colors hover:text-signal"
          >
            <svg
              className={`h-3.5 w-3.5 transition-transform duration-200 ${expanded ? "rotate-180" : ""}`}
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
            </svg>
            {expanded ? "Masquer les détails" : "Voir les détails"}
          </button>
        )}
      </div>

      {/* Expandable section */}
      {expanded && (
        <div className="border-t border-border/50 px-5 pb-5 pt-4 space-y-4 animate-fade-in">
          {hasDetails && (
            <div className="grid gap-3 sm:grid-cols-2">
              <DetailRow label="Chemin" value={entry.path} />
              <DetailRow label="SHA-256" value={entry.sha256 ? `${entry.sha256.slice(0, 16)}...${entry.sha256.slice(-8)}` : ""} />
              <DetailRow label="Éditeur" value={entry.publisher} />
              <DetailRow label="Réputation" value={entry.reputation_summary} />
            </div>
          )}

          {hasPS && (
            <div>
              <div className="mb-2 flex items-center justify-between">
                <p className="text-xs font-semibold uppercase tracking-wider text-subtle">
                  Commande PowerShell
                </p>
                <CopyButton text={entry.powershell.join("\n")} />
              </div>
              <pre className="code-block overflow-x-auto whitespace-pre-wrap leading-5">
                {entry.powershell.join("\n")}
              </pre>
            </div>
          )}
        </div>
      )}
    </article>
  );
}
