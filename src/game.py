import pandas as pd

from src import BOARD_SIZE, ROWS, COLS
from src.player import Player


class Game:
    """
    player one always goes first
    """

    def __init__(self, strategy1, strategy2, placement1, placement2):
        self.p1 = Player(strategy1, placement1)
        self.p2 = Player(strategy2, placement2)
        self.divider = pd.DataFrame({"|": ROWS})
        self.turns = 0
    
    def play(self, show=False):
        """
        returns:
            1|2: player who won
            turns: int
        """
        if show:
            print("Player one's placement:")
            print(self.p1.placements.as_board())
            print("Player two's placement:")
            print(self.p1.placements.as_board())
        while True:
            won = self.one_turn(self.p1, self.p2, show=show)
            if won:
                return 1, self.turns
            won = self.one_turn(self.p2, self.p1, show=show)
            if won:
                return 2, self.turns
    
    def one_turn(self, playerA, playerB, show):
        playerA.take_turn_against(playerB)
        if show:
            self.show_boards()
        self.turns += 1
        return playerA.has_won()

    def show_boards(self):
        print(pd.concat((self.p1.shots.data, self.divider, self.p2.shots.data), axis=1))
