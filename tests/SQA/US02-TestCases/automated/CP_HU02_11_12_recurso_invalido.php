<?php
/**
 * CP-HU02-11 – Intento de checkout hacia un usuario inactivo
 * CP-HU02-12 – Intento de checkout sobre un activo inexistente
 *
 * Técnica: Valores inválidos.
 *
 * DEFECTOS CONOCIDOS:
 *   DEF-US02-01 (CP-11): Snipe-IT permite checkout a usuarios con activated=false.
 *   DEF-US02-02 (CP-12): Snipe-IT retorna HTTP 200 al hacer checkout de un asset inexistente.
 * Ambos tests se marcan skip() hasta que los defectos sean corregidos en el sistema.
 */

beforeAll(function () {
    MasterData::init();
});

beforeEach(function () {
    $m = MasterData::init();
    $this->asset        = create_asset($m['model_id'], $m['rtd_status_id']);
    $this->inactiveUser = create_user('Usuario', 'Inactivo', activated: false);
});

afterEach(function () {
    if (!empty($this->asset['id']))        delete_asset($this->asset['id']);
    if (!empty($this->inactiveUser['id'])) delete_user($this->inactiveUser['id']);
});

// ---------------------------------------------------------------------------
// CP-HU02-11
// ---------------------------------------------------------------------------

test('CP-HU02-11: checkout hacia un usuario inactivo no debe asignar el activo', function () {
    $assetId        = $this->asset['id'];
    $inactiveUserId = $this->inactiveUser['id'];

    $resp = checkout_asset($assetId, $inactiveUserId);

    expect($resp['status'])->not->toBe('success',
        "El sistema no debe permitir asignar activos a usuarios inactivos");

    expect(get_asset_status_meta($assetId))->toBe('deployable',
        "El activo no debe cambiar de estado cuando el checkout es rechazado");
    expect(get_asset_assigned_user_id($assetId))->toBeNull(
        "El activo no debe quedar asignado a un usuario inactivo");
})->group('integracion', 'negativos', 'media')
  ->skip('DEF-US02-01: Snipe-IT permite checkout a usuarios con activated=false. ' .
         'El sistema retorna HTTP 200 / "Asset checked out successfully." en lugar de rechazar la asignación. ' .
         'Ver evidence/DEF-US02-01_checkout_usuario_inactivo.md');

// ---------------------------------------------------------------------------
// CP-HU02-12
// ---------------------------------------------------------------------------

test('CP-HU02-12: checkout sobre un activo inexistente debe devolver error controlado (404)', function () {
    $nonExistentAssetId = 999_999_999;

    $resp = api('POST', "/hardware/{$nonExistentAssetId}/checkout", [
        'checkout_to_type' => 'user',
        'assigned_user'    => $this->inactiveUser['id'],
        'note'             => 'SQA CP-HU02-12 activo inexistente',
    ]);

    $httpStatus = $resp['_http_status'];
    expect($httpStatus)->toBeGreaterThanOrEqual(400,
        "Se esperaba un error 4xx para un activo inexistente, se obtuvo HTTP {$httpStatus}")
    ->and($httpStatus)->toBeLessThan(500,
        "El sistema no debe devolver un error 500 para un activo inexistente. " .
        "HTTP {$httpStatus} recibido. Respuesta: " . json_encode($resp));
})->group('integracion', 'negativos', 'media')
  ->skip('DEF-US02-02: Snipe-IT retorna HTTP 200 al intentar checkout sobre el ID de activo 999999999 ' .
         '(no existente). Se esperaba HTTP 404. ' .
         'Ver evidence/DEF-US02-02_checkout_asset_inexistente.md');
