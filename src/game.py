import pandas as pd

from src import BOARD_SIZE, ROWS, COLS
from src.player import Player


class Game:
    """
    player one always goes first
    """

    def __init__(self, strategy1, strategy2, placement1, placement2):
        self.p1 = Player(strategy1, placement1, name="P1")
        self.p2 = Player(strategy2, placement2, name="P2")
        self.divider = pd.DataFrame({"|": ROWS})
        self.turns = 0
    
    def play(self, show=True):
        """
        returns:
            1|2: player who won
            turns: int
        """
        while True:
            won = self.one_turn(self.p1, self.p2, show=show)
            if won:
                self.show_boards()
                return 1, self.turns
            won = self.one_turn(self.p2, self.p1, show=show)
            if won:
                self.show_boards()
                return 2, self.turns
    
    def one_turn(self, playerA, playerB, show):
        if show:
            self.show_boards()
        playerA.take_turn_against(playerB)
        self.turns += 1
        return playerA.has_won()

    def show_boards(self):
        print("Player ones's shots:          Player two's shots:")
        print(pd.concat((self.p1.shots.data, self.divider, self.p2.shots.data), axis=1))
