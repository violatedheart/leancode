import unittest
from app import user_label
from helpers import find_user

class TestUsers(unittest.TestCase):
    def test_case_insensitive_lookup(self):
        users = [{"username": "Ada", "display": "Ada Lovelace"}]
        self.assertEqual(user_label(users, "ada"), "Ada Lovelace")
        self.assertEqual(find_user(users, "missing"), None)

if __name__ == "__main__": unittest.main()
