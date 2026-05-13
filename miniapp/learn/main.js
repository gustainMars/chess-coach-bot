import { getT }                                          from '../shared/i18n.js';
import { parseFen, buildBoard, renderHighlights,
         drawArrow, clearArrows }                        from '../shared/board.js';
import { getLearnOpenings, getLearnMoves }               from '../shared/api.js';
import { MESSAGES }                                      from './messages.js';

// ── Telegram init ─────────────────────────────────────────────────────────────
const tg = window.Telegram?.WebApp;
if (tg) { tg.ready(); tg.expand(); }

// ── i18n ──────────────────────────────────────────────────────────────────────
const T = getT(MESSAGES);

// ── Config ────────────────────────────────────────────────────────────────────
const API_URL = (new URLSearchParams(location.search).get('api') || '').replace(/\/$/, '');

// ── DOM refs ──────────────────────────────────────────────────────────────────
const svgBoard      = document.getElementById('board');
const fileLabelsEl  = document.getElementById('file-labels');
const openingSel    = document.getElementById('opening-select');
const moveCounterEl = document.getElementById('move-counter');
const statusEl      = document.getElementById('status');
const prevBtn       = document.getElementById('prev-btn');
const nextBtn       = document.getElementById('next-btn');
const testBtn       = document.getElementById('test-btn');

// ── Static UI text ────────────────────────────────────────────────────────────
document.getElementById('ui-title').textContent = T.title;
prevBtn.textContent  = T.prevBtn;
nextBtn.textContent  = T.nextBtn;
testBtn.textContent  = T.testBtn;

// ── State ─────────────────────────────────────────────────────────────────────
let openings     = [];        // [{eco, name, moves, fens}]
let current      = null;      // selected opening
let step         = 0;         // how many moves played (0 = start)
let mode         = 'browse';  // 'browse' | 'test'
let fromSq       = null;      // first click in test mode
let squares      = {};
let flipped      = false;

// ── Board helpers ─────────────────────────────────────────────────────────────
function rebuildBoard(fen) {
  while (svgBoard.firstChild) svgBoard.removeChild(svgBoard.firstChild);
  const { board, turn } = parseFen(fen);
  flipped = turn === 'b';
  const { squares: sq, files } = buildBoard(svgBoard, board, {
    flipped,
    onSquareClick: handleSquareClick,
  });
  squares = sq;
  fileLabelsEl.innerHTML = '';
  files.forEach(f => {
    const span = document.createElement('span');
    span.textContent = f;
    fileLabelsEl.appendChild(span);
  });
}

// ── Render step ───────────────────────────────────────────────────────────────
async function renderStep() {
  clearArrows(svgBoard);
  renderHighlights(squares, new Set(), new Set(), new Set());
  fromSq = null;

  if (!current) {
    moveCounterEl.textContent = '';
    statusEl.textContent = T.startPosition;
    statusEl.className   = '';
    prevBtn.disabled = true;
    nextBtn.disabled = true;
    testBtn.hidden   = true;
    return;
  }

  const fen = current.fens[step];
  rebuildBoard(fen);

  moveCounterEl.textContent = T.moveCounter(step, current.moves.length);

  prevBtn.disabled = step === 0;
  const atEnd      = step === current.moves.length;
  nextBtn.disabled = atEnd;
  testBtn.hidden   = atEnd || mode === 'test';

  if (mode === 'test') {
    testBtn.hidden    = true;
    statusEl.textContent = T.testInstruction;
    statusEl.className   = '';
    return;
  }

  if (atEnd) {
    statusEl.textContent = T.endOfLine;
    statusEl.className   = 'info';
  } else {
    statusEl.textContent = T.browseInstruction;
    statusEl.className   = '';
  }

  // Draw Lichess master arrows
  try {
    const moves = await getLearnMoves({
      apiUrl: API_URL, fen, initData: tg?.initData ?? '',
    });
    if (moves.length === 0) {
      if (!atEnd) statusEl.textContent = T.noMasterMoves;
    } else {
      const sans = moves.map(m => m.san).join(', ');
      statusEl.textContent = T.topMoves(sans);
      moves.slice(0, 3).forEach(({ uci }, i) => {
        const colours = ['#5288c180', '#27ae6080', '#e67e2280'];
        drawArrow(svgBoard, uci.slice(0, 2), uci.slice(2, 4), colours[i] ?? colours[0], flipped);
      });
    }
  } catch {
    // arrows are non-critical; silent fail
  }
}

// ── Navigation ────────────────────────────────────────────────────────────────
function goNext() {
  if (!current || step >= current.moves.length) return;
  step++;
  mode = 'browse';
  renderStep();
}

function goPrev() {
  if (step === 0) return;
  step--;
  mode = 'browse';
  renderStep();
}

// ── Test mode ─────────────────────────────────────────────────────────────────
function enterTestMode() {
  if (!current || step >= current.moves.length) return;
  mode = 'test';
  renderStep();
}

function handleSquareClick(sq) {
  if (mode !== 'test') return;

  if (fromSq === null) {
    const { board } = parseFen(current.fens[step]);
    if (!board[sq]) return;
    fromSq = sq;
    renderHighlights(squares, new Set([sq]), new Set(), new Set());
    statusEl.textContent = T.selectPiece(sq);
  } else if (sq === fromSq) {
    fromSq = null;
    renderHighlights(squares, new Set(), new Set(), new Set());
    statusEl.textContent = T.testInstruction;
  } else {
    evaluateTestMove(fromSq, sq);
  }
}

function evaluateTestMove(from, to) {
  const played = from + to;
  const expectedUci = current.fens[step + 1]
    ? _uciFromFens(current.fens[step], current.fens[step + 1], current.moves[step])
    : null;

  const theoryUci = _moveToUci(current.fens[step], current.moves[step]);

  clearArrows(svgBoard);
  renderHighlights(squares, new Set(), new Set(), new Set());
  fromSq = null;

  if (played === theoryUci) {
    statusEl.textContent = T.correct(current.moves[step]);
    statusEl.className   = 'correct';
    setTimeout(() => {
      step++;
      mode = 'browse';
      renderStep();
    }, 1200);
  } else {
    statusEl.textContent = T.wrong(current.moves[step]);
    statusEl.className   = 'wrong';
    if (theoryUci) {
      drawArrow(svgBoard, theoryUci.slice(0, 2), theoryUci.slice(2, 4), '#e74c3c', flipped);
    }
    setTimeout(() => {
      statusEl.textContent = T.testInstruction;
      statusEl.className   = '';
      clearArrows(svgBoard);
    }, 2000);
  }
}

// Derive UCI from two consecutive FENs by comparing positions.
// Simpler: we store moves[] as SAN, but we need UCI for comparison with
// what the user clicked. We convert the expected SAN to UCI via a lookup
// approach: find the square that disappeared and the square that appeared.
function _moveToUci(fen, san) {
  // Parse the SAN from the given FEN position by matching piece movement.
  // We compare FENs: the piece that moved "from" and "to".
  const step_idx = current.moves.indexOf(san, current.moves.indexOf(san));
  const fen_idx  = current.fens.indexOf(fen);
  if (fen_idx < 0 || fen_idx + 1 >= current.fens.length) return null;

  const before = _fenToPieceMap(current.fens[fen_idx]);
  const after  = _fenToPieceMap(current.fens[fen_idx + 1]);

  let fromSq = null, toSq = null;
  for (const sq in before) {
    if (!after[sq] || after[sq] !== before[sq]) {
      fromSq = sq;
      break;
    }
  }
  for (const sq in after) {
    if (!before[sq] || before[sq] !== after[sq]) {
      toSq = sq;
      break;
    }
  }
  return fromSq && toSq ? fromSq + toSq : null;
}

function _uciFromFens(fen1, fen2, san) {
  return _moveToUci(fen1, san);
}

function _fenToPieceMap(fen) {
  const ranks = fen.split(' ')[0].split('/');
  const map   = {};
  const files  = 'abcdefgh';
  ranks.forEach((rank, ri) => {
    let fi = 0;
    for (const ch of rank) {
      if ('12345678'.includes(ch)) {
        fi += parseInt(ch, 10);
      } else {
        map[files[fi] + (8 - ri)] = ch;
        fi++;
      }
    }
  });
  return map;
}

// ── Opening selector ──────────────────────────────────────────────────────────
async function populateSelector() {
  statusEl.textContent = T.loading;
  statusEl.className   = '';
  try {
    openings = await getLearnOpenings({ apiUrl: API_URL, initData: tg?.initData ?? '' });

    const placeholder = document.createElement('option');
    placeholder.value       = '';
    placeholder.textContent = T.selectPlaceholder;
    openingSel.appendChild(placeholder);

    for (let i = 0; i < openings.length; i++) {
      const opt = document.createElement('option');
      opt.value       = String(i);
      opt.textContent = `${openings[i].eco} — ${openings[i].name}`;
      openingSel.appendChild(opt);
    }
    openingSel.disabled = false;
  } catch {
    statusEl.textContent = T.connectionError;
    statusEl.className   = 'wrong';
  }
}

openingSel.addEventListener('change', () => {
  const idx = parseInt(openingSel.value, 10);
  current   = isNaN(idx) ? null : openings[idx];
  step      = 0;
  mode      = 'browse';
  renderStep();
});

// ── Button events ─────────────────────────────────────────────────────────────
prevBtn.addEventListener('click', goPrev);
nextBtn.addEventListener('click', goNext);
testBtn.addEventListener('click', enterTestMode);

// ── Init ──────────────────────────────────────────────────────────────────────
await populateSelector();
await renderStep();
