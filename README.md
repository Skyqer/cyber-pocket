# 🖥️ Cyber-Pocket

A personal system monitoring assistant that lives inside your PC and talks to you through Telegram. Built with **FastAPI**, **aiogram 3**, and **psutil** — it gives you real-time hardware stats, app logs, and an AI-powered Q&A assistant (via Gemini CLI), all from your phone.

---

## ✨ Features

| Feature | Description |
|---|---|
| 📊 **System Status** | CPU %, RAM %, disk usage, temperature, load average, uptime |
| 📈 **Live Graph** | CPU & RAM load chart built from a rolling 30-minute history |
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
│   ├── config.py            # Settings loaded from .env
│   └── logger.py            # Rotating file + console logger
├── bot/
│   ├── __init__.py
│   └── handlers.py          # All aiogram message handlers
├── services/
│   ├── system_monitor.py    # psutil metrics, graph generation, process list
│   ├── network.py           # Async speedtest-cli runner for internet checks
│   └── gemini_cli.py        # Async wrapper around Gemini CLI with safety filters
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

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) installed
- A Telegram bot token from [@BotFather](https://t.me/BotFather)
- *(Optional)* [Gemini CLI](https://github.com/google-gemini/gemini-cli) installed globally (`npm install -g @google/gemini-cli`) for `/ask` to work

### 1. Clone the repository

```bash
git clone https://github.com/Skyqer/cyber-pocket.git
cd cyber-pocket
```

### 2. Create and activate virtual environment

```bash
uv venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
uv pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and fill in your values:

```env
TELEGRAM_BOT_TOKEN=your_bot_token_from_botfather_here
TELEGRAM_ADMIN_ID=your_telegram_user_id_here
```

> You can find your Telegram user ID by messaging [@userinfobot](https://t.me/userinfobot).

### 5. Run the application

```bash
uv run uvicorn main:app --reload
```

The FastAPI server will start on `http://127.0.0.1:8000` and the Telegram bot will begin polling automatically.

---

## 🔒 Security Notes

- The `.env` file is **never committed** to git — it is listed in `.gitignore`.
- Gemini CLI requests are filtered through a **dangerous command blacklist** (`rm -rf`, `mkfs`, `shutdown`, etc.) — any response containing these patterns is blocked before being sent to the user.
- The bot only runs **locally on your machine** — it does not expose any ports to the internet.

---

## 📄 License

This project is for personal use. Feel free to fork and adapt it.
