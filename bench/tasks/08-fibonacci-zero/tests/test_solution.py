import unittest
from fibonacci import fibonacci

class TestFibonacci(unittest.TestCase):
    def test_initial_values(self):
        self.assertEqual([fibonacci(i) for i in range(7)], [0, 1, 1, 2, 3, 5, 8])

if __name__ == "__main__": unittest.main()
