import abc
import random

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from src import ROWS, COLS
from src.board import SquareState, Board
from src.placements import all_possible_ship_locations
from src.utils import get_all_valid_squares, plot_board, plot_grid_data


class ShipOrientation:
    UNKNOWN = -1
    HORIZONTAL = 0
    VERTICAL = 1

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

    def handle_simulated_shot(self, col, row):
        """
        handle result chosen by another method (ie, not this classes's own choose_shot method)
        """
        raise NotImplementedError()

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
        self.valid_squares = set(get_all_valid_squares())

    def choose_shot(self, board, opponents_sunk, name=None):
        # select random element from set
        return self.valid_squares.pop()


# Idea:
# generate some number of possible board placements
# shoot based on one of the boards based on some heuristic that makes it the most desirable
#   Based on result on real board, eliminate simulated boards that cannot be the real board
# once we run out of simulated boards, generate new set of boards that comply with current state of opponent's board
# continue shooting and generating boards until all opponent ships are shot down.

class SearchHuntStrategy(Strategy):
    # Bug: strategy seems to be retrying squares that have been tried before

    def __init__(self):
        self.valid_squares = set(get_all_valid_squares())
        self.possible_ship_squares = []
        self.current_ship_hits = []

    # opponents_sunk: list of names of ships that have been sunk
    def choose_shot(self, board, opponents_sunk, name=None):
        while len(self.possible_ship_squares) > 0:
            col, row = self.possible_ship_squares.pop()
            if (col,row) in self.valid_squares:
                self.valid_squares.remove((col,row))
                return col, row

        col, row = self.valid_squares.pop()
        return col, row

    def handle_result(self, col, row, result, sunk, name):
        if result == SquareState.SHIP:
            if sunk:
                self.possible_ship_squares = []
                self.current_ship_hits = []
            else:
                self.current_ship_hits.append((col,row))

                # populate possible_ship_squares with possible positions for the rest of the ship
                # if first random hit (psq empty) all four adjacent squares should be added to psq
                if len(self.possible_ship_squares) == 0:
                    self.possible_ship_squares.append((chr(ord(col)-1),row)) 
                    self.possible_ship_squares.append((chr(ord(col)+1),row))
                    self.possible_ship_squares.append((col,row-1))
                    self.possible_ship_squares.append((col,row+1))
                else:
                    # remove any squares in psq that are not in the same row or column as hit
                    for square in self.possible_ship_squares.copy():
                        if square[0] != col and square[1] != row:
                            self.possible_ship_squares.remove(square)

                    # add next possible shot based on current hit
                    if self.current_ship_hits[0][0] == col: # ship is vertical
                        # opposite direction to previous shot
                        step = (row - self.current_ship_hits[0][1]) // (row - self.current_ship_hits[0][1])
                        self.possible_ship_squares.append((col, row+step))
                    else:   # ship is horizontal
                        step = (ord(col) - ord(self.current_ship_hits[0][0])) // (ord(col) - ord(self.current_ship_hits[0][0]))
                        self.possible_ship_squares.append((chr(ord(col)+step), row))


class EliminationStrategy(Strategy):

    def __init__(self):
        self.possible_ships = all_possible_ship_locations()
        self.valid_squares = get_all_valid_squares()

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


class EliminationStrategyV2(Strategy):
    """
    faster version of the above
    """
    
    def __init__(self):
        possible_ships = all_possible_ship_locations()
        # dict( (col, row) => set(ShipPlacement) )
        self.squares_to_ships = {
            square: {ship for ship in possible_ships if ship.contains(*square)} for square in get_all_valid_squares()
        }


    def choose_shot(self, board, opponents_sunk, name=None):
        # shoot at place with the highest number of possible ship placements
        # self.show_distribution(board)
        best_square = max(self.squares_to_ships,
                            key=lambda x: len(self.squares_to_ships[x]) )
        return best_square
    
    def handle_result(self, col, row, result, sunk, name):
        # invalidate ships on a miss
        if result == SquareState.EMPTY:
            # get ships that are invalidated
            ships_to_remove = self.squares_to_ships[(col, row)]
            # remove invalid ships
            for square,shipset in self.squares_to_ships.items():
                shipset = {x for x in shipset if x not in ships_to_remove}
                self.squares_to_ships[square] = shipset

        # remove the invalidated square
        del self.squares_to_ships[(col, row)]
        # remove sunk ship possibilities
        if sunk:
            self.squares_to_ships = {
                square: {ship for ship in shipset if ship.name != name} for square,shipset in self.squares_to_ships.items()
            }

    def show_distribution(self, board):
        maxval = max([len(x) for x in self.squares_to_ships.values()])
        data = pd.Series(self.squares_to_ships.values(), index=self.squares_to_ships.keys())
        data = data.apply(lambda x: len(x))
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 5))
        final = data.unstack().T
        plot_grid_data(final, ax1, title="Possible Ships Count", vmin=0, vmax=34)
        board.plot(ax2)
        plt.show()
