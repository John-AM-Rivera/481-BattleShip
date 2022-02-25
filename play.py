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
    g = Game(UserStrategy, CSPStrategy, RandomPlacement, RandomPlacement)
    g.play(show=True)


if __name__ == "__main__":
    main()