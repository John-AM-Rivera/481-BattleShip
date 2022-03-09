import abc
import random

import numpy as np
import pandas as pd
from pygments import highlight
from src import BOTTOM_3_BOARD

from src import ROWS, COLS, SHIP_LENS
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

    # attribute that deter8mines whether the board should be flattened with
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

    def __init__(self):
        self.set_squares = BOTTOM_3_BOARD.copy()
        # print(self.set_squares)
        self.moves = 0

    def choose_shot(self, board, opponents_sunk, name=None):
        if len(self.set_squares) > 0:
            return self.create_Test_Condition()
        square = input("{}: Enter a square to fire on (ex: E4): ".format(name))
        # print(all_possible_ship_locations())
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

    def create_Test_Condition(self):
        location = self.set_squares.pop()
        self.moves += 1
        return location


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
    # Bug: does not account for adjacent ships

    def __init__(self):
        self.possible_ships = all_possible_ship_locations()
        self.valid_squares = list(itertools.product(COLS, ROWS))
        self.possible_ship_squares = []
        self.current_ship_hits = []

    # opponents_sunk: list of names of ships that have been sunk
    def choose_shot(self, board, opponents_sunk, name=None):
        while len(self.possible_ship_squares) > 0:
            col, row = self.possible_ship_squares.pop()
            if (col,row) in self.valid_squares:
                self.valid_squares.remove((col,row))
                return col, row

        ship_counts = [
            sum(ship.contains(*square) for ship in self.possible_ships) for square in self.valid_squares
        ]
        # shoot at place with the highest number of possible ship placements
        best_idx = np.argmax(ship_counts)
        return self.valid_squares.pop(best_idx)

    def handle_result(self, col, row, result, sunk, name):
        if result == SquareState.SHIP:
            if sunk:
                self.possible_ship_squares = []
                self.current_ship_hits = []
                self.possible_ships = {ship for ship in self.possible_ships if not ship.name == name}
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
        elif result == SquareState.EMPTY:
            self.possible_ships = {ship for ship in self.possible_ships if not ship.contains(col, row)}


# Uses EliminationStrategyV2
class SearchHuntStrategyV2(Strategy):
    # Bug: does not account for adjacent ships

    def __init__(self):
        possible_ships = all_possible_ship_locations()
        # dict( (col, row) => set(ShipPlacement) )
        self.squares_to_ships = {
            square: {ship for ship in possible_ships if ship.contains(*square)} for square in get_all_valid_squares()
        }
        self.possible_ship_squares = []
        self.current_ship_hits = []

    # opponents_sunk: list of names of ships that have been sunk
    def choose_shot(self, board, opponents_sunk, name=None):
        while len(self.possible_ship_squares) > 0:
            col, row = self.possible_ship_squares.pop()
            if (col,row) in self.squares_to_ships:
                return col, row

        # shoot at place with the highest number of possible ship placements
        # self.show_distribution(board)
        best_square = max(self.squares_to_ships,
                            key=lambda x: len(self.squares_to_ships[x]) )
        return best_square

    def handle_result(self, col, row, result, sunk, name):
        if result == SquareState.SHIP:
            if sunk:
                self.possible_ship_squares = []
                self.current_ship_hits = []
                self.squares_to_ships = {
                    square: {ship for ship in shipset if ship.name != name} for square,shipset in self.squares_to_ships.items()
                }
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
        # invalidate ships on a miss
        elif result == SquareState.EMPTY:
            # get ships that are invalidated
            ships_to_remove = self.squares_to_ships[(col, row)]
            # remove invalid ships
            for square,shipset in self.squares_to_ships.items():
                shipset = {x for x in shipset if x not in ships_to_remove}
                self.squares_to_ships[square] = shipset

        # remove the invalidated square
        del self.squares_to_ships[(col, row)]


# Accounts for adjacent ships
class SearchHuntStrategyV3(Strategy):

    def __init__(self):
        possible_ships = all_possible_ship_locations()
        self.squares_to_ships = {
            square: {ship for ship in possible_ships if ship.contains(*square)} for square in get_all_valid_squares()
        }
        self.possible_ship_squares = []
        self.current_ship_hits = []

    # opponents_sunk: list of names of ships that have been sunk
    def choose_shot(self, board, opponents_sunk, name=None):
        
        # Search around previous hits
        if len(self.current_ship_hits) > 0 and len(self.possible_ship_squares) == 0:
            hitIndex = 0
            while (len(self.possible_ship_squares) == 0) and (hitIndex < len(self.current_ship_hits)):
                col = self.current_ship_hits[hitIndex][0]
                row = self.current_ship_hits[hitIndex][1]
                if (chr(ord(col)-1),row) in self.squares_to_ships:
                    self.possible_ship_squares.append((chr(ord(col)-1),row))
                
                if (chr(ord(col)+1),row) in self.squares_to_ships:
                    self.possible_ship_squares.append((chr(ord(col)+1),row))

                if (col,row-1) in self.squares_to_ships:
                    self.possible_ship_squares.append((col,row-1))

                if (col,row+1) in self.squares_to_ships:
                    self.possible_ship_squares.append((col,row+1))
                
                hitIndex += 1
            # if len(self.possible_ship_squares) == 0:
            #     print("Could not add possible shots")
            #     print("curent ship hits: ", self.current_ship_hits)
            #     print("possible ship squares: ", self. possible_ship_squares)
            #     print("....................\n\n")


        # choose the adjacent square with highest number of possible ship placements
        self.possible_ship_squares.sort(key=lambda x: len(self.squares_to_ships[x]))

        while len(self.possible_ship_squares) > 0:
            col, row = self.possible_ship_squares.pop()
            if (col,row) in self.squares_to_ships:
                return col, row

        # shoot at place with the highest number of possible ship placements
        # self.show_distribution(board)
        best_square = max(self.squares_to_ships,
                            key=lambda x: len(self.squares_to_ships[x]) )
        return best_square

    def handle_result(self, col, row, result, sunk, name):
        if result == SquareState.SHIP:
            if sunk:
                sunk_size = SHIP_LENS[name]

                # remove hits that share row or column and fall within range of size of ship
                for square in self.current_ship_hits.copy():
                    if (square[0] == col or square[1] == row) and ((ord(square[0])+square[1])-(ord(col)+row)) < sunk_size:
                        self.current_ship_hits.remove(square)

                self.possible_ship_squares = []
                self.squares_to_ships = {
                    square: {ship for ship in shipset if ship.name != name} for square,shipset in self.squares_to_ships.items()
                }
            else:
                self.current_ship_hits.append((col,row))

                if len(self.current_ship_hits) > 1:
                    # remove any squares in that don't align with hit
                    for square in self.possible_ship_squares.copy():
                        if square[0] != col and square[1] != row:
                            self.possible_ship_squares.remove(square)

                    # add next possible shot based on current hit and adjacent hit
                    adjacent_hit = None
                    for square in self.current_ship_hits:
                        if (square[0] == col or square[1] == row) and abs((ord(square[0])+square[1])-(ord(col)+row)) == 1:
                            adjacent_hit = square

                    if adjacent_hit is None:
                        pass
                        # print("Current hit: ", (col, row))
                        # print("curent ship hits: ", self.current_ship_hits)
                        # print("possible ship squares: ", self. possible_ship_squares)
                    else:
                        # continue searching in a line
                        if adjacent_hit[0] == col: # ship is vertical
                            step = (row - adjacent_hit[1]) // abs(row - adjacent_hit[1])
                            if (col, row+step) in self.squares_to_ships:
                                self.possible_ship_squares.append((col, row+step))
                        else:   # ship is horizontal
                            step = (ord(col) - ord(adjacent_hit[0])) // abs(ord(col) - ord(adjacent_hit[0]))
                            if (chr(ord(col)+step), row) in self.squares_to_ships:
                                self.possible_ship_squares.append((chr(ord(col)+step), row))
        elif result == SquareState.EMPTY:
            # get ships that are invalidated
            ships_to_remove = self.squares_to_ships[(col, row)]
            # remove invalid ships
            for square,shipset in self.squares_to_ships.items():
                shipset = {x for x in shipset if x not in ships_to_remove}
                self.squares_to_ships[square] = shipset

        # remove the invalidated square
        del self.squares_to_ships[(col, row)]


# Accounts for adjacent ships and fixes issue where incoreect ship hits were being eliminated when a ship was sunk
# Still possible to confuse algorithm when a lot of ships are clustered adjacent to each other. Performance is not affected much.
class SearchHuntStrategyV4(Strategy):

    def __init__(self):
        possible_ships = all_possible_ship_locations()
        self.squares_to_ships = {
            square: {ship for ship in possible_ships if ship.contains(*square)} for square in get_all_valid_squares()
        }
        self.possible_ship_squares = []
        self.current_ship_hits = []
        self.ship_direction = ShipOrientation.UNKNOWN
        self.board = []
        self.previous_shot = None

    # opponents_sunk: list of names of ships that have been sunk
    def choose_shot(self, board, opponents_sunk, name=None):
        self.board = board

        # Search around previous hits
        if len(self.current_ship_hits) > 0 and len(self.possible_ship_squares) == 0:
            hitIndex = 0
            while (len(self.possible_ship_squares) == 0) and (hitIndex < len(self.current_ship_hits)):
                col = self.current_ship_hits[hitIndex][0]
                row = self.current_ship_hits[hitIndex][1]
                if (chr(ord(col)-1),row) in self.squares_to_ships:
                    self.possible_ship_squares.append((chr(ord(col)-1),row))
                
                if (chr(ord(col)+1),row) in self.squares_to_ships:
                    self.possible_ship_squares.append((chr(ord(col)+1),row))

                if (col,row-1) in self.squares_to_ships:
                    self.possible_ship_squares.append((col,row-1))

                if (col,row+1) in self.squares_to_ships:
                    self.possible_ship_squares.append((col,row+1))
                
                hitIndex += 1

        # choose the adjacent square with highest number of possible ship placements
        self.possible_ship_squares.sort(key=lambda x: len(self.squares_to_ships[x]))

        while len(self.possible_ship_squares) > 0:
            col, row = self.possible_ship_squares.pop()
            if (col,row) in self.squares_to_ships:
                return col, row

        # shoot at place with the highest number of possible ship placements
        # self.show_distribution(board)
        best_square = max(self.squares_to_ships,
                            key=lambda x: len(self.squares_to_ships[x]) )
        return best_square

    def handle_result(self, col, row, result, sunk, name):
        if result == SquareState.SHIP:
            if sunk:
                sunk_size = SHIP_LENS[name]

                # Handle size 2 ships
                if sunk_size == 2:
                    #find adjacent shot
                    adjacent_hit = None
                    for square in self.current_ship_hits:
                        if (square[0] == col or square[1] == row) and abs((ord(square[0])+square[1])-(ord(col)+row)) == 1:
                            adjacent_hit = square
                    
                    self.current_ship_hits.remove(adjacent_hit)
                else:
                    #find adjacent shot
                    adjacent_hit = None
                    for square in self.current_ship_hits:
                        if (square[0] == col or square[1] == row) and abs((ord(square[0])+square[1])-(ord(col)+row)) == 1:
                            adjacent_hit = square
                    
                    if adjacent_hit is not None:
                        if adjacent_hit[0] == col: # ship is vertical
                            self.ship_direction = ShipOrientation.VERTICAL
                        else:
                            self.ship_direction = ShipOrientation.HORIZONTAL

                    remove_count = 0
                    removed_hits = []
                    # remove hits that are along direction of ship that fall within range of size of ship
                    for square in self.current_ship_hits.copy():
                        if (self.ship_direction == ShipOrientation.VERTICAL) and (square[0] == col) and (abs((ord(square[0])+square[1])-(ord(col)+row)) < sunk_size):
                            removed_hits.append(square)
                            self.current_ship_hits.remove(square)
                            remove_count += 1
                        elif (self.ship_direction == ShipOrientation.HORIZONTAL) and (square[1] == row) and (abs((ord(square[0])+square[1])-(ord(col)+row)) < sunk_size):
                            removed_hits.append(square)
                            self.current_ship_hits.remove(square)
                            remove_count += 1
                    
                    # retry with different orientation if squares removed are less sunk ship size
                    if (remove_count+1) < sunk_size:
                        self.ship_direction ^= 1
                        self.current_ship_hits.extend(removed_hits)
                        for square in self.current_ship_hits.copy():
                            if (self.ship_direction == ShipOrientation.VERTICAL) and (square[0] == col) and (abs((ord(square[0])+square[1])-(ord(col)+row)) < sunk_size):
                                self.current_ship_hits.remove(square)
                            elif (self.ship_direction == ShipOrientation.HORIZONTAL) and (square[1] == row) and (abs((ord(square[0])+square[1])-(ord(col)+row)) < sunk_size):
                                self.current_ship_hits.remove(square)

                if len(self.current_ship_hits) == 0:
                    self.possible_ship_squares = []
                else:
                    # remove any squares in possible_ship_squares that align with sunk ship because we finished hunting it
                    for square in self.possible_ship_squares.copy():
                        if self.ship_direction == ShipOrientation.HORIZONTAL and square[1] == row:
                            self.possible_ship_squares.remove(square)
                        elif self.ship_direction == ShipOrientation.VERTICAL and square[0] == col:
                            self.possible_ship_squares.remove(square)
                self.ship_direction = ShipOrientation.UNKNOWN
                

                self.squares_to_ships = {
                    square: {ship for ship in shipset if ship.name != name} for square,shipset in self.squares_to_ships.items()
                }
            else:
                self.current_ship_hits.append((col,row))

                if len(self.current_ship_hits) > 1:
                    # remove any squares in possible_ship_squares that don't align with hit
                    for square in self.possible_ship_squares.copy():
                        if square[0] != col and square[1] != row:
                            self.possible_ship_squares.remove(square)

                    # add next possible shot based on current hit and adjacent hit
                    adjacent_hit = None
                    for square in self.current_ship_hits:
                        if (square[0] == col or square[1] == row) and abs((ord(square[0])+square[1])-(ord(col)+row)) == 1:
                            adjacent_hit = square

                    if adjacent_hit is not None:
                        # continue searching in a line
                        if adjacent_hit[0] == col: # ship is vertical
                            self.ship_direction = ShipOrientation.VERTICAL
                            step = (row - adjacent_hit[1]) // abs(row - adjacent_hit[1])
                            if (col, row+step) in self.squares_to_ships:
                                self.possible_ship_squares.append((col, row+step))
                        else:   # ship is horizontal
                            self.ship_direction = ShipOrientation.HORIZONTAL
                            step = (ord(col) - ord(adjacent_hit[0])) // abs(ord(col) - ord(adjacent_hit[0]))
                            if (chr(ord(col)+step), row) in self.squares_to_ships:
                                self.possible_ship_squares.append((chr(ord(col)+step), row))
        elif result == SquareState.EMPTY:
            # get ships that are invalidated
            ships_to_remove = self.squares_to_ships[(col, row)]
            # remove invalid ships
            for square,shipset in self.squares_to_ships.items():
                shipset = {x for x in shipset if x not in ships_to_remove}
                self.squares_to_ships[square] = shipset

        # remove the invalidated square
        del self.squares_to_ships[(col, row)]
        self.previous_shot = (col, row)

class CSPStrategy(Strategy):
    # Bug: strategy seems to be retrying squares that have been tried before

    def __init__(self):
        self.set_squares = BOTTOM_3_BOARD.copy()
        print(self.set_squares)
        self.moves = 0
        self.valid_squares = list(itertools.product(COLS, ROWS))
        self.valid_squares = set(get_all_valid_squares())
        self.possible_ship_squares = []
        self.current_ship_hits = []

    # opponents_sunk: list of names of ships that have been sunk
    def choose_shot(self, board, opponents_sunk, name=None):
        if len(self.set_squares) > 0:
            return self.create_Test_Condition()

    def shave_valid_squares(self, opponents_sunk):
        #TODO create a different shaving algorithm
        #previously I used the possible ship set to decrease the available squares 
        #I need to re assess the logic - John
        return

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

    def create_Test_Condition(self):
        location = self.set_squares.pop()
        self.moves += 1
        return location

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


class GreedyNNStrategy(Strategy):

    def __init__(self):
        from tensorflow import keras
        from src.nn_data_gen import get_sunk_indices
        self.get_sunk_indicies = get_sunk_indices
        self.model = keras.models.load_model("greedy_model.h5")
        self.valid_squares = get_all_valid_squares()
        self.board_index = None

    def choose_shot(self, board, opponents_sunk, name=None):
        # sunk vec
        sunk = np.zeros(len(SHIP_LENS))
        sunk[self.get_sunk_indicies(opponents_sunk)] = 1.0
        # board data
        grid = board.get_data().to_numpy()
        # add batchsize
        sunk = sunk[np.newaxis,...]
        grid = grid[np.newaxis,...]
        dct = {"grid": grid, "sunk": sunk}
        # generate pred
        pred = self.model.predict(dct)
        pred[grid != SquareState.UNKNOWN] = np.nan
        pred = np.squeeze(pred)

        # # plotting
        # fig, (a1, a2) = plt.subplots(1, 2)
        # plot_grid_data(pred, a1, title="predmap")
        # plot_board(board, a2, title="board")
        # plt.show()

        # order shots by preference
        if self.board_index is None:
            self.board_index = board.get_data(flat=True).index.to_numpy()
        shots = self.board_index[np.argsort(pred.flatten())]
        # select best valid shot
        for row, col in shots[::-1]:
            if (col, row) in self.valid_squares:
                return col, row
        raise ValueError("No more valid shots!")

    def handle_result(self, col, row, result, sunk, name):
        self.valid_squares.remove((col, row))

