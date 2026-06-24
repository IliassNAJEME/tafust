import hashlib
import json
import os
import platform
import subprocess
import urllib.error
import urllib.request


TRUSTED_PATH_PREFIXES = (
    os.environ.get("WINDIR", r"C:\Windows"),
    r"C:\Program Files",
    r"C:\Program Files (x86)",
)

TRUSTED_PUBLISHER_KEYWORDS = (
    "microsoft",
    "spotify",
    "anydesk",
    "asus",
    "apple",
    "mongodb",
    "google",
    "mozilla",
    "adobe",
)


def _safe_norm(value: str) -> str:
    return (value or "").strip().lower()


class ReputationService:
    def __init__(self):
        self.os_type = platform.system()
        self.vt_api_key = os.getenv("VIRUSTOTAL_API_KEY", "").strip()
        self._file_cache: dict[str, dict] = {}
        self._vt_cache: dict[str, dict] = {}

    def enrich_entry(self, entry: dict) -> dict:
        path = entry.get("path") or ""
        if not path:
            return entry

        cached = self._file_cache.get(path)
        if cached is None:
            cached = self._inspect_file(path)
            self._file_cache[path] = cached

        enriched = entry.copy()
        enriched.update(cached)

        sha256 = enriched.get("sha256", "")
        if sha256 and self.vt_api_key:
            vt_data = self._vt_cache.get(sha256)
            if vt_data is None:
                vt_data = self._lookup_virustotal(sha256)
                self._vt_cache[sha256] = vt_data
            enriched.update(vt_data)

        return enriched

    def _inspect_file(self, path: str) -> dict:
        exists = os.path.exists(path)
        result = {
            "path": path,
            "path_trusted": self._is_trusted_path(path),
            "sha256": "",
            "signature_status": "Unavailable",
            "signature_valid": False,
            "publisher": "",
            "company_name": "",
            "product_name": "",
            "publisher_trusted": False,
            "reputation_source": "local",
            "reputation_verdict": "unknown",
            "reputation_confidence": "low",
            "reputation_summary": "No cloud reputation configured.",
        }

        if not exists:
            result["reputation_summary"] = "Executable path is no longer available on disk."
            return result

        result["sha256"] = self._compute_sha256(path)

        if self.os_type == "Windows":
            signature = self._get_windows_signature(path)
            result.update(signature)
            metadata = self._get_windows_version_info(path)
            result.update(metadata)
            trust_blob = " ".join(
                [
                    _safe_norm(result.get("publisher", "")),
                    _safe_norm(result.get("company_name", "")),
                    _safe_norm(result.get("product_name", "")),
                ]
            )
            result["publisher_trusted"] = any(keyword in trust_blob for keyword in TRUSTED_PUBLISHER_KEYWORDS)
        else:
            result["reputation_summary"] = "Local signature verification is currently available on Windows only."

        return result

    def _is_trusted_path(self, path: str) -> bool:
        norm_path = os.path.normcase(path)
        return any(norm_path.startswith(os.path.normcase(prefix)) for prefix in TRUSTED_PATH_PREFIXES)

    def _compute_sha256(self, path: str) -> str:
        digest = hashlib.sha256()
        try:
            with open(path, "rb") as handle:
                for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                    digest.update(chunk)
        except OSError:
            return ""
        return digest.hexdigest()

    def _get_windows_signature(self, path: str) -> dict:
        env = os.environ.copy()
        env["TAFUST_TARGET_PATH"] = path
        command = [
            "powershell",
            "-NoProfile",
            "-Command",
            (
                "[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; "
                "$sig = Get-AuthenticodeSignature -LiteralPath $env:TAFUST_TARGET_PATH; "
                "$publisher = ''; "
                "if ($sig.SignerCertificate) { $publisher = $sig.SignerCertificate.Subject; } "
                "[PSCustomObject]@{"
                "Status = [string]$sig.Status; "
                "Publisher = [string]$publisher"
                "} | ConvertTo-Json -Compress"
            ),
        ]
        try:
            result = subprocess.run(command, capture_output=True, text=True, check=True, env=env)
            payload = json.loads(result.stdout or "{}")
        except Exception:
            return {
                "signature_status": "Unavailable",
                "signature_valid": False,
                "publisher": "",
            }

        return {
            "signature_status": payload.get("Status", "Unknown") or "Unknown",
            "signature_valid": payload.get("Status", "") == "Valid",
            "publisher": payload.get("Publisher", "") or "",
        }

    def _lookup_virustotal(self, sha256: str) -> dict:
        request = urllib.request.Request(
            f"https://www.virustotal.com/api/v3/files/{sha256}",
            headers={
                "x-apikey": self.vt_api_key,
                "accept": "application/json",
            },
            method="GET",
        )

        try:
            with urllib.request.urlopen(request, timeout=8) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                return {
                    "reputation_source": "virustotal",
                    "reputation_verdict": "unknown",
                    "reputation_confidence": "medium",
                    "reputation_summary": "Hash not found in VirusTotal.",
                }
            return {
                "reputation_source": "virustotal",
                "reputation_verdict": "unknown",
                "reputation_confidence": "low",
                "reputation_summary": f"VirusTotal lookup failed with HTTP {exc.code}.",
            }
        except Exception:
            return {
                "reputation_source": "virustotal",
                "reputation_verdict": "unknown",
                "reputation_confidence": "low",
                "reputation_summary": "VirusTotal lookup failed.",
            }

        stats = payload.get("data", {}).get("attributes", {}).get("last_analysis_stats", {})
        malicious = int(stats.get("malicious", 0))
        suspicious = int(stats.get("suspicious", 0))
        harmless = int(stats.get("harmless", 0))
        undetected = int(stats.get("undetected", 0))

        if malicious >= 5:
            verdict = "malicious"
            confidence = "high"
        elif malicious > 0 or suspicious > 0:
            verdict = "suspicious"
            confidence = "medium"
        elif harmless > 0 and malicious == 0 and suspicious == 0:
            verdict = "benign"
            confidence = "medium"
        else:
            verdict = "unknown"
            confidence = "medium"

        return {
            "reputation_source": "virustotal",
            "reputation_verdict": verdict,
            "reputation_confidence": confidence,
            "reputation_summary": (
                f"VirusTotal: malicious={malicious}, suspicious={suspicious}, "
                f"harmless={harmless}, undetected={undetected}"
            ),
            "vt_malicious": malicious,
            "vt_suspicious": suspicious,
            "vt_harmless": harmless,
            "vt_undetected": undetected,
            "vt_stats": stats,
        }

    def _get_windows_version_info(self, path: str) -> dict:
        env = os.environ.copy()
        env["TAFUST_TARGET_PATH"] = path
        command = [
            "powershell",
            "-NoProfile",
            "-Command",
            (
                "[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; "
                "$item = Get-Item -LiteralPath $env:TAFUST_TARGET_PATH; "
                "$info = $item.VersionInfo; "
                "[PSCustomObject]@{"
                "CompanyName = [string]$info.CompanyName; "
                "ProductName = [string]$info.ProductName"
                "} | ConvertTo-Json -Compress"
            ),
        ]
        try:
            result = subprocess.run(command, capture_output=True, text=True, check=True, env=env)
            payload = json.loads(result.stdout or "{}")
        except Exception:
            return {"company_name": "", "product_name": ""}

        return {
            "company_name": payload.get("CompanyName", "") or "",
            "product_name": payload.get("ProductName", "") or "",
        }
