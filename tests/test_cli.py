"""Exercise the actual CLI process and exit paths."""

import subprocess
import sys
import unittest


class CLITests(unittest.TestCase):
    def test_repl(self):
        result = subprocess.run(
            [sys.executable, "-m", "mini_redis"],
            input='SET user "Alice Smith"\nGET user\nHELLO\nquit\nSET ignored x\n',
            text=True, capture_output=True, check=True,
        )
        self.assertIn("mini-redis> OK", result.stdout)
        self.assertIn('mini-redis> "Alice Smith"', result.stdout)
        self.assertIn("(error) ERR unknown command 'HELLO'", result.stdout)
        self.assertEqual(result.stdout.count("OK"), 1)
        self.assertEqual(result.stderr, "")

    def test_eof_and_exit(self):
        for text in ("", "exit\n"):
            result = subprocess.run([sys.executable, "-m", "mini_redis"], input=text, text=True, capture_output=True)
            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stderr, "")
