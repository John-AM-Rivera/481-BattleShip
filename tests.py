import py_compile
import unittest
import random


from src import BOARD_SIZE, ROWS, COLS
from src.placements import ShipPlacement, RandomPlacement, TestPlacement_1
from src.board import SquareState
from src.game import Game, Simulation
from src import board 
from src.strategy import Strategy, UserStrategy, CSPStrategy, EliminationStrategy, SearchHuntStrategy


class Tests(unittest.TestCase):

    def test_ship_overlap(self):
        s1 = ShipPlacement("A", 4, "C", 4, "destroyer")
        s2 = ShipPlacement("B", 1, "B", 5, "carrier")
        s3 = ShipPlacement("C", 4, "F", 4, "battleship")
        s4 = ShipPlacement("C", 5, "E", 5, "submarine")
        s5 = ShipPlacement("G", 8, "H", 8, "patrol boat")

        self.assertEqual(s1.length, 3)
        self.assertEqual(s2.length, 5)
        self.assertEqual(s3.length, 4)
        self.assertEqual(s4.length, 3)
        self.assertEqual(s5.length, 2)

        self.assertTrue(s1.overlaps(s2))
        self.assertTrue(s2.overlaps(s1))
        self.assertTrue(s1.overlaps(s3))
        self.assertTrue(s3.overlaps(s1))
        for s in (s1, s2, s3):
            self.assertFalse(s4.overlaps(s))
            self.assertFalse(s.overlaps(s4))
            self.assertFalse(s5.overlaps(s))
            self.assertFalse(s.overlaps(s5))
        for s in (s1,s2,s3,s4,s5):
            self.assertTrue(s.overlaps(s))
        
    def test_ship_contains(self):
        s = ShipPlacement("C", 5, "E", 5, "destroyer")
        s2 = ShipPlacement("G", 8, "G", 9, "patrol boat")
        for row in ROWS:
            for col in COLS:
                contains = s.contains(col, row)
                if row == 5 and col in "CDE":
                    self.assertTrue(contains, f"{col} {row}")
                else:
                    self.assertFalse(contains, f"{col} {row}")
                contains2 = s2.contains(col, row)
                if col == "G" and row in [8, 9]:
                    self.assertTrue(contains2)
                else:
                    self.assertFalse(contains2)

    def test_ship_hit(self):
        s = ShipPlacement("D", 4, "D", 5, "patrol boat")
        # hit
        hit, sunk = s.check_hit("D", 5)
        self.assertTrue(hit)
        self.assertFalse(sunk)
        # miss
        hit, sunk = s.check_hit("D", 6)
        self.assertFalse(hit)
        self.assertFalse(sunk)
        # hit
        hit, sunk = s.check_hit("D", 4)
        self.assertTrue(hit)
        self.assertTrue(sunk)

    def test_dimension_reduction(self):
        print("Running CSP")
        random.seed(8008135)
        g = Game(UserStrategy, CSPStrategy, TestPlacement_1, TestPlacement_1)
        g.play(show=True)
        # sim = Simulation(EliminationStrategy, TestPlacement_1).run(max_secs=5)
        # sim1 = Simulation(SearchHuntStrategy, TestPlacement_1).run(max_secs=5)
        # print(sim1.metrics())

        # sim2 = Simulation(CSPStrategy, TestPlacement_1).run(max_secs=5)
        # print(sim2.metrics())

        # sim3 = Simulation(SearchHuntStrategy, RandomPlacement).run(max_secs=5)
        # print(sim3.metrics())

        # sim4 = Simulation(CSPStrategy, RandomPlacement).run(max_secs=5)
        # print(sim4.metrics())




if __name__ == "__main__":
    unittest.main()
