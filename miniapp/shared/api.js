/**
 * Fetch the list of openings the user has blunders in.
 *
 * @param {object} opts
 * @param {string} opts.apiUrl   - base URL (no trailing slash)
 * @param {string} opts.initData - Telegram.WebApp.initData for HMAC auth
 * @returns {Promise<Array<{eco: string, name: string, blunder_count: number}>>}
 */
export async function getStudyOpenings({ apiUrl, initData }) {
  const endpoint = apiUrl
    ? `${apiUrl}/miniapp/study/openings`
    : '/miniapp/study/openings';

  const resp = await fetch(endpoint, {
    method: 'GET',
    headers: { 'X-Telegram-Init-Data': initData },
  });

  if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
  return resp.json();
}

/**
 * Fetch the next unreviewed blunder card for the user.
 *
 * @param {object} opts
 * @param {string} opts.apiUrl   - base URL (no trailing slash)
 * @param {string} opts.initData - Telegram.WebApp.initData for HMAC auth
 * @param {string} [opts.eco]    - optional ECO filter (e.g. 'B20')
 * @returns {Promise<{
 *   blunder_id: number|null, fen: string, opening_name: string,
 *   opening_eco: string, quality: string, reset: boolean, expected_uci: string
 * }>}
 */
export async function getStudyCard({ apiUrl, initData, eco = '' }) {
  const base = apiUrl
    ? `${apiUrl}/miniapp/study/card`
    : '/miniapp/study/card';
  const url = eco ? `${base}?eco=${encodeURIComponent(eco)}` : base;

  const resp = await fetch(url, {
    method: 'GET',
    headers: { 'X-Telegram-Init-Data': initData },
  });

  if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
  return resp.json();
}

/**
 * Submit the user's move answer for a blunder card.
 *
 * @param {object} opts
 * @param {string} opts.apiUrl    - base URL (no trailing slash)
 * @param {number} opts.blunderId - blunder_id received from getStudyCard
 * @param {string} opts.move      - move in UCI format (e.g. 'e2e4')
 * @param {string} opts.initData  - Telegram.WebApp.initData for HMAC auth
 * @returns {Promise<{correct: boolean, expected_move: string, expected_uci: string}>}
 */
export async function submitStudyAnswer({ apiUrl, blunderId, move, initData }) {
  const endpoint = apiUrl
    ? `${apiUrl}/miniapp/study/answer`
    : '/miniapp/study/answer';

  const resp = await fetch(endpoint, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Telegram-Init-Data': initData,
    },
    body: JSON.stringify({ blunder_id: blunderId, move }),
  });

  if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
  return resp.json();
}

/**
 * Fetch a new attack training position from the backend.
 *
 * @param {object} opts
 * @param {string} opts.apiUrl   - base URL (no trailing slash)
 * @param {string} opts.initData - Telegram.WebApp.initData for HMAC auth
 * @returns {Promise<{ fen: string }>}
 */
export async function getPosition({ apiUrl, initData }) {
  const endpoint = apiUrl
    ? `${apiUrl}/miniapp/attack/position`
    : '/miniapp/attack/position';

  const resp = await fetch(endpoint, {
    method: 'GET',
    headers: { 'X-Telegram-Init-Data': initData },
  });

  if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
  return resp.json();
}

/**
 * Fetch the list of ECO openings available for learning.
 *
 * @param {object} opts
 * @param {string} opts.apiUrl   - base URL (no trailing slash)
 * @param {string} opts.initData - Telegram.WebApp.initData for HMAC auth
 * @returns {Promise<Array<{eco: string, name: string, moves: string[], fens: string[]}>>}
 */
export async function getLearnOpenings({ apiUrl, initData }) {
  const endpoint = apiUrl
    ? `${apiUrl}/miniapp/learn/openings`
    : '/miniapp/learn/openings';

  const resp = await fetch(endpoint, {
    method: 'GET',
    headers: { 'X-Telegram-Init-Data': initData },
  });

  if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
  return resp.json();
}

/**
 * Fetch the top master moves for a given FEN position.
 *
 * @param {object} opts
 * @param {string} opts.apiUrl   - base URL (no trailing slash)
 * @param {string} opts.fen      - FEN string of the position
 * @param {string} opts.initData - Telegram.WebApp.initData for HMAC auth
 * @returns {Promise<Array<{uci: string, san: string}>>}
 */
export async function getLearnMoves({ apiUrl, fen, initData }) {
  const endpoint = apiUrl
    ? `${apiUrl}/miniapp/learn/moves`
    : '/miniapp/learn/moves';
  const url = `${endpoint}?fen=${encodeURIComponent(fen)}`;

  const resp = await fetch(url, {
    method: 'GET',
    headers: { 'X-Telegram-Init-Data': initData },
  });

  if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
  return resp.json();
}

/**
 * Submit the user's piece selection to the backend for validation.
 *
 * @param {object} opts
 * @param {string}   opts.apiUrl   - base URL (no trailing slash)
 * @param {string}   opts.fen      - current board FEN
 * @param {string[]} opts.selected - list of selected square names (e.g. ['e4', 'd5'])
 * @param {string}   opts.initData - Telegram.WebApp.initData for HMAC auth
 * @returns {Promise<{correct: boolean, missed: string[], extra: string[], capturable: string[]}>}
 */
export async function checkCaptures({ apiUrl, fen, selected, initData }) {
  const endpoint = apiUrl
    ? `${apiUrl}/miniapp/attack/check`
    : '/miniapp/attack/check';

  const resp = await fetch(endpoint, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Telegram-Init-Data': initData,
    },
    body: JSON.stringify({ fen, selected }),
  });

  if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
  return resp.json();
}
