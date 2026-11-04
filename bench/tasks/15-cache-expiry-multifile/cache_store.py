class TTLCache:
    def __init__(self):
        self.entries = {}

    def put(self, key, value, now, ttl):
        self.entries[key] = (value, now + ttl)

    def get(self, key, now):
        entry = self.entries.get(key)
        if entry is None:
            return None
        value, deadline = entry
        if now > deadline:
            self.entries.pop(key, None)
            return None
        return value
