# Mini Redis Kanban

Source: [requirements](requirements). Deliverable: Python 3.8+ CLI Mini Redis. Required scope excludes networking, persistence, complex Redis types, and concurrency.

Move cards from **Backlog → Ready → In progress → Verify → Done**. A required card is Done only when its implementation, relevant tests, and documentation are complete.

## Backlog — optional bonuses

| ID | Task | Acceptance criteria |
| --- | --- | --- |
| B1 | Standalone dynamic array | append/get/set/remove; explicit capacity doubling. Heap already uses manual array growth, but this reusable API is not implemented. |
| B2 | Stack/queue/deque study | Add `STACK_QUEUE_DEQUE.md` explaining operations and applications. |
| B3 | Binary tree | Implement preorder, inorder, postorder, and level-order traversal. |
| B4 | Binary search tree | Implement insert/search/delete and sorted inorder traversal. |
| B5 | Pub/Sub | Add PUBLISH/SUBSCRIBE with channel messaging and linked-list message buffers. |

## Ready

No required cards remaining.

## In progress

None.

## Verify

None. All required cards passed validation.

## Done

| ID | Requirement / acceptance criteria | Implementation | Evidence |
| --- | --- | --- | --- |
| R1 | Independent doubly linked list; six O(1) node operations | `mini_redis/linked_list.py` | List operations and link invariants |
| R2 | Custom hash, chaining, put/get/remove/contains/keys/size, resize above 0.75 | `mini_redis/hash_map.py` | Forced collisions, growth threshold, Unicode keys |
| R3 | Minimum heap; push/pop/peek/size and both heapify directions | `mini_redis/min_heap.py` | Shuffled tuple ordering and array growth |
| R4 | SET/GET/DEL/EXISTS/DBSIZE/KEYS with Redis-style results | `mini_redis/store.py` | Basic commands, overwrite, empty keys/values |
| R5 | UTF-8 byte accounting; CONFIG/INFO; unlimited zero; LRU eviction; OOM | `mini_redis/store.py` | Memory totals, read/write recency, multiple evictions, atomic OOM |
| R6 | Heap TTL; missing/no-expiry sentinels; immediate expiry; overwrite resets TTL | `mini_redis/store.py` | Fake-clock boundaries, reschedule, delete/recreate, compaction |
| R7 | Prompt, parsing, quoting, standardized errors, exit/quit | `mini_redis/__main__.py` | Subprocess REPL, EOF/exit, command and integer errors |
| R8 | Python 3.8-compatible source; independent modules; docstrings; no forbidden collections | `mini_redis/` | Source review and syntax compatibility check |
| R9 | Explain implementation, decisions, run and verification commands | `README.md` | Architecture and usage documentation |

## Validation

- `python3 -m unittest discover -s tests -v`: **18 tests passed** on Python 3.14.7.
- All six runtime modules passed Python 3.8 grammar parsing and an AST check for forbidden collection literals/helpers/imports. Python 3.8 itself was not available for a runtime test.
- Optional bonuses are not claimed as completed.
