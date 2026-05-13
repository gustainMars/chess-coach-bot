# Spec: Full-Game Blunder Review + `/learn` Opening Command

## Context

Currently `find_blunders_in_game` only scans `max_half_moves=12` (6 full moves = opening phase) and
returns after the **first** blunder found. The user wants to:

1. Scan the **entire game** for blunders (not just the opening).
2. Split the current `/study` command into two distinct commands:
   - `/review_blunders` — review your own blunders from real games.
   - `/learn` — learn any opening from scratch, interactively, via miniapp + Lichess explorer.
3. (Future, not in scope now) `/puzzles` — personalized puzzles based on rating.

---

## Telegram Command Naming

`/review_blunders` is **valid** — Telegram Bot API supports underscores in command names.

---

## Rate Limiting Analysis

| Command | External API | Risk |
|---|---|---|
| `/analyze` + `review_blunders` blunder detection | **Stockfish only (local)** | None — no HTTP calls |
| `/learn` miniapp moves | Lichess Masters explorer | Low — user-paced clicks, 24 h DB cache per FEN |

The previous "too many requests" issue was from hitting Lichess explorer with bulk automated
requests. The new design avoids that: blunder detection never touches Lichess, and the learn
miniapp only calls Lichess on explicit user navigation (one FEN at a time, cached).

---

## Performance Concern: Full-Game Stockfish Analysis

Current: 12 half-moves × 2 analyses = 24 engine calls per game.
Full game (60-move game): 120 half-moves × 2 analyses = up to 240 engine calls per game.

**Mitigation**:
- Reduce `get_recent_games` window from **30 → 15 days** in `chesscom.py`.
- Reduce Stockfish depth from 12 → **10** for `find_blunders_in_game`.
- Cap blunders collected per game at **3** (worst ones by score drop).
- Progress bar shown in Telegram so user sees analysis advancing game-by-game.

---

## Architecture Changes

### `bot/services/deviation.py`
- Remove `max_half_moves` limit from `find_blunders_in_game`.
- Collect all blunders, sort descending by score drop, return top 3.
- Depth 12 → 10.

### `bot/services/chesscom.py`
- `get_recent_games` cutoff: 30 days → 15 days.

### `bot/handlers/analyze.py`
- `_save_blunders` accepts `on_progress(i, total)` async callback.
- Progress bar format: `⚙️ Scanning games...\n[████░░░░░░] 4/10`

### `bot/handlers/review_blunders.py` (renamed from `study.py`)
- Command: `/review_blunders`
- Uses `bot/utils/miniapp.miniapp_url("study")` — single `MINIAPP_URL` env var.

### `bot/handlers/learn.py` (new)
- Command: `/learn`
- Opens `miniapp_url("learn")`.

### `bot/utils/miniapp.py` (new)
- `miniapp_url(screen: str) -> str | None`
- Reads `MINIAPP_URL` + `WEBAPP_PUBLIC_URL` env vars.
- Guards against `screen == "shared"`.

### `miniapp/learn/` (new)
- Opening picker (from `/miniapp/learn/openings`)
- Step-through board using `miniapp/shared/board.js`
- Lichess master move arrows (from `/miniapp/learn/moves?fen=...`)
- "Try it yourself" test mode

### `bot/web/routes.py`
- `GET /miniapp/learn/openings` — ECO list from `data/eco.tsv`
- `GET /miniapp/learn/moves?fen=<fen>` — Lichess explorer + 24 h DB cache

### `main.py`
- Replace `study_router` with `review_blunders_router` + `learn_router`.

### `.env`
- `STUDY_MINIAPP_URL` → **deprecated**, replaced by `MINIAPP_URL=https://<host>/miniapp`
