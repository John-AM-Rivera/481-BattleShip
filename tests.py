import unittest

from src import BOARD_SIZE, ROWS, COLS
from src.placements import ShipPlacement
from src.board import SquareState

class Tests(unittest.TestCase):

    def test_ship_overlap(self):
        s1 = ShipPlacement("A", 4, "C", 4)
        s2 = ShipPlacement("B", 1, "B", 5)
        s3 = ShipPlacement("C", 4, "F", 4)
        s4 = ShipPlacement("C", 5, "E", 5)
        s5 = ShipPlacement("G", 8, "H", 8)

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
        s = ShipPlacement("C", 5, "E", 5)
        s2 = ShipPlacement("G", 8, "G", 9)
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
        s = ShipPlacement("D", 4, "D", 5)
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


if __name__ == "__main__":
    unittest.main()
