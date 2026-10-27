import unittest
from calculadora import sumar, restar


class TestCalculadora(unittest.TestCase):
    def test_sumar(self):
        self.assertEqual(sumar(7, 5), 12)

    def test_restar(self):
        self.assertEqual(restar(7, 5), 2)

    def test_restar_negativos(self):
        self.assertEqual(restar(5, 7), -2)


if __name__ == "__main__":
    unittest.main()
