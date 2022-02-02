import abc

import numpy as np
import pandas as pd

from src.board import SquareState


class Strategy(abc.ABC):
    """
    interface that other strategies should implement
    """

    @abc.abstractmethod
    def choose_shot(self, board, opponents_sunk, name=None):
        """
        args:
            board: board of known shots
            opponents_sunk: list(int), lengths of ships that have been sunk
            name: str
        returns:
            col: str (ex: "E")
            row: int (ex: 4)
        """
        ...

"""
concrete strategies
"""

class UserStrategy(Strategy):

    def choose_shot(self, board, opponents_sunk, name=None):
        square = input("{}: Enter a square to fire on (ex: E4): ".format(name))
        col, row = square
        row = int(row)
        return col, row


class RandomStrategy(Strategy):

    def choose_shot(self, board, opponents_sunk, name=None):
        flat_board = board.data.stack()
        valid_squares = flat_board[flat_board == SquareState.UNKNOWN].index.to_list()
        idx = np.random.randint(len(valid_squares))
        row, col = valid_squares[idx]
        return col, row

