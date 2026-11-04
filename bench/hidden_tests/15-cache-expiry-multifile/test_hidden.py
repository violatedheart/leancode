import unittest

from cache_api import lookup
from cache_store import TTLCache


class CacheExpiryTests(unittest.TestCase):
    def test_exact_deadline_is_expired_and_removed(self):
        cache = TTLCache()
        cache.put("a", 3, 10, 5)
        self.assertIsNone(lookup(cache, "a", 15))
        self.assertNotIn("a", cache.entries)

    def test_live_value_is_returned(self):
        cache = TTLCache()
        cache.put("a", 3, 10, 5)
        self.assertEqual(lookup(cache, "a", 14.99), 3)
