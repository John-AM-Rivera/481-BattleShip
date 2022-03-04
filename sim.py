import numpy as np
import pandas as pd
import time
from pprint import pprint

from src import BOARD_SIZE, benchmark
from src.board import Board, SquareState
from src.placements import *
from src.strategy import *

from src.game import Game, Simulation


def main():
    # RandomPlacement.show_distribution(10)
    # s = Simulation(EliminationStrategyV2, RandomPlacement).run(max_secs=10)
    s = Simulation(SearchHuntStrategyV3, RandomPlacement)
    s.run()
    # s.display_one(interval=100)
    pprint(s.metrics())


if __name__ == "__main__":
    main()