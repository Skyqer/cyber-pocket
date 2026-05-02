# 🖥️ Cyber-Pocket

A personal system monitoring assistant that lives inside your PC and talks to you through Telegram. Built with **FastAPI**, **aiogram 3**, and **psutil** — it gives you real-time hardware stats, app logs, and an AI-powered Q&A assistant (via Gemini CLI), all from your phone.

**Supported:** Windows 11 • Linux

---

## ✨ Features

| Feature | Description |
|---|---|
| 📊 **System Status** | CPU, RAM, GPU & VRAM %, disk usage, temperatures, load average, uptime |
| 📈 **Live Graph** | CPU & RAM load chart built from a rolling history |
| 🚨 **Smart Alerts** | Automatic Telegram notifications for high CPU/GPU load or temperature anomalies |
| 🔝 **Top Processes** | Top 5 processes by CPU consumption |
| 📝 **App Logs** | View the last 20 lines of the application log directly in Telegram |
| 🌐 **Speedtest** | Measure your internet download/upload speed and ping on demand |
| 🤖 **Ask Gemini** | Send any question to Google Gemini CLI and get an answer in chat |
| 🔒 **Safety Filters** | Dangerous shell commands and prompts are blocked before reaching Gemini |
| ⚡ **FastAPI Backend** | Lightweight HTTP server with a `/health` endpoint running alongside the bot |

---

## 🤖 Bot Commands

| Command | Description |
|---|---|
| `/start` | Welcome message and navigation keyboard |
| `/status` | Full system snapshot + CPU/RAM graph |
| `/logs` | Last 20 lines from `cyber_pocket.log` |
| `/speedtest` | Measure internet connection speed |
| `/ask <question>` | Ask Gemini CLI anything (IT-focused assistant) |
| `/help` | Command reference |

You can also use the **reply keyboard buttons** instead of typing commands:
- 📊 Статус → `/status`
- 📝 Логи → `/logs`
- 🌐 Speedtest → `/speedtest`
- ❓ Помощь → `/help`

---

## 🏗️ Project Structure

```
cyber-pocket/
├── main.py                  # FastAPI app + lifespan (bot + metrics collector)
├── core/
│   ├── config.py            # Settings loaded from .env + OS auto-detection
│   └── logger.py            # Rotating file + console logger
├── bot/
│   ├── __init__.py
│   └── handlers.py          # All aiogram message handlers
├── services/
│   ├── system_monitor.py    # psutil metrics, GPU (nvidia-smi / sysfs), graph
│   ├── network.py           # Async speedtest-cli runner for internet checks
│   ├── gemini_cli.py        # Async wrapper around Gemini CLI with safety filters
│   └── alerts.py            # Automated system monitoring & Telegram notifications
├── utils/
│   └── formatters.py        # Text formatting helpers for bot messages
├── logs/                    # Auto-created, excluded from git
├── .env                     # Your secrets (excluded from git)
├── .env.example             # Template for environment variables
└── .gitignore
```

---

## ⚙️ Tech Stack

- **[FastAPI](https://fastapi.tiangolo.com/)** — async web framework
- **[aiogram 3](https://docs.aiogram.dev/)** — Telegram Bot API framework
- **[psutil](https://pypi.org/project/psutil/)** — cross-platform system metrics
- **[matplotlib](https://matplotlib.org/)** — CPU/RAM load graph rendering
- **[speedtest-cli](https://github.com/sivel/speedtest-cli)** — internet bandwidth testing
- **[Google Gemini CLI](https://github.com/google-gemini/gemini-cli)** — AI assistant backend
- **[python-dotenv](https://pypi.org/project/python-dotenv/)** — environment variable management
- **[uv](https://docs.astral.sh/uv/)** — fast Python package manager

---

## 🚀 Getting Started

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) installed
- A Telegram bot token from [@BotFather](https://t.me/BotFather)
- *(Optional)* [Gemini CLI](https://github.com/google-gemini/gemini-cli) installed globally (`npm install -g @google/gemini-cli`) for `/ask` to work
- *(Windows, optional)* NVIDIA GPU drivers installed (for GPU monitoring via `nvidia-smi`)

### 1. Clone the repository

```bash
git clone https://github.com/Skyqer/cyber-pocket.git
cd cyber-pocket
```

### 2. Create and activate virtual environment

**Linux / macOS:**
```bash
uv venv
source .venv/bin/activate
```

**Windows (PowerShell):**
```powershell
uv venv
.venv\Scripts\Activate.ps1
```

**Windows (CMD):**
```cmd
uv venv
.venv\Scripts\activate.bat
```

### 3. Install dependencies

```bash
uv pip install -r requirements.txt
```

### 4. Configure environment variables

**Linux / macOS:**
```bash
cp .env.example .env
```

**Windows (PowerShell):**
```powershell
Copy-Item .env.example .env
```

Edit `.env` and fill in your values:

```env
TELEGRAM_BOT_TOKEN=your_bot_token_from_botfather_here
TELEGRAM_ADMIN_ID=your_telegram_user_id_here

# Optional: override OS auto-detection (windows / linux)
# OS_TYPE=windows
```

> You can find your Telegram user ID by messaging [@userinfobot](https://t.me/userinfobot).

### 5. Run the application

```bash
uv run uvicorn main:app --reload
```

The FastAPI server will start on `http://127.0.0.1:8000` and the Telegram bot will begin polling automatically.

---

## 🖥️ Platform Support

### Windows 11

| Feature | Method | Notes |
|---|---|---|
| CPU % | `psutil` | ✅ Full support |
| RAM | `psutil` | ✅ Full support |
| Disk | `psutil` | Uses `C:\` as root |
| CPU Temp | WMI (`MSAcpi_ThermalZoneTemperature`) | May require admin privileges; shows N/A if unavailable |
| GPU (NVIDIA) | `nvidia-smi` | ✅ Utilization + Temperature + VRAM |
| GPU (AMD) | Windows Performance Counters | ✅ Utilization + VRAM; temperature not available |
| Load Average | — | Not available on Windows (shows N/A) |
| Processes | `psutil` | ✅ Full support |
| Speedtest | `speedtest-cli` | ✅ Full support |
| Gemini CLI | `gemini` subprocess | ✅ Full support |

### Linux

| Feature | Method | Notes |
|---|---|---|
| CPU % | `psutil` | ✅ Full support |
| RAM | `psutil` | ✅ Full support |
| Disk | `psutil` | Uses `/` as root |
| CPU Temp | `psutil.sensors_temperatures()` | Supports k10temp, coretemp, etc. |
| GPU % / Temp / VRAM | sysfs (`/sys/class/drm`) | AMD/AMDGPU; NVIDIA via sysfs not implemented |
| Load Average | `os.getloadavg()` | ✅ Full support |
| Processes | `psutil` | ✅ Full support |
| Speedtest | `speedtest-cli` | ✅ Full support |
| Gemini CLI | `gemini` subprocess | ✅ Full support |

---

## 🔒 Security Notes

- The `.env` file is **never committed** to git — it is listed in `.gitignore`.
- Gemini CLI requests are filtered through a **dangerous command blacklist** — both Linux (`rm -rf`, `mkfs`, `shutdown`) and Windows (`del /f`, `format`, `reg delete`, `taskkill`) patterns are blocked.
- The bot only runs **locally on your machine** — it does not expose any ports to the internet.

---

## 📄 License

This project is for personal use. Feel free to fork and adapt it.
