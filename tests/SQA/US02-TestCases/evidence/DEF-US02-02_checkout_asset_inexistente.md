# DEF-US02-02 — Snipe-IT retorna HTTP 200 al hacer checkout de un activo inexistente

| Campo            | Detalle                                                              |
|------------------|----------------------------------------------------------------------|
| **ID**           | DEF-US02-02                                                          |
| **Caso asociado**| CP-HU02-12                                                           |
| **Módulo**       | Assets – Checkout (`POST /api/v1/hardware/{id}/checkout`)            |
| **Severidad**    | Alta                                                                 |
| **Prioridad**    | Alta                                                                 |
| **Tipo**         | Defecto de manejo de errores / respuesta HTTP incorrecta             |
| **Estado**       | Abierto / Documentado                                                |

## Descripción

Al enviar una petición de checkout hacia un ID de activo que no existe en la base de datos
(e.g. `hardware/999999999/checkout`), Snipe-IT responde con HTTP 200 en lugar de HTTP 404.
Este comportamiento impide que los clientes de la API detecten correctamente un recurso inexistente
y puede enmascarar errores de integración.

## Pasos para reproducir

1. Autenticarse con un token de administrador válido.
2. Enviar `POST /api/v1/hardware/999999999/checkout` con body:
   ```json
   { "checkout_to_type": "user", "assigned_user": <any_valid_user_id> }
   ```
3. Observar el código HTTP de la respuesta.

## Resultado esperado

```
HTTP 404 Not Found
{ "status": "error", "messages": "Asset not found." }
```

## Resultado obtenido

```
HTTP 200 OK
```

El sistema responde con HTTP 200, violando la semántica REST estándar para recursos no encontrados.

## Evidencia

- Test automatizado: `automated/CP_HU02_11_12_recurso_invalido.php`
- Marcado: `->skip('DEF-US02-02: ...')`

## Análisis

El endpoint de checkout no valida la existencia del activo antes de procesar la solicitud, o bien
el enrutamiento de Laravel captura la ruta con cualquier ID numérico y responde con 200 sin verificar
la existencia del recurso en la base de datos. Este es un defecto en el manejo de errores de la API REST.

## Recomendación

Verificar explícitamente la existencia del activo en el controlador de checkout antes de continuar.
Si el activo no existe, retornar HTTP 404 con un mensaje descriptivo (`"Asset not found."`).
