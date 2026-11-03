import unittest
from parse_value import parse_bool

class TestParseBool(unittest.TestCase):
    def test_values(self):
        self.assertIs(parse_bool(" YES "), True)
        self.assertIs(parse_bool("Off"), False)
        self.assertIs(parse_bool(True), True)

if __name__ == "__main__": unittest.main()
