from dataclasses import dataclass
from enum import Enum

class Outcome(str, Enum):
    WIN = "wins"
    LOSS = "losses"
    DRAW = "draws"

class Color(str, Enum):
    WHITE = "white"
    BLACK = "black"
    
@dataclass
class OpeningStat:
    eco: str
    name: str
    total: int
    wins: int
    losses: int
    draws: int
    
    @property
    def winrate(self):
        return round((self.wins / self.total) * 100) if self.total > 0 else 0
    
@dataclass
class OpeningAccumulator:
    name: str = "Unknown opening"
    wins: int = 0
    losses: int = 0
    draws: int = 0