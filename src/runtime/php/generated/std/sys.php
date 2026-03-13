<?php
// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/sys.py
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

function exit_($code) {
    $__s->exit_($code);
}

function set_argv($values) {
    $argv->clear();
    foreach ($values as $v) {
        $argv[] = $v;
    }
}

function set_path($values) {
    $path->clear();
    foreach ($values as $v) {
        $path[] = $v;
    }
}

function write_stderr($text) {
    $__s->stderr->write($text);
}

function write_stdout($text) {
    $__s->stdout->write($text);
}
