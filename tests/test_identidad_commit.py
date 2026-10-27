"""Prueba de aritmética sintética: el verificador debe evaluar el nuevo HEAD."""
import unittest
from calculadora import sumar, restar, multiplicar


class TestIdentidadCommit(unittest.TestCase):
    def test_operaciones(self):
        self.assertEqual(restar(multiplicar(9, 2), sumar(3, 4)), 11)


if __name__ == "__main__":
    unittest.main()
