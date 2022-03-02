import numpy as np
import pandas as pd
import abc

import matplotlib.pyplot as plt

from src import BOARD_SIZE, ROWS, COLS
from src.utils import plot_board

class SquareState:
    UNKNOWN = -1
    EMPTY = 0 # aka miss
    SHIP = 1 # aka hit

    MAP_TO_STR = {
        UNKNOWN: ".",
        EMPTY: "-",
        SHIP: "X",
    }

    MAP_TO_NAME = {
        UNKNOWN: "unknown",
        EMPTY: "empty",
        SHIP: "hit",
    }

    def __init__(self):
        raise NotImplementedError("You shouldn't be initializing an instance of this. Just use SquareState.EMPTY instead of SquareState().EMPTY, for example")


class Board():
    """
    class for board keeping track of shots
    indexing must be (column, row) order
    columns are capital letters: A,B,C...
    rows are 0-based number indexing: 0,1,2...
    """

    def __init__(self, initial_val, flat=False):
        """
        args:
            initial_val
            flat: whether to store the board as a flattened series (more efficient lookups)
        """
        self.data = pd.DataFrame(np.full((BOARD_SIZE, BOARD_SIZE), initial_val), columns=COLS)
        self.isflat = flat
        if flat:
            self.data = self.data.stack()

    def __repr__(self):
        return str(self.get_printable())

    def __getitem__(self, index):
        col, row = index
        return self.data.loc[row, col]
    
    def __setitem__(self, index, val):
        col, row = index
        self.data.loc[row, col] = val

    def get_data(self, flat=False):
        """
        get data as the standard square board, or flattened if flat=True
        """
        if self.isflat == flat:
            return self.data
        elif self.isflat:
            return self.data.unstack()
        else:
            return self.data.stack()

    def get_printable(self):
        """
        get data as the standard square board with strings as elems instead of ints
        """
        if self.isflat:
            data = self.data
        else:
            data = self.data.stack()
        data = data.map(SquareState.MAP_TO_STR)
        return data.unstack()

    def plot(self, ax=None):
        plot_board(self, ax=ax)
        plt.show()


