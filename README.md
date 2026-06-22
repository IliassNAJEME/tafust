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

## Run

```bash
python main.py
```

## Notes

- Runtime exports are written to `tafust_data/`, which is ignored by Git.
- The Go engine is optional and is not required to launch the Python application.

## License

This project is released under the MIT License. See `LICENSE`.
