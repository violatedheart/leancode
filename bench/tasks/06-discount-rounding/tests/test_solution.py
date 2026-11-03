import unittest
from pricing import discounted_total

class TestPricing(unittest.TestCase):
    def test_percentage_and_final_rounding(self):
        self.assertEqual(discounted_total([0.335, 0.335], 10), 0.6)

if __name__ == "__main__": unittest.main()
