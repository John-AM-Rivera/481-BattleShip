import numpy as np
import pandas as pd
import abc

from src import BOARD_SIZE, ROWS, COLS


class SquareState:
    UNKNOWN = "."
    EMPTY = "-"
    SHIP = "X"


def col_to_str(col):
    if isinstance(col, int):
        return COLS[col]
    return col

class ShotBoard(abc.ABC):
    """
    class for board keeping track of shots
    indexing must be (column, row) order
    columns are capital letters: A,B,C...
    rows are 0-based number indexing: 0,1,2...
    """

    def __init__(self):
        self.data = pd.DataFrame(np.full((BOARD_SIZE, BOARD_SIZE), SquareState.UNKNOWN), columns=COLS)

    def __repr__(self):
        return str(self.data)

    def __getitem__(self, index):
        col, row = index
        return self.data.loc[row, col]
    
    def __setitem__(self, index, val):
        col, row = index
        self.data.loc[row, col] = val





