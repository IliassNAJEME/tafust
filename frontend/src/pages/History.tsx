import { motion } from "framer-motion";
import { useHistory } from "../hooks/useHistory";
import { History as HistoryIcon, Trash2, ShieldCheck, ShieldAlert, AlertTriangle } from "lucide-react";
import { Button } from "../components/ui/button";
import { Card, CardHeader, CardTitle, CardContent } from "../components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../components/ui/table";

const getVerdictIcon = (verdict?: string) => {
  if (verdict?.includes("attention") || verdict?.includes("Critique")) return <ShieldAlert className="h-5 w-5 text-danger" />;
  if (verdict?.includes("healthy") || verdict?.includes("Sain")) return <ShieldCheck className="h-5 w-5 text-signal" />;
  return <AlertTriangle className="h-5 w-5 text-warning" />;
};

export default function History() {
  const { history, clearHistory } = useHistory();

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      className="space-y-6"
    >
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <HistoryIcon className="h-6 w-6 text-signal" />
          <h2 className="text-2xl font-bold text-mist">Historique des Scans</h2>
        </div>
        {history.length > 0 && (
          <Button 
            variant="destructive" 
            size="sm" 
            onClick={clearHistory}
            className="bg-danger/10 text-danger hover:bg-danger/20 border border-danger/30"
          >
            <Trash2 className="h-4 w-4 mr-2" />
            Vider l'historique
          </Button>
        )}
      </div>

      <Card className="border-border bg-card/50 backdrop-blur">
        <CardHeader>
          <CardTitle className="text-mist">Derniers audits ({history.length}/50)</CardTitle>
        </CardHeader>
        <CardContent>
          {history.length === 0 ? (
            <div className="py-12 text-center text-subtle">
              Aucun historique disponible. Lancez un scan pour voir les résultats ici.
            </div>
          ) : (
            <div className="rounded-md border border-border">
              <Table>
                <TableHeader className="bg-ink/50">
                  <TableRow className="border-border hover:bg-transparent">
                    <TableHead className="text-subtle">Date</TableHead>
                    <TableHead className="text-subtle">Verdict</TableHead>
                    <TableHead className="text-subtle text-right">Alertes</TableHead>
                    <TableHead className="text-subtle text-right">Surveillance</TableHead>
                    <TableHead className="text-subtle text-right">Total Ports</TableHead>
                    <TableHead className="text-subtle text-center">Loopback Exclu</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {history.map((entry) => (
                    <TableRow key={entry.id} className="border-border hover:bg-white/5">
                      <TableCell className="font-mono text-xs text-mist">
                        {new Date(entry.date).toLocaleString()}
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          {getVerdictIcon(entry.summary.verdict)}
                          <span className="text-sm font-medium text-mist truncate max-w-[200px]">
                            {entry.summary.verdict || "Inconnu"}
                          </span>
                        </div>
                      </TableCell>
                      <TableCell className="text-right font-mono text-danger">
                        {entry.summary.nb_alertes}
                      </TableCell>
                      <TableCell className="text-right font-mono text-warning">
                        {entry.summary.nb_surveiller}
                      </TableCell>
                      <TableCell className="text-right font-mono text-mist">
                        {entry.summary.total}
                      </TableCell>
                      <TableCell className="text-center text-subtle">
                        {entry.excludeLocal ? "Oui" : "Non"}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
}
