# Piloto sintético OpenClaw Nexus

Repositorio exclusivo de ensayos, sin código ni credenciales de Brentrix.

## Estado comprobado

- PR #1: CI positiva y merge con ruleset.
- PR #2: prueba defectuosa, sin merge.
- PR #3: CI y políticas aprobadas en SHA `b898a455cbb57135d265116a96b213df6374dfec`. Dictamen técnico independiente **reportado** en Issue #9; cero reviews formales GitHub. Sin merge ni despliegue.
- PR #4: evaluación desde código de main; PR #6: GitHub App `nx-piloto-policy-2026` publica checks con identidad independiente.
- PR #8: ensayo real de check falso; la App auténtica rechazó el cambio y GitHub bloqueó el merge. Cerrado sin merge.
- Ruleset `nexus-piloto-main`: exige `Piloto CI / Pruebas` (App 15368) y `Piloto / Politicas` (App 5502189). **No** requiere una review humana formal.

## Prototipo de firma de revisión (este PR)

`tests/revision_attestation.py` demuestra un contrato para vincular criptográficamente una declaración de revisión con repo, issue, PR, HEAD, base, digest del diff y digest del informe. El objeto JSON con claves ordenadas se firma con **Ed25519/OpenSSL** y se transporta con el prefijo `NEXUS_REVIEW_V1`. Una firma válida no puede reutilizarse contra otro SHA ni alterarse de APPROVE a BLOCK sin invalidarse.

`tests/test_revision_attestation.py`: 15 pruebas aisladas, con claves **efímeras de prueba** creadas al ejecutar tests. No contiene claves reales ni lee secretos.

**No es todavía un gate operativo, no publica checks de revisión y no autoriza merge.** El dictamen del Issue #9 es texto atribuido al revisor, no una firma del revisor. Ningún SHA-256 de evidencia sin firma acredita procedencia.

### Requisito imprescindible antes de activar

Una clave de firma del revisor deberá estar efectivamente fuera del alcance del ingeniero: usuario/UID, permisos, mounts, socket Docker, sudo y acceso a la clave deben inspeccionarse en Nexus. Subagentes con el mismo UID o archivos modificables por el ingeniero **no son independencia criptográfica**, aunque sus contextos sean distintos. Si no puede demostrarse el aislamiento, no activar el check obligatorio de revisión y conservar aprobación humana explícita.

Una vez aislado el firmante:
1. Anclar la **clave pública real** mediante revisión humana en una ruta confiable de main o environment protegido (nunca aceptar la clave pública contenida en el mismo comentario que la firma).
2. Firmar un reporte realmente revisado, con su `report_sha256` genuino, el diff y el SHA exacto de la revisión.
3. Configurar un workflow confiable desde main para verificar firma y estado actual del PR, y publicar un check distinto con la GitHub App existente. Comprobar casos positivo, modificado y stale.
4. Solo después estudiar si incluir ese check en el ruleset, siempre con autorización del operador. No interpretar un check como autorización para despliegue.

La política de rutas bloquea cambios en `.github` y scripts de autoridad. Cualquier actualización de esos componentes requiere **bootstrap de mantenimiento controlado con autorización explícita**, nunca relajar permanentemente el ruleset ni permitir que el ingeniero edite su propio gate.

## Pruebas

Ejecutar: `python -m unittest discover -s tests -p 'test_*.py' -v`.
La CLI `verificar_pr.py` es un verificador histórico de solo lectura; puede rechazar una revisión técnica sin review formal, por diseño. Nunca hace merge ni declara DONE.

## Límites

El piloto no es un staging de Brentrix, no dispone de rollback demostrado y no tiene conexión productiva con Nexus. Ningún check o comentario en GitHub convierte esos estados en DONE.
