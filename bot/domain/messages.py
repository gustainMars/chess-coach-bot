class Messages:
    SEARCHING_USER = "Searching for user *{username}*..."
    USER_NOT_FOUND = "User *{username}* not found on chess.com"
    NO_GAMES_FOUND = "No matches found for the user *{username}*"
    ANALYZING_GAMES = "⚙️ Analyzing {total} games..."
    DEBUG_NO_GAMES = "No matches found"
    DEBUG_INVALID_MOVE = "parse_moves: invalid token '{token}', stopping"
    ANALYZE_USAGE = (
        "Use like this: /analyze <username>\n"
        "Example: /analyze magnuscarlsen"
    )
    DEBUG_USAGE = "Use: /debug <username>"

    REPORT_HEADER = (
        "♟️ *Openings Analysis — {username}*\n_{total} matches in the last 30 days_\n\n"
    )
    PLAYING_WHITE = "*Playing as White:*\n"
    PLAYING_BLACK = "\n*Playing as Black:*\n"
    NO_WHITE_DATA = "_No data for white openings_\n"
    NO_BLACK_DATA = "_No data for black openings_\n"
    STUDY_SUGGESTION = (
        "\n📚 *Study suggestion:*\n"
        "Focus on improving the opening *{name}* - with a winrate of {winrate}%.\n"
        "Use /study to get personalized study materials for this opening.\n"
    )
    RATING_PROGRESS = (
        "\n🎉 *Rating up!* Rapid went from {prev} → {current} since last month."
        " Keep it up!\n"
    )

    STUDY_NO_BLUNDERS = (
        "You have no recorded blunders yet.\n"
        "Run /analyze <username> first to analyze your games."
    )
    STUDY_QUESTION = (
        "♟️ *{opening_name}* — {quality}\n\nWhat is the best move in this position?"
    )
    STUDY_CORRECT = (
        "✅ *Correct!* The best move was *{expected}*.\n\nUse /study for the next card."
    )
    STUDY_WRONG = (
        "❌ You played *{user_move}*, but the best move was *{expected}*.\n\n"
        "Use /study for the next card."
    )
    STUDY_INVALID_MOVE = (
        "⚠️ I couldn't understand that move. "
        "Reply with SAN (e.g. *Nf3*, *O-O*) or UCI format (e.g. *g1f3*)."
    )
    STUDY_DECK_RESET = (
        "🎉 You've reviewed all your blunders! Starting the deck over.\n\n"
    )

    ATTACK_QUESTION = (
        "⚔️ *Attack Training*\n\n"
        "Tap *all pieces that can be captured* in this position "
        "(regardless of whether the capture is good or not).\n"
        "Press *Check ✅* when done."
    )
    ATTACK_CORRECT = (
        "✅ *Correct!* All {count} capturable piece(s) identified.\n\n"
        "Use /attack for a new position."
    )
    ATTACK_WRONG_MISSED = "⚠️ Not quite — you missed: *{missed}*. Try again!"
    ATTACK_WRONG_EXTRA = "⚠️ Not quite — *{extra}* cannot be captured. Try again!"
    ATTACK_WRONG_BOTH = "⚠️ Missed: *{missed}* | Wrongly selected: *{extra}*. Try again!"
