<?php
declare(strict_types=1);

// ---------------------------------------------------------------------------
// Master data – created once per suite run, cleaned up at shutdown
// ---------------------------------------------------------------------------

/**
 * Manages session-scoped master data (category, manufacturer, model, status IDs).
 * Call MasterData::init() at the start of every test file; it is idempotent.
 */
final class MasterData
{
    private static ?array $cache = null;

    public static function init(): array
    {
        if (self::$cache === null) {
            self::$cache = self::create();
            register_shutdown_function([self::class, 'cleanup']);
        }
        return self::$cache;
    }

    private static function create(): array
    {
        $uid = strtoupper(substr(md5(uniqid((string) mt_rand(), true)), 0, 6));

        // Category
        usleep(1_200_000);
        $cat   = api('POST', '/categories', ['name' => "LaptopsHU02{$uid}", 'category_type' => 'asset']);
        $catId = $cat['payload']['id'] ?? null;

        // Manufacturer
        usleep(1_200_000);
        $man   = api('POST', '/manufacturers', ['name' => "FabHU02{$uid}"]);
        $manId = $man['payload']['id'] ?? null;

        // Model
        usleep(1_200_000);
        $model   = api('POST', '/models', [
            'name'            => "ModeloHU02{$uid}",
            'category_id'     => $catId,
            'manufacturer_id' => $manId,
        ]);
        $modelId = $model['payload']['id'] ?? null;

        // Status labels: find deployable (Ready to Deploy) and a non-deployable one
        $statuses    = api('GET', '/statuslabels?limit=50');
        $rtdId       = null;
        $undeployId  = null;
        $createdUndeploy = false;

        foreach ($statuses['rows'] ?? [] as $s) {
            $name  = strtolower($s['name'] ?? '');
            $stype = is_array($s['type'] ?? null) ? ($s['type']['statusType'] ?? '') : ($s['type'] ?? '');

            if ($stype === 'deployable' && $rtdId === null) {
                $rtdId = $s['id'];
            }
            if (in_array($stype, ['undeployable', 'pending', 'archived'], true) && $undeployId === null) {
                $undeployId = $s['id'];
            }
        }

        // Fall back to name matching if type field wasn't parsed
        if ($rtdId === null) {
            foreach ($statuses['rows'] ?? [] as $s) {
                if (str_contains(strtolower($s['name'] ?? ''), 'ready to deploy')) {
                    $rtdId = $s['id'];
                    break;
                }
            }
        }
        if ($undeployId === null) {
            foreach ($statuses['rows'] ?? [] as $s) {
                $n = strtolower($s['name'] ?? '');
                if (str_contains($n, 'pending') || str_contains($n, 'archived')) {
                    $undeployId = $s['id'];
                    break;
                }
            }
        }

        // If still no non-deployable status, create one
        if ($undeployId === null) {
            usleep(1_200_000);
            $nd         = api('POST', '/statuslabels', ['name' => "NoDeploy{$uid}", 'type' => 'undeployable']);
            $undeployId = $nd['payload']['id'] ?? null;
            $createdUndeploy = true;
        }

        if (!$rtdId) {
            throw new RuntimeException(
                "No 'Ready to Deploy' (deployable) status label found. " .
                "Create at least one deployable status label in Snipe-IT."
            );
        }

        return [
            'uid'              => $uid,
            'category_id'      => $catId,
            'manufacturer_id'  => $manId,
            'model_id'         => $modelId,
            'rtd_status_id'    => $rtdId,
            'undeploy_status_id' => $undeployId,
            'created_undeploy' => $createdUndeploy,
        ];
    }

    public static function cleanup(): void
    {
        if (self::$cache === null) {
            return;
        }
        $d = self::$cache;

        $toDelete = [
            ['/models/'        . ($d['model_id']        ?? 0), $d['model_id']],
            ['/categories/'    . ($d['category_id']     ?? 0), $d['category_id']],
            ['/manufacturers/' . ($d['manufacturer_id'] ?? 0), $d['manufacturer_id']],
        ];
        foreach ($toDelete as [$ep, $id]) {
            if ($id) {
                try { api('DELETE', $ep); } catch (\Throwable) {}
                usleep(400_000);
            }
        }
        if (($d['created_undeploy'] ?? false) && ($d['undeploy_status_id'] ?? null)) {
            try { api('DELETE', '/statuslabels/' . $d['undeploy_status_id']); } catch (\Throwable) {}
        }

        self::$cache = null;
    }
}

// ---------------------------------------------------------------------------
// User helpers
// ---------------------------------------------------------------------------

/**
 * Creates a test user with a unique username to avoid collisions between runs.
 *
 * @throws RuntimeException if the API rejects the creation.
 */
function create_user(string $first, string $last, bool $activated = true): array
{
    usleep(1_200_000);
    $uid  = substr(md5(uniqid((string) mt_rand(), true)), 0, 8);
    $resp = api('POST', '/users', [
        'first_name'            => $first,
        'last_name'             => $last,
        'username'              => strtolower("{$first}.{$last}.{$uid}"),
        'email'                 => strtolower("{$first}.{$last}.{$uid}@sqa.test"),
        'password'              => 'TestPass123!',
        'password_confirmation' => 'TestPass123!',
        'activated'             => $activated,
    ]);
    $user = $resp['payload'] ?? [];
    if (empty($user['id'])) {
        throw new RuntimeException(
            "Could not create user {$first} {$last}: " . json_encode($resp)
        );
    }
    return $user;
}

function delete_user(int $id): void
{
    try {
        api('DELETE', "/users/{$id}");
    } catch (\Throwable) {}
}

// ---------------------------------------------------------------------------
// Asset helpers
// ---------------------------------------------------------------------------

/**
 * Creates a hardware asset with a unique asset tag.
 *
 * @throws RuntimeException if the API rejects the creation.
 */
function create_asset(int $modelId, int $statusId): array
{
    usleep(1_200_000);
    $tag  = 'QA-HU02-' . strtoupper(substr(md5(uniqid((string) mt_rand(), true)), 0, 8));
    $resp = api('POST', '/hardware', [
        'asset_tag' => $tag,
        'model_id'  => $modelId,
        'status_id' => $statusId,
        'name'      => "Activo SQA HU02 {$tag}",
    ]);
    $asset = $resp['payload'] ?? [];
    if (empty($asset['id'])) {
        throw new RuntimeException(
            "Could not create asset (tag={$tag}): " . json_encode($resp)
        );
    }
    return $asset;
}

function delete_asset(int $id): void
{
    try {
        api('DELETE', "/hardware/{$id}");
    } catch (\Throwable) {}
}

function get_asset(int $id): array
{
    return api('GET', "/hardware/{$id}");
}

// Returns the status_meta string ('deployable', 'deployed', etc.) for an asset.
function get_asset_status_meta(int $assetId): string
{
    $asset = get_asset($assetId);
    $label = $asset['status_label'] ?? [];
    return is_array($label) ? ($label['status_meta'] ?? '') : '';
}

// Returns the assigned_to user ID or null if not assigned.
function get_asset_assigned_user_id(int $assetId): ?int
{
    $asset      = get_asset($assetId);
    $assignedTo = $asset['assigned_to'] ?? null;
    if (!is_array($assignedTo)) {
        return null;
    }
    $id = $assignedTo['id'] ?? null;
    return $id !== null ? (int) $id : null;
}

// ---------------------------------------------------------------------------
// Checkout helper
// ---------------------------------------------------------------------------

/**
 * Sends a checkout request for an asset to a user.
 *
 * @param  string|null $token  Bearer token; null means admin token.
 */
function checkout_asset(int $assetId, int $userId, ?string $token = null): array
{
    return api(
        'POST',
        "/hardware/{$assetId}/checkout",
        [
            'checkout_to_type' => 'user',
            'assigned_user'    => $userId,
            'note'             => 'SQA automated test HU02',
        ],
        $token
    );
}

// ---------------------------------------------------------------------------
// User asset lookup
// ---------------------------------------------------------------------------

/**
 * Returns the list of assets currently assigned to a user.
 */
function get_user_assets(int $userId): array
{
    $resp = api('GET', "/users/{$userId}/assets?limit=50");
    return $resp['rows'] ?? [];
}

/**
 * Returns true if the asset (identified by ID) appears in the user's assigned assets.
 */
function user_has_asset(int $userId, int $assetId): bool
{
    $assets = get_user_assets($userId);
    foreach ($assets as $a) {
        if (($a['id'] ?? null) === $assetId) {
            return true;
        }
    }
    return false;
}
