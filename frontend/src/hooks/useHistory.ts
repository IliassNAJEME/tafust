import { useState, useCallback } from "react";

export interface ScanHistoryEntry {
  id: string;
  date: string;
  excludeLocal: boolean;
  summary: {
    nb_alertes: number;
    nb_surveiller: number;
    nb_legitimes: number;
    total: number;
    verdict?: string;
  };
  raw_data?: any; // Mapped to the raw report if needed, though this can be large
}

export function useHistory() {
  const [history, setHistory] = useState<ScanHistoryEntry[]>(() => {
    try {
      const stored = localStorage.getItem("tafust_scan_history");
      if (stored) {
        return JSON.parse(stored);
      }
    } catch (e) {
      console.error("Error loading history", e);
    }
    return [];
  });

  const addEntry = useCallback((entry: Omit<ScanHistoryEntry, "id" | "date">) => {
    setHistory((prev) => {
      const newEntry: ScanHistoryEntry = {
        ...entry,
        id: crypto.randomUUID(),
        date: new Date().toISOString(),
      };
      
      const newHistory = [newEntry, ...prev].slice(0, 50); // Keep max 50
      localStorage.setItem("tafust_scan_history", JSON.stringify(newHistory));
      return newHistory;
    });
  }, []);

  const clearHistory = useCallback(() => {
    setHistory([]);
    localStorage.removeItem("tafust_scan_history");
  }, []);

  return { history, addEntry, clearHistory };
}
