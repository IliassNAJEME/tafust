import { useState } from "react";
import StatusBadge from "./StatusBadge";

function CopyButton({ text }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      /* silent */
    }
  };

  return (
    <button
      onClick={handleCopy}
      className={`flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-xs font-medium transition-all duration-200 ${
        copied
          ? "border-signal/40 bg-signal/10 text-signal"
          : "border-border text-subtle hover:border-signal/30 hover:text-mist"
      }`}
    >
      {copied ? (
        <>
          <svg className="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
          </svg>
          Copié !
        </>
      ) : (
        <>
          <svg className="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path strokeLinecap="round" strokeLinejoin="round" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
          </svg>
          Copier
        </>
      )}
    </button>
  );
}

function HardeningItem({ item, index }) {
  const [open, setOpen] = useState(false);
  const hasPS = item.powershell?.length > 0;
  const hasBash = item.bash?.length > 0;

  return (
    <div
      className="rounded-2xl border border-border glass-card overflow-hidden animate-fade-in"
      style={{ animationDelay: `${index * 0.06}s`, opacity: 0 }}
    >
      {/* Header */}
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center justify-between gap-4 p-5 text-left hover:bg-white/[0.02] transition-colors"
      >
        <div className="flex items-center gap-3 min-w-0">
          <StatusBadge level={item.risk_level} />
          <div className="min-w-0">
            <p className="truncate font-semibold text-mist">{item.label || item.proc}</p>
            {item.label && item.label !== item.proc && (
              <p className="font-mono text-xs text-subtle">{item.proc}</p>
            )}
          </div>
        </div>
        <svg
          className={`h-4 w-4 flex-shrink-0 text-subtle transition-transform duration-200 ${open ? "rotate-180" : ""}`}
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {open && (
        <div className="border-t border-border/50 px-5 pb-5 pt-4 space-y-4 animate-fade-in">
          <p className="text-sm leading-6 text-mist/75">{item.justification}</p>

          {hasPS && (
            <div>
              <div className="mb-2 flex items-center justify-between">
                <span className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-subtle">
                  <svg className="h-3.5 w-3.5 text-signal" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M4 6h16v2H4zm0 5h16v2H4zm0 5h16v2H4z"/>
                  </svg>
                  PowerShell
                </span>
                <CopyButton text={item.powershell.join("\n")} />
              </div>
              <pre className="code-block overflow-x-auto whitespace-pre-wrap leading-6">
                {item.powershell.join("\n")}
              </pre>
            </div>
          )}

          {hasBash && (
            <div>
              <div className="mb-2 flex items-center justify-between">
                <span className="text-xs font-semibold uppercase tracking-wider text-subtle">
                  Bash / Linux
                </span>
                <CopyButton text={item.bash.join("\n")} />
              </div>
              <pre className="code-block overflow-x-auto whitespace-pre-wrap leading-6 text-warning">
                {item.bash.join("\n")}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function HardeningPanel({ hardenings }) {
  if (!hardenings || hardenings.length === 0) {
    return (
      <div className="rounded-2xl border border-border py-10 text-center text-sm text-subtle glass-card">
        Aucune recommandation de durcissement disponible pour ce scan.
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {hardenings.map((item, i) => (
        <HardeningItem key={`${item.proc}-${i}`} item={item} index={i} />
      ))}
    </div>
  );
}
