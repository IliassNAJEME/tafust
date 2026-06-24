const RISK_CONFIG = {
  CRITIQUE: {
    bg: "bg-danger/15",
    border: "border-danger/30",
    text: "text-danger",
    dot: "bg-danger",
    icon: "🔴",
    label: "CRITIQUE",
  },
  "ÉLEVÉ": {
    bg: "bg-warning/15",
    border: "border-warning/30",
    text: "text-warning",
    dot: "bg-warning",
    icon: "🟠",
    label: "ÉLEVÉ",
  },
  "MODÉRÉ": {
    bg: "bg-amber-500/15",
    border: "border-amber-500/30",
    text: "text-amber-400",
    dot: "bg-amber-400",
    icon: "🟡",
    label: "MODÉRÉ",
  },
  FAIBLE: {
    bg: "bg-safe/10",
    border: "border-safe/25",
    text: "text-safe",
    dot: "bg-safe",
    icon: "🟢",
    label: "FAIBLE",
  },
  "TRÈS FAIBLE": {
    bg: "bg-signal/8",
    border: "border-signal/20",
    text: "text-signal",
    dot: "bg-signal",
    icon: "🟢",
    label: "TRÈS FAIBLE",
  },
};

export default function StatusBadge({ level, size = "sm" }) {
  const config = RISK_CONFIG[level] || {
    bg: "bg-subtle/10",
    border: "border-border",
    text: "text-subtle",
    dot: "bg-subtle",
    icon: "⚪",
    label: level || "INCONNU",
  };

  const sizeClasses = size === "lg"
    ? "px-3.5 py-1.5 text-sm gap-2"
    : "px-2.5 py-1 text-xs gap-1.5";

  return (
    <span
      className={`risk-badge ${config.bg} border ${config.border} ${config.text} ${sizeClasses}`}
    >
      <span className={`inline-block h-1.5 w-1.5 rounded-full ${config.dot} animate-pulse-ring`} />
      {config.label}
    </span>
  );
}

export { RISK_CONFIG };
