# Plan: Persistence Layer — Users, Opening Stats & Rating Tracking
 
## Context
 
After `/analyze`, computed stats currently vanish — nothing is persisted. The goal is to:
1. Save a monthly snapshot of each user's opening stats per color and ECO
2. Track the user's Chess.com rapid rating (fetched from the stats endpoint, not from PGN tags which reflect pre-game rating)
3. Congratulate the user when their rating improves vs. the previous month's snapshot
 
Rating is saved **once per month** (first `/analyze` of the month). Subsequent analyzes in the same month update wins/losses/draws but leave rating unchanged. Opening stats are always re-computed from scratch from the full month's games and overwrite the counters.
 
---
 
## Architecture Decisions
 
- **Session management:** context manager inside each repository function — short-lived, no session leaking between Telegram updates
- **Startup:** `dp.startup.register(on_startup)` (aiogram 3.x signal) calling `await init_db()`
- **Upsert:** `sqlalchemy.dialects.sqlite.insert` with `.on_conflict_do_update()` — `rating` excluded from the conflict update columns so it's only ever written on first insert of the month
- **DB failure isolation:** persistence block in the handler wrapped in `try/except` so a DB error never kills the user-facing response
 
---
 
## Files to Create
 
### `bot/db/database.py`
- Read `DATABASE_URL` from env (default: `sqlite+aiosqlite:///chess_bot.db`)
- `create_async_engine(url, echo=False)`
- `AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)` — `expire_on_commit=False` is required for async to avoid `MissingGreenlet` on attribute access post-commit
- `async def init_db()` → `conn.run_sync(Base.metadata.create_all)` (idempotent)
 
---
 
## Files to Modify
 
### `bot/db/models.py` (currently empty)
Two models using SQLAlchemy 2.0 `Mapped` + `mapped_column` style:
 
**`User`** — table `users`
- `username: Mapped[str]` PK (chess.com, already lowercased)
- `telegram_id: Mapped[Optional[int]]` BigInteger (Telegram IDs are 64-bit)
- `last_analyzed_at: Mapped[Optional[datetime]]`
 
**`UserOpeningStat`** — table `user_opening_stats`
- Composite PK: `(username, eco, color, month, year)`
- `username` FK → `users.username`
- `color: Mapped[str]` — `'white'` or `'black'`
- `rating: Mapped[Optional[int]]` — snapshot, written on INSERT only
- `total, wins, losses, draws: Mapped[int]`
 
---
 
### `bot/db/repository.py` (currently empty)
Three async functions, each opens its own session via `AsyncSessionLocal`:
 
**`upsert_user(username, telegram_id)`**
- `sqlite_insert(User).on_conflict_do_update(index_elements=["username"], set_={"last_analyzed_at": ..., "telegram_id": ...})`
- Compute `datetime.utcnow()` once before the statement to avoid microsecond drift between VALUES and SET
 
**`upsert_opening_stat(username, eco, color, month, year, rating, total, wins, losses, draws)`**
- `sqlite_insert(UserOpeningStat).on_conflict_do_update(index_elements=[all 5 PK fields], set_={"total": ..., "wins": ..., "losses": ..., "draws": ...})`
- `rating` intentionally excluded from `set_` — only set on INSERT (first of the month)
 
**`get_previous_rating(username, current_month, current_year) -> Optional[int]`**
- `select(UserOpeningStat.rating).where(year*12+month < current_year*12+current_month).order_by(...desc).limit(1)`
- Returns the most recent prior-month rating snapshot for this user (any ECO/color)
 
---
 
### `bot/services/chesscom.py`
Add `async def get_player_rating(username: str) -> Optional[int]`:
- `GET /pub/player/{username}/stats`
- Returns `data["chess_rapid"]["last"]["rating"]` or `None`
 
---
 
### `bot/handlers/analyze.py`
After computing `white_stats` / `black_stats`, add persistence block (inside `try/except`):
1. `rating = await get_player_rating(username)` (may be `None`)
2. `await upsert_user(username, message.from_user.id)`
3. Loop white_stats (color=`'white'`) + black_stats (color=`'black'`) → `await upsert_opening_stat(...)`
4. `prev_rating = await get_previous_rating(username, month, year)`
5. If `rating and prev_rating and rating > prev_rating` → append `Messages.RATING_PROGRESS` to report
 
Add to `bot/domain/messages.py`:
```
RATING_PROGRESS = "\n🎉 *Rating up!* Rapid went from {prev} → {current} since last month. Keep it up!\n"
```
 
---
 
### `main.py`
```python
from bot.db.database import init_db
 
async def on_startup(**kwargs):  # **kwargs required by aiogram signal system
    await init_db()
 
# inside main(), before start_polling:
dp.startup.register(on_startup)
```
 
---
 
## Unit Tests
 
Every new function must have a corresponding unit test. Tests live under `tests/` mirroring the `bot/` structure:
 
```
tests/
├── services/
│   ├── test_chesscom.py
│   ├── test_opening_extractor.py
│   └── test_stats.py
├── db/
│   └── test_repository.py
└── domain/
    └── test_opening.py
```
 
### Test coverage requirements per function
Each test module must cover:
- **Happy path** — expected input produces expected output
- **Edge cases** — empty lists, None values, boundary conditions (e.g. winrate 0%, 100%, exactly 45%, 55%)
- **Business rule validation** — e.g. rating only saved on first INSERT of the month, not on subsequent updates; `get_previous_rating` only returns rows from strictly prior months
- **None / validation returns** — functions that can return `None` must have a test asserting `None` is returned under the correct conditions (e.g. `get_player_rating` when user has no rapid games, `get_user_info` on 404)
 
### Test patterns
- Use `pytest` + `pytest-asyncio` for async functions
- Mock external HTTP calls with `unittest.mock.AsyncMock` / `respx` — never hit real Chess.com API in tests
- DB tests use an in-memory SQLite: `sqlite+aiosqlite:///:memory:` — never touch production DB
- Each test file has a `pytest.fixture` for the async engine / session if needed
 
### Files to create
- `tests/__init__.py`
- `tests/services/test_chesscom.py` — covers `get_user_info`, `get_recent_games`, `get_player_rating`
- `tests/services/test_opening_extractor.py` — covers `extract_opening_from`, `_opening_name_from_url`
- `tests/services/test_stats.py` — covers `aggregate_openings`, `top_openings`
- `tests/db/test_repository.py` — covers `upsert_user`, `upsert_opening_stat`, `get_previous_rating`
- `tests/domain/test_opening.py` — covers `OpeningStat.winrate` property, `Outcome` enum values
 
---
 
## Verification
 
1. Start bot locally (`python main.py`) — confirm `chess_bot.db` is created and tables exist
2. `/analyze <username>` — check `users` and `user_opening_stats` rows are inserted with correct month/year/rating
3. `/analyze` again same month — confirm counters updated but `rating` unchanged
4. Manually set a previous month's row with lower rating → `/analyze` should show congrats message
5. Simulate DB failure (wrong DB path) → bot still sends the report, error logged but not shown to user
6. Run `pytest tests/` — all tests pass