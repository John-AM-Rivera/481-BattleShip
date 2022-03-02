import numpy as np
import pandas as pd
from tqdm import tqdm

import matplotlib.pyplot as plt

import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers

from src import ROWS, COLS, BOARD_SIZE, SHIP_LENS
from src.utils import get_all_valid_squares, plot_board, plot_grid_data
from src.board import Board
from src.player import Player
from src.strategy import *
from src.placements import all_possible_ship_locations, RandomPlacement, NoPlacements


sorted_ships = sorted([(length, name) for name,length in SHIP_LENS.items()])
SHIP_INDS = {name:index for index,(length,name) in enumerate(sorted_ships)}

def get_sunk_indices(names):
    """
    consistent indicies representing which ships have been sunk
    """
    return list(map(SHIP_INDS.get, names))


class BoardGenerator(keras.utils.Sequence):
    """
    generate board states from strategy
    """

    def __init__(self, placement_strat, batchsize, batches_per_epoch, 
            shoot_strat=(EliminationStrategyV2, RandomStrategy),
            regen_each_epoch=False, turns_per_example=10):

        self.placement_strat = placement_strat
        self.shoot_strat = shoot_strat
        self.batchsize = batchsize
        self.batches_per_epoch = batches_per_epoch
        self.regen_each_epoch = regen_each_epoch
        self.turns_per_example = turns_per_example

        self.X = np.empty((self.batches_per_epoch * self.batchsize, BOARD_SIZE, BOARD_SIZE), dtype=float)
        self.Xsunk = np.zeros((self.batches_per_epoch * self.batchsize, len(SHIP_LENS)), dtype=float)
        self.Y = np.empty((self.batches_per_epoch * self.batchsize, BOARD_SIZE, BOARD_SIZE), dtype=float)

        self.generate_epoch()

    def on_epoch_end(self):
        if self.regen_each_epoch:
            self.generate_epoch()
        else:
            shuffling = np.random.permutation(self.batches_per_epoch * self.batchsize)
            self.X = self.X[shuffling]
            self.Xsunk = self.Xsunk[shuffling]
            self.Y = self.Y[shuffling]

    def generate_epoch(self):
        indices = np.arange(self.batches_per_epoch * self.batchsize)
        np.random.shuffle(indices)

        def add_example(agent, target, index):
            # add board states to data
            self.X[index] = agent.shots.get_data().to_numpy()
            self.Y[index] = target_board

            # zero-one encode which ships are sunk
            sunk_inds = get_sunk_indices(agent.opponents_sunk)
            self.Xsunk[index, sunk_inds] = 1.0

        agent = None
        for index in tqdm(indices):
            # handle when the game has been completed and should be reinitialized
            if agent is None or agent.has_won():
                # select shoot strat randomly if multiple given
                if isinstance(self.shoot_strat, tuple):
                    shoot_strat = np.random.choice(self.shoot_strat)
                else:
                    shoot_strat = self.shoot_strat
                agent = Player(shoot_strat, NoPlacements, "agent")
                target = Player(NoStrategy, self.placement_strat, "target")
                target_board = target.placements.as_board().get_data().to_numpy()

                # add clean board
                add_example(agent, target, index)
                # random turns offset
                for _ in range(np.random.randint(1,self.turns_per_example)):
                    agent.take_turn_against(target)
            else:
                add_example(agent, target, index)
                # add new shots to the board
                for _ in range(self.turns_per_example):
                    if agent.has_won():
                        break
                    agent.take_turn_against(target)

    def __getitem__(self, index):
        start_ind = index * self.batchsize
        x = self.X[start_ind:start_ind+self.batchsize]
        xsunk = self.Xsunk[start_ind:start_ind+self.batchsize]
        y = self.Y[start_ind:start_ind+self.batchsize]
        return {"grid": x, "sunk": xsunk}, y

    def __len__(self):
        return self.batches_per_epoch

