export const MESSAGES = {
  en: {
    title:           '📖 Blunder Review',
    allOpenings:     'All openings',
    loading:         'Loading…',
    instruction:     'Pick your move — tap a piece, then tap the destination',
    selectPiece:     (sq) => `Selected ${sq} — tap destination`,
    correct:         (move) => `✅ Correct! The best move was ${move}.`,
    wrong:           (played, expected) =>
      `❌ You played ${played}, but the best move was ${expected}.`,
    noBlunders:      'No blunders yet. Run /analyze first to analyse your games.',
    deckReset:       '🎉 All blunders reviewed! Starting over.',
    nextBtn:         'Next →',
    connectionError: '⚠️ Connection error. Tap Next to retry.',
  },
  pt: {
    title:           '📖 Revisão de Blunders',
    allOpenings:     'Todas as aberturas',
    loading:         'Carregando…',
    instruction:     'Faça o seu lance — toque numa peça e depois no destino',
    selectPiece:     (sq) => `Selecionado ${sq} — toque no destino`,
    correct:         (move) => `✅ Correto! O melhor lance foi ${move}.`,
    wrong:           (played, expected) =>
      `❌ Você jogou ${played}, mas o melhor lance era ${expected}.`,
    noBlunders:      'Nenhum blunder registrado. Use /analyze primeiro.',
    deckReset:       '🎉 Todos os blunders revisados! Recomeçando.',
    nextBtn:         'Próximo →',
    connectionError: '⚠️ Erro de conexão. Toque em Próximo para tentar de novo.',
  },
};
