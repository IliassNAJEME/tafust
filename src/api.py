import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from src.scanner_manager import ScannerManager

try:
    from dotenv import find_dotenv, load_dotenv
except Exception:
    find_dotenv = None
    load_dotenv = None


def _resolve_dotenv_path() -> str:
    dotenv_path = ""
    if find_dotenv is not None:
        dotenv_path = find_dotenv(usecwd=True)
    if dotenv_path:
        return dotenv_path

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    candidate = os.path.join(project_root, ".env")
    return candidate if os.path.exists(candidate) else ""


def _load_env_file_fallback(path: str) -> None:
    if not path or not os.path.exists(path):
        return

    with open(path, "r", encoding="utf-8") as env_file:
        for raw_line in env_file:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ[key.strip()] = value.strip().strip('"').strip("'")


dotenv_path = _resolve_dotenv_path()
if load_dotenv is not None:
    load_dotenv(dotenv_path or None, override=True)
else:
    _load_env_file_fallback(dotenv_path)


def _parse_csv_env(name: str) -> list[str]:
    configured = os.getenv(name, "")
    return [value.strip() for value in configured.split(",") if value.strip()]


def _resolve_allowed_origins() -> list[str]:
    configured = _parse_csv_env("TAFUST_ALLOWED_ORIGINS")
    if configured:
        return configured

    return [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://localhost:5173",
        "https://127.0.0.1:5173",
    ]


def _resolve_allowed_origin_regex() -> str | None:
    configured = os.getenv("TAFUST_ALLOWED_ORIGIN_REGEX", "").strip()
    return configured or None


def _resolve_allowed_hosts() -> list[str]:
    configured = _parse_csv_env("TAFUST_ALLOWED_HOSTS")
    if configured:
        return configured

    return [
        "localhost",
        "127.0.0.1",
        "::1",
    ]


def _https_is_enforced() -> bool:
    return os.getenv("TAFUST_FORCE_HTTPS", "").strip().lower() in {"1", "true", "yes", "on"}


def create_app() -> FastAPI:
    app = FastAPI(
        title="Tafust API",
        version="0.1.0",
        description="HTTP API for the Tafust network audit engine.",
    )

    origins = _resolve_allowed_origins()
    origin_regex = _resolve_allowed_origin_regex()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_origin_regex=origin_regex,
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=_resolve_allowed_hosts(),
    )

    manager = ScannerManager()

    @app.middleware("http")
    async def add_security_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "same-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        if _https_is_enforced():
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response

    @app.get("/api/health")
    def health() -> dict:
        return {
            "status": "ok",
            "os": manager.os_type,
            "exclude_local": manager.exclude_local,
            "has_virustotal_key": bool(os.getenv("VIRUSTOTAL_API_KEY")),
            "https_required": _https_is_enforced(),
        }

    @app.get("/api/report")
    def last_report() -> dict:
        return {
            "report": manager.last_report,
            "raw_results": manager.last_results,
        }

    @app.post("/api/scan")
    def run_scan(payload: dict | None = None) -> dict:
        request = payload or {}
        manager.exclude_local = bool(request.get("exclude_local", False))
        report = manager.run_scan()
        return {
            "report": report,
            "raw_results": manager.last_results,
        }

    return app


app = create_app()
