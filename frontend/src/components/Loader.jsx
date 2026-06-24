export default function Loader() {
  return (
    <div className="flex flex-col items-center justify-center gap-6 py-20 animate-fade-in">
      {/* Radar ring animation */}
      <div className="relative flex h-24 w-24 items-center justify-center">
        <span className="absolute inset-0 rounded-full border border-signal/30 animate-ping" />
        <span
          className="absolute inset-2 rounded-full border border-signal/20 animate-ping"
          style={{ animationDelay: "0.3s" }}
        />
        <span
          className="absolute inset-4 rounded-full border border-signal/10 animate-ping"
          style={{ animationDelay: "0.6s" }}
        />
        {/* Center icon */}
        <div className="relative flex h-10 w-10 items-center justify-center rounded-full bg-signal/10 border border-signal/30">
          <svg
            className="h-5 w-5 text-signal animate-spin"
            style={{ animationDuration: "3s" }}
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z"
            />
          </svg>
        </div>
      </div>

      <div className="text-center">
        <p className="text-base font-semibold text-signal">Scan en cours...</p>
        <p className="mt-1 text-sm text-subtle">
          Inspection des ports et processus actifs
        </p>
      </div>

      {/* Progress steps */}
      <div className="flex flex-col gap-2 w-64">
        {[
          "Collecte des connexions réseau",
          "Résolution des processus",
          "Analyse des risques",
        ].map((step, i) => (
          <div
            key={step}
            className="flex items-center gap-3 animate-fade-in"
            style={{ animationDelay: `${i * 0.4}s`, opacity: 0 }}
          >
            <span className="h-1.5 w-1.5 rounded-full bg-signal animate-pulse" />
            <span className="text-xs text-subtle">{step}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
