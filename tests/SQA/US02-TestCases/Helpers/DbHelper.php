<?php
declare(strict_types=1);

// ---------------------------------------------------------------------------
// Direct MariaDB access via docker exec
// Used as fallback when the Snipe-IT API does not expose the needed data.
// Primary use: querying action_logs for CP-HU02-04.
// ---------------------------------------------------------------------------

/**
 * Executes a SQL query inside the Snipe-IT MariaDB container.
 *
 * @throws RuntimeException if Docker exec fails or MariaDB reports an error.
 */
function db_query(string $sql): string
{
    $container = $_ENV['SNIPEIT_DB_CONTAINER'] ?? 'snipeit-db-1';
    $user      = $_ENV['SNIPEIT_DB_USER']      ?? 'snipeit_user';
    $pass      = $_ENV['SNIPEIT_DB_PASS']      ?? '';
    $db        = $_ENV['SNIPEIT_DB_NAME']       ?? 'snipeit_db';

    $cmd = sprintf(
        'docker exec %s mariadb -u %s -p%s %s -N -s -e %s 2>&1',
        escapeshellarg($container),
        escapeshellarg($user),
        escapeshellarg($pass),
        escapeshellarg($db),
        escapeshellarg($sql)
    );

    $output = shell_exec($cmd) ?? '';
    if (str_starts_with(trim($output), 'ERROR')) {
        throw new RuntimeException("DB query failed: {$output}");
    }
    return trim($output);
}

/**
 * Counts action_log entries for a given asset and action type.
 * Snipe-IT stores assets as 'App\Models\Asset' in the item_type column.
 */
function count_action_logs(int $assetId, string $actionType = 'checkout'): int
{
    $escapedType = str_replace("'", "''", $actionType);
    $sql = "SELECT COUNT(*) FROM action_logs "
         . "WHERE item_id = {$assetId} "
         . "AND item_type = 'App\\\\Models\\\\Asset' "
         . "AND action_type = '{$escapedType}';";

    try {
        $result = db_query($sql);
        return (int) $result;
    } catch (\Throwable $e) {
        // If Docker/DB is unreachable skip gracefully; the caller handles this.
        throw $e;
    }
}

/**
 * Returns the most recent action_log row for an asset as an associative array.
 * Returns [] if no row found or DB is unreachable.
 */
function get_latest_action_log(int $assetId, string $actionType = 'checkout'): array
{
    $escapedType = str_replace("'", "''", $actionType);
    $sql = "SELECT id, action_type, target_id, target_type, created_at "
         . "FROM action_logs "
         . "WHERE item_id = {$assetId} "
         . "AND item_type = 'App\\\\Models\\\\Asset' "
         . "AND action_type = '{$escapedType}' "
         . "ORDER BY created_at DESC LIMIT 1;";

    try {
        $row = db_query($sql);
    } catch (\Throwable) {
        return [];
    }

    if ($row === '') {
        return [];
    }

    $parts = explode("\t", $row);
    return [
        'id'          => $parts[0] ?? null,
        'action_type' => $parts[1] ?? null,
        'target_id'   => $parts[2] ?? null,
        'target_type' => $parts[3] ?? null,
        'created_at'  => $parts[4] ?? null,
    ];
}
