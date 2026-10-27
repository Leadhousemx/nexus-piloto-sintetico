# Piloto sintético de Nexus

Este repositorio es exclusivamente de pruebas. No contiene código, claves ni datos de Brentrix.

## Primera iteración

- Un cambio de código Python real y tres pruebas con `unittest`.
- Workflow `Piloto CI` sobre PR a `main` y push a `main`, sin secretos y con permiso `contents: read`.
- Script `verificar_pr.py` de solo lectura que consulta el SHA del PR, checks GitHub Actions de ese SHA, cambios de workflows y reviews; **nunca** hace merge, deploy ni afirma `DONE`.
- Inicialmente el PR agrega el propio workflow, por lo que el verificador debe señalar `CAMBIO_DE_CI_REQUIERE_APROBACION_HUMANA`. No se toma ese resultado como aprobación automática.

## Ejecutar localmente

```bash
python -m unittest discover -s tests -p 'test_*.py' -v
python verificar_pr.py Leadhousemx/nexus-piloto-sintetico 1
```

## Seguridad y alcance

No ejecutar código de PR con `pull_request_target`; no proporcionar tokens de escritura a jobs del PR. Los check-runs son evidencia de CI, no de aprobación independiente, integridad inmutable del workflow ni despliegue. **Los rulesets aún deben configurarse fuera de este PR.**

La prueba negativa de push directo solo se considera demostrada cuando GitHub la rechaza con un ruleset activo. Los tests negativos de revisión, commit cambiado y rollback se ejecutarán en fases posteriores, con evidencia concreta. No existen todavía staging ni despliegues.
