import numpy as np
import pandas as pd
import abc

from src import SHIP_LENS, COLS, ROWS, BOARD_SIZE
from src.board import SquareState



def all_possible_ship_locations(_cache={}):
    """
    A dataframe of all valid ship placements. Caches results so multiple calls don't recompute the same data
    returns:
        list(ShipPlacement)
    """
    if "result" in _cache:
        placements = _cache["result"]
    else:
        lengths = pd.DataFrame({"length": SHIP_LENS})
        directions = pd.DataFrame({"is_vert": [0, 1]}) # vertical or horizontal
        # upper left column and row
        cols = pd.DataFrame({"col_start": range(len(COLS))})
        rows = pd.DataFrame({"row_start": range(len(COLS))})
        data = lengths.merge(directions, how="cross"
                ).merge(cols, how="cross"
                ).merge(rows, how="cross")
        # calculate lower right ship position
        data["col_end"] = data["col_start"] + ((1-data["is_vert"]) * data["length"])
        data["row_end"] = data["row_start"] + (data["is_vert"] * data["length"])
        # filter ships that fall outside the board
        data = data[data["col_end"] < BOARD_SIZE]
        data = data[data["row_end"] < BOARD_SIZE]
        # change columns from ints to letters
        data["col_start"] = data["col_start"].apply(lambda x: COLS[x])
        data["col_end"] = data["col_end"].apply(lambda x: COLS[x])
        # save to cache
        upperlefts = data[["col_start", "row_start"]].to_records(index=False)
        bottomrights = data[["col_end", "row_end"]].to_records(index=False)
        placements = zip(upperlefts, bottomrights)
        _cache["result"] = placements
    return [ShipPlacement(*p) for p in placements]


class ShipPlacement:

    def __init__(self, upperleft, bottomright):
        """
        args:
            upperleft, bottomright: tuples of form (column, row)
        """
        self.upperleft = upperleft
        self.bottomright = bottomright
        self.hits = 0
        self.length = 1 + (ord(bottomright[0]) - ord(upperleft[0])) + (bottomright[1] - upperleft[1])
    
    def is_sunk(self):
        return self.hits == self.length

    def __repr__(self):
        return "Ship, {} to {}".format(self.upperleft, self.bottomright)

    def __iter__(self):
        """
        allow unpacking:
        s = ShipPlacement(("A", 3), ("A", 5))
        "A":"A", 3:5 = s
        """
        return (slice(*x) for x in zip(self.upperleft, self.bottomright))

    def check_hit(self, col, row):
        """
        return whether this column and row are within a ship's extent
        args:
            loc: tuple(col, row)
        """
        hit = (self.upperleft <= (col, row) <= self.bottomright) and \
            (col == self.upperleft[0] or row == self.upperleft[1])
        if hit:
            self.hits += 1
        return hit, self.is_sunk()



class PlacementStrategy(abc.ABC):
    """
    base class for placement strategies
    """

    def __init__(self):
        self.ships = self.generate_placements()
    
    @abc.abstractmethod
    def generate_placements(self):
        ...

    def check_hit(self, col, row):
        """
        returns:
            status: SquareState
            sunk: bool
            length: length of sunk ship, only applicable if sunk
        """
        for i,ship in enumerate(self.ships):
            hit, sunk = ship.check_hit(col, row)
            if sunk:
                self.ships.pop(i)
                return SquareState.SHIP, True, ship.length
            if hit:
                return SquareState.SHIP, False, None
        return SquareState.EMPTY, False, None

