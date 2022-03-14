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
    # s = Simulation(EliminationStrategyV2, TestPlacement_2)
    # s = Simulation(GreedyNNStrategy, RandomPlacement)
    # s = Simulation(CSPStrategy, TestPlacement_2)
    s = Simulation(CSPStrategy, RandomPlacement)
    s.run()
    # s.display_one(interval=50)
    s = Simulation(SearchHuntStrategyV4, RandomPlacement).run(max_secs=240)
    # s = Simulation(SearchHuntStrategyV4, RandomPlacement)
    # s.run()
    # s.display_one(interval=100)
    print(s.metrics())


if __name__ == "__main__":
    main()