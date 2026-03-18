<?php
// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/time.py
// generated-by: tools/gen_runtime_from_manifest.py

declare(strict_types=1);

$__pytra_time_native_candidates = [
    __DIR__ . '/time_native.php',
    dirname(__DIR__, 2) . '/native/std/time_native.php',
];
foreach ($__pytra_time_native_candidates as $__pytra_time_native_path) {
    if (is_file($__pytra_time_native_path)) {
        require_once $__pytra_time_native_path;
        break;
    }
}
if (!function_exists('__pytra_time_perf_counter')) {
    throw new RuntimeException('time_native.php not found for generated PHP runtime lane');
}

function perf_counter(): float {
    return __pytra_time_perf_counter();
}
