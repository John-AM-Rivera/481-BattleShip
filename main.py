import numpy as np
import pandas as pd

from src import BOARD_SIZE
from src.placements import all_possible_ship_locations, ShipPlacement
from src.board import ShotBoard, SquareState


board = ShotBoard()

ship = ShipPlacement(("C", 4), ("C", 7))

board[ship] = SquareState.SHIP
board["E", 4] = SquareState.EMPTY
board["G", 8] = SquareState.SHIP

print(board)
