import unittest
from ttlcache import TTLCache


class TestTTLCache(unittest.TestCase):

    def test_raises_on_nonexist(self):
        cache = TTLCache()

        with self.assertRaises(KeyError):
            cache["not-here"]

    def test_set_get(self):
        now = 11.0
        def mock_time_func(): return now

        cache = TTLCache(time_func=mock_time_func)

        # 1. set value and immediately check get is ok
        cache.set("a", (1, 2), ttl=3)
        self.assertEqual(cache["a"], (1, 2))

        # 2. advance time
        now += 2.0

        # 3. check that get is still ok
        self.assertEqual(cache["a"], (1, 2))

        # 4. advance time
        now += 1.01

        # 5. key should be expired now
        with self.assertRaises(KeyError):
            cache["a"]


if __name__ == "__main__":
    unittest.main()
