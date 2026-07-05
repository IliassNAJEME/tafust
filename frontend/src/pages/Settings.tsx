import { motion } from "framer-motion";
import { useSettings } from "../hooks/useSettings";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "../components/ui/card";
import { Label } from "../components/ui/label";
import { Input } from "../components/ui/input";
import { Switch } from "../components/ui/switch";
import { Settings as SettingsIcon, Save } from "lucide-react";
import { Button } from "../components/ui/button";

export default function Settings() {
  const { settings, setSettings } = useSettings();

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      className="max-w-3xl mx-auto space-y-6"
    >
      <div className="flex items-center gap-3 mb-6">
        <SettingsIcon className="h-6 w-6 text-signal" />
        <h2 className="text-2xl font-bold text-mist">Paramètres</h2>
      </div>

      <Card className="border-border bg-card/50 backdrop-blur">
        <CardHeader>
          <CardTitle className="text-mist">Filtres de Scan</CardTitle>
          <CardDescription className="text-subtle">
            Configurez le comportement du moteur de scan local.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label className="text-base text-mist">Exclure Loopback</Label>
              <p className="text-sm text-subtle">
                Ignorer les services écoutant uniquement sur 127.0.0.1 ou ::1.
              </p>
            </div>
            <Switch
              checked={settings.exclude_local}
              onCheckedChange={(c: boolean) => setSettings({ ...settings, exclude_local: c })}
              className="data-[state=checked]:bg-signal"
            />
          </div>
        </CardContent>
      </Card>

      <Card className="border-border bg-card/50 backdrop-blur">
        <CardHeader>
          <CardTitle className="text-mist">Avancé (Pré-intégration)</CardTitle>
          <CardDescription className="text-subtle">
            Ces paramètres sont sauvegardés localement, mais nécessitent une future mise à jour du backend pour être appliqués.
            {/* TODO: Envoyer timeout, threads, et port_range au backend dans /api/scan */}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="grid gap-2">
            <Label htmlFor="timeout" className="text-mist">Timeout (ms)</Label>
            <Input
              id="timeout"
              type="number"
              value={settings.timeout}
              onChange={(e: any) => setSettings({ ...settings, timeout: Number(e.target.value) })}
              className="bg-ink border-border text-mist focus-visible:ring-signal"
            />
            <p className="text-xs text-subtle">Délai d'attente maximum pour la résolution d'un port.</p>
          </div>

          <div className="grid gap-2">
            <Label htmlFor="threads" className="text-mist">Threads</Label>
            <Input
              id="threads"
              type="number"
              value={settings.threads}
              onChange={(e: any) => setSettings({ ...settings, threads: Number(e.target.value) })}
              className="bg-ink border-border text-mist focus-visible:ring-signal"
            />
            <p className="text-xs text-subtle">Nombre de workers pour l'analyse réseau.</p>
          </div>

          <div className="grid gap-2">
            <Label htmlFor="port_range" className="text-mist">Plages de Ports</Label>
            <Input
              id="port_range"
              type="text"
              value={settings.port_range}
              onChange={(e: any) => setSettings({ ...settings, port_range: e.target.value })}
              className="bg-ink border-border text-mist font-mono focus-visible:ring-signal"
              placeholder="Ex: 1-1024, 8080, 443"
            />
            <p className="text-xs text-subtle">Liste ou plages de ports à scanner spécifiquement.</p>
          </div>
        </CardContent>
      </Card>

      <div className="flex justify-end pt-4">
        <Button className="bg-signal text-ink hover:bg-signal-dim gap-2">
          <Save className="h-4 w-4" />
          Sauvegardé automatiquement
        </Button>
      </div>
    </motion.div>
  );
}
