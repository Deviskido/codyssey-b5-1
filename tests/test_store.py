"""Command semantics tested without sleeping or wall-clock dependencies."""

import unittest

from mini_redis.store import INTEGER_ERROR, OOM_ERROR, MiniRedis


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.now = 100.0
        self.store = MiniRedis(clock=lambda: self.now)

    def run_command(self, command, expected):
        self.assertEqual(self.store.execute(command), expected, command)
        entries = [self.store.data.get(key) for key in self.store.data.keys()]
        self.assertEqual(self.store.used_memory, sum(entry.byte_size for entry in entries))
        self.assertEqual(self.store.data.size(), self.store.lru.size)
        self.assertEqual(sorted(self.store.data.keys()), sorted(self.store.lru))

    def test_basic_commands(self):
        self.run_command("KEYS", "(empty array)")
        self.run_command("GET a", "(nil)")
        self.run_command('set a "Alice Smith"', "OK")
        self.run_command("GET a", '"Alice Smith"')
        self.run_command("EXISTS a", "(integer) 1")
        self.run_command("DBSIZE", "(integer) 1")
        self.run_command("KEYS", '1. "a"')
        self.run_command("DEL a", "(integer) 1")
        self.run_command("DEL a", "(integer) 0")
        self.run_command("EXISTS a", "(integer) 0")
        self.run_command('SET "" ""', "OK")
        self.run_command('GET ""', '""')

    def test_utf8_accounting_and_overwrite(self):
        self.run_command('SET 한 "글"', "OK")
        self.run_command("INFO memory", "used_memory:6\nmaxmemory:0\nevicted_keys:0")
        self.run_command("SET 한 a", "OK")
        self.assertEqual(self.store.used_memory, 4)
        self.run_command("DEL 한", "(integer) 1")
        self.assertEqual(self.store.used_memory, 0)

    def test_lru_get_and_set(self):
        self.run_command("CONFIG SET maxmemory 4", "OK")
        for key in ("a", "b"):
            self.run_command("SET " + key + " x", "OK")
        self.run_command("GET a", '"x"')
        self.run_command("SET c x", "OK")
        self.run_command("GET b", "(nil)")
        self.assertEqual(self.store.evicted_keys, 1)
        self.run_command("SET a y", "OK")
        self.run_command("SET d z", "OK")
        self.run_command("GET c", "(nil)")
        self.assertEqual(self.store.evicted_keys, 2)

    def test_non_access_commands_do_not_touch_lru(self):
        for key in ("a", "b"):
            self.run_command("SET " + key + " x", "OK")
        self.run_command("EXISTS a", "(integer) 1")
        self.run_command("EXPIRE a 20", "(integer) 1")
        self.run_command("TTL a", "(integer) 20")
        self.run_command("CONFIG SET maxmemory 2", "OK")
        self.run_command("GET a", "(nil)")
        self.run_command("GET b", '"x"')

    def test_oom_preserves_value_and_ttl(self):
        self.run_command("CONFIG SET maxmemory 4", "OK")
        self.run_command("SET a x", "OK")
        self.run_command("EXPIRE a 10", "(integer) 1")
        self.run_command("SET a oversized", OOM_ERROR)
        self.run_command("SET new oversized", OOM_ERROR)
        self.run_command("GET a", '"x"')
        self.run_command("TTL a", "(integer) 10")
        self.assertEqual(self.store.evicted_keys, 0)

    def test_multiple_evictions_and_unlimited(self):
        self.run_command("CONFIG SET maxmemory 6", "OK")
        for key in ("a", "b", "c"):
            self.run_command("SET " + key + " x", "OK")
        self.run_command("SET d 12345", "OK")
        self.assertEqual(self.store.evicted_keys, 3)
        self.run_command("DBSIZE", "(integer) 1")
        self.run_command("CONFIG SET maxmemory 0", "OK")
        self.run_command("SET e unlimited", "OK")
        self.run_command("DBSIZE", "(integer) 2")

    def test_ttl_boundary_and_global_sweep(self):
        self.run_command("TTL missing", "(integer) -2")
        self.run_command("EXPIRE missing 10", "(integer) 0")
        self.run_command("SET a x", "OK")
        self.run_command("TTL a", "(integer) -1")
        self.run_command("EXPIRE a 3", "(integer) 1")
        self.now += 0.1
        self.run_command("TTL a", "(integer) 2")
        self.now = 103
        self.run_command("DBSIZE", "(integer) 0")
        self.run_command("KEYS", "(empty array)")
        self.run_command("GET a", "(nil)")
        self.run_command("TTL a", "(integer) -2")
        self.assertEqual(self.store.evicted_keys, 0)

    def test_stale_expiration_after_reschedule_overwrite_and_recreate(self):
        self.run_command("SET a old", "OK")
        self.run_command("EXPIRE a 2", "(integer) 1")
        self.run_command("EXPIRE a 4", "(integer) 1")
        self.now = 102
        self.run_command("GET a", '"old"')
        self.run_command("SET a new", "OK")
        self.run_command("TTL a", "(integer) -1")
        self.now = 104
        self.run_command("GET a", '"new"')
        self.run_command("EXPIRE a 2", "(integer) 1")
        self.run_command("DEL a", "(integer) 1")
        self.run_command("SET a recreated", "OK")
        self.run_command("EXPIRE a 5", "(integer) 1")
        self.now = 106
        self.run_command("GET a", '"recreated"')
        self.now = 109
        self.run_command("GET a", "(nil)")

    def test_immediate_expiry(self):
        for seconds in (0, -1):
            self.run_command("SET a x", "OK")
            self.run_command("EXPIRE a " + str(seconds), "(integer) 1")
            self.run_command("EXISTS a", "(integer) 0")

    def test_expiration_precedes_eviction(self):
        self.run_command("CONFIG SET maxmemory 4", "OK")
        self.run_command("SET a x", "OK")
        self.run_command("SET b x", "OK")
        self.run_command("EXPIRE b 1", "(integer) 1")
        self.now += 1
        self.run_command("SET c x", "OK")
        self.assertEqual(self.store.evicted_keys, 0)
        self.run_command("GET a", '"x"')

    def test_heap_tombstones_are_bounded(self):
        self.run_command("SET a x", "OK")
        for i in range(200):
            self.run_command("EXPIRE a " + str(i + 1), "(integer) 1")
        self.assertLessEqual(self.store.expirations.size(), 64)
        self.now += 200
        self.run_command("GET a", "(nil)")

    def test_errors(self):
        self.run_command("HELLO", "(error) ERR unknown command 'HELLO'")
        for command in ("SET", "GET", "DEL", "EXISTS", "DBSIZE x", "KEYS x", "CONFIG", "INFO", "EXPIRE", "TTL"):
            self.run_command(command, "(error) ERR wrong number of arguments for '{}' command".format(command.split()[0]))
        for value in ("abc", "1.1", "1_000", "--1", "9223372036854775808", "١"):
            self.run_command("CONFIG SET maxmemory " + value, INTEGER_ERROR)
            self.run_command("EXPIRE missing " + value, INTEGER_ERROR)
        self.run_command("CONFIG SET maxmemory -1", INTEGER_ERROR)
        self.run_command('SET a "unterminated', "(error) ERR unbalanced quotes in request")
        self.run_command("INFO other", "(error) ERR unsupported INFO section")
        self.run_command("CONFIG GET other 1", "(error) ERR unsupported CONFIG option")
        self.run_command("  ", "")
