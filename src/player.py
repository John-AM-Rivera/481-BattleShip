from src.board import Board, SquareState
from src.strategy import Strategy
from src.placements import PlacementStrategy
from src import SHIP_LENS


class Player:

    def __init__(self, strategy: Strategy, placements: PlacementStrategy, name):
        self.placements = placements
        self.strategy = strategy
        self.opponents_sunk = []
        self.name = name
        # board to keep track of our shots
        self.shots = Board(SquareState.UNKNOWN)

    def has_won(self):
        return len(self.opponents_sunk) == len(SHIP_LENS)

    def __repr__(self):
        result = "Player " + self.name + "\n"
        result += "Placements:\n"
        result += str(self.placements.as_board())
        result += "\nShots:\n"
        result += str(self.shots)
        return result
    
    def take_turn_against(self, opponent):
        """
        shoot at opponent
        """
        col, row = self.strategy.choose_shot(self.shots, self.opponents_sunk, name=self.name)
        result, sunk, length = opponent.placements.check_hit(col, row)
        if sunk:
            self.opponents_sunk.append(length)
        self.shots[col, row] = result
