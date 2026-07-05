import React, { useEffect, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { Activity, LayoutDashboard, History, Settings, ShieldAlert, Zap } from "lucide-react";
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

const API_BASE = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/$/, "");

const NAV_ITEMS = [
  { name: "Dashboard",   path: "/",         icon: LayoutDashboard },
  { name: "Résultats",   path: "/results",  icon: Activity },
  { name: "Historique",  path: "/history",  icon: History },
  { name: "Paramètres",  path: "/settings", icon: Settings },
];

export default function MainLayout({ children }: { children: React.ReactNode }) {
  const location = useLocation();
  const [health, setHealth] = useState<any>(undefined);
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    fetch(`${API_BASE}/api/health`)
      .then((r) => r.json())
      .then(setHealth)
      .catch(() => setHealth(null));
  }, []);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 10);
    window.addEventListener("scroll", onScroll);
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  const apiOnline = health !== null && health !== undefined;

  return (
    <div className="relative min-h-screen bg-ink text-mist font-sans overflow-x-hidden">
      {/* ── Background ── */}
      <div className="bg-grid pointer-events-none fixed inset-0 opacity-60" />
      <div className="pointer-events-none fixed inset-x-0 top-0 h-[500px] bg-[radial-gradient(ellipse_at_50%_-20%,rgba(0,255,163,0.07)_0%,transparent_60%)]" />

      {/* ── Particle-like accent blobs ── */}
      <div className="pointer-events-none fixed top-1/4 -right-32 h-80 w-80 rounded-full bg-signal/3 blur-3xl" />
      <div className="pointer-events-none fixed bottom-1/4 -left-32 h-80 w-80 rounded-full bg-signal/2 blur-3xl" />

      <div className="relative mx-auto flex max-w-7xl flex-col min-h-screen px-4 py-5 md:px-6 xl:px-8">

        {/* ── HEADER ── */}
        <header
          className={cn(
            "sticky top-4 z-50 mb-6 rounded-2xl border transition-all duration-300",
            scrolled
              ? "glass-card border-signal/15 shadow-glow"
              : "glass-card border-border/60"
          )}
        >
          {/* Top shimmer line */}
          <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-signal/40 to-transparent rounded-t-2xl" />

          <div className="relative flex items-center justify-between px-5 py-3.5 gap-4">

            {/* Logo + brand */}
            <div className="flex items-center gap-4">
              <div className="relative flex h-11 w-11 items-center justify-center rounded-xl border border-signal/30 bg-signal/10 animate-glow-pulse">
                <ShieldAlert className="h-6 w-6 text-signal" />
                <span className="absolute -top-1 -right-1 h-2.5 w-2.5 rounded-full border border-ink bg-signal animate-pulse" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-xs font-black uppercase tracking-[0.35em] text-signal">
                    Tafust
                  </span>
                  <span className="rounded border border-border/70 px-1.5 py-0.5 font-mono text-[9px] text-subtle/70">
                    v0.1
                  </span>
                </div>
                <div className="text-sm font-bold text-mist leading-none mt-0.5">
                  Network Security Audit
                </div>
              </div>
            </div>

            {/* Center — nav */}
            <nav className="flex items-center gap-1">
              {NAV_ITEMS.map((item) => {
                const Icon = item.icon;
                const isActive = location.pathname === item.path;
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    className={cn(
                      "nav-item text-sm relative",
                      isActive ? "nav-item-active" : "nav-item-inactive"
                    )}
                  >
                    <Icon className="h-4 w-4 shrink-0" />
                    <span className="hidden md:inline">{item.name}</span>
                    {isActive && (
                      <span className="absolute -bottom-0.5 left-1/2 -translate-x-1/2 h-px w-4/5 bg-signal/60 rounded-full" />
                    )}
                  </Link>
                );
              })}
            </nav>

            {/* Right — API status */}
            <div
              className={cn(
                "flex items-center gap-2 rounded-xl border px-3 py-2 text-xs font-medium transition-all",
                apiOnline
                  ? "border-signal/20 bg-signal/5 text-signal"
                  : "border-danger/20 bg-danger/5 text-danger"
              )}
            >
              <span className={`h-2 w-2 rounded-full ${apiOnline ? "bg-signal animate-pulse" : "bg-danger"}`} />
              <span className="hidden sm:inline">
                Agent {apiOnline ? "connecté" : "déconnecté"}
              </span>
              <Zap className="h-3.5 w-3.5 sm:hidden" />
            </div>
          </div>

          {/* Bottom shimmer */}
          <div className="absolute inset-x-0 bottom-0 h-px bg-gradient-to-r from-transparent via-border/50 to-transparent rounded-b-2xl" />
        </header>

        {/* ── CONTENT ── */}
        <main className="flex-1">
          {children}
        </main>

        {/* ── FOOTER ── */}
        <footer className="mt-10 flex items-center justify-between border-t border-border/40 pt-4 text-xs text-subtle/60">
          <span>Tafust Network Security Audit — Local Analysis Engine</span>
          <span className="font-mono">v0.1.0</span>
        </footer>
      </div>
    </div>
  );
}
