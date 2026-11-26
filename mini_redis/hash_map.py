"""String-key hash map using explicit hashing and list chaining."""

from .linked_list import DoublyLinkedList


class HashMap:
    """Expected O(1) lookups; double buckets above 0.75 load."""

    def __init__(self, capacity=8):
        if capacity < 1:
            raise ValueError("capacity must be positive")
        self._buckets = [None] * capacity
        self._size = 0

    @staticmethod
    def _hash(key):
        # Polynomial rolling hash over UTF-8 bytes, bounded to 64 bits.
        value = 0
        for byte in key.encode("utf-8"):
            value = (value * 131 + byte) & 0xFFFFFFFFFFFFFFFF
        return value

    def _find(self, key):
        bucket = self._buckets[self._hash(key) % len(self._buckets)]
        node = bucket.head if bucket is not None else None
        while node is not None:
            if node.data[0] == key:
                return bucket, node
            node = node.next
        return bucket, None

    def put(self, key, value):
        bucket, node = self._find(key)
        if node is not None:
            node.data = (key, value)
            return
        index = self._hash(key) % len(self._buckets)
        if bucket is None:
            bucket = DoublyLinkedList()
            self._buckets[index] = bucket
        bucket.insert_back((key, value))
        self._size += 1
        if self._size * 4 > len(self._buckets) * 3:
            old = self._buckets
            self._buckets = [None] * (len(old) * 2)
            self._size = 0
            for chain in old:
                if chain is not None:
                    for old_key, old_value in chain:
                        self.put(old_key, old_value)

    def get(self, key, default=None):
        _, node = self._find(key)
        return default if node is None else node.data[1]

    def contains(self, key):
        return self._find(key)[1] is not None

    def remove(self, key):
        bucket, node = self._find(key)
        if node is None:
            return False
        bucket.remove_node(node)
        self._size -= 1
        return True

    def keys(self):
        for bucket in self._buckets:
            if bucket is not None:
                for key, _ in bucket:
                    yield key

    def size(self):
        return self._size
