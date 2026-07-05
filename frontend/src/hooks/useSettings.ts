import { useState, useEffect } from "react";

export interface TafustSettings {
  exclude_local: boolean;
  timeout: number;
  threads: number;
  port_range: string;
}

const DEFAULT_SETTINGS: TafustSettings = {
  exclude_local: false,
  timeout: 5000,
  threads: 10,
  port_range: "1-1024",
};

export function useSettings() {
  const [settings, setSettings] = useState<TafustSettings>(() => {
    try {
      const stored = localStorage.getItem("tafust_settings");
      if (stored) {
        return { ...DEFAULT_SETTINGS, ...JSON.parse(stored) };
      }
    } catch (e) {
      console.error("Error loading settings", e);
    }
    return DEFAULT_SETTINGS;
  });

  useEffect(() => {
    localStorage.setItem("tafust_settings", JSON.stringify(settings));
  }, [settings]);

  return { settings, setSettings };
}
