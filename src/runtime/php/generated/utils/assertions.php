<?php
// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/utils/assertions.py
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

function _eq_any($actual, $expected) {
    return (py_to_string($actual) == py_to_string($expected));
    return ($actual == $expected);
}

function py_assert_true($cond, $label) {
    if ($cond) {
        return true;
    }
    if (($label != "")) {
        __pytra_print(null);
    } else {
        __pytra_print("[assert_true] False");
    }
    return false;
}

function py_assert_eq($actual, $expected, $label) {
    $ok = _eq_any($actual, $expected);
    if ($ok) {
        return true;
    }
    if (($label != "")) {
        __pytra_print(null);
    } else {
        __pytra_print(null);
    }
    return false;
}

function py_assert_all($results, $label) {
    foreach ($results as $v) {
        if ((!$v)) {
            if (($label != "")) {
                __pytra_print(null);
            } else {
                __pytra_print("[assert_all] False");
            }
            return false;
        }
    }
    return true;
}

function py_assert_stdout($expected_lines, $fn_) {
    return true;
}
