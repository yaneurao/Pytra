<?php
// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/built_in/contains.py
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

function py_contains_dict_object($values, $key) {
    $needle = strval($key);
    foreach ($values as $cur) {
        if (($cur == $needle)) {
            return true;
        }
    }
    return false;
}

function py_contains_list_object($values, $key) {
    foreach ($values as $cur) {
        if (($cur == $key)) {
            return true;
        }
    }
    return false;
}

function py_contains_set_object($values, $key) {
    foreach ($values as $cur) {
        if (($cur == $key)) {
            return true;
        }
    }
    return false;
}

function py_contains_str_object($values, $key) {
    $needle = strval($key);
    $haystack = strval($values);
    $n = __pytra_len($haystack);
    $m = __pytra_len($needle);
    if (($m == 0)) {
        return true;
    }
    $i = 0;
    $last = ($n - $m);
    while (($i <= $last)) {
        $j = 0;
        $ok = true;
        while (($j < $m)) {
            if (($haystack[($i + $j)] != $needle[$j])) {
                $ok = false;
                break;
            }
            $j += 1;
        }
        if ($ok) {
            return true;
        }
        $i += 1;
    }
    return false;
}
