<?php
/**
 * CP-HU02-09 – Intento de checkout sin seleccionar destinatario en Checkout to
 * CP-HU02-10 – Intento de checkout usando un usuario inexistente (ID inválido)
 *
 * Técnica: Valores inválidos.
 */

beforeAll(function () {
    MasterData::init();
});

beforeEach(function () {
    $m = MasterData::init();
    $this->asset = create_asset($m['model_id'], $m['rtd_status_id']);
});

afterEach(function () {
    if (!empty($this->asset['id'])) delete_asset($this->asset['id']);
});

// ---------------------------------------------------------------------------
// CP-HU02-09
// ---------------------------------------------------------------------------

test('CP-HU02-09: checkout sin destinatario debe ser rechazado y el activo permanece sin cambios', function () {
    $assetId = $this->asset['id'];

    $resp = api('POST', "/hardware/{$assetId}/checkout", [
        'checkout_to_type' => 'user',
        'note' => 'SQA CP-HU02-09 sin destinatario',
    ]);

    // El sistema debe rechazar la solicitud (no éxito)
    expect($resp['status'])->not->toBe('success',
        "El sistema no debe permitir checkout sin destinatario. Respuesta: " . json_encode($resp));

    // El activo debe permanecer en estado Ready to Deploy (deployable)
    $metaAfter = get_asset_status_meta($assetId);
    expect($metaAfter)->toBe('deployable',
        "El activo debe permanecer en estado deployable cuando el checkout es rechazado. " .
        "Estado actual: {$metaAfter}");

    // El activo no debe quedar asignado a ningún usuario
    expect(get_asset_assigned_user_id($assetId))->toBeNull(
        "El activo no debe quedar asignado a ningún usuario cuando el checkout es rechazado"
    );
})->group('integracion', 'negativos', 'high');

// ---------------------------------------------------------------------------
// CP-HU02-10
// ---------------------------------------------------------------------------

test('CP-HU02-10: checkout con un ID de usuario inexistente debe ser rechazado', function () {
    $assetId       = $this->asset['id'];
    $nonExistentId = 999_999_999; // ID que casi seguramente no existe

    $resp = api('POST', "/hardware/{$assetId}/checkout", [
        'checkout_to_type' => 'user',
        'assigned_user'    => $nonExistentId,
        'note'             => 'SQA CP-HU02-10 usuario inexistente',
    ]);

    // El sistema debe rechazar la solicitud
    expect($resp['status'])->not->toBe('success',
        "El sistema no debe permitir checkout a un usuario inexistente. Respuesta: " . json_encode($resp));

    // El activo debe permanecer en estado Ready to Deploy sin ninguna asignación
    expect(get_asset_status_meta($assetId))->toBe('deployable',
        "El activo no debe cambiar de estado cuando el usuario destino no existe");

    expect(get_asset_assigned_user_id($assetId))->toBeNull(
        "El activo no debe quedar asignado cuando el usuario destino no existe"
    );
})->group('integracion', 'negativos', 'high');
