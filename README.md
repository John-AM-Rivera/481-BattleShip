# BattleShip

A project by John Rivera, Joel Valdovinos, and Julian Rice

CSC 481: Knowledge-Based Systems  
Dr. Canaan  
California Polytechnic State University  
Winter 2022  


## Acknowledgements

All code is our own, except:

The game engine was conceptually inspired in part by:

Rochford, A. (2021). “Playing Battleship with Bayesian Search Theory, Thompson Sampling, and Approximate Bayesian Computation.” Available: https://austinrochford.com/posts/2021-09-02-battleship-bayes.html  [Accessed: 26-Jan-2022].

The neural network architecture is a modified version of that provided by:

Keras Team. "Keras Documentation: Image segmentation with a u-net-like architecture". Keras. https://keras.io/examples/vision/oxford_pets_image_segmentation/ [Accessed: 16-Mar-2022]

## Setup

`conda-env.yml` lists the required packages, and can be used to create a virtual environment with conda if you have it on your system already (see [creating a conda environment from yml](https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html#creating-an-environment-from-an-environment-yml-file))

Note that tensorflow is only required when using the Greedy Neural Network strategy, and the code is structured so that Tensorflow is only imported if it is needed.

You can run the script `tests.py` to verify that the basic mechanics of the game engine are working as intended with your installation.

## How to Play

Running `main.py` enables you to play against an algorithmic opponent of your choosing, or even pit two algorithms against eachother. By default, it will run UserStrategy (ie, you choose the shots) against the best performing algorithm, SearchHunt, providing both players with starting positions chosen by Random Placement. Supply the `--help` (or `-h`) flag the script for a more detailed description of how to customize each player.

In order to use the Greedy Neural Network model, you must train it first with the `greedy_nn_trail.py` script.


## How to Re-Create Performance Tests

`demos.ipynb` contains the exact outputs that we provided in our report. You can also re-run any cells to reproduce these outputs (subject to variations due to random chance). This notebook also demonstrates simple methods for visualizing strategies as they play. 

On an 8-core laptop, the notebook in its entirety took approximately 45 minutes to run. About half of that time was spent on simulating the Entropy Strategy, because it can occasionally get itself into situations that it finds difficult to sample compatible boards from.