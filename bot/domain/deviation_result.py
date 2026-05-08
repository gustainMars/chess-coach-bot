from dataclasses import dataclass


@dataclass
class DeviationResult:
    move_number: int
    user_move: str
    expected_move: str
    fen: str
