# Mini Redis

Python 3.8+ CLI implementation of the supplied [requirements](requirements). No third-party dependencies, networking, persistence, or concurrency. Project work is tracked in [KANBAN.md](KANBAN.md).

## Run

```sh
python3 -m mini_redis
```

Use `quit`, `exit`, EOF, or Ctrl-C to stop. Commands are case-insensitive. Keys and values are case-sensitive; quote values containing spaces.

```text
mini-redis> CONFIG SET maxmemory 30
OK
mini-redis> SET user:1 "Alice"
OK
mini-redis> SET user:2 "Bob"
OK
mini-redis> SET user:3 "Charlie"
OK
mini-redis> GET user:1
(nil)
mini-redis> INFO memory
used_memory:22
maxmemory:30
evicted_keys:1
mini-redis> EXPIRE user:2 3
(integer) 1
```

## Commands

| Command | Behavior |
| --- | --- |
| `SET key value` | Store a string, clear existing TTL, mark most recently used |
| `GET key` | Return a quoted value or `(nil)`; successful reads update LRU |
| `DEL key` | Delete; return 1 or 0 |
| `EXISTS key` | Return 1 or 0 without updating LRU |
| `DBSIZE` | Count live keys |
| `KEYS` | List live keys; no patterns or order guarantee |
| `CONFIG SET maxmemory bytes` | Nonnegative byte limit; 0 means unlimited |
| `INFO memory` | Show used memory, limit, and cumulative LRU evictions |
| `EXPIRE key seconds` | Set TTL; nonpositive seconds delete immediately |
| `TTL key` | Whole remaining seconds; -1 for no TTL, -2 for absent key |

Integers must be signed 64-bit decimal values. Shell-style quoting supports empty strings, quoted spaces, and escaped quotes. Malformed commands return errors and leave the REPL running.

## Implementation and decisions

- `linked_list.py`: independent doubly linked list. Nodes hold `prev`, `next`, and `data`. Direct node references make insertion, removal, and moving to the front O(1).
- `hash_map.py`: custom polynomial UTF-8 hash with doubly linked collision chains. Buckets double when load exceeds 0.75. Lookup is expected O(1), with O(n) worst-case collisions; insertion is amortized expected O(1).
- `min_heap.py`: manually doubled array with explicit upward/downward heap repair. Push/pop are O(log n); peek is O(1). Fixed-capacity Python lists provide indexed storage only.
- `store.py`: map entries reference their LRU nodes. The head is most recently used; the tail is evicted first. Memory counts only UTF-8 bytes of live keys plus values. Oversized single writes fail before changing existing values, TTLs, or LRU order.
- TTL records contain `(expire_at, generation, key)`. Unique generations prevent old records from deleting recreated keys. DEL, overwrite, and eviction invalidate TTL records logically; stale heap records are ignored and periodically compacted to bound accumulation. This is the requirements' permitted lazy deletion strategy.
- Every command first removes all due expirations, so KEYS, DBSIZE, INFO, and eviction see live data. Time uses a monotonic clock; no background thread is needed. While the CLI is idle, cleanup waits for the next command.
- TTL rounds down to whole seconds. Expiration does not increment `evicted_keys`. Lowering `maxmemory` evicts immediately; 0 disables the limit. Only successful SET and GET update recency.

Runtime code does not use `dict`, `set`, `collections`, built-in hashing, `heapq`, or an existing cache implementation. Standard-library parsing/time utilities do not replace the custom structures.

## Verify

```sh
python3 -m unittest discover -s tests -v
```

Tests cover structural invariants, forced collisions and resizing, heap ordering, all commands and errors, UTF-8 accounting, multiple evictions, OOM atomicity, TTL boundaries, stale expiration records, and the real REPL. An injected clock avoids timing-dependent sleeps.

Optional bonus structures and Pub/Sub are tracked separately in the Kanban backlog.
# codyssey-b5-1
