"""Run with python3 -m mini_redis."""

from .store import MiniRedis


def main():
    """Interactive command loop; EOF, Ctrl-C, exit and quit end cleanly."""
    store = MiniRedis()
    while True:
        try:
            line = input("mini-redis> ")
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if line.strip().lower() in ("exit", "quit"):
            break
        result = store.execute(line)
        if result:
            print(result)


if __name__ == "__main__":
    main()
