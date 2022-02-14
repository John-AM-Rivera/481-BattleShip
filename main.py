import time
from pprint import pprint

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from src import BOARD_SIZE, benchmark
from src.board import Board, SquareState
from src.game import Game, Simulation
from src.placements import *
from src.strategy import *

def main():
    # print(RandomPlacement().as_board())
    # RandomPlacement.show_distribution(1000)

    # simulate elimination strategy against random placement
    sim = Simulation(RandomStrategy, RandomPlacement).run(max_secs=5)
    pprint(sim.metrics())

    # s = Simulation(EliminationStrategy, RandomPlacement).run(3)
    # pprint(s.metrics())


if __name__ == "__main__":
    main()
