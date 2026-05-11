import { getT }                                               from '../shared/i18n.js';
import { parseFen, buildBoard, renderHighlights,
         drawArrow, clearArrows }                             from '../shared/board.js';
import { getStudyOpenings, getStudyCard, submitStudyAnswer }  from '../shared/api.js';
import { MESSAGES }                                          from './messages.js';

// ── Telegram init ─────────────────────────────────────────────────────────────
const tg = window.Telegram?.WebApp;
if (tg) { tg.ready(); tg.expand(); }

// ── i18n ──────────────────────────────────────────────────────────────────────
const T = getT(MESSAGES);

// ── Config ────────────────────────────────────────────────────────────────────
const API_URL = (new URLSearchParams(location.search).get('api') || '').replace(/\/$/, '');

// ── Static UI text ────────────────────────────────────────────────────────────
document.getElementById('ui-title').textContent  = T.title;
document.getElementById('next-btn').textContent  = T.nextBtn;

// ── State ─────────────────────────────────────────────────────────────────────
let currentCard  = null;   // full card object from getStudyCard
let flipped      = false;
let squares      = {};
let fromSq       = null;   // first click (source square), null when not selected
let phase        = 'loading'; // 'loading' | 'selecting' | 'answered' | 'empty'

// ── DOM refs ──────────────────────────────────────────────────────────────────
const svgBoard     = document.getElementById('board');
const statusEl     = document.getElementById('status');
const nextBtn      = document.getElementById('next-btn');
const ecoFilter    = document.getElementById('eco-filter');
const openingInfo  = document.getElementById('opening-info');
const openingName  = document.getElementById('opening-name');
const qualityChip  = document.getElementById('quality-chip');
const fileLabelsEl = document.getElementById('file-labels');

// ── Opening filter ────────────────────────────────────────────────────────────
async function populateFilter() {
  try {
    const openings = await getStudyOpenings({ apiUrl: API_URL, initData: tg?.initData ?? '' });
    const allOpt   = document.createElement('option');
    allOpt.value       = '';
    allOpt.textContent = T.allOpenings;
    ecoFilter.appendChild(allOpt);

    for (const { eco, name, blunder_count } of openings) {
      const opt = document.createElement('option');
      opt.value       = eco;
      opt.textContent = `${eco} — ${name} (${blunder_count})`;
      ecoFilter.appendChild(opt);
    }
    ecoFilter.disabled = false;
  } catch {
    // filter stays disabled — user can still study all openings
  }
}

// ── Board ─────────────────────────────────────────────────────────────────────
function rebuildBoard(fen) {
  while (svgBoard.firstChild) svgBoard.removeChild(svgBoard.firstChild);

  const { board, turn } = parseFen(fen);
  flipped = turn === 'b';

  const { squares: newSquares, files } = buildBoard(svgBoard, board, {
    flipped,
    onSquareClick: handleSquareClick,
  });
  squares = newSquares;

  fileLabelsEl.innerHTML = '';
  files.forEach(f => {
    const span = document.createElement('span');
    span.textContent = f;
    fileLabelsEl.appendChild(span);
  });
}

// ── Load card ─────────────────────────────────────────────────────────────────
async function loadCard() {
  phase   = 'loading';
  fromSq  = null;
  nextBtn.hidden = true;
  openingInfo.hidden = true;
  statusEl.textContent = T.loading;
  statusEl.className   = '';
  clearArrows(svgBoard);

  const eco = ecoFilter.value;

  try {
    const card = await getStudyCard({ apiUrl: API_URL, initData: tg?.initData ?? '', eco });

    if (card.blunder_id === null) {
      phase = 'empty';
      statusEl.textContent = T.noBlunders;
      return;
    }

    currentCard = card;

    if (card.reset) {
      statusEl.textContent = T.deckReset;
      await new Promise(r => setTimeout(r, 1800));
    }

    rebuildBoard(card.fen);
    openingName.textContent = card.opening_name;
    qualityChip.textContent = card.quality;
    qualityChip.className   = card.quality === 'mistake' ? 'mistake' : '';
    openingInfo.hidden      = false;

    statusEl.textContent = T.instruction;
    statusEl.className   = '';
    phase = 'selecting';
  } catch {
    statusEl.textContent = T.connectionError;
    statusEl.className   = 'wrong';
    nextBtn.hidden       = false;
    phase = 'empty';
  }
}

// ── Square interaction ────────────────────────────────────────────────────────
function handleSquareClick(sq) {
  if (phase !== 'selecting') return;

  if (fromSq === null) {
    const { board } = parseFen(currentCard.fen);
    if (!board[sq]) return;            // clicked empty square — ignore

    fromSq = sq;
    renderHighlights(squares, new Set([sq]), new Set(), new Set());
    statusEl.textContent = T.selectPiece(sq);
  } else if (sq === fromSq) {
    fromSq = null;                     // deselect
    renderHighlights(squares, new Set(), new Set(), new Set());
    statusEl.textContent = T.instruction;
  } else {
    submitMove(fromSq, sq);
  }
}

// ── Submit ────────────────────────────────────────────────────────────────────
async function submitMove(from, to) {
  phase = 'loading';
  const move = from + to;

  try {
    const data = await submitStudyAnswer({
      apiUrl:    API_URL,
      blunderId: currentCard.blunder_id,
      move,
      initData:  tg?.initData ?? '',
    });

    clearArrows(svgBoard);
    renderHighlights(squares, new Set(), new Set(), new Set());

    if (data.correct) {
      statusEl.textContent = T.correct(data.expected_move);
      statusEl.className   = 'correct';
    } else {
      statusEl.textContent = T.wrong(move, data.expected_move);
      statusEl.className   = 'wrong';
      if (data.expected_uci && data.expected_uci.length >= 4) {
        const expFrom = data.expected_uci.slice(0, 2);
        const expTo   = data.expected_uci.slice(2, 4);
        drawArrow(svgBoard, expFrom, expTo, '#e74c3c', flipped);
      }
    }

    phase = 'answered';
    nextBtn.hidden = false;
  } catch {
    statusEl.textContent = T.connectionError;
    statusEl.className   = 'wrong';
    phase = 'answered';
    nextBtn.hidden = false;
  }
}

// ── Next button ───────────────────────────────────────────────────────────────
nextBtn.addEventListener('click', loadCard);

// ── Opening filter change ─────────────────────────────────────────────────────
ecoFilter.addEventListener('change', loadCard);

// ── Init ──────────────────────────────────────────────────────────────────────
await populateFilter();
await loadCard();
