"""

"""

import time
from pprint import pprint
import argparse
import inspect

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from src import BOARD_SIZE, benchmark
from src.board import Board, SquareState
from src.game import Game, Simulation
from src.placements import *
from src.strategy import *
from src import placements, strategy

def load_subclasses(module, superclass):
    names = dir(module)
    clss = {name.lower().strip(): getattr(module, name) for name in names}
    clss = {name:cls for name,cls in clss.items() if inspect.isclass(cls) and issubclass(cls, superclass) and cls != superclass}
    return clss

SHOOT_STRATS = load_subclasses(strategy, Strategy)
PLACEMENT_STRATS = load_subclasses(placements, PlacementStrategy)

def get_strat(name, reference):
    name = name.lower().strip()
    if name not in reference:
        raise ValueError(f"'{name}' is not a valid strategy")
    return reference[name]

def get_strats(shoot, placement):
    return get_strat(shoot, SHOOT_STRATS), get_strat(placement, PLACEMENT_STRATS)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-p0",type=str,nargs=2,default=("userstrategy", "randomplacement"),metavar=("P0_STRAT","P0_PLACEMENT"),help="player 0: name of shooting strategy and name of placement strategy")
    parser.add_argument("-p1",type=str,nargs=2,default=("SearchHuntStrategyV4","randomplacement"), metavar=("P1_STRAT","P1_PLACEMENT"),help="player 1: name of shooting strategy and name of placement strategy")
    ARGS = parser.parse_args()

    shoot0, placement0 = get_strats(*ARGS.p0)
    shoot1, placement1 = get_strats(*ARGS.p1)
    game = Game(shoot0(), shoot1(), placement0(), placement1())
    print(game)

    print("P0 Ships:")
    print(game.p0.placements.as_board())
    game.play(show=True)



if __name__ == "__main__":
    main()
