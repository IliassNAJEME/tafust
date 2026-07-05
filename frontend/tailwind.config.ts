import type { Config } from "tailwindcss";

export default {
  darkMode: ["class"],
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "ui-monospace", "monospace"],
      },
      colors: {
        ink: "#070d1a",
        panel: "#0b1425",
        card: "#0f1d32",
        border: "#1a2d4a",
        mist: "#d7e3f4",
        signal: "#00ffa3",
        "signal-dim": "#00c97e",
        danger: "#ff4757",
        "danger-dim": "#c0392b",
        warning: "#ffa502",
        "warning-dim": "#e67e00",
        safe: "#2ed573",
        "safe-dim": "#1db954",
        ember: "#ff6b35",
        steel: "#132238",
        subtle: "#8ba4c0",
        background: "var(--background)",
        foreground: "var(--foreground)",
        primary: {
          DEFAULT: "var(--primary)",
          foreground: "var(--primary-foreground)",
        },
        secondary: {
          DEFAULT: "var(--secondary)",
          foreground: "var(--secondary-foreground)",
        },
        destructive: {
          DEFAULT: "var(--destructive)",
          foreground: "var(--destructive-foreground)",
        },
        muted: {
          DEFAULT: "var(--muted)",
          foreground: "var(--muted-foreground)",
        },
        accent: {
          DEFAULT: "var(--accent)",
          foreground: "var(--accent-foreground)",
        },
        popover: {
          DEFAULT: "var(--popover)",
          foreground: "var(--popover-foreground)",
        },
        input: "var(--input)",
        ring: "var(--ring)",
      },
      boxShadow: {
        glow: "0 0 40px rgba(0, 255, 163, 0.12)",
        "glow-sm": "0 0 20px rgba(0, 255, 163, 0.08)",
        "glow-danger": "0 0 30px rgba(255, 71, 87, 0.15)",
        "glow-warning": "0 0 30px rgba(255, 165, 2, 0.15)",
        card: "0 4px 24px rgba(0, 0, 0, 0.4)",
        "card-hover": "0 8px 40px rgba(0, 0, 0, 0.6)",
      },
      keyframes: {
        "fade-in": {
          "0%": { opacity: "0", transform: "translateY(12px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "fade-in-fast": {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        "slide-up": {
          "0%": { opacity: "0", transform: "translateY(24px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "slide-in-right": {
          "0%": { opacity: "0", transform: "translateX(24px)" },
          "100%": { opacity: "1", transform: "translateX(0)" },
        },
        "pulse-ring": {
          "0%, 100%": { opacity: "1", transform: "scale(1)" },
          "50%": { opacity: "0.4", transform: "scale(1.15)" },
        },
        "ping-slow": {
          "75%, 100%": { transform: "scale(2)", opacity: "0" },
        },
        "scan-line": {
          "0%": { transform: "translateY(-100%)" },
          "100%": { transform: "translateY(100vh)" },
        },
        "glow-pulse": {
          "0%, 100%": { boxShadow: "0 0 20px rgba(0,255,163,0.10), 0 0 40px rgba(0,255,163,0.05)" },
          "50%": { boxShadow: "0 0 40px rgba(0,255,163,0.25), 0 0 80px rgba(0,255,163,0.10)" },
        },
        "glow-pulse-danger": {
          "0%, 100%": { boxShadow: "0 0 20px rgba(255,71,87,0.15)" },
          "50%": { boxShadow: "0 0 40px rgba(255,71,87,0.35)" },
        },
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
        "counter-up": {
          "0%": { opacity: "0", transform: "translateY(8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "toast-in": {
          "0%": { opacity: "0", transform: "translateX(100%)" },
          "100%": { opacity: "1", transform: "translateX(0)" },
        },
        "toast-out": {
          "0%": { opacity: "1", transform: "translateX(0)" },
          "100%": { opacity: "0", transform: "translateX(100%)" },
        },
        "gradient-x": {
          "0%, 100%": { backgroundSize: "200% 200%", backgroundPosition: "left center" },
          "50%": { backgroundSize: "200% 200%", backgroundPosition: "right center" },
        },
      },
      animation: {
        "fade-in": "fade-in 0.4s ease-out forwards",
        "fade-in-fast": "fade-in-fast 0.2s ease-out forwards",
        "slide-up": "slide-up 0.5s ease-out forwards",
        "slide-in-right": "slide-in-right 0.35s ease-out forwards",
        "pulse-ring": "pulse-ring 2s ease-in-out infinite",
        "ping-slow": "ping-slow 2s cubic-bezier(0,0,0.2,1) infinite",
        "scan-line": "scan-line 2s linear infinite",
        "glow-pulse": "glow-pulse 3s ease-in-out infinite",
        "glow-pulse-danger": "glow-pulse-danger 2s ease-in-out infinite",
        shimmer: "shimmer 2s linear infinite",
        "counter-up": "counter-up 0.5s ease-out forwards",
        "toast-in": "toast-in 0.3s ease-out forwards",
        "toast-out": "toast-out 0.3s ease-in forwards",
        "gradient-x": "gradient-x 4s ease infinite",
      },
      backgroundImage: {
        "grid-pattern":
          "linear-gradient(rgba(0,255,163,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(0,255,163,0.03) 1px, transparent 1px)",
        "gradient-radial-signal":
          "radial-gradient(ellipse at 50% 0%, rgba(0,255,163,0.08) 0%, transparent 60%)",
        "gradient-radial-danger":
          "radial-gradient(ellipse at 50% 0%, rgba(255,71,87,0.08) 0%, transparent 60%)",
      },
      backgroundSize: {
        "grid-sm": "24px 24px",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
} satisfies Config;
