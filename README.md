# 🧿 Tafust - Cross-Platform Security Monitor

**Tafust** is a professional, beginner-friendly cybersecurity tool designed for intelligent system port analysis. It is fully **cross-platform**, supporting both **Linux** and **Windows** environments.

## 🚀 Key Features

- **Cross-Platform Compatibility**: Automatically detects your OS and uses the appropriate system commands (`ss` for Linux, `netstat` for Windows).
- **Intelligent Risk Engine**: Calculates a numerical Risk Score (0-100) based on interface exposure, process reputation, and port type.
- **Process Mapping (via psutil)**: Automatically maps PIDs to human-readable process names (e.g., `sshd`, `brave`, `explorer.exe`).
- **Graphical Dashboard**: A clean Tkinter interface with a real-time risk summary and detailed findings.
- **Educational Reasoning**: Explains the rationale behind every risk classification to help users learn defensive cybersecurity.

## 💻 Supported Operating Systems

- **Linux**: Uses `ss -tulnp` for detailed socket analysis.
- **Windows**: Uses `netstat -ano` combined with `psutil` for process identification.

## 🛠️ How to Use

1. **Install Dependencies**:
   ```bash
   pip install psutil Pillow
   ```
2. **Run the App**:
   ```bash
   python3 tafust.py
   ```

> [!IMPORTANT]
> **Admin Privileges**: For full process visibility (especially on Windows), it is highly recommended to run the tool with administrative or root privileges.

## ⚖️ Risk Statuses
- ✅ **SAFE (0-30)**: Trusted local or standard encrypted services.
- ⚠️ **WARNING (31-70)**: Unknown processes or services on unusual ports.
- 🚨 **SUSPICIOUS (71-100)**: Unrecognized processes exposed on external network interfaces.

---
*Created for cross-platform educational cybersecurity learning and defensive monitoring.*
