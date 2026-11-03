import unittest
from parse_value import parse_bool

class HiddenBoolTests(unittest.TestCase):
    def test_zero_one_and_invalid(self):
        self.assertIs(parse_bool("0"), False)
        self.assertIs(parse_bool("1"), True)
        with self.assertRaises(ValueError): parse_bool("maybe")
