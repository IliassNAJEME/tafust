from collections import defaultdict
from datetime import datetime


WINDOWS_SYSTEM_PROCS = {
    "system",
    "svchost.exe",
    "lsass.exe",
    "wininit.exe",
    "winlogon.exe",
    "services.exe",
    "spoolsv.exe",
    "csrss.exe",
    "smss.exe",
    "ntoskrnl.exe",
    "explorer.exe",
    "dwm.exe",
    "taskhost.exe",
    "taskhostw.exe",
    "sihost.exe",
    "runtimebroker.exe",
    "fontdrvhost.exe",
    "audiodg.exe",
    "searchindexer.exe",
    "wuauclt.exe",
    "msdtc.exe",
    "dllhost.exe",
    "conhost.exe",
    "ctfmon.exe",
}

TRUSTED_VENDOR_KEYWORDS = [
    "armourycrate",
    "roglive",
    "asus",
    "manycam",
    "antigravity",
    "language_server",
    "onedrive",
    "microsoftonedrive",
]

REMOTE_ACCESS_KEYWORDS = [
    "anydesk",
    "teamviewer",
    "rustdesk",
    "vnc",
    "screenconnect",
    "splashtop",
]

SENSITIVE_PORTS = {
    21: ("FTP", "Unencrypted file transfer service."),
    22: ("SSH", "Remote shell access. Monitor closely when exposed."),
    23: ("Telnet", "Legacy unencrypted remote access."),
    3389: ("RDP", "Windows remote desktop service."),
    445: ("SMB", "Windows file sharing. Frequent lateral movement target."),
    139: ("NetBIOS", "Legacy Windows sharing protocol."),
    5900: ("VNC", "Remote desktop service."),
    6379: ("Redis", "In-memory database, risky if exposed without auth."),
    9200: ("Elasticsearch", "Commonly exposed search engine endpoint."),
}

SERVICE_CATALOG = {
    135: ("RPC Endpoint Mapper", "Windows RPC / COM broker."),
    139: ("NetBIOS Session", "Windows local network sharing."),
    445: ("SMB File Sharing", "Windows file sharing."),
    554: ("RTSP Media Sharing", "Windows Media Player network sharing."),
    1883: ("MQTT Broker", "Common MQTT development broker."),
    2869: ("UPnP SSDP", "Windows device discovery service."),
    3389: ("RDP", "Windows remote desktop."),
    5040: ("CDPSvc", "Connected Devices Platform service."),
    7680: ("WUDO", "Windows Update Delivery Optimization."),
    10243: ("UPnP HTTP", "Windows UPnP service."),
    12177: ("ArmouryCrate IPC", "ASUS Armoury Crate local IPC."),
    27017: ("MongoDB", "MongoDB database."),
    42050: ("OneDrive Sync", "Microsoft OneDrive sync service."),
    49664: ("Dynamic RPC (lsass)", "Windows dynamic RPC port."),
    49665: ("Dynamic RPC (wininit)", "Windows dynamic RPC port."),
    49666: ("Dynamic RPC (svchost)", "Windows dynamic RPC port."),
    49667: ("Dynamic RPC (svchost)", "Windows dynamic RPC port."),
    49668: ("Dynamic RPC (spoolsv)", "Windows dynamic RPC port."),
    49670: ("Dynamic RPC (services)", "Windows dynamic RPC port."),
    7070: ("Remote Access Service", "Non-standard remote access service."),
}

WATCHLIST_PROCS = {
    "wmpnetwk.exe": (
        "Windows Media Player Network Sharing",
        "Optional media sharing service. Safe when intentional, but often unnecessary.",
        "WMPNetworkSvc",
        None,
    ),
    "mosquitto.exe": (
        "Mosquitto MQTT Broker",
        "MQTT broker bound locally for development use.",
        "mosquitto",
        "sudo systemctl stop mosquitto",
    ),
    "mongod.exe": (
        "MongoDB",
        "MongoDB bound locally for development use.",
        "MongoDB",
        "sudo systemctl stop mongod",
    ),
}


def normalize(name: str) -> str:
    return (name or "").strip().lower()


def is_local_address(ip: str) -> bool:
    clean = (ip or "").strip("[]").lower()
    return clean in ("127.0.0.1", "::1", "localhost", "0:0:0:0:0:0:0:1")


def _is_system_process(proc: str) -> bool:
    return normalize(proc) in WINDOWS_SYSTEM_PROCS


def _is_vendor_process(proc: str) -> bool:
    norm = normalize(proc)
    return any(keyword in norm for keyword in TRUSTED_VENDOR_KEYWORDS)


def _is_remote_access_tool(proc: str) -> bool:
    norm = normalize(proc)
    return any(keyword in norm for keyword in REMOTE_ACCESS_KEYWORDS)


def _exposure_label(ip: str) -> str:
    clean = (ip or "").strip("[]").lower()
    if is_local_address(ip):
        return "Loopback only - external intrusion risk is minimal."
    if clean in ("0.0.0.0", "::"):
        return "Listening on all interfaces."
    return f"Listening on network interface {ip}."


def _local_trust_summary(entry: dict) -> str:
    facts = []
    if entry.get("signature_valid"):
        facts.append("valid signature")
    if entry.get("publisher"):
        facts.append(f"publisher={entry['publisher']}")
    if entry.get("company_name"):
        facts.append(f"company={entry['company_name']}")
    if entry.get("path_trusted"):
        facts.append("trusted install path")
    if entry.get("sha256"):
        facts.append(f"sha256={entry['sha256'][:12]}...")
    if entry.get("reputation_source") == "virustotal":
        facts.append(entry.get("reputation_summary", "VirusTotal consulted"))
    return "; ".join(facts)


def _cloud_signal(entry: dict) -> tuple[int, int]:
    return (
        int(entry.get("vt_malicious", 0) or 0),
        int(entry.get("vt_suspicious", 0) or 0),
    )


def _classify_entry(entry: dict) -> dict:
    proc = entry.get("proc", "Unknown")
    port = entry.get("port", 0)
    ip = entry.get("ip", "?")
    proto = entry.get("proto", "TCP")
    norm = normalize(proc)
    is_local = is_local_address(ip)
    cloud_verdict = entry.get("reputation_verdict", "unknown")
    trusted_signature = bool(entry.get("signature_valid"))
    trusted_publisher = bool(entry.get("publisher_trusted"))
    trusted_path = bool(entry.get("path_trusted"))
    trusted_company = bool(entry.get("company_name")) and trusted_publisher
    trusted_local_evidence = trusted_signature or trusted_publisher or trusted_path or trusted_company
    local_evidence = _local_trust_summary(entry)
    vt_malicious, vt_suspicious = _cloud_signal(entry)

    catalog_label, catalog_desc = SERVICE_CATALOG.get(port, ("", ""))
    result = {
        "proc": proc,
        "port": port,
        "ip": ip,
        "proto": proto,
        "pid": entry.get("pid"),
        "path": entry.get("path", ""),
        "publisher": entry.get("publisher", ""),
        "company_name": entry.get("company_name", ""),
        "signature_status": entry.get("signature_status", "Unavailable"),
        "sha256": entry.get("sha256", ""),
        "reputation_source": entry.get("reputation_source", "local"),
        "reputation_verdict": cloud_verdict,
        "reputation_summary": entry.get("reputation_summary", ""),
        "label": catalog_label or proc,
        "justification": catalog_desc or "",
        "exposure": _exposure_label(ip),
        "category": "SYSTÈME_LÉGITIME",
        "risk_level": "TRÈS FAIBLE",
        "risk_icon": "🟢",
        "powershell": [],
        "bash": [],
        "is_local": is_local,
        "group": norm,
        "hardening_note": "",
    }

    if cloud_verdict == "malicious":
        result["category"] = "ALERTE"
        result["risk_level"] = "CRITIQUE"
        result["risk_icon"] = "🔴"
        result["justification"] = (
            f"Cloud reputation marked '{proc}' as malicious. {entry.get('reputation_summary', '')}"
        )
        return result

    if cloud_verdict == "suspicious":
        result["category"] = "À_SURVEILLER" if trusted_local_evidence else "ALERTE"
        result["risk_level"] = "MODÉRÉ" if trusted_local_evidence else "ÉLEVÉ"
        result["risk_icon"] = "🟡" if trusted_local_evidence else "🔴"
        if trusted_local_evidence:
            result["justification"] = (
                f"Cloud reputation raised a weak warning for '{proc}', "
                f"but local trust evidence exists. {entry.get('reputation_summary', '')}"
            )
            if vt_malicious > 0:
                result["hardening_note"] = (
                    "Weak cloud signal detected for an otherwise trusted application. "
                    "Recheck if more engines start flagging it."
                )
        else:
            result["justification"] = (
                f"Cloud reputation marked '{proc}' as suspicious. {entry.get('reputation_summary', '')}"
            )
        return result

    if _is_system_process(proc):
        result["justification"] = catalog_desc or f"Windows core service detected ({proc})."
        if port in (445, 139) and not is_local:
            result["hardening_note"] = "Disable Windows file sharing if you do not use it on this machine."
            result["powershell"] = [
                "# Disable Windows file sharing if unused",
                "Set-SmbServerConfiguration -EnableSMB1Protocol $false -Force",
                'Disable-NetAdapterBinding -Name "*" -ComponentID ms_server',
            ]
        return result

    if norm in WATCHLIST_PROCS:
        label, justif, svc_ps, svc_bash = WATCHLIST_PROCS[norm]
        result["label"] = label
        result["category"] = "À_SURVEILLER"
        result["risk_level"] = "FAIBLE" if is_local else "MODÉRÉ"
        result["risk_icon"] = "🟡"
        result["justification"] = justif
        result["hardening_note"] = justif
        if not is_local and svc_ps:
            result["powershell"] = [
                f"# Stop and disable {label}",
                f'Stop-Service -Name "{svc_ps}" -Force',
                f'Set-Service -Name "{svc_ps}" -StartupType Disabled',
            ]
        if svc_bash:
            result["bash"] = [svc_bash]
        return result

    if port in SENSITIVE_PORTS and not is_local and not (trusted_signature or trusted_publisher):
        sens_name, sens_desc = SENSITIVE_PORTS[port]
        result["label"] = sens_name
        result["category"] = "ALERTE"
        result["risk_level"] = "CRITIQUE" if port == 23 else "ÉLEVÉ"
        result["risk_icon"] = "🔴"
        result["justification"] = f"{sens_desc} Unknown or untrusted process exposed on the network."
        return result

    if _is_remote_access_tool(proc):
        result["label"] = catalog_label or "Remote Access Tool"
        result["category"] = "À_SURVEILLER"
        result["risk_level"] = "MODÉRÉ" if not is_local else "FAIBLE"
        result["risk_icon"] = "🟡"
        if trusted_signature or trusted_publisher or cloud_verdict == "benign":
            result["justification"] = (
                f"Legitimate remote access software detected ({proc}). "
                f"Monitor only if this service is intentional. {local_evidence}"
            ).strip()
        else:
            result["justification"] = (
                f"Remote access behavior detected for '{proc}'. Verify that it is expected. {local_evidence}"
            ).strip()
        result["hardening_note"] = "Disable this remote access tool when not needed."
        return result

    if (trusted_signature or trusted_company) and (trusted_publisher or trusted_path or cloud_verdict == "benign"):
        result["category"] = "SYSTÈME_LÉGITIME" if is_local else "À_SURVEILLER"
        result["risk_level"] = "TRÈS FAIBLE" if is_local else "FAIBLE"
        result["risk_icon"] = "🟢" if is_local else "🟡"
        result["justification"] = (
            f"Trusted application evidence detected ({proc}). {local_evidence or 'Local trust evidence available.'}"
        ).strip()
        return result

    if _is_vendor_process(proc):
        result["category"] = "À_SURVEILLER" if not is_local else "SYSTÈME_LÉGITIME"
        result["risk_level"] = "FAIBLE" if not is_local else "TRÈS FAIBLE"
        result["risk_icon"] = "🟡" if not is_local else "🟢"
        result["justification"] = (
            f"Known vendor application detected ({proc}). "
            f"{entry.get('reputation_summary', '') if (vt_malicious or vt_suspicious) else local_evidence}"
        ).strip()
        return result

    if is_local:
        result["category"] = "À_SURVEILLER"
        result["risk_level"] = "FAIBLE"
        result["risk_icon"] = "🟡"
        result["justification"] = (
            f"Unknown local-only process ({proc}). External risk is low, but origin should be confirmed. {local_evidence}"
        ).strip()
    else:
        result["category"] = "ALERTE"
        result["risk_level"] = "ÉLEVÉ"
        result["risk_icon"] = "🔴"
        result["justification"] = (
            f"Unknown network-exposed process ({proc}) on {ip}:{port}/{proto}. No strong trust evidence was found."
        )
        result["powershell"] = [
            f"# Inspect the process listening on port {port}",
            f"Get-NetTCPConnection -LocalPort {port} | "
            "Select-Object LocalPort, State, OwningProcess | "
            "ForEach-Object { Get-Process -Id $_.OwningProcess | Select-Object Name, Id, Path }",
        ]
        result["hardening_note"] = f"Review process path, publisher, and installation source for '{proc}'."

    return result


def _deduplicate(raw_results: list[dict]) -> list[dict]:
    seen = set()
    out = []
    for entry in raw_results:
        key = (
            normalize(entry.get("proc", "")),
            entry.get("port", 0),
            entry.get("ip", ""),
        )
        if key not in seen:
            seen.add(key)
            out.append(entry)
    return out


def _group_legitimes(entries: list[dict]) -> list[dict]:
    groups: dict[str, list] = defaultdict(list)
    for entry in entries:
        groups[normalize(entry["proc"])].append(entry)

    merged = []
    for proc_norm, group in groups.items():
        ports = sorted({entry["port"] for entry in group})
        ips = sorted({entry["ip"] for entry in group})
        base = group[0].copy()
        base["ports_list"] = ports
        base["ips_list"] = ips
        base["count"] = len(group)
        base["hardening_note"] = next((entry["hardening_note"] for entry in group if entry.get("hardening_note")), "")
        base["powershell"] = next((entry["powershell"] for entry in group if entry.get("powershell")), [])
        merged.append(base)

    return sorted(merged, key=lambda item: normalize(item["proc"]))


def analyze(raw_results: list[dict]) -> dict:
    deduped = _deduplicate(raw_results)

    alertes = []
    surveiller = []
    legitimes = []

    for entry in deduped:
        classified = _classify_entry(entry)
        category = classified["category"]
        if category == "ALERTE":
            alertes.append(classified)
        elif category == "À_SURVEILLER":
            surveiller.append(classified)
        else:
            legitimes.append(classified)

    risk_order = {"CRITIQUE": 0, "ÉLEVÉ": 1, "MODÉRÉ": 2, "FAIBLE": 3, "TRÈS FAIBLE": 4}
    alertes = sorted(alertes, key=lambda item: (risk_order.get(item["risk_level"], 9), item["port"]))
    surveiller = sorted(surveiller, key=lambda item: (risk_order.get(item["risk_level"], 9), item["port"]))
    legitimes_grouped = _group_legitimes(legitimes)

    hardenings = []
    seen_ps = set()
    all_entries = alertes + surveiller + legitimes
    for entry in all_entries:
        if (entry.get("powershell") or entry.get("hardening_note")) and entry["proc"] not in seen_ps:
            seen_ps.add(entry["proc"])
            hardenings.append(
                {
                    "proc": entry["proc"],
                    "label": entry.get("label", entry["proc"]),
                    "risk_level": entry.get("risk_level", ""),
                    "risk_icon": entry.get("risk_icon", ""),
                    "justification": entry.get("hardening_note") or entry.get("justification", ""),
                    "powershell": entry.get("powershell", []),
                    "bash": entry.get("bash", []),
                }
            )

    nb_a = len(alertes)
    nb_s = len(surveiller)
    nb_l = len(legitimes)

    if nb_a > 0:
        verdict = "Audit needs attention"
        verdict_detail = (
            f"{nb_a} critical finding(s) require review. "
            f"{nb_s} service(s) should be monitored. {nb_l} legitimate entries were filtered."
        )
    elif nb_s > 0:
        verdict = "System looks healthy"
        verdict_detail = (
            f"No critical threat found. {nb_s} service(s) remain worth monitoring. "
            f"{nb_l} entries were classified as legitimate."
        )
    else:
        verdict = "System looks healthy"
        verdict_detail = f"No anomaly detected. {nb_l} legitimate entries confirmed."

    meta = {
        "date": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "total_raw": len(raw_results),
        "total_unique": len(deduped),
    }

    summary = {
        "verdict": verdict,
        "verdict_detail": verdict_detail,
        "total": len(deduped),
        "false_positives": nb_l,
        "nb_alertes": nb_a,
        "nb_surveiller": nb_s,
        "nb_legitimes": nb_l,
    }

    return {
        "meta": meta,
        "summary": summary,
        "alertes": alertes,
        "surveiller": surveiller,
        "legitimes": legitimes_grouped,
        "hardenings": hardenings,
    }
