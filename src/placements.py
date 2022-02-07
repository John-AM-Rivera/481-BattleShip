import numpy as np
import pandas as pd
import abc

from src import SHIP_LENS, COLS, ROWS, BOARD_SIZE
from src.board import SquareState, Board

"""
Base classes & functions
"""

def all_possible_ship_locations(_cache={}):
    """
    A list of all valid ship placements. Caches results so multiple calls don't recompute the same data
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
        data["col_end"] = data["col_start"] + ((1-data["is_vert"]) * (data["length"]-1))
        data["row_end"] = data["row_start"] + (data["is_vert"] * (data["length"]-1))
        # filter ships that fall outside the board
        data = data[data["col_end"] < BOARD_SIZE]
        data = data[data["row_end"] < BOARD_SIZE]
        # change columns from ints to letters
        data["col_start"] = data["col_start"].apply(lambda x: COLS[x])
        data["col_end"] = data["col_end"].apply(lambda x: COLS[x])
        # save to cache
        placements = data[["col_start", "row_start", "col_end", "row_end"]].to_records(index=False)
        _cache["result"] = placements
    return [ShipPlacement(*p) for p in placements]


class ShipPlacement:
    """
    object representing the placement of a specific ship in a specific location
    """

    def __init__(self, col_start, row_start, col_end, row_end):
        self.col_start = col_start
        self.col_end = col_end
        self.row_start = row_start
        self.row_end = row_end
        self.hits = 0
        self.length = 1 + (ord(col_end) - ord(col_start)) + (row_end - row_start)
    
    def is_sunk(self):
        return self.hits == self.length

    def __repr__(self):
        return "Ship, {}{} to {}{}".format(self.col_start, self.row_start, self.col_end, self.row_end)

    def __eq__(self, other):
        if not isinstance(other, ShipPlacement):
            return False
        return self.col_start == other.col_start and self.col_end == other.col_end and \
            self.row_start == other.row_start and self.row_end == other.row_end

    def __iter__(self):
        """
        allow unpacking:
        s = ShipPlacement(("A", 3), ("A", 5))
        slice("A":"A"), slice(3:5) = s
        """
        return iter((slice(self.col_start, self.row_start), slice(self.col_end, self.row_end)))

    def contains(self, col, row):
        """
        check whether a square is within this ship
        """
        return (self.col_start <= col <= self.col_end) and (self.row_start <= row <= self.row_end)

    def check_hit(self, col, row):
        """
        return whether this column and row are within a ship's extent
        args:
            loc: tuple(col, row)
        """
        hit = self.contains(col, row)
        if hit:
            self.hits += 1
        return hit, self.is_sunk()

    def overlaps(self, other):
        """
        checks if two ship placements overlap
        """
        return (self.col_end >= other.col_start) and (other.col_end >= self.col_start) \
            and (self.row_end >= other.row_start) and (other.row_end >= self.row_start)


class PlacementStrategy(abc.ABC):
    """
    base class for placement strategies
    """

    def __init__(self):
        self.ships = self.generate_placements()
    
    def __repr__(self):
        return str(self.as_board())

    def __eq__(self, other):
        if not isinstance(other, PlacementStrategy):
            return False
        return self.ships == other.ships

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

    def as_board(self):
        board = Board(SquareState.EMPTY)
        for s in self.ships:
            board[s] = SquareState.SHIP
        return board

"""
specific strats
"""


class RandomPlacement(PlacementStrategy):

    def generate_placements(self):
        possible = all_possible_ship_locations()
        selected = []
        for length in SHIP_LENS:
            possible_subset = [x for x in possible if x.length == length]
            # print(length, possible_subset)
            idx = np.random.randint(len(possible_subset))
            ship = possible_subset[idx]
            selected.append(ship)
            possible = [x for x in possible if not x.overlaps(ship)]
        return selected
