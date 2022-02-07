import pandas as pd
import time

from src import BOARD_SIZE, ROWS, COLS
from src.player import Player
from src.strategy import UserStrategy


class Simulation:
    """
    simulate a one-sided game, ie one shooting strategy vs one placement strategy
    """

    def __init__(self, strategy0, placement1):
        self.strategy = strategy0
        self.placement = placement1
        # counters
        self.turns = []
        # store time of various components
        self.total_timers = {}
        self.active_timers = {}
    
    def _start_timer(self, name):
        self.active_timers[name+" time"] = time.perf_counter()

    def _end_timer(self, name):
        t = time.perf_counter()
        name += " time"
        if name not in self.total_timers:
            self.total_timers[name] = 0
        self.total_timers[name] += t - self.active_timers.pop(name)

    def run(self, n):
        self._start_timer("total")
        for _ in range(n):
            # use placeholders for shooter's placements, target's shot strat
            self._start_timer("init")
            shooter = Player(self.strategy, lambda: None, "shooter")
            target = Player(UserStrategy, self.placement, "target")
            self._end_timer("init")
            self._start_timer("play")
            while not shooter.has_won():
                shooter.take_turn_against(target)
            self._end_timer("play")
            self.turns.append(shooter.turns)
        self._end_timer("total")
        # make sure there are no running timings
        assert len(self.active_timers) == 0
        return self

    def metrics(self):
        newvals = {
            "n_simulations": len(self.turns),
            "avg_turns": sum(self.turns) / len(self.turns),
        }
        return dict(**self.total_timers, **newvals)



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
        print(pd.concat((self.p0.shots.get_data(), self.divider, self.p1.shots.get_data()), axis=1))
