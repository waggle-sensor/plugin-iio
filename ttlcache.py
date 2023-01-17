import time


class TTLCache:

    def __init__(self, time_func=time.monotonic):
        self.cache = {}
        self.time_func = time_func
    
    def __getitem__(self, key):
        item, time, ttl = self.cache[key]
        if self.time_func() - time > ttl:
            raise KeyError(key)
        return item
    
    def set(self, key, value, ttl):
        time = self.time_func()
        self.cache[key] = (value, time, ttl)
