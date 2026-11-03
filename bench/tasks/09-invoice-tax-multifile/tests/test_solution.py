import unittest
from invoice import total

class TestInvoice(unittest.TestCase):
    def test_discount_applies_before_tax(self):
        self.assertEqual(total([10, 5], "US", discount=5), 11)

if __name__ == "__main__": unittest.main()
