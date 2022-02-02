import numpy as np
import pandas as pd

from src import BOARD_SIZE
from src.placements import all_possible_ship_locations, ShipPlacement, RandomPlacement
from src.board import ShotBoard, SquareState
from src.strategy import UserStrategy

from src.game import Game

g = Game(UserStrategy(), UserStrategy(), RandomPlacement(), RandomPlacement())

g.play(show=True)

