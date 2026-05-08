# Study Mini App & Analyze — Improvement Spec

## 1. `/analyze` — Sliding 30-Day Window (implemented)

The `[months]` parameter has been removed. Instead of fetching full calendar months,
`get_recent_games` now:

1. Computes a cutoff timestamp = `now - 30 days`.
2. Fetches only the monthly archives that overlap that window (1–2 archives).
3. Filters each game by `end_time >= cutoff` before returning.

This prevents abuse (e.g. `months=5000`) and gives a consistent, date-accurate window
regardless of when during the month the command is run.

---

## 2. Opening Data Source

### Problem
Even with 1400+ games, `/analyze` rarely finds blunders. The current deviation logic
compares game moves against a static ECO book that covers only 4–8 half-moves per
variation. A game that plays a less-common but theoretically sound move deviates from
the book immediately, producing a low-quality or missing blunder.

### Proposed solution: Lichess Opening Explorer

Replace the static book with the Lichess Opening Explorer API (free, no auth):

```
GET https://explorer.lichess.ovh/lichess?fen=<FEN>&topGames=0&recentGames=0
```

The response contains the most-played moves for that position across millions of
Lichess games, along with win/draw/loss counts per move.

**New deviation detection flow:**
1. Replay the game move-by-move with `python-chess`.
2. At each half-move, query the Explorer API for the current FEN.
3. If the player's move is absent from the top-N Explorer moves **and** Stockfish eval
   drops by more than the blunder threshold → record as a blunder.
4. Cache Explorer responses by FEN in a new `opening_explorer_cache` SQLite table
   (30-day TTL) to stay within API rate limits.

---

## 3. Study Mini App — Interactive Board

### Problem
`/study` sends a static PNG and waits for a text move in SAN/UCI format. This is
unintuitive for most players and gives no visual feedback.

### Proposed solution
Replace the static image + text input with a Mini App using the same `board.js`
component as Attack Training (same Lichess piece set, same SVG board).

**Interaction — two-click move input:**
1. User taps a piece → piece is highlighted with a blue ring.
2. User taps a destination square → move is submitted to the backend.
3. Backend validates and returns `correct`, the expected move, and optional
   explanation.
4. Mini App shows a green overlay (correct) or red overlay with the expected move
   drawn as an arrow (wrong).

**Bot command change:**
- `/study` sends a message with an "Open Study" WebApp button (no image, same pattern
  as `/attack`).
- The Mini App fetches the next blunder via `GET /miniapp/study/card`.

**Backend endpoints:**
```
GET  /miniapp/study/card?eco=<ECO>   → { blunder_id, fen, opening_name, quality }
POST /miniapp/study/answer           → { blunder_id, move }
                                     ← { correct, expected_move }
```

**Frontend file structure:**
```
miniapp/
  study/
    index.html      # HTML structure only
    styles.css
    main.js         # two-click move logic, result overlay
    messages.js     # i18n strings
  shared/
    board.js        # reused as-is
    api.js          # add getStudyCard() and submitStudyAnswer()
    i18n.js         # reused as-is
```

---

## 4. Opening Selector

### Problem
The study deck cycles through all blunders. Users who want to focus on a specific
opening (e.g. only the Sicilian) have no way to do so.

### Proposed solution

**Backend endpoint:**
```
GET /miniapp/study/openings
← [{ eco: "B20", name: "Sicilian Defense", blunder_count: 12 }, ...]
```
Returns openings the user has blunders in, sorted by blunder count descending.

**Mini App selector:**
- At the top of the study screen, show a `<select>` dropdown populated from the
  endpoint (fetched once on load).
- Default option: "All openings".
- Selecting an ECO filters the deck: subsequent `GET /miniapp/study/card` calls
  include `?eco=B20`.
- On mobile, the native `<select>` renders as the platform's native picker — no
  extra library needed.
