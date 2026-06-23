import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.scanner_manager import ScannerManager


def create_app() -> FastAPI:
    app = FastAPI(
        title="Tafust API",
        version="0.1.0",
        description="HTTP API for the Tafust network audit engine.",
    )

    allowed_origins = os.getenv("TAFUST_ALLOWED_ORIGINS", "http://localhost:5173")
    origins = [origin.strip() for origin in allowed_origins.split(",") if origin.strip()]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins or ["*"],
        allow_credentials=True,
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
