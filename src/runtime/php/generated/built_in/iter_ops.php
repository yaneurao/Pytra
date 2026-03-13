<?php
// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/built_in/iter_ops.py
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

function py_reversed_object($values) {
    $out = [];
    foreach ($values as $value) {
        $out[] = $value;
    }
    return reversed($out);
}

function py_enumerate_object($values, $start) {
    $out = [];
    $i = $start;
    foreach ($values as $value) {
        $out[] = [$i, $value];
        $i += 1;
    }
    return $out;
}
