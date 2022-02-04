import numpy as np
import pandas as pd
import abc

from src import BOARD_SIZE, ROWS, COLS


class SquareState:
    UNKNOWN = "."
    EMPTY = "-" # aka miss
    SHIP = "X" # aka hit

    def __init__(self):
        raise NotImplementedError("You shouldn't be initializing an instance of this. Just use SquareState.EMPTY instead of SquareState().EMPTY, for example")


class Board(abc.ABC):
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
            flat: whether to store the board as a flattened series (better format for some Strategies to work with)
        """
        self.isflat = flat
        self.data = pd.DataFrame(np.full((BOARD_SIZE, BOARD_SIZE), initial_val), columns=COLS)
        if flat:
            self.data = self.data.stack()

    def __repr__(self):
        return str(self.data)

    def __getitem__(self, index):
        col, row = index
        return self.data.loc[row, col]
    
    def __setitem__(self, index, val):
        col, row = index
        self.data.loc[row, col] = val

    def get_data(self):
        """
        get data as the standard square board
        """
        if self.isflat:
            return self.data.unstack()
        else:
            return self.data
