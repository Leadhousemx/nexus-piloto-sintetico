"""Caso sintético para disparar CI y el gate de políticas confiable."""
import unittest
from calculadora import multiplicar, sumar


class TestPropiedadAritmetica(unittest.TestCase):
    def test_distributividad(self):
        a, b, c = 4, 5, 7
        self.assertEqual(multiplicar(a, sumar(b, c)),
                         sumar(multiplicar(a, b), multiplicar(a, c)))


if __name__ == "__main__":
    unittest.main()
