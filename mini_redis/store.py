"""Command execution, exact UTF-8 accounting, LRU and lazy heap expiry."""

import math
import shlex
import time

from .hash_map import HashMap
from .linked_list import DoublyLinkedList
from .min_heap import MinHeap


INTEGER_ERROR = "(error) ERR value is not an integer or out of range"
OOM_ERROR = "(error) OOM command not allowed when used_memory > 'maxmemory'"


class Entry:
    """Live value with its LRU node and current expiry generation."""

    def __init__(self, value, node, byte_size):
        self.value = value
        self.node = node
        self.byte_size = byte_size
        self.expire_at = None
        self.generation = 0


class MiniRedis:
    """Expire due keys before every command; clock injection enables exact tests."""

    def __init__(self, clock=time.monotonic):
        self.data = HashMap()
        self.lru = DoublyLinkedList()
        self.expirations = MinHeap()
        self.used_memory = 0
        self.maxmemory = 0
        self.evicted_keys = 0
        self._generation = 0
        self._clock = clock

    def _delete(self, key):
        entry = self.data.get(key)
        if entry is None:
            return 0
        self.used_memory -= entry.byte_size
        self.lru.remove_node(entry.node)
        self.data.remove(key)
        # Heap records are tombstones after removal: generations never repeat.
        return 1

    def _expire_due(self, now):
        while self.expirations.size() and self.expirations.peek()[0] <= now:
            deadline, generation, key = self.expirations.pop()
            entry = self.data.get(key)
            if entry is not None and entry.generation == generation and entry.expire_at == deadline:
                self._delete(key)

    def _compact_expirations(self):
        # Bound lazy tombstones after repeated EXPIRE/SET/DEL operations.
        if self.expirations.size() > max(64, self.data.size() * 2):
            heap = MinHeap()
            for key in self.data.keys():
                entry = self.data.get(key)
                if entry.expire_at is not None:
                    heap.push((entry.expire_at, entry.generation, key))
            self.expirations = heap

    def _evict(self):
        while self.maxmemory and self.used_memory > self.maxmemory:
            self._delete(self.lru.tail.data)
            self.evicted_keys += 1

    @staticmethod
    def _integer(text):
        digits = text[1:] if text[:1] in ("+", "-") else text
        if not digits or any(c < "0" or c > "9" for c in digits):
            raise ValueError
        number = int(text)
        if number < -(2 ** 63) or number > 2 ** 63 - 1:
            raise ValueError
        return number

    @staticmethod
    def _quote(value):
        return '"' + value.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t') + '"'

    def execute(self, line):
        """Parse one command and return its Redis-style text response."""
        now = self._clock()
        self._expire_due(now)
        try:
            args = shlex.split(line)
        except ValueError:
            return "(error) ERR unbalanced quotes in request"
        if not args:
            return ""
        try:
            return self._execute(args, now)
        finally:
            self._compact_expirations()

    def _execute(self, args, now):
        cmd = args[0].upper()
        commands = ("SET", "GET", "DEL", "EXISTS", "DBSIZE", "KEYS", "CONFIG", "INFO", "EXPIRE", "TTL")
        arities = (3, 2, 2, 2, 1, 1, 4, 2, 3, 2)
        if cmd not in commands:
            return "(error) ERR unknown command '{}'".format(args[0])
        if len(args) != arities[commands.index(cmd)]:
            return "(error) ERR wrong number of arguments for '{}' command".format(args[0])
        if cmd == "CONFIG":
            if args[1].upper() != "SET" or args[2].lower() != "maxmemory":
                return "(error) ERR unsupported CONFIG option"
            try:
                limit = self._integer(args[3])
                if limit < 0:
                    raise ValueError
            except ValueError:
                return INTEGER_ERROR
            self.maxmemory = limit
            self._evict()
            return "OK"
        if cmd == "INFO":
            if args[1].lower() != "memory":
                return "(error) ERR unsupported INFO section"
            return "used_memory:{}\nmaxmemory:{}\nevicted_keys:{}".format(self.used_memory, self.maxmemory, self.evicted_keys)
        if cmd == "DBSIZE":
            return "(integer) {}".format(self.data.size())
        if cmd == "KEYS":
            return "\n".join("{}. {}".format(i, self._quote(key)) for i, key in enumerate(self.data.keys(), 1)) or "(empty array)"
        key = args[1]
        entry = self.data.get(key)
        if cmd == "SET":
            byte_size = len(key.encode("utf-8")) + len(args[2].encode("utf-8"))
            if self.maxmemory and byte_size > self.maxmemory:
                return OOM_ERROR
            if entry is not None:
                self._delete(key)
            self.data.put(key, Entry(args[2], self.lru.insert_front(key), byte_size))
            self.used_memory += byte_size
            self._evict()
            return "OK"
        if cmd == "GET":
            if entry is None:
                return "(nil)"
            self.lru.move_to_front(entry.node)
            return self._quote(entry.value)
        if cmd == "DEL":
            return "(integer) {}".format(self._delete(key))
        if cmd == "EXISTS":
            return "(integer) {}".format(int(entry is not None))
        if cmd == "EXPIRE":
            try:
                seconds = self._integer(args[2])
            except ValueError:
                return INTEGER_ERROR
            if entry is None:
                return "(integer) 0"
            if seconds <= 0:
                self._delete(key)
            else:
                self._generation += 1
                entry.generation = self._generation
                entry.expire_at = now + seconds
                self.expirations.push((entry.expire_at, entry.generation, key))
            return "(integer) 1"
        if entry is None:
            return "(integer) -2"
        if entry.expire_at is None:
            return "(integer) -1"
        return "(integer) {}".format(max(0, math.floor(entry.expire_at - now)))
