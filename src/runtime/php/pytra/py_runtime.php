<?php
declare(strict_types=1);

require_once __DIR__ . '/utils/png.php';
require_once __DIR__ . '/utils/gif.php';
require_once __DIR__ . '/std/time.php';

function __pytra_print(...$args): void {
    if (count($args) === 0) {
        echo PHP_EOL;
        return;
    }
    $parts = [];
    foreach ($args as $arg) {
        if (is_bool($arg)) {
            $parts[] = $arg ? "True" : "False";
            continue;
        }
        if ($arg === null) {
            $parts[] = "None";
            continue;
        }
        if (is_array($arg)) {
            $parts[] = json_encode($arg, JSON_UNESCAPED_UNICODE);
            continue;
        }
        $parts[] = (string)$arg;
    }
    echo implode(" ", $parts) . PHP_EOL;
}

function __pytra_len($v): int {
    if (is_string($v)) {
        return strlen($v);
    }
    if (is_array($v)) {
        return count($v);
    }
    return 0;
}

function __pytra_truthy($v): bool {
    if (is_bool($v)) {
        return $v;
    }
    if ($v === null) {
        return false;
    }
    if (is_int($v) || is_float($v)) {
        return $v != 0;
    }
    if (is_string($v)) {
        return strlen($v) > 0;
    }
    if (is_array($v)) {
        return count($v) > 0;
    }
    return (bool)$v;
}

function __pytra_int($v): int {
    if (is_int($v)) {
        return $v;
    }
    if (is_bool($v)) {
        return $v ? 1 : 0;
    }
    if (is_float($v)) {
        return (int)$v;
    }
    if (is_string($v) && is_numeric($v)) {
        return (int)$v;
    }
    return 0;
}

function __pytra_float($v): float {
    if (is_float($v)) {
        return $v;
    }
    if (is_int($v) || is_bool($v)) {
        return (float)$v;
    }
    if (is_string($v) && is_numeric($v)) {
        return (float)$v;
    }
    return 0.0;
}

function __pytra_str_isdigit($s): bool {
    if (!is_string($s) || $s === '') {
        return false;
    }
    return preg_match('/^[0-9]+$/', $s) === 1;
}

function __pytra_str_isalpha($s): bool {
    if (!is_string($s) || $s === '') {
        return false;
    }
    return preg_match('/^[A-Za-z]+$/', $s) === 1;
}

function __pytra_str_slice($s, $start, $stop) {
    if (!is_string($s)) {
        return '';
    }
    $n = strlen($s);
    $a = (int)$start;
    $b = (int)$stop;
    if ($a < 0) {
        $a += $n;
    }
    if ($b < 0) {
        $b += $n;
    }
    if ($a < 0) {
        $a = 0;
    }
    if ($b < $a) {
        return '';
    }
    return substr($s, $a, $b - $a);
}

function __pytra_index($container, $index): int {
    $i = __pytra_int($index);
    $n = 0;
    if (is_array($container)) {
        $n = count($container);
    } elseif (is_string($container)) {
        $n = strlen($container);
    }
    if ($i < 0) {
        $i += $n;
    }
    return $i;
}

function __pytra_noop(...$_args) {
    return null;
}

function __pytra_array_is_list_like(array $v): bool {
    $i = 0;
    foreach ($v as $k => $_value) {
        if (!is_int($k) || $k !== $i) {
            return false;
        }
        $i += 1;
    }
    return true;
}

function __pytra_contains($container, $item): bool {
    if (is_array($container)) {
        if (__pytra_array_is_list_like($container)) {
            return in_array($item, $container, true);
        }
        return array_key_exists($item, $container);
    }
    if (is_string($container)) {
        return strpos($container, (string)$item) !== false;
    }
    return false;
}

function bytearray($v = 0): array {
    if (is_int($v) || is_float($v) || is_bool($v)) {
        $n = (int)$v;
        if ($n <= 0) {
            return [];
        }
        return array_fill(0, $n, 0);
    }
    if (is_string($v)) {
        $out = [];
        $n = strlen($v);
        $i = 0;
        while ($i < $n) {
            $out[] = ord($v[$i]);
            $i += 1;
        }
        return $out;
    }
    if (is_array($v)) {
        return array_values($v);
    }
    return [];
}

function bytes($v = null): array {
    if ($v === null) {
        return [];
    }
    if (is_array($v)) {
        return array_values($v);
    }
    if (is_string($v)) {
        return bytearray($v);
    }
    return bytearray($v);
}

function __pytra_list_repeat($v, int $count): array {
    if (!is_array($v) || $count <= 0) {
        return [];
    }
    $out = [];
    $i = 0;
    while ($i < $count) {
        foreach ($v as $item) {
            $out[] = $item;
        }
        $i += 1;
    }
    return $out;
}

function grayscale_palette(): array {
    $out = [];
    $i = 0;
    while ($i < 256) {
        $out[] = $i;
        $out[] = $i;
        $out[] = $i;
        $i += 1;
    }
    return $out;
}
