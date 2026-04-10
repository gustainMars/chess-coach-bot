import re

def _opening_name_from_url(eco_url: str) -> str:
    slug = eco_url.split("/openings/")[-1]
    parts = slug.split("-")
    clean_parts = []
    for part in parts:
        if part and part[0].isdigit():
            break
        clean_parts.append(part)
    return " ".join(clean_parts).replace("s ", "'s ", 1)

def extract_opening_from(pgn_str: str) -> dict:
    """Extracts relevant information from a PGN match."""
    
    def get_tag(tag):
        match = re.search(rf'\[{tag} "(.+?)"\]', pgn_str)
        return match.group(1) if match else "?"
    
    eco = get_tag("ECO")
    eco_url = get_tag("ECOUrl")
    
    opening_name = "Unknown opening"
    if eco_url and eco_url != "?":
        opening_name = _opening_name_from_url(eco_url)
        
    return {      
        "opening_eco": eco,
        "opening_name": opening_name,
    }