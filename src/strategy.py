import abc
import random
from turtle import right, up

import numpy as np
import pandas as pd
from src import BOARD_SIZE, BOTTOM_3_BOARD, FULL_BOARD
from src import BOTTOM_9X9_BOARD
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

    # attribute that determines whether the board should be flattened with
    # DataFrame.stack(). Flat has faster lookup than square, so should be preferred
    require_square_board = False

    def __init__(self):
        """
        only override this method to set attributes that should be kept
        between all games this strategy is used in. For example, a cutoff parameter
        that remains unchanged between games. Transient things like which squares
        are currently valid should be initialized in the `reinitialize` method 
        since they are only relevant to their particular game.

        Additionally, all params must have defaults, so that init can be called
        with no arguments
        """

    def reinitialize(self):
        """
        initialize game-specific data for this strategy. All arguments must have defaults
        """

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
        This method should not modify the board object
        """
        ...

    def handle_result(self, col, row, result, sunk, board, name):
        """
        update internal state in response to the result of a shot. Default
        behavior is to do nothing
        args:
            col, row: shot we chose
            result: shot result
            sunk: bool
            name: name of sunk ship, only applicable if sunk
            board: Board object
        This method should not modify the board object
        """
        pass

class NoStrategy(Strategy):

    def choose_shot(self, *args, **kwargs):
        raise NotImplementedError()


"""
concrete strategies
"""

class UserStrategy(Strategy):

    def reinitialize(self):
        self.fired_upon = []

    def choose_shot(self, board, opponents_sunk, name=None):
        while True:
            square = input("{}: Enter a square to fire on (ex: E4): ".format(name))
            try:
                col, row = square.strip()
                row = int(row)
            except Exception as e:
                print("Could not parse your input:", str(e))
                continue # retry the loop

            if (col,row) in self.fired_upon:
                print("You have already fired there!")
            else:
                # breaks loop
                return col, row
    
    def handle_result(self, col, row, result, sunk, board, name):
        self.fired_upon.append( (col,row) )
        if result == SquareState.SHIP:
            if sunk:
                print(f"{col}{row}: You sunk my {name}!")
            else:
                print(f"{col}{row}: Hit!")
        else:
            print(f"{col}{row}: Miss.")


class RandomStrategy(Strategy):

    def reinitialize(self):
        self.valid_squares = set(get_all_valid_squares())

    def choose_shot(self, board, opponents_sunk, name=None):
        # select random element from set
        return self.valid_squares.pop()



"""
Four versions of SearchHunt, kept to show development of thoughts. The last
is the most up-to-date version
"""


# Idea:
# generate some number of possible board placements
# shoot based on one of the boards based on some heuristic that makes it the most desirable
#   Based on result on real board, eliminate simulated boards that cannot be the real board
# once we run out of simulated boards, generate new set of boards that comply with current state of opponent's board
# continue shooting and generating boards until all opponent ships are shot down.

class SearchHuntStrategyV1(Strategy):
    # Bug: does not account for adjacent ships

    def reinitialize(self):
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

    def handle_result(self, col, row, result, sunk, board, name):
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

    def reinitialize(self):
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

    def handle_result(self, col, row, result, sunk, board, name):
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

    def reinitialize(self):
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

    def handle_result(self, col, row, result, sunk, board, name):
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
class SearchHuntStrategy(Strategy):

    def reinitialize(self):
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

    def handle_result(self, col, row, result, sunk, board, name):
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



"""
Constraint Propogation
"""

class CSPStrategy(Strategy):

    # NOTE: A lot of the attributes are unused as they were originally made for testing. 
    # Their analysis will be explained in the Final Report
    def reinitialize(self):
        self.set_squares = {}
        self.ships_afloat = ["carrier", "patrolboat", "battleship", "submarine", "destroyer"]
        self.possible_ships_loc = list(all_possible_ship_locations())
        self.ship_tiles_available = 17
        self.hits_available = 17
        self.possible_ships = all_possible_ship_locations()
        self.row_info = [0 for i in range(10)]
        self.col_info = [0 for i in range(10)]
        self.moves = 0
        self.hits_found = []
        self.valid_squares = get_all_valid_squares()
        self.possible_ship_squares = []
        self.current_ship_hits = []

    def choose_shot(self, board, opponents_sunk, name=None):
        self.printCurrentInfo()
        # probabilites from Elimination Strategy
        ship_counts = [
            sum(ship.contains(*square) for ship in self.possible_ships) for square in self.valid_squares
        ]
        self.propagate_probabilites(ship_counts, board, opponents_sunk)
        best_idx = np.argmax(ship_counts)
        return self.valid_squares.pop(best_idx)

    # probabilities are increased for hits for which we do not know cardinality yet. This gives us more information during play 
    # thus faster discovery time of hidden ships
    def propagate_probabilites(self, ship_counts, board, opponents_sunk):
        for hit_loc in self.hits_found:
            if self.hit_cardinality(hit_loc):
                self.multiply_cardinality(ship_counts, hit_loc)
        return

    def get_cardinal_coord(self, hit_loc):
        col = hit_loc[0]
        row = hit_loc[1]
        left = (col, row - 1)
        right = (col, row + 1)
        above = ((chr(ord(col) + 1)), row)
        down = ((chr(ord(col) - 1)), row)
        return left, right, above, down

    def hit_cardinality(self, hit_loc) -> bool:
        left, right, above, down = self.get_cardinal_coord(hit_loc)
        return left in self.hits_found or right in self.hits_found or above in self.hits_found or down in self.hits_found

    def multiply_cardinality(self, ship_counts, hit_loc):
        left, right, above, down = self.get_cardinal_coord(hit_loc)
        card_lst = [left, right, above, down]
        for coord in card_lst:
            if coord in self.valid_squares:
                ship_counts[self.valid_squares.index(coord)] *= 10
        return

    def handle_result(self, col, row, result, sunk, name, board):
        if result == SquareState.SHIP:
            self.row_info[row] += 1
            self.col_info[ord(col) - 65] += 1
            self.hits_found.append((col, row))
            self.hits_available -= 1
            if sunk:
                self.ships_afloat.remove(name)
                self.reduceShipTiles(name)
                # print("Ship was Sunk!")
                self.possible_ships = {ship for ship in self.possible_ships if not ship.name == name}
            # else:
            #     print("Ship was Hit!")
        elif result == SquareState.EMPTY:
            self.possible_ships = {ship for ship in self.possible_ships if not ship.contains(col, row)}

    # tracks available ship tiles (CAN BE DELETED BUT IS USEFUL FOR OTHER GAMEMODES)                
    def reduceShipTiles(self, name):
        if (name == "patrolboat"):
            self.ship_tiles_available -= 2
            for ship in self.possible_ships_loc:
                if ship.name == name:
                    self.possible_ships_loc.remove(ship)
        elif (name == "destroyer" or name == "submarine"):
            self.ship_tiles_available -= 3
        elif (name == "battleship"):
            self.ship_tiles_available -= 4
        else:            
            self.ship_tiles_available -= 5

    # print statements for information representation during development
    def printCurrentInfo(self):
        # print("Row Information: " + str(self.row_info))
        # print("Col Information: " + str(self.col_info))
        # print("Ships Afloat: " + str(self.ships_afloat))
        # print("Ship tiles Left = " + str(self.ship_tiles_available))
        # print("Hit tiles Left = " + str(self.hits_available))
        # print("valid squares: " + str(self.valid_squares))
        return



"""
Elimination strategy: two versions, last is most up to date
"""

class EliminationStrategyV1(Strategy):

    def reinitialize(self):
        self.possible_ships = all_possible_ship_locations()
        self.valid_squares = get_all_valid_squares()

    def choose_shot(self, board, opponents_sunk, name=None):
        ship_counts = [
            sum(ship.contains(*square) for ship in self.possible_ships) for square in self.valid_squares
        ]
        # shoot at place with the highest number of possible ship placements
        best_idx = np.argmax(ship_counts)
        return self.valid_squares.pop(best_idx)
    
    def handle_result(self, col, row, result, sunk, board, name):
        # invalidate ships on a miss
        if result == SquareState.EMPTY:
            self.possible_ships = {ship for ship in self.possible_ships if not ship.contains(col, row)}
        # remove sunk ship possibilities
        if sunk:
            self.possible_ships = {ship for ship in self.possible_ships if not ship.name == name}


class EliminationStrategy(Strategy):
    """
    faster version of the above
    """
    
    def reinitialize(self):
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
    
    def handle_result(self, col, row, result, sunk, board, name):
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

"""
Neural-Network strategy
"""

class GreedyNNStrategy(Strategy):
    
    def reinitialize(self):
        from tensorflow import keras
        from src.nn_data_gen import get_sunk_indices
        self.get_sunk_indices = get_sunk_indices
        self.model = keras.models.load_model("greedy_model.h5")
        self.valid_squares = get_all_valid_squares()
        self.board_index = None

    def choose_shot(self, board, opponents_sunk, name=None):
        # sunk vec
        sunk = np.zeros(len(SHIP_LENS))
        sunk[self.get_sunk_indices(opponents_sunk)] = 1.0
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

    def handle_result(self, col, row, result, sunk, board, name):
        self.valid_squares.remove((col, row))



"""
Monte-carlo sampling strategies. Two variants
"""


class BackTrackError(Exception):
    """
    error to signal we need to backtrack in our placement process
    """

class SamplingStrategy(Strategy, abc.ABC):
    """
    Base class for strategies that sample possible valid boards to determine a next shot
    """

    def __init__(self, n_samples=10):
        self.n_samples = 10

    def reinitialize(self):
        possible_ships = list(all_possible_ship_locations())
        random.shuffle(possible_ships)
        self.squares_to_ships = {
            square: [ship for ship in possible_ships if ship.contains(*square)] for square in get_all_valid_squares()
        }
        self.names_to_ships = { 
            name: [ship for ship in possible_ships if ship.name == name] for name in SHIP_LENS.keys()
        }
        # boards from previous iteration that are still valid
        self.sampled_placements = []

    def generate_selection_order(self, sunk_names):
        # ship names sorted sunk, then randomly
        keyfunc = lambda name: (name in sunk_names, np.random.rand())
        self.selection_order = sorted(SHIP_LENS.keys(), key=keyfunc, reverse=True)
        self.lengths = [SHIP_LENS[x] for x in self.selection_order]
        self.last_ind = len(SHIP_LENS) - 1

    def placements_to_df(self, ships):
        board = Board(SquareState.EMPTY, flat=True)
        for s in ships:
            board[s] = SquareState.SHIP
        return board.get_data(flat=True)

    def count_hits(self, board, ship):
        squared_placed_in = board[ship]
        return squared_placed_in[squared_placed_in == SquareState.SHIP].sum()

    def sample_one_placement(self, board, selected, index, hits_remaining):
        """
        randomly sample a placement that satisfies board
        this function acts recursively, selecting ships one at a time
        args:
            selected: ships selected so far
            index: index into `self.selection_order` of what ship we are selecting currently
            hits_remaining: number of hits that are left uncovered
        """
        # the ship we are placing currently
        name = self.selection_order[index]
        # get number of hits we need to cover with this ship in order to possibly cover all hits in the future
        hits_required_now = hits_remaining - sum(self.lengths[index+1:])
        # counter for number of times backtracked
        backtracks = 0
        # keep track of placements we've already tried
        placements_tried = []


        def is_valid(ship):
            """
            helper to check a placement doesn't overlap with previous placements 
            and satisfies hit constraints
            """
            return (ship not in placements_tried) and \
                (not any(ship.overlaps(x) for x in selected)) and \
                (hits_required_now <= 0 or self.count_hits(board, ship) >= hits_required_now)
    
        def try_recurse(ship):
            """
            helper to handle the logic of recursing and backtracking
            returns whether a valid set of placements was achieved
            """
            nonlocal backtracks, selected, placements_tried, index
            placements_tried.append(ship)
            selected.append(ship)
            if index == self.last_ind:
                return True
            else:
                n_hits = self.count_hits(board, ship)
                try:
                    self.sample_one_placement(board, selected, index+1, hits_remaining - n_hits)
                    return True
                except BackTrackError:
                    # backtrack
                    # print("backtrack", index)
                    selected.pop()
                    backtracks += 1
                    # allow backtracking `index` times
                    if backtracks > index - 1:
                        raise BackTrackError("too many backtracks")
                return False
        
        # try to choose a placement on a hit if such a placement exists
        if hits_remaining > 0:
            hit_squares = board.get_hits()
            indices = np.random.permutation(len(hit_squares))
            for ind in indices:
                hit_row, hit_col = hit_squares[ind]
                # get ships with this name that could be placed in this square
                ships_here = self.squares_to_ships[(hit_col,hit_row)]
                ships_here = [x for x in ships_here if x.name == name and is_valid(x)]
                random.shuffle(ships_here)
                if len(ships_here):
                    # try to pick one with multiple hits, if possible
                    if hits_remaining > 1:
                        for ship in ships_here:
                            if self.count_hits(board, ship) > 1:
                                if try_recurse(ship):
                                    return selected
                    # otherwise just grab a random one (first is random since list is shuffled)
                    if try_recurse(ships_here[0]):
                        return selected
        # otherwise pick a random spot
        # randomly order ships
        indices = np.random.permutation(len(self.names_to_ships[name]))
        for ind in indices:
            ship = self.names_to_ships[name][ind]
            # check doesn't conflict with other placements and has proper number of hits
            if is_valid(ship):
                if try_recurse(ship):
                    return selected

        raise BackTrackError("options exhausted")

    @abc.abstractmethod
    def rank_values(self, series):
        """
        given a pandas series, where the elements are how many ships were
        found in the simulations at that square, sort the series so that the most
        promising squares are first
        """
        raise NotImplementedError()

    def choose_shot(self, board, opponents_sunk, name=None):
        n_hits = board.num_hits()
        # print(board)
        
        # sample the number of placements it takes to reach self.n_samples placements again
        need_to_sample = self.n_samples - len(self.sampled_placements)
        # print(need_to_sample)
        for i in range(need_to_sample):
            # print("sample", i)
            while True:
                self.generate_selection_order(opponents_sunk)
                try:
                    placements = self.sample_one_placement(board, [], 0, n_hits)
                    break # leave while loop
                except BackTrackError as e:
                    # print("retry:", e)
                    continue # retry with new selection order

            self.sampled_placements.append(
                self.placements_to_df(placements)
            )
        # sum over list of dfs, which sums them elementwise
        summed_board = sum(self.sampled_placements)

        ranked_squares = self.rank_values(summed_board).index
        for row, col in ranked_squares:
            if board[col,row] == SquareState.UNKNOWN:
                return col, row
        raise RuntimeError("No valid shots")


    def handle_result(self, col, row, result, sunk, board, name):
        # invalidate ships on a miss
        if result == SquareState.EMPTY:
            # get ships that are invalidated
            ships_to_remove = self.squares_to_ships[(col, row)]
            # remove invalid ships
            for square,shipset in self.squares_to_ships.items():
                shipset = [x for x in shipset if x not in ships_to_remove]
                self.squares_to_ships[square] = shipset
            for name,shipset in self.names_to_ships.items():
                shipset = [x for x in shipset if x not in ships_to_remove]
                self.names_to_ships[name] = shipset

        # remove sampled placements that can be pruned now
        self.sampled_placements = [x for x in self.sampled_placements if x[row,col] == result]

        # remove sunk ship possibilities
        if sunk:
            self.squares_to_ships = {
                square: [ship for ship in shipset if ship.name != name] for square,shipset in self.squares_to_ships.items()
            }
            # only valid ship placements for sunk ships are those that:
            # * contain the square we know sunk it
            # * contain only hits
            self.names_to_ships[name] = [
                ship for ship in self.names_to_ships[name] if ship.contains(col, row) and \
                    self.count_hits(board, ship) == SHIP_LENS[ship.name]
            ]


class EntropyStrategy(SamplingStrategy):

    def rank_values(self, series):
        splitval = self.n_samples / 2 + 0.5 # break ties toward there being a hit
        diffs = (series - splitval).abs()
        return diffs.sort_values()

class GreedySamplingStrategy(SamplingStrategy):

    def rank_values(self, series):
        return series.sort_values(ascending=False)




"""
Class for combining two different strategies
"""

class CombinedStrat(Strategy):
    """
    strategy that combines two others, by playing the first one until a condition
    is met, and then using the second one from then on
    """

    def __init__(self, s1, s2, condition="turns", cutoff=30):
        self.s1 = s1
        self.s2 = s2

        self.cutoff = cutoff
        if condition == "turns":
            self.condition = self.turns_condition
        elif condition == "hits":
            self.condition = self.hits_condition
        else:
            raise ValueError()
    
    def turns_condition(self):
        return self.turn_no >= self.cutoff
    
    def hits_condition(self):
        return self.hits > self.cutoff

    def reinitialize(self):
        # initialize strats
        self.s1.reinitialize()
        self.s2.reinitialize()
        # counter for turn number of next turn
        self.turn_no = 1
        self.hits = 0
    
    def choose_shot(self, *args, **kwargs):
        # print("turn", self.turn_no)
        if self.condition():
            strat = self.s2
        else:
            strat = self.s1
        return strat.choose_shot(*args, **kwargs)

    def handle_result(self, **kwargs):
        if kwargs["result"] == SquareState.SHIP:
            self.hits += 1
        self.s1.handle_result(**kwargs)
        self.s2.handle_result(**kwargs)
        self.turn_no += 1

