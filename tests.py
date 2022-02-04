import unittest

from src import BOARD_SIZE, ROWS, COLS
from src.placements import ShipPlacement

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
        for row in ROWS:
            for col in COLS:
                contains = s.contains(col, row)
                if row == 5 and col in "CDE":
                    self.assertTrue(contains, f"{col} {row}")
                else:
                    self.assertFalse(contains, f"{col} {row}")


if __name__ == "__main__":
    unittest.main()
