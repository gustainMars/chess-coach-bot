/**
 * Detect the user's preferred language from the Telegram WebApp context,
 * falling back to the browser locale. Returns the first matching key found
 * in `availableKeys`, or 'en' if nothing matches.
 *
 * @param {string[]} availableKeys — keys present in the MESSAGES object of a screen
 * @returns {string}
 */
export function detectLang(availableKeys) {
  const tgLang = window.Telegram?.WebApp?.initDataUnsafe?.user?.language_code ?? '';
  const raw    = tgLang || navigator.language || 'en';
  const prefix = raw.split('-')[0].toLowerCase();
  return availableKeys.includes(prefix) ? prefix : 'en';
}

/**
 * Resolve the translation object for the current user.
 *
 * @param {Record<string, object>} messages — the MESSAGES object from a screen
 * @returns {object} — the resolved translation map
 */
export function getT(messages) {
  const lang = detectLang(Object.keys(messages));
  return messages[lang] ?? messages['en'];
}
