<?php
declare(strict_types=1);

use GuzzleHttp\Client;

// ---------------------------------------------------------------------------
// Environment accessors
// ---------------------------------------------------------------------------

function snipe_base_url(): string
{
    return rtrim($_ENV['SNIPEIT_BASE_URL'] ?? 'http://localhost:8000', '/');
}

function snipe_admin_token(): string
{
    return $_ENV['SNIPEIT_API_TOKEN'] ?? '';
}

function snipe_noperm_token(): string
{
    return $_ENV['SNIPEIT_NOPERM_TOKEN'] ?? '';
}

// ---------------------------------------------------------------------------
// Core HTTP client
// ---------------------------------------------------------------------------

/**
 * Calls the Snipe-IT REST API.
 *
 * Returns the decoded JSON body with an extra '_http_status' key added.
 * Retries automatically up to $retries times on HTTP 429 (rate limit).
 *
 * @param  string      $method   HTTP verb (GET, POST, PATCH, DELETE)
 * @param  string      $endpoint API path starting with '/' e.g. '/hardware/1/checkout'
 * @param  array       $body     Request body (sent as JSON)
 * @param  string|null $token    Bearer token; defaults to admin token from .env
 * @param  int         $retries  Maximum number of attempts on 429
 * @return array       Decoded response + '_http_status'
 */
function api(
    string  $method,
    string  $endpoint,
    array   $body    = [],
    ?string $token   = null,
    int     $retries = 3
): array {
    $token ??= snipe_admin_token();
    $url    = snipe_base_url() . '/api/v1' . $endpoint;

    $client  = new Client(['timeout' => 15, 'http_errors' => false]);
    $headers = [
        'Authorization' => 'Bearer ' . $token,
        'Accept'        => 'application/json',
        'Content-Type'  => 'application/json',
    ];

    for ($attempt = 0; $attempt < $retries; $attempt++) {
        $options = ['headers' => $headers];
        if (!empty($body)) {
            $options['json'] = $body;
        }

        $response = $client->request(strtoupper($method), $url, $options);
        $code     = $response->getStatusCode();

        if ($code === 429 && $attempt < $retries - 1) {
            sleep(8 * ($attempt + 1)); // 8 s, 16 s
            continue;
        }

        $json = json_decode((string) $response->getBody(), true) ?? [];
        $json['_http_status'] = $code;
        return $json;
    }

    return [
        '_http_status' => 429,
        'status'       => 'error',
        'messages'     => 'Rate limit exceeded after all retries',
    ];
}
