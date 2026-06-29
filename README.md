# Tafust

Tafust is a desktop security auditing tool for inspecting listening ports, mapping them to local processes, and producing a beginner-friendly risk report. The project targets defensive learning and local system visibility on Windows and Linux.

## Features

- Cross-platform port discovery with `netstat` on Windows and `ss` on Linux
- Process mapping with `psutil`
- Risk classification with contextual explanations
- Desktop interface built with `customtkinter`
- JSON export of the latest scan results

## Project Structure

- `main.py`: application entry point
- `src/`: UI and analysis logic
- `config/whitelist.json`: allowed service definitions
- `engine/scanner.go`: optional Go experiment for banner grabbing

## Requirements

- Python 3.10+
- Windows or Linux
- Administrator/root privileges recommended for complete process visibility

## Installation

```bash
pip install -r requirements.txt
```

## Web Architecture

Tafust now includes a web interface architecture based on:

- `FastAPI` for exposing the existing Python scan engine over HTTP
- `React + Tailwind CSS` for a modern dashboard UI

For development, the frontend uses a Vite proxy so the browser can call `/api`
without exposing a second origin by default. For deployment, plan to serve the
frontend and API behind the same HTTPS domain or behind a reverse proxy.

### Backend API

Run the API server from the project root:

```bash
uvicorn src.api:app --reload
```

Available endpoints:

- `GET /api/health`
- `GET /api/report`
- `POST /api/scan`

Copy `.env.example` to `.env` and configure explicit browser origins and hosts:

```bash
TAFUST_ALLOWED_ORIGINS=http://localhost:5173,https://localhost:5173
TAFUST_ALLOWED_HOSTS=localhost,127.0.0.1
TAFUST_FORCE_HTTPS=false
```

Security notes:

- By default, the API no longer allows every origin.
- The API now validates the request host header.
- Security headers are added automatically.
- Enable `TAFUST_FORCE_HTTPS=true` only when the app is actually served over HTTPS.

### Frontend

Install and run the React app:

```bash
cd frontend
npm install
npm run dev
```

Copy `frontend/.env.example` to `frontend/.env` if you need to override defaults.

Default behavior:

- The dev server listens on `127.0.0.1:5173`
- Browser requests to `/api` are proxied to `http://127.0.0.1:8000`
- `VITE_API_BASE_URL` can stay empty when frontend and API share the same origin

Optional environment variables:

```bash
VITE_API_BASE_URL=
VITE_BACKEND_URL=http://127.0.0.1:8000
VITE_DEV_HOST=127.0.0.1
VITE_DEV_HTTPS=false
VITE_DEV_SSL_CERT=
VITE_DEV_SSL_KEY=
```

To use HTTPS in local development, provide a trusted local certificate and set:

```bash
VITE_DEV_HTTPS=true
VITE_DEV_SSL_CERT=frontend/certs/localhost.pem
VITE_DEV_SSL_KEY=frontend/certs/localhost-key.pem
```

If you expose the dev server on your LAN, also add that origin explicitly in
`TAFUST_ALLOWED_ORIGINS`.

### Deployment Guidance

Recommended production shape:

1. Build the frontend with `npm run build`.
2. Serve `frontend/dist` behind `nginx`, `Caddy`, or another HTTPS reverse proxy.
3. Reverse-proxy `/api` to `uvicorn` so the browser stays on a single origin.
4. Set `TAFUST_ALLOWED_ORIGINS` to your real HTTPS domain only.
5. Set `TAFUST_ALLOWED_HOSTS` to your real domain only.
6. Set `TAFUST_FORCE_HTTPS=true`.

Example production values:

```bash
TAFUST_ALLOWED_ORIGINS=https://tafust.example.com
TAFUST_ALLOWED_HOSTS=tafust.example.com
TAFUST_FORCE_HTTPS=true
VITE_API_BASE_URL=
```

## Run

```bash
python main.py
```

## Windows Desktop Build

Tafust can be packaged as a standalone Windows desktop executable with `PyInstaller`.

### Build prerequisites

- Windows
- Python virtual environment in `.\venv`
- Dependencies installed from `requirements.txt`

### Build command

From the project root in PowerShell:

```powershell
.\build_windows.ps1 -Clean
```

Output:

- `dist\Tafust.exe`

### Notes for the packaged app

- The executable embeds `config/whitelist.json` and `img/logo.png`.
- Runtime exports are written to `%LOCALAPPDATA%\Tafust\tafust_data`.
- You can place a `.env` file next to `Tafust.exe` to provide `VIRUSTOTAL_API_KEY`.
- The optional Go engine is not bundled unless you also provide `engine/scanner.exe`.

## Notes

- Runtime exports are written to `tafust_data/`, which is ignored by Git.
- The Go engine is optional and is not required to launch the Python application.
- Add a `.env` file with `VIRUSTOTAL_API_KEY=...` to enable optional cloud hash reputation lookups.

## Reputation Pipeline

Tafust now combines several signals before flagging a process:

- Local executable path collection
- SHA-256 hashing of the executable
- Windows Authenticode signature verification when available
- Optional VirusTotal hash lookup when `VIRUSTOTAL_API_KEY` is configured

Without an API key, the application still works and falls back to local trust signals only.

## License

This project is released under the MIT License. See `LICENSE`.
