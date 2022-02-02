from src.board import ShotBoard
from src.strategy import Strategy
from src.placements import PlacementStrategy
from src import SHIP_LENS


class Player:

    def __init__(self, strategy: Strategy, placements: PlacementStrategy):
        self.placements = placements
        self.strategy = strategy
        # where this player has shot at the opponent
        self.shots = ShotBoard()
        self.opponents_sunk = []

    def has_won(self):
        return len(self.opponents_sunk) == len(SHIP_LENS)

    def __repr__(self):
        result = "Placements:\n"
        result += str(self.placements)
        result += "\nShots:\n"
        result += str(self.shots)
        return result
    
    def take_turn_against(self, opponent):
        """
        shoot at opponent
        """
        col, row = self.strategy.choose_shot(self.shots, self.opponents_sunk)
        result, sunk, length = opponent.placements.check_hit(col, row)
        if sunk:
            self.opponents_sunk.append(length)
        self.shots[col, row] = result
