import { useEffect, useState } from "react";

const ICONS = {
  success: (
    <svg className="h-4 w-4 text-signal" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
    </svg>
  ),
  error: (
    <svg className="h-4 w-4 text-danger" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
    </svg>
  ),
  info: (
    <svg className="h-4 w-4 text-signal" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path strokeLinecap="round" strokeLinejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  ),
};

const STYLES = {
  success: "border-signal/30 bg-signal/10",
  error: "border-danger/30 bg-danger/10",
  info: "border-border bg-card",
};

export default function Toast({ message, type = "info", onClose }) {
  const [leaving, setLeaving] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => {
      setLeaving(true);
      setTimeout(onClose, 300);
    }, 4000);
    return () => clearTimeout(timer);
  }, [onClose]);

  return (
    <div
      className={`flex items-start gap-3 rounded-xl border p-4 shadow-card backdrop-blur
        ${STYLES[type]}
        ${leaving ? "animate-toast-out" : "animate-toast-in"}
      `}
    >
      <span className="mt-0.5 flex-shrink-0">{ICONS[type]}</span>
      <p className="text-sm text-mist leading-5">{message}</p>
      <button
        onClick={() => { setLeaving(true); setTimeout(onClose, 300); }}
        className="ml-auto flex-shrink-0 text-subtle hover:text-mist transition-colors"
      >
        <svg className="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </div>
  );
}

export function ToastContainer({ toasts, removeToast }) {
  return (
    <div className="fixed bottom-6 right-6 z-50 flex w-80 flex-col gap-2">
      {toasts.map((t) => (
        <Toast key={t.id} message={t.message} type={t.type} onClose={() => removeToast(t.id)} />
      ))}
    </div>
  );
}
