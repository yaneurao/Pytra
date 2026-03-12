<?php
// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/built_in/numeric_ops.py
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

function sum($values) {
    if ((__pytra_len($values) == 0)) {
        return 0;
    }
    $acc = ($values[__pytra_index($values, 0)] - $values[__pytra_index($values, 0)]);
    $i = 0;
    $n = __pytra_len($values);
    while (($i < $n)) {
        $acc += $values[__pytra_index($values, $i)];
        $i += 1;
    }
    return $acc;
}

function py_min($a, $b) {
    if (($a < $b)) {
        return $a;
    }
    return $b;
}

function py_max($a, $b) {
    if (($a > $b)) {
        return $a;
    }
    return $b;
}
