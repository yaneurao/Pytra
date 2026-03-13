<?php
// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/os_path.py
// generated-by: tools/gen_runtime_from_manifest.py

declare(strict_types=1);

$__pytra_runtime_candidates = [
    dirname(__DIR__) . '/py_runtime.php',
    dirname(__DIR__, 2) . '/native/built_in/py_runtime.php',
];
foreach ($__pytra_runtime_candidates as $__pytra_runtime_path) {
    if (is_file($__pytra_runtime_path)) {
        require_once $__pytra_runtime_path;
        break;
    }
}
if (!function_exists('__pytra_len')) {
    throw new RuntimeException('py_runtime.php not found for generated PHP runtime lane');
}

function join($a, $b) {
    return $__path->join($a, $b);
}

function dirname($p) {
    return $__path->dirname($p);
}

function basename($p) {
    return $__path->basename($p);
}

function splitext($p) {
    return $__path->splitext($p);
}

function abspath($p) {
    return $__path->abspath($p);
}

function exists($p) {
    return $__path->exists($p);
}
