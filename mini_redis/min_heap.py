"""Binary minimum heap backed by a manually grown array."""


class MinHeap:
    """O(log n) push/pop and O(1) peek; elements must be comparable."""

    def __init__(self):
        self._items = [None] * 8
        self._size = 0

    def size(self):
        return self._size

    def peek(self):
        return self._items[0] if self._size else None

    def push(self, item):
        if self._size == len(self._items):
            grown = [None] * (len(self._items) * 2)
            for i in range(self._size):
                grown[i] = self._items[i]
            self._items = grown
        self._items[self._size] = item
        self._size += 1
        self._heapify_up(self._size - 1)

    def pop(self):
        if not self._size:
            return None
        result = self._items[0]
        self._size -= 1
        self._items[0] = self._items[self._size]
        self._items[self._size] = None
        if self._size:
            self._heapify_down(0)
        return result

    def _heapify_up(self, index):
        while index:
            parent = (index - 1) // 2
            if self._items[parent] <= self._items[index]:
                break
            self._items[parent], self._items[index] = self._items[index], self._items[parent]
            index = parent

    def _heapify_down(self, index):
        while index * 2 + 1 < self._size:
            child = index * 2 + 1
            if child + 1 < self._size and self._items[child + 1] < self._items[child]:
                child += 1
            if self._items[index] <= self._items[child]:
                break
            self._items[index], self._items[child] = self._items[child], self._items[index]
            index = child
