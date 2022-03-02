import pickle
import os, sys

import numpy as np
import pandas as pd

import matplotlib.pyplot as plt

import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, callbacks, optimizers

from src import ROWS, COLS, BOARD_SIZE, SHIP_LENS
from src.utils import get_all_valid_squares, plot_board, plot_grid_data
from src.board import Board
from src.player import Player
from src.strategy import RandomStrategy, NoStrategy
from src.placements import all_possible_ship_locations, RandomPlacement, NoPlacements

from src.nn_data_gen import BoardGenerator, data_generate_or_load



def main():
    train_gen, val_data, test_gen = data_generate_or_load()

    model = keras.models.load_model("greedy_model.h5")
    print("\nTest set evaluation:")
    model.evaluate(test_gen)

    val_x = val_data[0]
    val_y = val_data[1]
    pred = model.predict(val_x)
    for i in range(0, 100, 10):
        fig, (ax1, ax2) = plt.subplots(1, 2)
        plot_grid_data(val_x["grid"][i], ax1, title="target")
        plot_grid_data(pred[i], ax2, title="pred")
        plt.show()
        plt.close()


if __name__ == "__main__":
    main()