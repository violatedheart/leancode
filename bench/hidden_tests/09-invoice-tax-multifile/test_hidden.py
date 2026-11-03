import unittest
from invoice import total

class HiddenInvoiceTests(unittest.TestCase):
    def test_unknown_country_and_rounding(self):
        self.assertEqual(total([0.335, 0.335], "XX"), 0.67)
