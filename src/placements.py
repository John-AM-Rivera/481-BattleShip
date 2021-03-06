import abc
import random
import itertools

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src import BOARD_SIZE, COLS, ROWS, SHIP_LENS
from src.board import Board, SquareState
from src.utils import plot_grid_data, get_all_valid_squares

"""
Base classes & functions
"""

def all_possible_ship_locations(_cache={}):
    """
    A list of all valid ship placements. Caches results so multiple calls don't recompute the same data
    returns:
        set(ShipPlacement)
    """
    if "result" in _cache:
        placements = _cache["result"]
    else:
        names = pd.DataFrame({"name": list(SHIP_LENS.keys())})
        directions = pd.DataFrame({"is_vert": [0, 1]}) # vertical or horizontal
        cols = pd.DataFrame({"col_start": range(len(COLS))})
        rows = pd.DataFrame({"row_start": range(len(COLS))})
        # cartesian product of possible values
        data = names.merge(directions, how="cross"
                ).merge(cols, how="cross"
                ).merge(rows, how="cross")
        # convert name to length
        data["length"] = data["name"].apply(lambda x: SHIP_LENS[x]) 
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
        placements = data[["col_start", "row_start", "col_end", "row_end", "name"]].to_records(index=False)
        _cache["result"] = placements
    return {ShipPlacement(*p) for p in placements}


class ShipPlacement:
    """
    object representing the placement of a specific ship in a specific location
    """

    def __init__(self, col_start, row_start, col_end, row_end, name):
        self.col_start = col_start
        self.col_end = col_end
        self.row_start = row_start
        self.row_end = row_end
        self.name = name
        self.hits = 0
        self.length = 1 + (ord(col_end) - ord(col_start)) + (row_end - row_start)
        self._id_attrs = (self.name, self.col_start, self.col_end, self.row_start, self.row_end)
    
    def is_sunk(self):
        return self.hits == self.length

    def __repr__(self):
        return "{}({}{}-{}{})".format(self.name.capitalize(), self.col_start, self.row_start, self.col_end, self.row_end)

    def __eq__(self, other):
        if not isinstance(other, ShipPlacement):
            return False
        return self._id_attrs == other._id_attrs

    def __hash__(self):
        return hash(self._id_attrs)

    def __iter__(self):
        """
        allow unpacking:
        s = ShipPlacement(("A", 3), ("A", 5))
        slice("A":"A"), slice(3:5) = s
        """
        return iter((slice(self.col_start, self.col_end), slice(self.row_start, self.row_end)))

    def contains(self, col, row):
        """
        check whether a square is within this ship
        """
        return (self.col_start <= col <= self.col_end) and (self.row_start <= row <= self.row_end)

    def check_hit(self, col, row):
        """
        return whether this column and row are within a ship's extent
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

    def reinitialize(self):
        self.ships = self.generate_placements()
    
    def __repr__(self):
        return str(self.as_board())

    def __eq__(self, other):
        if not isinstance(other, PlacementStrategy):
            return False
        return self.ships == other.ships

    @abc.abstractmethod
    def generate_placements(self):
        """
        main method to override. Should return a list of 5 ship placements
        """
        ...

    def check_hit(self, col, row):
        """
        returns:
            status: SquareState
            sunk: bool
            name: name of sunk ship, only applicable if sunk
        """
        for i,ship in enumerate(self.ships):
            hit, sunk = ship.check_hit(col, row)
            if sunk:
                self.ships.pop(i)
                return SquareState.SHIP, True, ship.name
            if hit:
                return SquareState.SHIP, False, None
        return SquareState.EMPTY, False, None

    def as_board(self, flat=False):
        board = Board(SquareState.EMPTY, flat=flat)
        for s in self.ships:
            board[s] = SquareState.SHIP
        return board

    def show_distribution(self, n_samples):
        """
        simulate N placements and return the board representing the probability
        distribution of ship placements
        """
        total = None
        for _ in range(n_samples):
            self.reinitialize()
            df = self.as_board(flat=True).data
            if total is None:
                total = df
            else:
                total += df
        final = total.unstack() / n_samples
        plot_grid_data(final, title=self.__class__.__name__ + f" distribution ({n_samples} samples)")
        plt.show()


class NoPlacements(PlacementStrategy):

    def generate_placements(self, *args, **kwargs):
        return []


"""
specific strats
"""


class RandomPlacement(PlacementStrategy):

    def generate_placements(self):
        possible = all_possible_ship_locations()
        selected = []
        for name in SHIP_LENS.keys():
            possible_subset = [x for x in possible if x.name == name]
            idx = np.random.randint(len(possible_subset))
            ship = possible_subset[idx]
            selected.append(ship)
            possible = [x for x in possible if not x.overlaps(ship)]
        return selected


class EvenPlacement(PlacementStrategy):

    def generate_placements(self):
        possible = all_possible_ship_locations()
        squares = get_all_valid_squares()
        random.shuffle(squares)
        selected = []
        for name in SHIP_LENS.keys():
            # select a random square
            for square in squares:
                # choose ship containing that square
                possible_subset = [
                    x for x in possible if x.name == name and x.contains(*square)
                ]
                if len(possible_subset):
                    break
            else:
                raise RuntimeError("Something is wrong...")
            ship = random.choice(possible_subset)
            selected.append(ship)
            # invalidate invalid squares and ships
            squares = [x for x in squares if not ship.contains(*x)]
            possible = [x for x in possible if not x.overlaps(ship)]
        return selected

class CornerPlacement(PlacementStrategy):

    def get_corner_squares(self):
        corner_cols = COLS[:2] + COLS[-2:]
        corner_rows = ROWS[:2] + ROWS[-2:]
        return list(itertools.product(corner_cols, corner_rows))

    def generate_placements(self):
        possible = all_possible_ship_locations()
        squares = self.get_corner_squares()
        random.shuffle(squares)
        selected = []
        for name in SHIP_LENS.keys():
            # select a random square
            for square in squares:
                # choose ship containing that square
                possible_subset = [
                    x for x in possible if x.name == name and x.contains(*square)
                ]
                if len(possible_subset):
                    break
            else:
                raise RuntimeError("Something is wrong...")
            ship = random.choice(possible_subset)
            selected.append(ship)
            # invalidate invalid squares and ships
            squares = [x for x in squares if not ship.contains(*x)]
            possible = [x for x in possible if not x.overlaps(ship)]
        return selected


class TestPlacement_1(PlacementStrategy):

    def generate_placements(self):
        testBoard = [ShipPlacement('J', 8, 'J', 9, "patrol boat"), \
                     ShipPlacement('B', 5, 'B', 7, "destroyer"), \
                     ShipPlacement('C', 2, 'E', 2, "submarine"), \
                     ShipPlacement('D', 7, 'G', 7, "battleship"), \
                     ShipPlacement('G', 2, 'G', 6, "carrier")]
        return testBoard

class TestPlacement_2(PlacementStrategy):

    def generate_placements(self):
        testBoard = [ShipPlacement('J', 8, 'J', 9, "patrolboat"), \
                     ShipPlacement('H', 7, 'J', 7, "destroyer"), \
                     ShipPlacement('C', 2, 'E', 2, "submarine"), \
                     ShipPlacement('B', 5, 'B', 8, "battleship"), \
                     ShipPlacement('G', 2, 'G', 6, "carrier")]
        return testBoard

class adjacentPlacement_1(PlacementStrategy):

    def generate_placements(self):
        testBoard = [ShipPlacement('J', 8, 'J', 9, "patrolboat"), \
                     ShipPlacement('B', 5, 'B', 7, "destroyer"), \
                     ShipPlacement('C', 2, 'E', 2, "submarine"), \
                     ShipPlacement('D', 7, 'G', 7, "battleship"), \
                     ShipPlacement('E', 6, 'I', 6, "carrier")]
        return testBoard
