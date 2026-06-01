<?php
/**
 * CP-HU02-14 – Intento de checkout por un usuario sin permisos
 *
 * Técnica: Control de permisos.
 * Verifica que un usuario autenticado sin permisos de checkout recibe 403 Forbidden
 * y que el activo no es modificado.
 */

beforeAll(function () {
    MasterData::init();
});

beforeEach(function () {
    $m = MasterData::init();
    $this->user  = create_user('Receptor', 'Valido');
    $this->asset = create_asset($m['model_id'], $m['rtd_status_id']);
});

afterEach(function () {
    if (!empty($this->user['id']))  delete_user($this->user['id']);
    if (!empty($this->asset['id'])) delete_asset($this->asset['id']);
});

test('CP-HU02-14: usuario sin permisos de checkout recibe error de autorización y el activo no cambia', function () {
    $nopermToken = snipe_noperm_token();

    if (empty($nopermToken)) {
        $this->markTestSkipped(
            'SNIPEIT_NOPERM_TOKEN no está configurado en .env. ' .
            'Generar un token API para el usuario viewer (sin permisos de checkout) y añadirlo al .env.'
        );
    }

    $assetId = $this->asset['id'];
    $userId  = $this->user['id'];

    // Enviar solicitud de checkout usando el token del usuario restringido
    $resp = checkout_asset($assetId, $userId, $nopermToken);

    $httpStatus = $resp['_http_status'];

    // Debe ser 403 Forbidden (o 401 si el token es inválido, pero no 200/success)
    expect($httpStatus)->not->toBe(200,
        "Un usuario sin permisos no debe recibir HTTP 200. Respuesta: " . json_encode($resp));
    expect($resp['status'] ?? '')->not->toBe('success',
        "Un usuario sin permisos no debe poder hacer checkout exitosamente");

    expect($httpStatus)->toBeIn([401, 403],
        "Se esperaba HTTP 403 (o 401) para un usuario sin permisos de checkout, " .
        "se obtuvo HTTP {$httpStatus}. Respuesta: " . json_encode($resp));

    // El activo debe permanecer en su estado original, sin asignar
    expect(get_asset_status_meta($assetId))->toBe('deployable',
        "El activo no debe cambiar de estado si el checkout fue denegado");
    expect(get_asset_assigned_user_id($assetId))->toBeNull(
        "El activo no debe quedar asignado cuando el checkout fue denegado por falta de permisos");
})->group('integracion', 'negativos', 'permisos', 'high');
