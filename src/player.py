from src.board import Board, SquareState
from src.strategy import Strategy
from src.placements import PlacementStrategy
from src import SHIP_LENS, benchmark


class Player:
    """
    args:
        strategy, placement: classes of type Strategy, PlacementStrategy (not initialized instances, just the raw class)
    """

    def __init__(self, strategy: Strategy, placements: PlacementStrategy, name):
        self.placements = placements()
        self.strategy = strategy()
        self.opponents_sunk = []
        self.name = name
        # board to keep track of our shots
        self.shots = Board(SquareState.UNKNOWN, flat=self.strategy.require_flat_board)
        # number of turns
        self.turns = 0

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
        benchmark("shoot")
        col, row = self.strategy.choose_shot(self.shots, self.opponents_sunk, name=self.name)
        benchmark("shoot")
        benchmark("check hit")
        result, sunk, length = opponent.placements.check_hit(col, row)
        benchmark("check hit")
        if sunk:
            self.opponents_sunk.append(length)
        # add shot to our board
        self.shots[col, row] = result
        self.turns += 1
