const SVG_NS = 'http://www.w3.org/2000/svg';

const LIGHT = '#F0D9B5';
const DARK  = '#B58863';

const PIECES_CDN =
  'https://cdn.jsdelivr.net/gh/lichess-org/lila@master/public/piece/cburnett/';
const PIECE_NAMES = {
  K: 'wK', Q: 'wQ', R: 'wR', B: 'wB', N: 'wN', P: 'wP',
  k: 'bK', q: 'bQ', r: 'bR', b: 'bB', n: 'bN', p: 'bP',
};

function svgEl(tag, attrs = {}) {
  const e = document.createElementNS(SVG_NS, tag);
  for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, v);
  return e;
}

/**
 * Parse a FEN string into a square→piece-char map and the active turn.
 *
 * @param {string} fen
 * @returns {{ board: Record<string, string>, turn: 'w'|'b' }}
 */
export function parseFen(fen) {
  const [placement, turn = 'w'] = fen.split(' ');
  const board = {};
  placement.split('/').forEach((row, ri) => {
    let fi = 0;
    for (const ch of row) {
      if (/\d/.test(ch)) { fi += +ch; }
      else { board[String.fromCharCode(97 + fi) + (8 - ri)] = ch; fi++; }
    }
  });
  return { board, turn };
}

/**
 * Build an interactive 8×8 SVG board.
 *
 * @param {SVGSVGElement} svgEl - the `<svg>` element to populate
 * @param {Record<string, string>} board - square→piece map from parseFen()
 * @param {object} opts
 * @param {boolean} opts.flipped - true when black is at bottom (black's turn)
 * @param {(sq: string) => void} opts.onSquareClick - called with square name on tap/click
 * @returns {{ squares: Record<string, {ring: SVGElement, highlight: SVGElement}>, files: string[], ranks: number[] }}
 */
export function buildBoard(svgEl, board, { flipped, onSquareClick }) {
  const files = flipped ? ['h','g','f','e','d','c','b','a'] : ['a','b','c','d','e','f','g','h'];
  const ranks = flipped ? [1,2,3,4,5,6,7,8] : [8,7,6,5,4,3,2,1];
  const squares = {};

  for (let row = 0; row < 8; row++) {
    for (let col = 0; col < 8; col++) {
      const sq    = files[col] + ranks[row];
      const light = (col + row) % 2 === 0;

      svgEl.appendChild(svgEl_rect(col, row, light ? LIGHT : DARK));

      const highlight = svgEl_rect(col, row, 'none');
      highlight.setAttribute('opacity', '0');
      highlight.setAttribute('pointer-events', 'none');
      svgEl.appendChild(highlight);

      const ring = svgEl_circle(col, row, 'none');
      ring.setAttribute('pointer-events', 'none');
      svgEl.appendChild(ring);

      if (board[sq]) {
        const img = svgEl_piece(col, row, board[sq]);
        if (img) svgEl.appendChild(img);
      }

      const hit = svgEl_rect(col, row, 'transparent');
      hit.dataset.sq = sq;
      hit.addEventListener('click', (e) => onSquareClick(e.currentTarget.dataset.sq));
      svgEl.appendChild(hit);

      squares[sq] = { ring, highlight };
    }
  }

  return { squares, files, ranks };
}

/**
 * Update SVG highlights to reflect selection and optional result overlays.
 *
 * @param {Record<string, {ring: SVGElement, highlight: SVGElement}>} squares
 * @param {Set<string>} selected
 * @param {Set<string>} missed  - squares to highlight yellow (answer was missed)
 * @param {Set<string>} extra   - squares to highlight red (wrongly selected)
 */
export function renderHighlights(squares, selected, missed, extra) {
  for (const [sq, { ring, highlight }] of Object.entries(squares)) {
    ring.setAttribute('stroke', 'none');
    highlight.setAttribute('opacity', '0');

    if (missed.has(sq)) {
      highlight.setAttribute('fill', '#f39c12');
      highlight.setAttribute('opacity', '0.40');
    } else if (extra.has(sq)) {
      highlight.setAttribute('fill', '#e74c3c');
      highlight.setAttribute('opacity', '0.40');
    } else if (selected.has(sq)) {
      ring.setAttribute('stroke', '#2ecc71');
    }
  }
}

// ── SVG primitive helpers (internal) ──────────────────────────────────────────

function svgEl_rect(col, row, fill) {
  return svgEl('rect', { x: col, y: row, width: 1, height: 1, fill });
}

function svgEl_circle(col, row, stroke) {
  return svgEl('circle', {
    cx: col + 0.5, cy: row + 0.5, r: 0.44,
    fill: 'none', stroke, 'stroke-width': 0.07,
  });
}

function svgEl_piece(col, row, pieceChar) {
  const name = PIECE_NAMES[pieceChar];
  if (!name) return null;
  return svgEl('image', {
    href: `${PIECES_CDN}${name}.svg`,
    x: col, y: row, width: 1, height: 1,
    'pointer-events': 'none',
  });
}
