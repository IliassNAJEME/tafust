export default function ScanPanel({
  excludeLocal,
  setExcludeLocal,
  onScan,
  loading,
  error,
  demoMode = false,
}) {
  return (
    <div className="rounded-2xl border border-border glass-card p-6 shadow-card">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h2 className="text-base font-semibold text-mist">
            {demoMode ? "Tester la demo publique" : "Lancer un scan"}
          </h2>
          <p className="mt-0.5 text-xs text-subtle">
            {demoMode
              ? "Cette version publique charge un rapport d'exemple. Le scan reel reste local."
              : "Inspecte les ports en ecoute et classe les processus par niveau de risque"}
          </p>
        </div>
        <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-xl border border-signal/20 bg-signal/5">
          <svg className="h-5 w-5 text-signal" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
          </svg>
        </div>
      </div>

      <div className="mt-5 flex flex-wrap items-center gap-4">
        <label
          className={`flex items-center gap-3 rounded-xl border px-4 py-2.5 text-sm transition-colors ${
            demoMode
              ? "cursor-not-allowed border-border/60 bg-ink/20 opacity-60"
              : "cursor-pointer border-border bg-ink/40 hover:border-signal/30"
          }`}
          htmlFor="exclude-local-toggle"
        >
          <div className="relative">
            <input
              id="exclude-local-toggle"
              type="checkbox"
              className="sr-only"
              checked={excludeLocal}
              disabled={demoMode}
              onChange={(e) => setExcludeLocal(e.target.checked)}
            />
            <div
              className={`h-5 w-9 rounded-full border transition-all duration-200 ${
                excludeLocal ? "border-signal/40 bg-signal/20" : "border-border bg-ink"
              }`}
            >
              <div
                className={`absolute top-0.5 h-4 w-4 rounded-full border transition-all duration-200 ${
                  excludeLocal
                    ? "left-4 border-signal bg-signal"
                    : "left-0.5 border-subtle bg-subtle"
                }`}
              />
            </div>
          </div>
          <span className="text-subtle">
            Exclure les listeners <span className="font-mono text-xs text-mist">loopback</span>
          </span>
        </label>

        <button
          type="button"
          onClick={onScan}
          disabled={loading}
          className="btn-signal min-w-[160px] flex-1"
          id="launch-scan-btn"
        >
          {loading ? (
            <>
              <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path strokeLinecap="round" strokeLinejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              Chargement...
            </>
          ) : (
            <>
              <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
              </svg>
              {demoMode ? "Recharger la demo" : "Lancer l'audit"}
            </>
          )}
        </button>
      </div>

      {demoMode && (
        <div className="mt-4 rounded-xl border border-signal/20 bg-signal/5 px-4 py-3 text-sm text-subtle">
          Site public en mode demo. Pour scanner une machine reelle, il faut lancer Tafust localement.
        </div>
      )}

      {error && (
        <div className="mt-4 flex items-center gap-2 rounded-xl border border-danger/30 bg-danger/10 px-4 py-3 text-sm text-danger animate-fade-in">
          <svg className="h-4 w-4 flex-shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
          </svg>
          {error}
        </div>
      )}
    </div>
  );
}
