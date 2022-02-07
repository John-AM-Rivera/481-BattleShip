import numpy as np
import pandas as pd
import time
from pprint import pprint

from src import BOARD_SIZE, benchmark
from src.board import Board, SquareState
from src.placements import *
from src.strategy import *

from src.game import Game, Simulation


s = Simulation(RandomStrategy, RandomPlacement).run(3)
pprint(s.metrics())

s = Simulation(EliminationStrategy, RandomPlacement).run(3)
pprint(s.metrics())