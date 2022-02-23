import time

import pandas as pd
import numpy as np

import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib.animation as mpl_animation


from src import BOARD_SIZE, ROWS, COLS


SQUARESTATE_CMAP = plt.cm.get_cmap('RdBu_r', 3)


def create_board_blot(data, ax, title="", animated=False):
    from src.board import SquareState
    im = plt.imshow(data, cmap=SQUARESTATE_CMAP, animated=animated, vmin=-1, vmax=1)
    # plt.colorbar()
    values = [-1, 0, 1]
    colors = [ im.cmap(im.norm(value)) for value in values]
    # create a patch (proxy artist) for every color 
    patches = [ mpl.patches.Patch(color=colors[i], label=SquareState.MAP_TO_NAME[values[i]] ) for i in range(len(values)) ]
    # put those patched as legend-handles into the legend
    plt.legend(handles=patches, bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0. )

    plt.xticks(np.arange(0, 10), COLS)
    plt.yticks(np.arange(0, 10), ROWS)
    ax.set_xticks(np.arange(-.5, 10, 1), minor=True)
    ax.set_yticks(np.arange(-.5, 10, 1), minor=True)

    # Gridlines based on minor ticks
    ax.grid(which='minor', color='w', linestyle='-', linewidth=2)
    return im


def animate_boards(ims, fig, interval=50, save_as=None, ipynb=False):
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



