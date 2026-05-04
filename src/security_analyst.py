"""
security_analyst.py — Moteur d'Audit de Sécurité Tafust
Pipeline : Normalisation → Catégorisation → Contextualisation → Rapport structuré

Rapport en 4 sections :
  1. Résumé Exécutif
  2. Matrice des Risques
  3. Analyse Technique Détaillée
  4. Recommandations de Hardening
"""

from datetime import datetime
from collections import defaultdict

# ==============================================================================
# BASE DE CONNAISSANCE
# ==============================================================================

# Composants Windows natifs — signature OS, toujours légitimes
WINDOWS_SYSTEM_PROCS = {
    "system", "svchost.exe", "lsass.exe", "wininit.exe", "winlogon.exe",
    "services.exe", "spoolsv.exe", "csrss.exe", "smss.exe", "ntoskrnl.exe",
    "explorer.exe", "dwm.exe", "taskhost.exe", "taskhostw.exe", "sihost.exe",
    "runtimebroker.exe", "fontdrvhost.exe", "audiodg.exe", "searchindexer.exe",
    "wuauclt.exe", "msdtc.exe", "dllhost.exe", "conhost.exe", "ctfmon.exe",
}

# Mots-clés d'éditeurs de confiance (logiciels tiers connus)
TRUSTED_VENDOR_KEYWORDS = [
    "armourycrate", "roglive", "asus", "manycam", "antigravity",
    "language_server", "onedrive", "microsoftonedrive",
]

# Ports sensibles — nécessitent une justification contextuelle
SENSITIVE_PORTS = {
    21:   ("FTP",              "Transfert de fichiers non chiffré. Exposition critique."),
    22:   ("SSH",              "Accès shell distant. Surveiller si exposé hors localhost."),
    23:   ("Telnet",           "Protocole non chiffré obsolète. À désactiver immédiatement."),
    3389: ("RDP",              "Bureau à distance Windows. Vecteur d'attaque fréquent."),
    445:  ("SMB",              "Partage fichiers Windows. Sensible aux ransomwares (WannaCry)."),
    139:  ("NetBIOS",          "Partage réseau legacy. Désactivable en environnement moderne."),
    5900: ("VNC",              "Bureau à distance non Microsoft. Vérifier l'authentification."),
    6379: ("Redis",            "Base de données en mémoire. Critique si exposée sans auth."),
    9200: ("Elasticsearch",    "Moteur de recherche. Souvent exposé sans authentification."),
}

# Catalogue de services avec descriptions techniques
SERVICE_CATALOG = {
    135:   ("RPC Endpoint Mapper",        "Windows natif — Broker de communication RPC/COM. Requis par l'OS."),
    139:   ("NetBIOS Session",            "Partage réseau Windows legacy. Présent sur interfaces physiques."),
    445:   ("SMB (File Sharing)",         "Partage de fichiers Windows. Actif sur le réseau local."),
    554:   ("RTSP (Media Streaming)",     "Windows Media Player Network Sharing. Service de streaming multimédia."),
    1883:  ("MQTT Broker (Mosquitto)",    "Broker IoT open-source. Isolé sur loopback — usage développement."),
    2869:  ("UPnP/SSDP",                 "Découverte de périphériques réseau. Windows natif."),
    3389:  ("RDP",                        "Bureau à distance Windows."),
    5040:  ("CDPSvc",                     "Connected Devices Platform. Service Windows natif."),
    7680:  ("WUDO",                       "Windows Update Delivery Optimization — partage de mises à jour."),
    10243: ("UPnP HTTP",                  "Service UPnP Windows. Natif."),
    12177: ("ArmouryCrate IPC",           "Interface de communication interne ASUS Armoury Crate."),
    27017: ("MongoDB",                    "Base de données NoSQL. Isolée sur loopback — usage développement."),
    42050: ("OneDrive Sync",              "Service de synchronisation Microsoft OneDrive."),
    49664: ("RPC Dynamique (lsass)",      "Port RPC dynamique alloué par l'OS Windows. Normal."),
    49665: ("RPC Dynamique (wininit)",    "Port RPC dynamique alloué par l'OS Windows. Normal."),
    49666: ("RPC Dynamique (svchost)",    "Port RPC dynamique alloué par l'OS Windows. Normal."),
    49667: ("RPC Dynamique (svchost)",    "Port RPC dynamique alloué par l'OS Windows. Normal."),
    49668: ("RPC Dynamique (spoolsv)",    "Port RPC dynamique alloué par l'OS Windows. Normal."),
    49670: ("RPC Dynamique (services)",   "Port RPC dynamique alloué par l'OS Windows. Normal."),
}

# Processus en watchlist : légitimes mais potentiellement superflus
# Format : proc_normalized → (label, justification, service_name_ps, bash_cmd)
WATCHLIST_PROCS = {
    "wmpnetwk.exe": (
        "Windows Media Player Network Sharing",
        "Service de partage multimédia WMP. Exposé sur 0.0.0.0 (toutes interfaces). "
        "Non nécessaire si le partage de médias sur le réseau n'est pas utilisé.",
        "WMPNetworkSvc",
        None,
    ),
    "mosquitto.exe": (
        "Mosquitto MQTT Broker",
        "Broker MQTT open-source. Isolé sur loopback (127.0.0.1/::1) — "
        "risque d'intrusion externe nul. Légitime pour le développement IoT.",
        "mosquitto",
        "sudo systemctl stop mosquitto",
    ),
    "mongod.exe": (
        "MongoDB",
        "Base de données NoSQL. Isolée sur loopback (127.0.0.1) — "
        "non exposée au réseau. Standard en développement local.",
        "MongoDB",
        "sudo systemctl stop mongod",
    ),
}

# ==============================================================================
# HELPERS
# ==============================================================================

def _normalize(name: str) -> str:
    return name.strip().lower()


def _is_local_address(ip: str) -> bool:
    """Retourne True si l'adresse est loopback (trafic local uniquement)."""
    clean = ip.strip("[]").lower()
    return clean in ("127.0.0.1", "::1", "localhost", "0:0:0:0:0:0:0:1")


def _is_system_process(proc: str) -> bool:
    return _normalize(proc) in WINDOWS_SYSTEM_PROCS


def _is_vendor_process(proc: str) -> bool:
    norm = _normalize(proc)
    return any(kw in norm for kw in TRUSTED_VENDOR_KEYWORDS)


def _exposure_label(ip: str) -> str:
    """Retourne une description lisible de l'exposition réseau."""
    clean = ip.strip("[]").lower()
    if _is_local_address(ip):
        return "Loopback (127.0.0.1/::1) — trafic local uniquement, risque d'intrusion externe : NUL"
    if clean in ("0.0.0.0", "::"):
        return "Toutes interfaces (0.0.0.0/[::]) — exposé sur l'ensemble des cartes réseau"
    return f"Interface réseau physique ({ip}) — exposé sur le LAN"


# ==============================================================================
# CLASSIFICATION D'UNE ENTRÉE
# ==============================================================================

def _classify_entry(entry: dict) -> dict:
    """
    Enrichit une entrée brute avec :
      category   : SYSTÈME_LÉGITIME | À_SURVEILLER | ALERTE
      risk_level : TRÈS FAIBLE | FAIBLE | MODÉRÉ | ÉLEVÉ | CRITIQUE
      label      : Nom lisible du service
      justification : Explication technique du classement
      powershell : Commandes de remédiation (si applicable)
      bash       : Commandes Bash équivalentes (si applicable)
      group      : Nom de groupe normalisé (pour regroupement dans l'UI)
    """
    proc     = entry.get("proc", "Inconnu")
    port     = entry.get("port", 0)
    ip       = entry.get("ip", "?")
    proto    = entry.get("proto", "TCP")
    norm     = _normalize(proc)
    is_local = _is_local_address(ip)

    catalog_label, catalog_desc = SERVICE_CATALOG.get(port, ("", ""))
    exposure = _exposure_label(ip)

    result = {
        "proc":          proc,
        "port":          port,
        "ip":            ip,
        "proto":         proto,
        "label":         catalog_label or proc,
        "justification": catalog_desc or "",
        "exposure":      exposure,
        "category":      "SYSTÈME_LÉGITIME",
        "risk_level":    "TRÈS FAIBLE",
        "risk_icon":     "🟢",
        "powershell":    [],
        "bash":          [],
        "is_local":      is_local,
        "group":         norm,
        "hardening_note": "",
    }

    # ── RÈGLE 1 : Composant Windows natif ─────────────────────────────────────
    if _is_system_process(proc):
        result["category"]      = "SYSTÈME_LÉGITIME"
        result["risk_level"]    = "TRÈS FAIBLE"
        result["risk_icon"]     = "🟢"
        result["justification"] = (
            catalog_desc or
            f"Processus noyau/OS Windows ({proc}). Signé Microsoft. "
            "Présence normale quelle que soit l'interface d'écoute."
        )
        # SMB/NetBIOS sur interface physique → note de hardening, mais pas d'alerte
        if port in (445, 139) and not is_local:
            result["hardening_note"] = (
                "Le partage SMB/NetBIOS est actif sur le réseau local. "
                "Si aucun partage de fichiers n'est nécessaire, "
                "envisagez de le désactiver pour réduire la surface d'attaque."
            )
            result["powershell"] = [
                "# Désactiver le partage de fichiers Windows (si non utilisé) :",
                'Set-SmbServerConfiguration -EnableSMB1Protocol $false -Force',
                'Disable-NetAdapterBinding -Name "*" -ComponentID ms_server',
            ]
        return result

    # ── RÈGLE 2 : Éditeur de confiance connu ──────────────────────────────────
    if _is_vendor_process(proc):
        result["category"]      = "SYSTÈME_LÉGITIME"
        result["risk_level"]    = "TRÈS FAIBLE"
        result["risk_icon"]     = "🟢"
        result["justification"] = (
            catalog_desc or
            f"Logiciel tiers identifié ({proc}) — éditeur reconnu. "
            f"Écoute sur {ip}:{port}. {exposure}."
        )
        return result

    # ── RÈGLE 3 : Processus en watchlist ──────────────────────────────────────
    if norm in WATCHLIST_PROCS:
        label, justif, svc_ps, svc_bash = WATCHLIST_PROCS[norm]
        result["label"]         = label
        result["category"]      = "À_SURVEILLER"
        result["risk_level"]    = "FAIBLE" if is_local else "MODÉRÉ"
        result["risk_icon"]     = "🟡"
        result["justification"] = justif
        result["hardening_note"] = justif
        if not is_local and svc_ps:
            result["powershell"] = [
                f'# Arrêter et désactiver "{label}" :',
                f'Stop-Service -Name "{svc_ps}" -Force',
                f'Set-Service -Name "{svc_ps}" -StartupType Disabled',
            ]
        if svc_bash:
            result["bash"] = [svc_bash]
        return result

    # ── RÈGLE 4 : Port sensible connu ─────────────────────────────────────────
    if port in SENSITIVE_PORTS:
        sens_name, sens_desc = SENSITIVE_PORTS[port]
        if is_local:
            result["category"]      = "À_SURVEILLER"
            result["risk_level"]    = "FAIBLE"
            result["risk_icon"]     = "🟡"
            result["justification"] = (
                f"{sens_desc} — Isolé sur loopback. "
                "Risque d'intrusion externe : NUL. À surveiller si un logiciel inconnu écoute."
            )
        else:
            result["category"]      = "ALERTE"
            result["risk_level"]    = "ÉLEVÉ" if port != 23 else "CRITIQUE"
            result["risk_icon"]     = "🔴"
            result["justification"] = (
                f"{sens_desc} Processus '{proc}' expose le port {port} "
                f"sur {ip}. Vérification immédiate recommandée."
            )
            result["powershell"] = [
                f"# Identifier le processus sur le port {port} :",
                f"Get-NetTCPConnection -LocalPort {port} | Select-Object State, LocalPort, OwningProcess | "
                f"ForEach-Object {{ Get-Process -Id $_.OwningProcess }}",
                f"# Bloquer le port via le pare-feu Windows :",
                f'New-NetFirewallRule -DisplayName "Block_{sens_name}_{port}" '
                f'-Direction Inbound -LocalPort {port} -Protocol TCP -Action Block',
            ]
        result["label"] = sens_name
        return result

    # ── RÈGLE 5 : Processus inconnu ───────────────────────────────────────────
    if is_local:
        result["category"]      = "À_SURVEILLER"
        result["risk_level"]    = "FAIBLE"
        result["risk_icon"]     = "🟡"
        result["justification"] = (
            f"Processus non répertorié ({proc}) — écoute sur {ip}:{port}. "
            "Port loopback uniquement : risque d'intrusion externe NUL. "
            "Vérifier l'origine du processus si inconnu."
        )
    else:
        result["category"]      = "ALERTE"
        result["risk_level"]    = "ÉLEVÉ"
        result["risk_icon"]     = "🔴"
        result["justification"] = (
            f"Processus inconnu '{proc}' exposé sur {ip}:{port}/{proto}. "
            "Aucune correspondance dans la base de confiance. "
            "Investigation requise."
        )
        result["powershell"] = [
            f"# Identifier le processus écoutant sur le port {port} :",
            f"Get-NetTCPConnection -LocalPort {port} | "
            "Select-Object LocalPort, State, OwningProcess | "
            "ForEach-Object { Get-Process -Id $_.OwningProcess | Select-Object Name, Id, Path }",
        ]
        result["hardening_note"] = (
            f"Service inconnu '{proc}' exposé sur le réseau. "
            "Vérifier dans le Gestionnaire de tâches → onglet Services."
        )

    return result


# ==============================================================================
# NORMALISATION & REGROUPEMENT
# ==============================================================================

def _deduplicate(raw_results: list[dict]) -> list[dict]:
    """Supprime les doublons exacts (même proc + port + ip)."""
    seen = set()
    out  = []
    for e in raw_results:
        key = (_normalize(e.get("proc", "")), e.get("port", 0), e.get("ip", ""))
        if key not in seen:
            seen.add(key)
            out.append(e)
    return out


def _group_legitimes(entries: list[dict]) -> list[dict]:
    """
    Regroupe les entrées SYSTÈME_LÉGITIME par nom de processus.
    Réduit N lignes de svchost.exe en 1 entrée consolidée.
    """
    groups: dict[str, list] = defaultdict(list)
    for e in entries:
        groups[_normalize(e["proc"])].append(e)

    merged = []
    for proc_norm, group in groups.items():
        ports    = sorted({e["port"] for e in group})
        ips      = sorted({e["ip"] for e in group})
        base     = group[0].copy()
        base["ports_list"]  = ports
        base["ips_list"]    = ips
        base["count"]       = len(group)
        # Agréger les notes de hardening non vides
        hardening = next((e["hardening_note"] for e in group if e.get("hardening_note")), "")
        base["hardening_note"] = hardening
        base["powershell"] = next((e["powershell"] for e in group if e.get("powershell")), [])
        merged.append(base)

    return sorted(merged, key=lambda x: _normalize(x["proc"]))


# ==============================================================================
# POINT D'ENTRÉE PUBLIC
# ==============================================================================

def analyze(raw_results: list[dict]) -> dict:
    """
    Pipeline complet d'analyse.

    Retourne :
    {
        "meta":         { date, total_raw, total_unique },
        "summary":      { verdict, verdict_detail, nb_alertes, nb_surveiller, nb_legitimes, ... },
        "alertes":      [ entrées classifiées ],
        "surveiller":   [ entrées classifiées ],
        "legitimes":    [ entrées groupées par processus ],
        "hardenings":   [ { proc, label, justification, powershell, bash } ],
    }
    """
    deduped = _deduplicate(raw_results)

    alertes    = []
    surveiller = []
    legitimes  = []

    for entry in deduped:
        classified = _classify_entry(entry)
        cat = classified["category"]
        if cat == "ALERTE":
            alertes.append(classified)
        elif cat == "À_SURVEILLER":
            surveiller.append(classified)
        else:
            legitimes.append(classified)

    # Trier par niveau de risque décroissant
    risk_order = {"CRITIQUE": 0, "ÉLEVÉ": 1, "MODÉRÉ": 2, "FAIBLE": 3, "TRÈS FAIBLE": 4}
    alertes    = sorted(alertes,    key=lambda x: (risk_order.get(x["risk_level"], 9), x["port"]))
    surveiller = sorted(surveiller, key=lambda x: (risk_order.get(x["risk_level"], 9), x["port"]))

    # Regrouper les légitimes
    legitimes_grouped = _group_legitimes(legitimes)

    # Construire la liste de recommandations de hardening
    hardenings = []
    all_entries = alertes + surveiller + [e for g in [legitimes] for e in g]
    seen_ps = set()
    for e in all_entries:
        ps = e.get("powershell", [])
        note = e.get("hardening_note", "")
        if (ps or note) and e["proc"] not in seen_ps:
            seen_ps.add(e["proc"])
            hardenings.append({
                "proc":          e["proc"],
                "label":         e.get("label", e["proc"]),
                "risk_level":    e.get("risk_level", ""),
                "risk_icon":     e.get("risk_icon", ""),
                "justification": note or e.get("justification", ""),
                "powershell":    ps,
                "bash":          e.get("bash", []),
            })

    # Verdict global
    nb_a = len(alertes)
    nb_s = len(surveiller)
    nb_l = len(legitimes)

    if nb_a > 0:
        verdict        = "Audit nécessitant attention"
        verdict_detail = (
            f"{nb_a} anomalie(s) critique(s) détectée(s) nécessitant investigation. "
            f"{nb_s} service(s) à surveiller. {nb_l} entrées légitimes écartées."
        )
    elif nb_s > 0:
        verdict        = "Système sain"
        verdict_detail = (
            f"Aucune menace critique. {nb_s} service(s) légitimes mais optimisables. "
            f"{nb_l} faux positifs écartés."
        )
    else:
        verdict        = "Système sain"
        verdict_detail = f"Aucune anomalie. {nb_l} entrées légitimes confirmées."

    meta = {
        "date":        datetime.now().strftime("%d/%m/%Y %H:%M"),
        "total_raw":   len(raw_results),
        "total_unique":len(deduped),
    }

    summary = {
        "verdict":        verdict,
        "verdict_detail": verdict_detail,
        "total":          len(deduped),
        "false_positives":nb_l,
        "nb_alertes":     nb_a,
        "nb_surveiller":  nb_s,
        "nb_legitimes":   nb_l,
    }

    return {
        "meta":       meta,
        "summary":    summary,
        "alertes":    alertes,
        "surveiller": surveiller,
        "legitimes":  legitimes_grouped,
        "hardenings": hardenings,
    }
