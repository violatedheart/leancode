import unittest
from palindrome import is_palindrome

class TestPalindrome(unittest.TestCase):
    def test_plain(self):
        self.assertTrue(is_palindrome("Never odd or even!"))
    def test_false(self):
        self.assertFalse(is_palindrome("hello"))

if __name__ == "__main__": unittest.main()
