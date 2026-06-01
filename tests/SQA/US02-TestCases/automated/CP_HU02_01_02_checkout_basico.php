<?php
/**
 * CP-HU02-01 – Asignación exitosa de un activo disponible a un usuario válido
 * CP-HU02-02 – Cambio de estado del activo de Ready to Deploy a Deployed
 */

beforeAll(function () {
    MasterData::init();
});

beforeEach(function () {
    $m = MasterData::init();
    $this->user  = create_user('Juan', 'Perez');
    $this->asset = create_asset($m['model_id'], $m['rtd_status_id']);
});

afterEach(function () {
    if (!empty($this->user['id']))  delete_user($this->user['id']);
    if (!empty($this->asset['id'])) delete_asset($this->asset['id']);
});

// ---------------------------------------------------------------------------
// CP-HU02-01
// ---------------------------------------------------------------------------

test('CP-HU02-01: checkout exitoso retorna status success y mensaje de confirmación', function () {
    $resp = checkout_asset($this->asset['id'], $this->user['id']);

    // toContain() is variadic in Pest 3 — pass only the needle, no second argument
    expect($resp['status'])->toBe('success',
        "Se esperaba status 'success', se obtuvo: " . json_encode($resp));
    expect($resp['messages'] ?? '')->toContain('checked out successfully');
})->group('integracion', 'positivos', 'high');

// ---------------------------------------------------------------------------
// CP-HU02-02
// ---------------------------------------------------------------------------

test('CP-HU02-02: el estado del activo cambia a Deployed tras el checkout', function () {
    $assetId = $this->asset['id'];

    // Verify precondition: asset is currently in a deployable (Ready to Deploy) state
    $metaBefore = get_asset_status_meta($assetId);
    expect($metaBefore)->toBe('deployable',
        "Precondición: el activo debe estar en estado deployable antes del checkout");

    checkout_asset($assetId, $this->user['id']);

    $metaAfter = get_asset_status_meta($assetId);
    expect($metaAfter)->toBe('deployed',
        "El activo debe quedar en estado 'deployed' después del checkout. " .
        "Estado obtenido: {$metaAfter}");
})->group('integracion', 'positivos', 'high');
