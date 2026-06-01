<?php
/**
 * CP-HU02-08 – Visualización del activo asignado en el perfil del usuario
 *
 * Técnica: Caja negra.
 * Verifica que, después del checkout, el activo aparece en la lista de activos
 * asignados al usuario (GET /users/{id}/assets).
 */

beforeAll(function () {
    MasterData::init();
});

beforeEach(function () {
    $m = MasterData::init();
    $this->user  = create_user('Sofia', 'Torres');
    $this->asset = create_asset($m['model_id'], $m['rtd_status_id']);
});

afterEach(function () {
    if (!empty($this->user['id']))  delete_user($this->user['id']);
    if (!empty($this->asset['id'])) delete_asset($this->asset['id']);
});

test('CP-HU02-08: el activo aparece en la sección de activos asignados del perfil del usuario tras el checkout', function () {
    $assetId = $this->asset['id'];
    $userId  = $this->user['id'];

    // Antes del checkout: el activo NO debe estar en los activos del usuario
    expect(user_has_asset($userId, $assetId))->toBeFalse(
        "Precondición: el activo no debe aparecer en el perfil del usuario antes del checkout"
    );

    checkout_asset($assetId, $userId);

    // After checkout: asset MUST appear in the user's assets
    expect(user_has_asset($userId, $assetId))->toBeTrue(
        "El activo {$assetId} debe aparecer en la lista de activos del usuario {$userId} " .
        "después del checkout. Activos actuales: " . json_encode(get_user_assets($userId))
    );
})->group('integracion', 'positivos', 'high');
