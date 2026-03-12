<?php
// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/built_in/sequence.py
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

function py_range($start, $stop, $step) {
    $out = [];
    if (($step == 0)) {
        return $out;
    }
    if (($step > 0)) {
        $i = $start;
        while (($i < $stop)) {
            $out[] = $i;
            $i += $step;
        }
    } else {
        $i = $start;
        while (($i > $stop)) {
            $out[] = $i;
            $i += $step;
        }
    }
    return $out;
}

function py_repeat($v, $n) {
    if (($n <= 0)) {
        return "";
    }
    $out = "";
    $i = 0;
    while (($i < $n)) {
        $out .= $v;
        $i += 1;
    }
    return $out;
}
