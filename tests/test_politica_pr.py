import unittest
from politica_pr import evaluate, path_allowed

SHA = 'a' * 40
WF = 345


def fixtures():
    run = dict(event='pull_request', name='Piloto CI', workflow_id=WF,
               conclusion='success', status='completed', head_sha=SHA)
    pr = dict(state='open', draft=False, base={'ref': 'main', 'repo': {'full_name': 'owner/test'}},
              head={'sha': SHA, 'repo': {'full_name': 'owner/test'}}, changed_files=2)
    files = [dict(filename='calculadora.py', status='modified'),
             dict(filename='tests/test_multiplicar.py', status='added')]
    return run, pr, files


class TestPoliticas(unittest.TestCase):
    def test_camino_valido(self):
        self.assertEqual(evaluate(*fixtures(), WF), [])

    def test_ci_roja(self):
        run, pr, files = fixtures()
        run['conclusion'] = 'failure'
        self.assertIn('CI_NO_APROBADA', evaluate(run, pr, files, WF))

    def test_head_movido(self):
        run, pr, files = fixtures()
        pr['head']['sha'] = 'b' * 40
        self.assertIn('SHA_DESACTUALIZADO', evaluate(run, pr, files, WF))

    def test_workflow_suplantado(self):
        run, pr, files = fixtures()
        run['workflow_id'] = WF + 1
        self.assertIn('WORKFLOW_ID_INVALIDO', evaluate(run, pr, files, WF))

    def test_draft(self):
        run, pr, files = fixtures()
        pr['draft'] = True
        self.assertIn('PR_NO_LISTO', evaluate(run, pr, files, WF))

    def test_archivo_workflow(self):
        run, pr, files = fixtures()
        files[1]['filename'] = '.github/workflows/piloto-ci.yml'
        self.assertIn('RUTA_NO_AUTORIZADA', evaluate(run, pr, files, WF))

    def test_fork(self):
        run, pr, files = fixtures()
        pr['head']['repo']['full_name'] = 'external/fork'
        self.assertIn('FORK_NO_ADMITIDO', evaluate(run, pr, files, WF))

    def test_lista_incompleta(self):
        run, pr, files = fixtures()
        pr['changed_files'] = 3
        self.assertIn('LISTADO_ARCHIVOS_INCOMPLETO', evaluate(run, pr, files, WF))

    def test_renombrado_y_borrado(self):
        run, pr, files = fixtures()
        files[1]['status'] = 'removed'
        self.assertIn('OPERACION_ARCHIVO_NO_AUTORIZADA', evaluate(run, pr, files, WF))

    def test_restriccion_rutas(self):
        self.assertTrue(path_allowed('tests/test_operacion.py'))
        self.assertFalse(path_allowed('tests/helpers/malicioso.py'))
        self.assertFalse(path_allowed('.github/workflows/revisor.yml'))
        self.assertFalse(path_allowed('verificar_pr.py'))


if __name__ == '__main__':
    unittest.main()
