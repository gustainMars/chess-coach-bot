import { getT }                               from '../shared/i18n.js';
import { parseFen, buildBoard, renderHighlights } from '../shared/board.js';
import { checkCaptures }                      from '../shared/api.js';
import { MESSAGES }                           from './messages.js';

// ── Telegram init ─────────────────────────────────────────────────────────────
const tg = window.Telegram?.WebApp;
if (tg) { tg.ready(); tg.expand(); }

// ── i18n ──────────────────────────────────────────────────────────────────────
const T = getT(MESSAGES);

// ── URL params ────────────────────────────────────────────────────────────────
const params  = new URLSearchParams(location.search);
const FEN     = params.get('fen') || 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1';
const API_URL = (params.get('api') || '').replace(/\/$/, '');

// ── Apply static text ─────────────────────────────────────────────────────────
document.getElementById('ui-title').textContent    = T.title;
document.getElementById('ui-subtitle').textContent = T.subtitle;
document.getElementById('status').textContent      = T.instruction;
document.getElementById('check-btn').textContent   = T.checkBtn;

// ── Build board ───────────────────────────────────────────────────────────────
const { board, turn } = parseFen(FEN);
const svgBoard = document.getElementById('board');

const { squares, files } = buildBoard(svgBoard, board, {
  flipped: turn === 'b',
  onSquareClick: handleSquareClick,
});

// File coordinate labels
const fileLabelEl = document.getElementById('file-labels');
files.forEach(f => {
  const span = document.createElement('span');
  span.textContent = f;
  fileLabelEl.appendChild(span);
});

// ── State ─────────────────────────────────────────────────────────────────────
let selected   = new Set();
let frozen     = false;
let lastMissed = new Set();
let lastExtra  = new Set();

// ── Interaction ───────────────────────────────────────────────────────────────
function handleSquareClick(sq) {
  if (frozen || !board[sq]) return;
  if (selected.has(sq)) selected.delete(sq);
  else selected.add(sq);
  render();
}

function render() {
  renderHighlights(squares, selected, lastMissed, lastExtra);

  const btn  = document.getElementById('check-btn');
  const info = document.getElementById('selected-info');

  if (!frozen) {
    btn.disabled    = selected.size === 0;
    btn.textContent = T.checkBtn;
    info.textContent = selected.size > 0
      ? T.selectedInfo([...selected].sort().join(', '))
      : '';
  }
}

// ── Submit ────────────────────────────────────────────────────────────────────
async function submitAnswer() {
  const btn    = document.getElementById('check-btn');
  const status = document.getElementById('status');

  btn.disabled    = true;
  btn.textContent = T.checking;
  frozen = true;

  try {
    const data = await checkCaptures({
      apiUrl:   API_URL,
      fen:      FEN,
      selected: [...selected],
      initData: tg?.initData ?? '',
    });
    showResult(data, btn, status);
  } catch {
    status.textContent = T.connectionError;
    status.className   = 'wrong';
    btn.textContent    = T.checkBtn;
    btn.disabled       = selected.size === 0;
    frozen = false;
    render();
  }
}

function showResult(data, btn, status) {
  if (data.correct) {
    status.textContent = T.correct(selected.size);
    status.className   = 'correct';
    btn.textContent    = T.newPosition;
    btn.disabled       = false;
    document.getElementById('selected-info').textContent = '';
    btn.onclick = () => tg ? tg.close() : window.close();
  } else {
    lastMissed = new Set(data.missed ?? []);
    lastExtra  = new Set(data.extra  ?? []);

    const m = [...lastMissed].sort().join(', ');
    const e = [...lastExtra].sort().join(', ');
    status.textContent = (lastMissed.size && lastExtra.size)
      ? T.both(m, e)
      : lastMissed.size ? T.missed(m) : T.extra(e);
    status.className = 'wrong';

    // Unfreeze after 2 s so the user can adjust the selection
    setTimeout(() => {
      frozen = false;
      lastMissed.clear();
      lastExtra.clear();
      status.textContent = T.instruction;
      status.className   = '';
      render();
    }, 2000);
  }
  render();
}

document.getElementById('check-btn').addEventListener('click', submitAnswer);
render();
