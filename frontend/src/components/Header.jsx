import logo from "../../../img/logo.png";

export default function Header({ health }) {
  const apiOnline = health !== null && health !== undefined;

  return (
    <header className="relative overflow-hidden rounded-2xl border border-border glass-card shadow-card">
      <div className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-signal/40 to-transparent" />
      <div className="pointer-events-none absolute left-0 top-0 h-48 w-full bg-gradient-radial-signal opacity-60" />

      <div className="relative flex flex-col gap-6 p-6 md:flex-row md:items-center md:justify-between md:gap-8 lg:p-8">
        <div className="flex items-center gap-5">
          <div className="relative flex-shrink-0">
            <div className="absolute -inset-1 rounded-2xl bg-signal/10 blur-md" />
            <img
              src={logo}
              alt="Tafust logo"
              className="relative h-16 w-16 rounded-2xl border border-signal/20 object-contain shadow-glow-sm"
            />
          </div>
          <div>
            <div className="flex items-center gap-2.5">
              <span className="text-xs font-semibold uppercase tracking-[0.3em] text-signal">
                Tafust
              </span>
              <span className="rounded border border-border px-1.5 py-0.5 font-mono text-[10px] text-subtle">
                v0.1
              </span>
            </div>
            <h1 className="mt-1 text-2xl font-bold text-mist md:text-3xl">
              Network Security Audit
            </h1>
            <p className="mt-1 text-sm text-subtle">
              Ports · Processus · Classification des risques
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-3 md:flex-col md:items-end md:gap-2">
          <div className="flex items-center gap-2 rounded-lg border border-border bg-ink/40 px-3 py-2">
            <span className={`h-2 w-2 rounded-full ${apiOnline ? "bg-signal animate-pulse" : "bg-danger"}`} />
            <span className="text-xs font-medium text-subtle">
              API{" "}
              <span className={apiOnline ? "text-signal" : "text-danger"}>
                {apiOnline ? "en ligne" : "hors ligne"}
              </span>
            </span>
          </div>

          {health?.os && (
            <div className="flex items-center gap-2 rounded-lg border border-border bg-ink/40 px-3 py-2">
              <svg className="h-3.5 w-3.5 text-subtle" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 17.25v1.007a3 3 0 01-.879 2.122L7.5 21h9l-.621-.621A3 3 0 0115 18.257V17.25m6-12V15a2.25 2.25 0 01-2.25 2.25H5.25A2.25 2.25 0 013 15V5.25m18 0A2.25 2.25 0 0018.75 3H5.25A2.25 2.25 0 003 5.25m18 0H3" />
              </svg>
              <span className="font-mono text-xs text-mist">{health.os}</span>
            </div>
          )}

          <div
            className={`flex items-center gap-2 rounded-lg border px-3 py-2 ${
              health?.has_virustotal_key
                ? "border-signal/20 bg-signal/5"
                : "border-border bg-ink/40"
            }`}
          >
            <svg className={`h-3.5 w-3.5 ${health?.has_virustotal_key ? "text-signal" : "text-subtle"}`} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
            </svg>
            <span className="text-xs text-subtle">
              VirusTotal{" "}
              <span className={health?.has_virustotal_key ? "text-signal" : "text-warning"}>
                {health?.has_virustotal_key ? "actif" : "non configuré"}
              </span>
            </span>
          </div>
        </div>
      </div>
    </header>
  );
}
