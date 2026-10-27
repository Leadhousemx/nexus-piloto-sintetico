"""Caso sintético para comparar identidad GitHub App y Actions."""
import unittest
from calculadora import sumar


class TestFirmaIndependiente(unittest.TestCase):
    def test_operacion(self):
        self.assertEqual(sumar(20, 22), 42)


if __name__ == "__main__":
    unittest.main()
