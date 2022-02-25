import time
import itertools

import pandas as pd
import numpy as np

import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib.animation as mpl_animation


from src import BOARD_SIZE, ROWS, COLS


def get_all_valid_squares():
    return list(itertools.product(COLS, ROWS))


SQUARESTATE_CMAP = plt.cm.get_cmap('RdBu_r', 3)
STANDARD_CMAP = 'RdBu_r'


def plot_board(board, ax=None, title="Board State"):
    """
    plot a board on an axes
    args:
        board: src.board.Board
        ax: optional matplotlib axes to plot on
    """
    if ax is not None:
        plt.sca(ax)
    else:
        ax = plt.gca()
    data = board.get_data()
    create_board_blot(data, ax, title=title)


def plot_grid_data(data, ax=None, title=None, cmap=STANDARD_CMAP, **kwargs):
    """
    args:
        data: pd.DataFrame in the shape of a board, or a dict in the form {(col,row): value}
        ax: optional matplotlib axes to plot on
        kwargs passed to plt.imshow
    """
    if ax is not None:
        plt.sca(ax)
    else:
        ax = plt.gca()
    if isinstance(data, dict):
        data = pd.DataFrame(data.values(), index=data.keys()).unstack().T
    cmap = plt.cm.get_cmap(cmap)
    cmap.set_bad('gray')
    plt.imshow(data, cmap=cmap, **kwargs)
    plt.colorbar()
    plt.title(title)
    set_plot_gridlines(ax)


def set_plot_gridlines(ax):
    """
    add ticks, tick labels, and gridlines to an axes
    """
    plt.xticks(np.arange(0, 10), COLS)
    plt.yticks(np.arange(0, 10), ROWS)
    ax.set_xticks(np.arange(-.5, 10, 1), minor=True)
    ax.set_yticks(np.arange(-.5, 10, 1), minor=True)

    # Gridlines based on minor ticks
    ax.grid(which='minor', color='w', linestyle='-', linewidth=2)


def create_board_blot(data, ax, title=None, animated=False):
    """
    create one frame of an animated board plot
    """
    from src.board import SquareState
    im = plt.imshow(data, cmap=SQUARESTATE_CMAP, animated=animated, vmin=-1, vmax=1)
    values = [-1, 0, 1]
    colors = [ im.cmap(im.norm(value)) for value in values]
    # create a patch (proxy artist) for every color 
    patches = [ mpl.patches.Patch(color=colors[i], label=SquareState.MAP_TO_NAME[values[i]] ) for i in range(len(values)) ]
    # put those patched as legend-handles into the legend
    plt.legend(handles=patches, bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0. )

    set_plot_gridlines(ax)
    plt.title(title)

    return im


def animate_boards(ims, fig, interval=50, save_as=None, ipynb=False):
    """
    turn a series of plt.imshow results into an animation
    """
    ims = [[im] for im in ims]
    ani = mpl_animation.ArtistAnimation(fig, ims, interval=interval, blit=True,
                                repeat_delay=1000, repeat=True)
    if ipynb:
        ani.save(".ipynb_temp.mp4")
        plt.close()
        from IPython.display import Video
        return Video(".ipynb_temp.mp4")
    elif save_as is not None:
        ani.save(save_as)
    else:
        plt.show()



