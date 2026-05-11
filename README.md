# Chess Coach Bot

Telegram bot that analyzes your Chess.com games, identifies your most-used openings, detects deviations, and offers interactive training exercises.

---

## Features

| Command | Description |
|---------|-------------|
| `/analyze <username> [months]` | Fetches up to 6 months of games from Chess.com, calculates winrate per opening (white/black), detects deviations from the main line, and saves blunders to the local database. Default: 1 month. |
| `/study` | Flashcard loop: shows a board position from a saved blunder and asks the user to enter the correct move. Cycles through all unreviewed blunders, then resets. |
| `/attack` | Generates a random middlegame position and opens a Telegram Mini App where the user taps all pieces that can be captured. |
| `/help` | Lists available commands. |

---

## Architecture

```
chess-coach-bot/
├── main.py                     # Entry point — starts bot polling + HTTP server
├── Dockerfile                  # python:3.13-slim + libcairo2 + stockfish
├── Procfile                    # For Railway: worker: python3 main.py
│
├── bot/
│   ├── handlers/               # Telegram command handlers (aiogram routers)
│   │   ├── analyze.py          # /analyze
│   │   ├── study.py            # /study (flashcards)
│   │   ├── attack_training.py  # /attack
│   │   └── start.py            # /start, /help
│   │
│   ├── services/               # Business logic (no Telegram dependency)
│   │   ├── chesscom.py         # Chess.com public API client
│   │   ├── opening_extractor.py# Extract opening name/ECO from PGN
│   │   ├── deviation.py        # Detect deviations from opening main line
│   │   ├── move_validator.py   # Validate user move input
│   │   ├── stats.py            # Aggregate opening statistics
│   │   ├── attack_generator.py # Generate attack positions
│   │   └── board_renderer.py   # FEN → PNG via python-chess + cairosvg
│   │
│   ├── db/
│   │   ├── models.py           # SQLAlchemy models (User, OpeningStat, Blunder)
│   │   ├── repository.py       # Async CRUD helpers
│   │   └── database.py         # Engine + SessionFactory setup
│   │
│   ├── domain/                 # Pure data types and UI strings
│   │   ├── messages.py         # All bot-facing strings (Messages class)
│   │   ├── opening.py          # OpeningStat dataclass, Color enum
│   │   ├── move_quality.py     # MoveQuality enum
│   │   └── deviation_result.py # DeviationResult dataclass
│   │
│   ├── middleware/
│   │   └── qa_guard.py         # Restricts all handlers to ALLOWED_USER_ID when BOT_ENV=qa
│   │
│   ├── utils/
│   │   └── telegram_auth.py    # HMAC validation of Telegram initData (Mini App)
│   │
│   └── web/
│       └── routes.py           # aiohttp HTTP server — POST /miniapp/attack/check
│
├── miniapp/                    # Telegram Mini App (static frontend)
│   ├── attack/
│   │   ├── index.html          # HTML structure only
│   │   ├── styles.css
│   │   ├── messages.js         # UI strings in en/pt
│   │   └── main.js             # Screen logic (ES module)
│   └── shared/
│       ├── board.js            # SVG board builder, FEN parser, highlight renderer
│       ├── api.js              # fetch wrapper for /miniapp/attack/check
│       └── i18n.js             # Language detection (Telegram locale → browser)
│
└── bot/tests/                  # pytest test suite mirroring bot/ structure
```

---

## Running locally

### Prerequisites

- Python 3.10+
- `stockfish` binary: `sudo apt install stockfish` (Ubuntu) or `brew install stockfish` (macOS)
- `libcairo2`: `sudo apt install libcairo2` (Ubuntu) or `brew install cairo` (macOS)
- A Telegram bot token from [@BotFather](https://t.me/BotFather)

### 1. Clone and create the virtual environment

```bash
git clone https://github.com/<your-org>/chess-coach-bot.git
cd chess-coach-bot

python3 -m venv venv
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Create a `.env` file at the project root:

```env
# Required
TELEGRAM_TOKEN=123456:ABC-your-token-here

# Database (SQLite, created automatically on first run)
DATABASE_URL=sqlite+aiosqlite:///chess_bot.db

# Stockfish binary path (check with: which stockfish)
STOCKFISH_PATH=/usr/bin/stockfish

# Mini App (only needed for /attack with the web board)
MINIAPP_URL=https://your-github-pages-url/attack
WEBAPP_PUBLIC_URL=http://localhost:8080   # public URL of the HTTP server
WEBAPP_PORT=8080                          # local port for the Mini App API

# QA mode (optional — restricts bot to your user ID)
# BOT_ENV=qa
# ALLOWED_USER_ID=123456789
```

### 4. Run the bot

```bash
python main.py
```

This starts two things simultaneously:
- **Telegram bot** (long polling)
- **HTTP server** on `WEBAPP_PORT` (default `8080`) serving the Mini App API

---

## Running tests

```bash
pytest bot/tests/ -q
```

All 96 tests must pass. Never use `--ignore` — if an import fails due to a missing dependency, install it.

---

## Environment variables reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `TELEGRAM_TOKEN` | Yes | — | Bot token from @BotFather |
| `DATABASE_URL` | No | `sqlite+aiosqlite:///chess_bot.db` | SQLAlchemy async DB URL |
| `STOCKFISH_PATH` | No | `stockfish` | Path to Stockfish binary |
| `MINIAPP_URL` | No | — | Hosted URL of `miniapp/attack/` |
| `WEBAPP_PUBLIC_URL` | No | — | Public URL of the bot's HTTP server (passed to Mini App as `?api=`) |
| `WEBAPP_PORT` | No | `8080` | Port for the aiohttp HTTP server |
| `BOT_ENV` | No | — | Set to `qa` to restrict access to `ALLOWED_USER_ID` |
| `ALLOWED_USER_ID` | No | — | Your Telegram user ID (only used when `BOT_ENV=qa`) |

---

## Deploy (Docker)

### Build and run locally with Docker

```bash
docker build -t chess-bot .

docker run -d --restart=always \
  -v $(pwd)/data:/app/data \
  -e TELEGRAM_TOKEN=your-token \
  -e DATABASE_URL=sqlite+aiosqlite:////app/data/chess.db \
  -e STOCKFISH_PATH=stockfish \
  -p 8080:8080 \
  --name chess-bot chess-bot
```

### Deploy to Oracle Cloud (Always Free)

Pushes to `main` trigger the CI pipeline (`.github/workflows/ci.yml`) which:
1. Runs the full test suite
2. SSHs into the Oracle Cloud VM, pulls the latest code, rebuilds and restarts the Docker container

Required GitHub secrets: `OCI_HOST`, `OCI_USER`, `OCI_SSH_KEY`, `TELEGRAM_TOKEN`.

---

## Mini App setup

The `/attack` board runs as a Telegram Mini App hosted on GitHub Pages or Vercel.

1. Deploy `miniapp/` to a static host (e.g. GitHub Pages at `https://user.github.io/chess-coach-bot/miniapp/attack/`)
2. Set `MINIAPP_URL` to that URL in the bot's environment
3. Set `WEBAPP_PUBLIC_URL` to the publicly reachable URL of the bot's HTTP server (e.g. `https://your-oracle-vm-ip:8080`)
4. The bot passes both as query params to the Mini App: `?fen=...&api=...`

The Mini App auto-detects the user's language from `Telegram.WebApp.initDataUnsafe.user.language_code` (currently supports `en` and `pt`).
