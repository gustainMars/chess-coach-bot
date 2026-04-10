import csv

_openings = []

def load_openings(path: str = "data/eco.tsv"):
    """Loads the ECO opening database from the TSV file."""
    global _openings
    if _openings:
        return
    
    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            _openings.append({
                "eco": row["eco"],
                "name": row["name"],
                "pgn": row["pgn"],
                "uci": row.get("uci", ""),
            })

def find_opening(moves_pgn: str) -> dict:
    """
    Receives the moves in PGN format (e.g., "1. e4 e5 2. Nf3")
    Returns the most specific opening found.
    """
    load_openings()
    
    best_match = None
    best_length = 0
    
    moves_pgn = moves_pgn.strip()
    
    for opening in _openings:
        pgn = opening["pgn"].strip()
        if moves_pgn.startswith(pgn) or pgn in moves_pgn:
            if len(pgn) > best_length:
                best_match = opening
                best_length = len(pgn)
                
    return best_match or {"eco": "?", "name": "Unknown opening", "pgn": ""}