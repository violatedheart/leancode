import unittest

from api import list_items


class PaginationTests(unittest.TestCase):
    def test_zero_based_cursor_and_next_only_when_more(self):
        values = ["a", "b", "c"]
        self.assertEqual(list_items(values, 2), {"items": ["a", "b"], "next_cursor": "2"})
        self.assertEqual(list_items(values, 2, "2"), {"items": ["c"], "next_cursor": None})
