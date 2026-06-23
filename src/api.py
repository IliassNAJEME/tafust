import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.scanner_manager import ScannerManager


def _resolve_allowed_origins() -> list[str]:
    configured = os.getenv("TAFUST_ALLOWED_ORIGINS")
    if configured:
        return [origin.strip() for origin in configured.split(",") if origin.strip()]

    return ["*"]


def _resolve_allowed_origin_regex() -> str | None:
    configured = os.getenv("TAFUST_ALLOWED_ORIGIN_REGEX")
    if configured:
        return configured

    return ".*"


def create_app() -> FastAPI:
    app = FastAPI(
        title="Tafust API",
        version="0.1.0",
        description="HTTP API for the Tafust network audit engine.",
    )

    origins = _resolve_allowed_origins()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins or ["*"],
        allow_origin_regex=_resolve_allowed_origin_regex(),
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    manager = ScannerManager()

    @app.get("/api/health")
    def health() -> dict:
        return {
            "status": "ok",
            "os": manager.os_type,
            "exclude_local": manager.exclude_local,
            "has_virustotal_key": bool(os.getenv("VIRUSTOTAL_API_KEY")),
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
