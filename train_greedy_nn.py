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

from src.nn_data_gen import BoardGenerator

def build_model():
    """
    https://keras.io/examples/vision/oxford_pets_image_segmentation/
    """
    assert BOARD_SIZE == 10

    grid_input = keras.Input(shape=(BOARD_SIZE, BOARD_SIZE), name="grid")
    sunk_vec_input = keras.Input(shape=(len(SHIP_LENS),), name="sunk")
    
    # expand dims
    grid = layers.Reshape((BOARD_SIZE,BOARD_SIZE,1))(grid_input)
    sunk_vec = layers.Reshape((1,1,len(SHIP_LENS)))(sunk_vec_input)

    # make 16x16
    grid = layers.ZeroPadding2D(3)(grid)

    ### [First half of the network: downsampling inputs] ###

    # Entry block
    x = layers.Conv2D(16, 3, strides=1, padding="same")(grid)
    x = layers.BatchNormalization()(x)
    x = layers.Activation("relu")(x)

    previous_block_activation = x  # Set aside residual

    # Blocks 1, 2, 3 are identical apart from the feature depth.
    for filters in [32, 64, 64, 128]:
        x = layers.Activation("relu")(x)
        x = layers.SeparableConv2D(filters, 3, padding="same")(x)
        x = layers.BatchNormalization()(x)

        # x = layers.Activation("relu")(x)
        # x = layers.SeparableConv2D(filters, 3, padding="same")(x)
        # x = layers.BatchNormalization()(x)

        x = layers.MaxPooling2D(3, strides=2, padding="same")(x)

        # Project residual
        residual = layers.Conv2D(filters, 1, strides=2, padding="same")(
            previous_block_activation
        )
        x = layers.add([x, residual])  # Add back residual
        previous_block_activation = x  # Set aside next residual

    x = layers.Activation("relu")(x)
    x = layers.Concatenate(axis=-1)([x, sunk_vec])
    x = layers.Conv2D(128, 1)(x)
    x = layers.BatchNormalization()(x)

    ### [Second half of the network: upsampling inputs] ###

    for filters in [128, 64, 64, 32]:
        x = layers.Activation("relu")(x)
        x = layers.Conv2DTranspose(filters, 3, padding="same")(x)
        x = layers.BatchNormalization()(x)

        # x = layers.Activation("relu")(x)
        # x = layers.Conv2DTranspose(filters, 3, padding="same")(x)
        # x = layers.BatchNormalization()(x)

        x = layers.UpSampling2D(2)(x)

        # Project residual
        residual = layers.UpSampling2D(2)(previous_block_activation)
        residual = layers.Conv2D(filters, 1, padding="same")(residual)
        x = layers.add([x, residual])  # Add back residual
        previous_block_activation = x  # Set aside next residual

    # crop to correct size
    x = x[:,3:-3,3:-3]

    # Add a per-pixel prediction layer
    outputs = layers.Conv2D(1, 1, activation="sigmoid", padding="same")(x)

    # Define the model
    model = keras.Model([grid_input, sunk_vec_input], outputs)
    return model


def data_generate_or_load():
    names = ["train", "val", "test"]
    gens = []
    if os.path.exists("data/train.pickle"):
        for name in names:
            with open(f"data/{name}.pickle", "rb") as f:
                gens.append(pickle.load(f))
    else:
        train_gen = BoardGenerator(RandomPlacement, 32, 1000)
        val_data = BoardGenerator(RandomPlacement, 1000, 1)[0] # loads one big batch
        test_gen = BoardGenerator(RandomPlacement, 1, 1000)
        gens = [train_gen, val_data, test_gen]
        os.makedirs("data", exist_ok=True)
        for i,name in enumerate(names):
            with open(f"data/{name}.pickle", "wb") as f:
                pickle.dump(gens[i], f)
    return gens


def main():
    print("Generating data...")
    train_gen, val_data, test_gen = data_generate_or_load()

    # fig, (ax1, ax2) = plt.subplots(1, 2)
    # plot_grid_data(val_data[0]["grid"][0], ax1)
    # plot_grid_data(val_data[1][0], ax2)
    # plt.show()

    print("Building model")
    model = build_model()
    model.summary()

    callback_list = [
        callbacks.EarlyStopping(patience=6, verbose=1),
        callbacks.ModelCheckpoint("greedy_model.h5", save_best_only=True, verbose=1),
        callbacks.ReduceLROnPlateau(factor=0.1, patience=4, verbose=1)
    ]

    model.compile(
        loss="binary_crossentropy",
        optimizer=optimizers.Adam(0.01),
        metrics=["mse"],
    )
    model.fit(
        train_gen,
        validation_data=val_data,
        epochs=50,
        callbacks=callback_list
    )

    model.evaluate(test_gen)

    

if __name__ == "__main__":
    main()
    # keras.models.load_model("model.h5")
