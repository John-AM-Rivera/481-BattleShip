import unittest

import pandas as pd
import numpy as np
import random as random

from src import BOARD_SIZE, ROWS, COLS
from src.placements import ShipPlacement, all_possible_ship_locations, TestPlacement_1, TestPlacement_2
from src.board import SquareState
from src.game import Game, Simulation
from src.strategy import UserStrategy, CSPStrategy, EliminationStrategy

class Tests(unittest.TestCase):

    def test_ship_overlap(self):
        # initialize
        s1 = ShipPlacement("A", 4, "C", 4, "submarine")
        s2 = ShipPlacement("B", 1, "B", 5, "carrier")
        s3 = ShipPlacement("C", 4, "F", 4, "battleship")
        s4 = ShipPlacement("C", 5, "E", 5, "destroyer")
        s5 = ShipPlacement("G", 8, "H", 8, "patrolboat")

        self.assertEqual(s1.length, 3)
        self.assertEqual(s2.length, 5)
        self.assertEqual(s3.length, 4)
        self.assertEqual(s4.length, 3)
        self.assertEqual(s5.length, 2)

        # overlapping ships
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

        # overlapping individual squares
        s6 = ShipPlacement("I", 5, "K", 5, "submarine")
        s7 = ShipPlacement("G", 8, "G", 9, "patrolboat")
        
        self.ship_contains_helper(s1, "ABC", [4])
        self.ship_contains_helper(s2, "B", [1,2,3,4,5])
        self.ship_contains_helper(s3, "CDEF", [4])
        self.ship_contains_helper(s4, "CDE", [5])
        self.ship_contains_helper(s5, "GH", [8])
        self.ship_contains_helper(s6, "IJK", [5])
        self.ship_contains_helper(s7, "G", [8,9])


    def ship_contains_helper(self, ship, true_cols, true_rows):
        for row in ROWS:
            for col in COLS:
                contains = ship.contains(col, row)
                hit, sunk = ship.check_hit(col, row)
                if row in true_rows and col in true_cols:
                    self.assertTrue(contains, f"{col} {row}")
                    self.assertTrue(hit)
                else:
                    self.assertFalse(contains, f"{col} {row}")
                    self.assertFalse(hit)

    def test_ship_sunk(self):
        s = ShipPlacement("D", 4, "D", 5, "patrolboat")
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

    def test_choice_reduction(self):
        print("Running CSP")
        g = Game(CSPStrategy, CSPStrategy, TestPlacement_2, TestPlacement_2)
        g.play(show=True)
        sim1 = Simulation(CSPStrategy, TestPlacement_1)
        sim1.run()
        print(sim1.metrics())


    def test_ship_eq(self):
        s1 = ShipPlacement("A", 4, "C", 4, "submarine")
        s2 = ShipPlacement("B", 1, "B", 5, "carrier")
        s3 = ShipPlacement("C", 4, "F", 4, "battleship")

        s4 = ShipPlacement("B", 1, "B", 5, "carrier")

        self.assertFalse(s1 == s4)
        self.assertTrue(s2 == s4)
        self.assertFalse(s3 == s4)
        
        self.assertTrue(s3 == s3)

        all_ships = list(all_possible_ship_locations())
        for i in range(len(all_ships)):
            for j in range(len(all_ships)):
                if i == j:
                    self.assertTrue(all_ships[i] == all_ships[j])
                    self.assertTrue(str(all_ships[i]) == str(all_ships[j]))
                else:
                    self.assertFalse(all_ships[i] == all_ships[j])
                    self.assertFalse(str(all_ships[i]) == str(all_ships[j]))





if __name__ == "__main__":
    unittest.main()
