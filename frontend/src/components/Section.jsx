import { useState } from "react";
import EntryCard from "./EntryCard";

const RISK_LEVELS = ["CRITIQUE", "ÉLEVÉ", "MODÉRÉ", "FAIBLE", "TRÈS FAIBLE"];

const FILTER_COLORS = {
  CRITIQUE: "border-danger/30 bg-danger/5 text-danger hover:bg-danger/10",
  "ÉLEVÉ": "border-warning/30 bg-warning/5 text-warning hover:bg-warning/10",
  "MODÉRÉ": "border-amber-500/30 bg-amber-500/5 text-amber-400 hover:bg-amber-500/10",
  FAIBLE: "border-safe/30 bg-safe/5 text-safe hover:bg-safe/10",
  "TRÈS FAIBLE": "border-signal/30 bg-signal/5 text-signal hover:bg-signal/10",
};

export default function Section({ title, subtitle, items, compact = false }) {
  const [activeFilters, setActiveFilters] = useState([]);

  if (!items || items.length === 0) return null;

  // Collect which risk levels are present
  const presentLevels = RISK_LEVELS.filter((lvl) =>
    items.some((item) => item.risk_level === lvl)
  );

  const toggleFilter = (level) => {
    setActiveFilters((prev) =>
      prev.includes(level) ? prev.filter((l) => l !== level) : [...prev, level]
    );
  };

  const filtered =
    activeFilters.length === 0
      ? items
      : items.filter((item) => activeFilters.includes(item.risk_level));

  return (
    <section className="space-y-4">
      {/* Header */}
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-mist">{title}</h2>
          <p className="mt-1 text-sm text-subtle">{subtitle}</p>
        </div>
        <span className="rounded-full border border-border bg-card px-3 py-1 font-mono text-sm text-subtle">
          {filtered.length}
          {filtered.length !== items.length && (
            <span className="text-subtle/60"> / {items.length}</span>
          )}
        </span>
      </div>

      {/* Filters */}
      {presentLevels.length > 1 && (
        <div className="flex flex-wrap gap-2">
          {presentLevels.map((lvl) => {
            const isActive = activeFilters.includes(lvl);
            const count = items.filter((i) => i.risk_level === lvl).length;
            return (
              <button
                key={lvl}
                onClick={() => toggleFilter(lvl)}
                className={`filter-pill border transition-all duration-150 ${
                  isActive
                    ? FILTER_COLORS[lvl] + " opacity-100"
                    : "opacity-70 hover:opacity-100"
                }`}
              >
                {lvl}
                <span className="ml-1.5 rounded-full bg-current/10 px-1.5 py-0.5 font-mono text-[10px]">
                  {count}
                </span>
              </button>
            );
          })}
          {activeFilters.length > 0 && (
            <button
              onClick={() => setActiveFilters([])}
              className="filter-pill border-border text-subtle hover:text-mist hover:border-border/80"
            >
              ✕ Réinitialiser
            </button>
          )}
        </div>
      )}

      {/* Cards grid */}
      <div className="grid gap-4 xl:grid-cols-2">
        {filtered.map((entry, index) => (
          <EntryCard
            key={`${entry.proc}-${entry.port || "group"}-${index}`}
            entry={entry}
            compact={compact}
            index={index}
          />
        ))}
      </div>

      {filtered.length === 0 && (
        <div className="rounded-2xl border border-border py-10 text-center text-sm text-subtle glass-card">
          Aucune entrée pour ce filtre.
        </div>
      )}
    </section>
  );
}
