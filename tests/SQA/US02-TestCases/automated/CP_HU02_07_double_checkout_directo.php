<?php
/**
 * CP-HU02-07 – Intento de checkout mediante petición directa sobre un activo ya desplegado
 *
 * Técnica: Prueba negativa / Seguridad funcional.
 * Verifica que el sistema rechaza un checkout sobre un activo ya en estado Deployed,
 * incluso si se intenta mediante una petición directa al backend.
 */

beforeAll(function () {
    MasterData::init();
});

beforeEach(function () {
    $m = MasterData::init();

    // Usuario principal: recibe el primer checkout (válido)
    $this->userA  = create_user('Carlos', 'Ramirez');
    // Usuario secundario: es el destino del segundo checkout (inválido) intentado
    $this->userB  = create_user('Laura', 'Gomez');
    $this->asset  = create_asset($m['model_id'], $m['rtd_status_id']);

    // Ejecutar el primer checkout (válido) para que el activo ahora esté Deployed
    checkout_asset($this->asset['id'], $this->userA['id']);
});

afterEach(function () {
    if (!empty($this->userA['id']))  delete_user($this->userA['id']);
    if (!empty($this->userB['id']))  delete_user($this->userB['id']);
    if (!empty($this->asset['id']))  delete_asset($this->asset['id']);
});

test('CP-HU02-07: un activo ya desplegado no puede volver a ser asignado mediante petición directa', function () {
    $assetId = $this->asset['id'];
    $userAId = $this->userA['id'];
    $userBId = $this->userB['id'];

    // Verificar precondición: el activo está Deployed y asignado al usuario A
    expect(get_asset_status_meta($assetId))->toBe('deployed',
        "Precondición: el activo debe estar en estado Deployed antes del segundo intento");
    expect(get_asset_assigned_user_id($assetId))->toBe($userAId,
        "Precondición: el activo debe estar asignado al usuario A");

    // Intentar un segundo checkout hacia el usuario B
    $resp = checkout_asset($assetId, $userBId);

    // El sistema debe rechazar la solicitud
    expect($resp['status'])->not->toBe('success',
        "El sistema no debe permitir un segundo checkout sobre un activo ya desplegado. " .
        "Respuesta completa: " . json_encode($resp));

    // Verificar que la asignación original no ha cambiado
    expect(get_asset_assigned_user_id($assetId))->toBe($userAId,
        "El activo debe seguir asignado al usuario A después del intento fallido");

    expect(get_asset_status_meta($assetId))->toBe('deployed',
        "El estado del activo no debe cambiar después del intento de doble checkout");
})->group('integracion', 'negativos', 'high');
