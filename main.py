import numpy as np
import pandas as pd
import time

from src import BOARD_SIZE, benchmark
from src.placements import all_possible_ship_locations, ShipPlacement, RandomPlacement
from src.board import Board, SquareState
from src.strategy import UserStrategy, RandomStrategy

from src.game import Game, Simulation


s = Simulation(RandomStrategy, RandomPlacement).run(100)
print(s.metrics())