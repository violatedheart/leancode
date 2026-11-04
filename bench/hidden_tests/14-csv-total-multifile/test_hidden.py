import unittest

from report import total_amount


class CsvTotalTests(unittest.TestCase):
    def test_decimal_sum_is_exact(self):
        self.assertEqual(total_amount([{"amount": "0.10"}, {"amount": "0.20"}]), 0.30)

    def test_blank_rows_are_ignored(self):
        self.assertEqual(total_amount([{"amount": "1.25"}, {"amount": ""}, {}]), 1.25)
