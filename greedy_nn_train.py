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
import src.greedy_nn_eval

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

    # expand sunk vec
    sunk_vec = layers.Conv2D(32, 1)(sunk_vec)
    sunk_vec = layers.BatchNormalization()(sunk_vec)
    sunk_vec = layers.Activation("relu")(sunk_vec)

    # make 16x16
    grid = layers.ZeroPadding2D(3)(grid)

    ### [First half of the network: downsampling inputs] ###

    # Entry block
    x = layers.Conv2D(16, 3, strides=1, padding="same")(grid)
    x = layers.BatchNormalization()(x)
    x = layers.Activation("relu")(x)

    # skip connection outputs
    down_outputs = []
    # Set aside residual
    previous_block_activation = x 

    # Blocks 1, 2, 3 are identical apart from the feature depth.
    for filters in [16, 32, 32, 64]:
        x = layers.Activation("relu")(x)
        x = layers.SeparableConv2D(filters, 3, padding="same")(x)
        x = layers.BatchNormalization()(x)

        down_outputs.append(x)

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

    for filters in [128, 64, 32, 32]:
        x = layers.Activation("relu")(x)
        x = layers.Conv2DTranspose(filters, 3, padding="same")(x)
        x = layers.BatchNormalization()(x)

        x = layers.UpSampling2D(2)(x)

        # Skip connection residual
        x = layers.Concatenate(axis=-1)([x, down_outputs.pop()])  # Add back residual

    # crop to correct size
    x = layers.Cropping2D(3)(x)

    # Add a per-pixel prediction layer
    outputs = layers.Conv2D(1, 3, activation="sigmoid", padding="same")(x)

    # Define the model
    model = keras.Model([grid_input, sunk_vec_input], outputs)
    return model



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

    try:
        keras.utils.plot_model(model, "model.png", show_shapes=True)
    except Exception as e:
        print("Can't plot model:", e)

    callback_list = [
        callbacks.EarlyStopping(patience=6, verbose=1),
        callbacks.ModelCheckpoint("greedy_model.h5", save_best_only=True, verbose=1),
        callbacks.ReduceLROnPlateau(factor=0.1, patience=3, verbose=1)
    ]

    model.compile(
        loss="binary_crossentropy",
        optimizer=optimizers.Adam(0.005),
        metrics=["mse"],
    )
    try:
        model.fit(
            train_gen,
            validation_data=val_data,
            epochs=50,
            callbacks=callback_list
        )
    except KeyboardInterrupt:
        print("Training ended manually")

    # evaluate
    greedy_nn_eval.main()

    

if __name__ == "__main__":
    main()
    # keras.models.load_model("model.h5")
