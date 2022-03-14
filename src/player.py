from src.board import Board, SquareState
from src.strategy import Strategy
from src.placements import PlacementStrategy
from src import SHIP_LENS, benchmark


class Player:
    """
    args:
        strategy, placement: type Strategy, PlacementStrategy
    """

    def __init__(self, strategy: Strategy, placements: PlacementStrategy, name):
        assert isinstance(strategy, Strategy)
        assert isinstance(placements, PlacementStrategy)
        self.placements = placements
        self.strategy = strategy
        self.placements.reinitialize()
        self.strategy.reinitialize()

        self.opponents_sunk = []
        self.name = name
        # board to keep track of our shots
        self.shots = Board(SquareState.UNKNOWN, flat=(not self.strategy.require_square_board))
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
        col, row = self.strategy.choose_shot(self.shots, self.opponents_sunk, name=self.name)
        result, sunk, name = opponent.placements.check_hit(col, row)
        if sunk:
            self.opponents_sunk.append(name)
        # add shot to our board
        self.shots[col, row] = result
        self.strategy.handle_result(col=col, row=row, board=self.shots, result=result, sunk=sunk, name=name)
        self.turns += 1
