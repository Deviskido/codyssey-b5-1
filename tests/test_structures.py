"""Structural invariants and collision/resize behavior."""

import random
import unittest

from mini_redis.hash_map import HashMap
from mini_redis.linked_list import DoublyLinkedList
from mini_redis.min_heap import MinHeap


class StructureTests(unittest.TestCase):
    def test_list_operations(self):
        linked = DoublyLinkedList()
        self.assertIsNone(linked.remove_front())
        self.assertIsNone(linked.remove_back())
        a = linked.insert_front("a")
        b = linked.insert_back("b")
        c = linked.insert_front("c")
        linked.move_to_front(b)
        self.assertEqual(list(linked), ["b", "c", "a"])
        self.assertIs(linked.head.next.prev, b)
        self.assertEqual(linked.remove_node(c), "c")
        self.assertEqual(linked.remove_back(), "a")
        self.assertEqual(linked.remove_front(), "b")
        self.assertEqual(linked.size, 0)
        self.assertIsNone(linked.head)
        self.assertIsNone(linked.tail)
        with self.assertRaises(ValueError):
            linked.remove_node(a)

    def test_hash_collisions_and_resize(self):
        class CollisionMap(HashMap):
            @staticmethod
            def _hash(key):
                return 0

        table = CollisionMap(4)
        for i in range(100):
            table.put(str(i), i)
        self.assertEqual(table.size(), 100)
        self.assertEqual(len(table._buckets), 256)
        for i in range(100):
            self.assertEqual(table.get(str(i)), i)
        table.put("0", None)
        self.assertTrue(table.contains("0"))
        self.assertEqual(table.size(), 100)
        for key in ("0", "50", "99"):
            self.assertTrue(table.remove(key))
            self.assertFalse(table.remove(key))
        self.assertEqual(table.size(), 97)
        self.assertEqual(len(list(table.keys())), 97)

    def test_hash_threshold_and_unicode(self):
        table = HashMap(4)
        for key in ("a", "b", "한글"):
            table.put(key, key)
        self.assertEqual(len(table._buckets), 4)
        table.put("four", 4)
        self.assertEqual(len(table._buckets), 8)
        self.assertEqual(table.get("한글"), "한글")
        self.assertIsNone(table.get("missing"))

    def test_heap_order_and_growth(self):
        heap = MinHeap()
        self.assertIsNone(heap.pop())
        self.assertIsNone(heap.peek())
        items = [(i % 13, str(i)) for i in range(200)]
        random.Random(42).shuffle(items)
        for item in items:
            heap.push(item)
        self.assertEqual(heap.peek(), min(items))
        self.assertEqual([heap.pop() for _ in items], sorted(items))
        self.assertEqual(heap.size(), 0)
        heap.push((1, "again"))
        self.assertEqual(heap.pop(), (1, "again"))
