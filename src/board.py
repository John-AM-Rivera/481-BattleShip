import numpy as np
import pandas as pd
import abc

from src import BOARD_SIZE, ROWS, COLS


class SquareState:
    UNKNOWN = -1
    EMPTY = 0 # aka miss
    SHIP = 1 # aka hit

    MAP_TO_STR = {
        UNKNOWN: ".",
        EMPTY: "-",
        SHIP: "X",
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

    def get_printable(self):
        """
        get data as the standard square board
        """
        if self.isflat:
            data = self.data
        else:
            data = self.data.stack()
        data = data.map(SquareState.MAP_TO_STR)
        return data.unstack()
