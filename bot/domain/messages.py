class Messages:
    SEARCHING_USER = "Searching for user *{username}*..."
    USER_NOT_FOUND = "User *{username}* not found on chess.com"
    NO_GAMES_FOUND = "No matches found for the user *{username}*"
    ANALYZING_GAMES = "⚙️ Analyzing {total} games..."
    DEBUG_NO_GAMES = "No matches found"
    DEBUG_INVALID_MOVE = "parse_moves: invalid token '{token}', stopping"
    ANALYZE_USAGE = "Use like this: /analyze <username>\nExample: /analyze magnuscarlsen"
    DEBUG_USAGE = "Use: /debug <username>"

    REPORT_HEADER = "♟️ *Openings Analysis — {username}*\n_{total} matches on the last month_\n\n"
    PLAYING_WHITE = "*Playing as White:*\n"
    PLAYING_BLACK = "\n*Playing as Black:*\n"
    NO_WHITE_DATA = "_No data for white openings_\n"
    NO_BLACK_DATA = "_No data for black openings_\n"
    STUDY_SUGGESTION = (
        "\n📚 *Study suggestion:*\n"
        "Focus on improving the opening *{name}* - with a winrate of {winrate}%.\n"
        "Use /study to get personalized study materials for this opening.\n"
    )
    RATING_PROGRESS = "\n🎉 *Rating up!* Rapid went from {prev} → {current} since last month. Keep it up!\n"

    STUDY_NO_BLUNDERS = (
        "You have no recorded blunders yet.\n"
        "Run /analyze <username> first to analyze your games."
    )
    STUDY_QUESTION = "♟️ *{opening_name}* — {quality}\n\nWhat is the best move in this position?"
    STUDY_CORRECT = "✅ *Correct!* The best move was *{expected}*.\n\nUse /study for the next card."
    STUDY_WRONG = "❌ You played *{user_move}*, but the best move was *{expected}*.\n\nUse /study for the next card."
    STUDY_INVALID_MOVE = (
        "⚠️ I couldn't understand that move. "
        "Reply with SAN (e.g. *Nf3*, *O-O*) or UCI format (e.g. *g1f3*)."
    )
    STUDY_DECK_RESET = "🎉 You've reviewed all your blunders! Starting the deck over.\n\n"
