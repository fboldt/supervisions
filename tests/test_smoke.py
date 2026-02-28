import unittest

from supervisions.main import get_message


class SmokeTest(unittest.TestCase):
    def test_message(self) -> None:
        self.assertEqual(get_message(), "supervisions scaffold is ready")


if __name__ == "__main__":
    unittest.main()
