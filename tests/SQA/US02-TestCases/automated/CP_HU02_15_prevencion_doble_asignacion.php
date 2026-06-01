<?php
/**
 * CP-HU02-15 – Prevención de doble checkout por doble envío o solicitudes simultáneas
 *
 * Técnica: Prueba negativa / Integridad de datos.
 * Verifica que el sistema evita crear dos asignaciones activas sobre el mismo activo
 * cuando se ejecutan dos checkouts consecutivos rápidos.
 */

beforeAll(function () {
    MasterData::init();
});

beforeEach(function () {
    $m = MasterData::init();
    $this->userA = create_user('Mario', 'Fernandez');
    $this->userB = create_user('Elena', 'Vargas');
    $this->asset = create_asset($m['model_id'], $m['rtd_status_id']);
});

afterEach(function () {
    if (!empty($this->userA['id'])) delete_user($this->userA['id']);
    if (!empty($this->userB['id'])) delete_user($this->userB['id']);
    if (!empty($this->asset['id'])) delete_asset($this->asset['id']);
});

test('CP-HU02-15: solo el primer checkout es aceptado; el segundo es rechazado y la asignación original se mantiene', function () {
    $assetId = $this->asset['id'];
    $userAId = $this->userA['id'];
    $userBId = $this->userB['id'];

    // Primer checkout → debe tener éxito
    $resp1 = checkout_asset($assetId, $userAId);
    expect($resp1['status'])->toBe('success',
        "El primer checkout debe realizarse exitosamente. Respuesta: " . json_encode($resp1));

    // Enviar inmediatamente un segundo checkout (simulando envío doble / condición de carrera)
    $resp2 = checkout_asset($assetId, $userBId);

    // El segundo checkout debe ser rechazado
    expect($resp2['status'])->not->toBe('success',
        "El segundo checkout sobre el mismo activo debe ser rechazado. " .
        "Respuesta: " . json_encode($resp2));

    // Estado final: el activo está Deployed y asignado SOLO al usuario A
    expect(get_asset_status_meta($assetId))->toBe('deployed',
        "El activo debe estar en estado Deployed después del primer checkout exitoso");

    $finalAssigned = get_asset_assigned_user_id($assetId);
    expect($finalAssigned)->toBe($userAId,
        "El activo debe seguir asignado únicamente al usuario A (id={$userAId}). " .
        "Usuario asignado actualmente: {$finalAssigned}");

    // El usuario B NO debe tener el activo en su perfil
    expect(user_has_asset($userBId, $assetId))->toBeFalse(
        "El activo no debe aparecer en el perfil del usuario B, ya que su checkout fue rechazado"
    );
})->group('integracion', 'negativos', 'high');
