<?php
declare(strict_types=1);

require_once __DIR__ . '/vendor/autoload.php';

// Load environment variables from .env (safe: no error if file missing)
$dotenv = Dotenv\Dotenv::createImmutable(__DIR__);
$dotenv->safeLoad();
