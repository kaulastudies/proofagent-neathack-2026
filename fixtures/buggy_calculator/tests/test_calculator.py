import unittest
from calculator import calculate_total


class AcceptanceTests(unittest.TestCase):
    def test_no_discount(self):
        self.assertEqual(calculate_total([10, 20], 0), 30)

    def test_single_discount(self):
        self.assertEqual(calculate_total([10, 20], 5), 25)

    def test_boundary_full_discount(self):
        self.assertEqual(calculate_total([10, 20], 30), 0)


if __name__ == '__main__':
    unittest.main()
