import abc
import itertools
import random

import numpy as np
import pandas as pd

from src.board import SquareState, Board, ROWS, COLS
from src.placements import all_possible_ship_locations


class Strategy(abc.ABC):
    """
    interface that other strategies should implement
    """

    # attribute that determines whether the board should be flattened with
    # DataFrame.stack(). Flat has faster lookup than square, so should be preferred
    require_square_board = False

    @abc.abstractmethod
    def choose_shot(self, board, opponents_sunk, name=None):
        """
        args:
            board: board of known shots
            opponents_sunk: list(str), names of ships that have been sunk
            name: str, of this player
        returns:
            col: str (ex: "E")
            row: int (ex: 4)
        """
        ...

    def handle_result(self, col, row, result, sunk, name):
        """
        update internal state in response to the result of a shot. Default
        behavior is to do nothing
        args:
            col, row: shot we chose
            result: shot result
            sunk: bool
            name: name of sunk ship, only applicable if sunk
        """
        pass

class NoStrategy(Strategy):

    def choose_shot(self, *args, **kwargs):
        raise NotImplementedError()


"""
concrete strategies
"""

class UserStrategy(Strategy):

    def choose_shot(self, board, opponents_sunk, name=None):
        square = input("{}: Enter a square to fire on (ex: E4): ".format(name))
        col, row = square
        row = int(row)
        return col, row
    
    def handle_result(self, col, row, result, sunk, name):
        if result == SquareState.SHIP:
            if sunk:
                print(f"{col}{row}: You sunk my {name}!")
            else:
                print(f"{col}{row}: Hit!")
        else:
            print(f"{col}{row}: Miss.")


class RandomStrategy(Strategy):

    def __init__(self):
        self.valid_squares = set(itertools.product(COLS, ROWS))

    def choose_shot(self, board, opponents_sunk, name=None):
        # select random element from set
        return self.valid_squares.pop()


class EliminationStrategy(Strategy):

    def __init__(self):
        self.possible_ships = all_possible_ship_locations()
        self.valid_squares = list(itertools.product(COLS, ROWS))

    def choose_shot(self, board, opponents_sunk, name=None):
        ship_counts = [
            sum(ship.contains(*square) for ship in self.possible_ships) for square in self.valid_squares
        ]
        # shoot at place with the highest number of possible ship placements
        best_idx = np.argmax(ship_counts)
        return self.valid_squares.pop(best_idx)
    
    def handle_result(self, col, row, result, sunk, name):
        # invalidate ships on a miss
        if result == SquareState.EMPTY:
            self.possible_ships = {ship for ship in self.possible_ships if not ship.contains(col, row)}
        # remove sunk ship possibilities
        if sunk:
            self.possible_ships = {ship for ship in self.possible_ships if not ship.name == name}

