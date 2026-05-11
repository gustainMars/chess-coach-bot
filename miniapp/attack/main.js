import { getT }                                   from '../shared/i18n.js';
import { parseFen, buildBoard, renderHighlights } from '../shared/board.js';
import { checkCaptures, getPosition }             from '../shared/api.js';
import { MESSAGES }                               from './messages.js';

// ── Telegram init ─────────────────────────────────────────────────────────────
const tg = window.Telegram?.WebApp;
if (tg) { tg.ready(); tg.expand(); }

// ── i18n ──────────────────────────────────────────────────────────────────────
const T = getT(MESSAGES);

// ── Config ────────────────────────────────────────────────────────────────────
const API_URL = (new URLSearchParams(location.search).get('api') || '').replace(/\/$/, '');

// ── Static UI text ────────────────────────────────────────────────────────────
document.getElementById('ui-title').textContent    = T.title;
document.getElementById('ui-subtitle').textContent = T.subtitle;
document.getElementById('check-btn').textContent   = T.checkBtn;

// ── State ─────────────────────────────────────────────────────────────────────
let currentFen   = '';
let currentBoard = {};
let squares      = {};
let selected     = new Set();
let lastMissed   = new Set();
let lastExtra    = new Set();
let frozen       = false;
let resultMode   = false;

// ── Board ─────────────────────────────────────────────────────────────────────
function rebuildBoard(fen) {
  const svgBoard = document.getElementById('board');
  while (svgBoard.firstChild) svgBoard.removeChild(svgBoard.firstChild);

  const { board, turn } = parseFen(fen);
  currentBoard = board;

  const { squares: newSquares, files } = buildBoard(svgBoard, board, {
    flipped: turn === 'b',
    onSquareClick: handleSquareClick,
  });
  squares = newSquares;

  const fileLabelEl = document.getElementById('file-labels');
  fileLabelEl.innerHTML = '';
  files.forEach(f => {
    const span = document.createElement('span');
    span.textContent = f;
    fileLabelEl.appendChild(span);
  });
}

// ── Load position from API ────────────────────────────────────────────────────
async function loadPosition() {
  selected.clear();
  lastMissed = new Set();
  lastExtra  = new Set();
  frozen     = false;
  resultMode = false;

  const status = document.getElementById('status');
  const btn    = document.getElementById('check-btn');
  status.textContent = T.loading;
  status.className   = '';
  btn.disabled       = true;
  btn.textContent    = T.checkBtn;
  document.getElementById('selected-info').textContent = '';

  try {
    const data = await getPosition({ apiUrl: API_URL, initData: tg?.initData ?? '' });
    currentFen = data.fen;
    rebuildBoard(currentFen);
    status.textContent = T.instruction;
    render();
  } catch {
    status.textContent = T.connectionError;
    status.className   = 'wrong';
  }
}

// ── Interaction ───────────────────────────────────────────────────────────────
function handleSquareClick(sq) {
  if (frozen || !currentBoard[sq]) return;
  if (selected.has(sq)) selected.delete(sq);
  else selected.add(sq);
  render();
}

function render() {
  renderHighlights(squares, selected, lastMissed, lastExtra);
  const btn  = document.getElementById('check-btn');
  const info = document.getElementById('selected-info');

  if (!resultMode) {
    btn.disabled     = selected.size === 0;
    btn.textContent  = T.checkBtn;
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
      fen:      currentFen,
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
  lastMissed = new Set(data.missed ?? []);
  lastExtra  = new Set(data.extra  ?? []);
  renderHighlights(squares, selected, lastMissed, lastExtra);

  if (data.correct) {
    status.textContent = T.correct(selected.size);
    status.className   = 'correct';
    btn.textContent    = T.newPosition;
    btn.disabled       = false;
    resultMode         = true;
    document.getElementById('selected-info').textContent = '';
  } else {
    const m = [...lastMissed].sort().join(', ');
    const e = [...lastExtra].sort().join(', ');
    status.textContent = (lastMissed.size && lastExtra.size)
      ? T.both(m, e)
      : lastMissed.size ? T.missed(m) : T.extra(e);
    status.className = 'wrong';

    setTimeout(() => {
      frozen     = false;
      lastMissed = new Set();
      lastExtra  = new Set();
      status.textContent = T.instruction;
      status.className   = '';
      render();
    }, 2000);
  }
}

// ── Button ────────────────────────────────────────────────────────────────────
document.getElementById('check-btn').addEventListener('click', () => {
  if (resultMode) loadPosition();
  else submitAnswer();
});

// ── Init ──────────────────────────────────────────────────────────────────────
loadPosition();
