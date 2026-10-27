"""Prueba sintética para activar la evaluación de la GitHub App."""
import unittest
from calculadora import multiplicar, restar


class TestFirmaPolitica(unittest.TestCase):
    def test_valor(self):
        self.assertEqual(restar(multiplicar(8, 8), 4), 60)


if __name__ == "__main__":
    unittest.main()
