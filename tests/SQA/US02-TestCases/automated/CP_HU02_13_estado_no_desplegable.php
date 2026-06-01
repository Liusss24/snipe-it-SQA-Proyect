<?php
/**
 * CP-HU02-13 – Intento de checkout sobre un activo con estado no desplegable
 *
 * Técnica: Transición de estados / Prueba negativa.
 * Verifica que el sistema bloquea el checkout de activos cuyo estado no es deployable.
 */

beforeAll(function () {
    MasterData::init();
});

beforeEach(function () {
    $m = MasterData::init();

    if (empty($m['undeploy_status_id'])) {
        $this->skipReason = "No se encontró un status label no desplegable en el sistema.";
        $this->user  = null;
        $this->asset = null;
        return;
    }

    $this->user  = create_user('Pedro', 'Sanchez');
    $this->asset = create_asset($m['model_id'], $m['undeploy_status_id']);
});

afterEach(function () {
    if (!empty($this->user['id']))  delete_user($this->user['id']);
    if (!empty($this->asset['id'])) delete_asset($this->asset['id']);
});

test('CP-HU02-13: un activo con estado no desplegable no puede ser asignado mediante checkout', function () {
    if (!empty($this->skipReason)) {
        $this->markTestSkipped($this->skipReason);
    }

    $assetId = $this->asset['id'];
    $userId  = $this->user['id'];

    // Verify precondition: asset is NOT in a deployable state
    $metaBefore = get_asset_status_meta($assetId);
    expect($metaBefore)->not->toBe('deployable',
        "Precondición: el activo no debe estar en estado deployable para esta prueba. " .
        "Estado actual: {$metaBefore}");

    // Attempt checkout on a non-deployable asset
    $resp = checkout_asset($assetId, $userId);

    // The system must reject the request
    expect($resp['status'])->not->toBe('success',
        "El sistema no debe permitir checkout de un activo no desplegable. " .
        "Respuesta completa: " . json_encode($resp));

    // Asset state and assignment must remain unchanged
    expect(get_asset_status_meta($assetId))->toBe($metaBefore,
        "El estado del activo no debe cambiar después de un checkout rechazado");
    expect(get_asset_assigned_user_id($assetId))->toBeNull(
        "El activo no debe quedar asignado a ningún usuario");
})->group('integracion', 'negativos', 'high');
