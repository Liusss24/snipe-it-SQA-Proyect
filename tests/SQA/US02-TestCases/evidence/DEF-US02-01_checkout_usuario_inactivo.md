# DEF-US02-01 — Snipe-IT permite checkout de activo a usuario inactivo

| Campo            | Detalle                                                              |
|------------------|----------------------------------------------------------------------|
| **ID**           | DEF-US02-01                                                          |
| **Caso asociado**| CP-HU02-11                                                           |
| **Módulo**       | Assets – Checkout (`POST /api/v1/hardware/{id}/checkout`)            |
| **Severidad**    | Media                                                                |
| **Prioridad**    | Media                                                                |
| **Tipo**         | Defecto de validación / lógica de negocio                            |
| **Estado**       | Abierto / Documentado                                                |

## Descripción

Snipe-IT permite asignar un activo a un usuario cuyo campo `activated` es `false` (usuario inactivo).
El sistema debería rechazar la asignación hacia usuarios no habilitados, ya que un usuario inactivo
no puede iniciar sesión ni gestionar activos, y asignarle uno puede generar un estado incoherente.

## Pasos para reproducir

1. Crear un usuario con `activated = false` vía `POST /api/v1/users`.
2. Crear un activo con estado Ready to Deploy.
3. Enviar `POST /api/v1/hardware/{id}/checkout` con `assigned_user = {inactiveUserId}`.
4. Observar la respuesta del sistema.

## Resultado esperado

```
{ "status": "error", "messages": "..." }   // HTTP 4xx o mensaje de error de validación
```

El activo permanece en estado Ready to Deploy, sin asignación.

## Resultado obtenido

```json
{
  "status": "success",
  "messages": "Asset checked out successfully.",
  "payload": { "asset": "QA-HU02-AFB6843D" }
}
```

HTTP 200 — el sistema acepta el checkout sin validar el estado activo del usuario receptor.

## Evidencia

- Test automatizado: `automated/CP_HU02_11_12_recurso_invalido.php`
- Grupo: `integracion`, `negativos`, `media`
- Marcado: `->skip('DEF-US02-01: ...')`

## Análisis

Snipe-IT no valida el campo `activated` del usuario destino en el endpoint de checkout de activos.
Esto difiere del comportamiento esperado según las precondiciones del caso de prueba y las buenas
prácticas de gestión de activos (solo usuarios activos deberían poder recibir asignaciones).

## Recomendación

Añadir validación en el controlador de checkout de activos para verificar que el usuario receptor
tenga `activated = true` antes de procesar la asignación. Si el usuario está inactivo, retornar un
error 422 con mensaje descriptivo.
