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

p0_default = ("userstrategy", "randomplacement")
p1_default = ("SearchHuntStrategy","randomplacement")

usage_msg = f"""
    $ python3 main.py [-p0 STRAT PLACEMENT] [-p1 STRAT PLACEMENT]
where STRAT and PLACEMENT are the names of shooting and placement strategies (case insensitive). This will play the respective players against eachother, reporting game state as it develops. To play as a human in the game, select the userstrategy; all others are algorithmically preprogrammed

If not specified, player 0 defaults to {p0_default} and player 1 defaults to {p1_default}.

All shooting strategies: {list(SHOOT_STRATS.keys())}

All placement strategies: {list(PLACEMENT_STRATS.keys())}
"""

def main():
    parser = argparse.ArgumentParser(usage=usage_msg)
    parser.add_argument("-p0",type=str,nargs=2,default=p0_default,metavar=("P0_STRAT","P0_PLACEMENT"),help="player 0: name of shooting strategy and name of placement strategy")
    parser.add_argument("-p1",type=str,nargs=2,default=p1_default, metavar=("P1_STRAT","P1_PLACEMENT"),help="player 1: name of shooting strategy and name of placement strategy")
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
