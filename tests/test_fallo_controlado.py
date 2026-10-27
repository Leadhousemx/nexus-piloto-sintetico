"""Prueba negativa sintética intencional: este PR NO debe fusionarse."""
import unittest


class TestFalloControlado(unittest.TestCase):
    def test_ci_detecta_resultado_incorrecto(self):
        self.assertEqual(7, 12, "FALLO_INTENCIONAL_PILOTO: comprobar bloqueo de CI")


if __name__ == "__main__":
    unittest.main()
