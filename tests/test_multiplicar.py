import unittest
from calculadora import multiplicar


class TestMultiplicar(unittest.TestCase):
    def test_dos_positivos(self):
        self.assertEqual(multiplicar(6, 7), 42)

    def test_signos(self):
        self.assertEqual(multiplicar(-3, 4), -12)

    def test_cero(self):
        self.assertEqual(multiplicar(99, 0), 0)


if __name__ == "__main__":
    unittest.main()
