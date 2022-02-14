import time
import multiprocessing

import pandas as pd
import numpy as np

from src import BOARD_SIZE, ROWS, COLS
from src.player import Player
from src.strategy import UserStrategy, Strategy, NoStrategy
from src.placements import PlacementStrategy, NoPlacements



class Timer:

    def __init__(self):
        # store time of various components
        self.total_timers = {}
        self.active_timers = {}

    def start(self, name):
        self.active_timers[name] = time.perf_counter()

    def end(self, name):
        t = time.perf_counter()
        if name not in self.total_timers:
            self.total_timers[name] = 0
        self.total_timers[name] += t - self.active_timers.pop(name)

    def get(self, name):
        return time.perf_counter() - self.active_timers[name]
    
    def merge(self, other):
        self.total_timers = {k:self.total_timers[k]+other.total_timers[k] for k in self.total_timers}



class Simulation:
    """
    simulate a one-sided game, ie one shooting strategy vs one placement strategy
    """

    def __init__(self, strategy0, placement1):
        self.strategy = strategy0
        self.placement = placement1
        # counters
        self.turns = []
        self.timings = None

    def _run_one_thread(self, max_secs):
        timer = Timer()
        turns = []
        timer.start("total")
        while True:
            timer.start("init")
            shooter = Player(self.strategy, NoPlacements, "shooter")
            target = Player(NoStrategy, self.placement, "target")
            timer.end("init")
            timer.start("play")
            while not shooter.has_won():
                shooter.take_turn_against(target)
            timer.end("play")
            turns.append(shooter.turns)
            if timer.get("total") > max_secs:
                break
        timer.end("total")
        return turns, timer.total_timers

    def run(self, max_secs=20):
        print("Simulating", max_secs, "(ish) seconds of", self.strategy.__name__, "and", self.placement.__name__, "in", multiprocessing.cpu_count(), "processes")
        with multiprocessing.Pool(multiprocessing.cpu_count()) as pool:
            results = pool.map(
                self._run_one_thread, 
                [max_secs for _ in range(multiprocessing.cpu_count())],
                chunksize=1
            )
            for turns, timings in results:
                self.turns += turns
                if self.timings is None:
                    self.timings = timings
                else:
                    self.timings = {k:self.timings[k]+timings[k] for k in self.timings}
        return self

    def metrics(self):
        metric_vals = {
            "n_simulations": len(self.turns),
            "total_turns": np.sum(self.turns),
            "avg_turns": np.mean(self.turns),
            "std_dev_turns": np.std(self.turns),
        }
        metric_vals["time"] = {
            "cumulative_sec": self.timings,
            "per_game_sec": {k:v/metric_vals["n_simulations"] for k,v in self.timings.items()},
            "per_turn_ms": self.timings["play"]/metric_vals["total_turns"]*1000,
        }
        return metric_vals



class Game:
    """
    player 0 always goes first
    __init__ args:
        strategyX, placementX: classes of type Strategy, PlacementStrategy (not initialized instances, just the raw class)
    """

    def __init__(self, strategy0, strategy1, placement0, placement1):
        self.p0 = Player(strategy0, placement0, name="P1")
        self.p1 = Player(strategy1, placement1, name="P2")
        self.divider = pd.DataFrame({" ": ROWS})
    
    def play(self, show=False):
        """
        returns:
            0|1: player who won
            turns: int
        """
        while True:
            self.one_turn(self.p0, self.p1, show=show)
            if self.p0.has_won():
                if show:
                    self.show_boards()
                return 0, self.p0.turns
            self.one_turn(self.p1, self.p0, show=show)
            if self.p1.has_won():
                if show:
                    self.show_boards()
                return 1, self.p1.turns
    
    def one_turn(self, playerA, playerB, show):
        if show:
            self.show_boards()
        playerA.take_turn_against(playerB)


    def show_boards(self):
        print("Player zeros's shots:            Player ones's shots:")
        print(pd.concat((self.p0.shots.get_printable(), self.divider, self.p1.shots.get_printable()), axis=1))
