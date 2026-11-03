import unittest
from palindrome import is_palindrome

class HiddenPalindromeTests(unittest.TestCase):
    def test_unicode_and_empty(self):
        self.assertTrue(is_palindrome("Ésope reste ici et se repose"))
        self.assertTrue(is_palindrome("..."))
