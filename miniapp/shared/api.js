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
