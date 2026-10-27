# Migración del control de políticas a una GitHub App independiente

Alcance: sólo `Leadhousemx/nexus-piloto-sintetico`, sin acceso a Brentrix.

## Motivo

El PR #5 demostró que un workflow de PR puede publicar un check llamado
`Piloto / Politicas` como `github-actions` sin haber ejecutado la política.
Por tanto, ni el nombre ni `github-actions` son identidad independiente.

Esta actualización restringe la publicación a un token de instalación de la App
`nx-piloto-policy-2026` (o al slug que efectivamente se haya registrado).

## Requisitos administrativos **ANTES del merge de este PR**

1. En los ajustes de la GitHub App, verificar permisos:
   Checks **Read & write**, Actions **Read-only**, Contents **Read-only**,
   Pull requests **Read-only**, resto sin acceso.
2. Instalarla usando **Only select repositories** y elegir exclusivamente
   `Leadhousemx/nexus-piloto-sintetico`. No seleccionar todos los repos.
3. En GitHub App > General, usar **Generate a private key**. No adjuntar
   la clave a PR, mensaje o archivo versionado.
4. En el repositorio, ir a **Settings > Environments** y crear
   `nx-piloto-policy`. Configurar **Deployment branches and tags** como
   **Protected branches only**. En este repositorio sólo `main` está protegida.
   No permitir ramas libres en este environment.
5. Crear dentro de **este environment** (no a nivel global del repositorio):
   - Variable `NX_POLICY_APP_CLIENT_ID`: Client ID de la GitHub App.
   - Secret `NX_POLICY_APP_PRIVATE_KEY`: contenido completo del archivo
     PEM descargado al generar la clave privada.
   La clave privada nunca se comparte en ChatGPT.
6. No fusionar este PR hasta confirmar que la App está instalada y que el
   environment existe y tiene restricciones configuradas.

## Verificaciones posteriores al merge (sin tocar producción)

- Actualizar un PR sintético que sólo cambie `calculadora.py` o `tests/*.py`.
- Verificar que `Piloto / Politicas` se publica por **la App nueva**, no por
  `github-actions`; cotejar `app.id` con la instalación real.
- Probar PR draft (check FAIL) y PR listo (check SUCCESS), sobre nuevos SHA.
- Probar que el GITHUB_TOKEN del workflow no puede publicar un check con la
  identidad de la App.
- Sólo entonces evaluar agregar `Piloto / Politicas` como required check con
  fuente `nx-piloto-policy-2026`, y comprobar su aplicación efectiva.
- No fusionar PR #2 ni el PR de suplantación #5. No desplegar nada.

## Seguridad y limitaciones

El workflow `workflow_run` ejecuta código de `main` y **nunca** hace checkout
del HEAD del PR; cualquier edición de CI exige merge separado y explícito.
Un environment sin restricciones o el almacenamiento de PEM como secreto global
sería un fallo de seguridad de configuración.

Un check de políticas no sustituye revisión semántica independiente, no autoriza
merges por sí solo ni demuestra despliegues. El evaluador existente conserva la
prohibición de declarar DONE.

En el workflow no hay secretos de Brentrix, claves SSH ni permisos de despliegue.
