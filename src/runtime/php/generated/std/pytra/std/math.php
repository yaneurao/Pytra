<?php
// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/math.py
// generated-by: tools/gen_runtime_from_manifest.py

declare(strict_types=1);

$__pytra_math_native_candidates = [
    __DIR__ . '/math_native.php',
    dirname(__DIR__, 2) . '/native/std/math_native.php',
];
foreach ($__pytra_math_native_candidates as $__pytra_math_native_path) {
    if (is_file($__pytra_math_native_path)) {
        require_once $__pytra_math_native_path;
        break;
    }
}
if (!function_exists('__pytra_math_pi')) {
    throw new RuntimeException('math_native.php not found for generated PHP runtime lane');
}

$pi = __pytra_math_pi();
$e = __pytra_math_e();

function sqrt($x): float {
    return __pytra_math_sqrt($x);
}

function sin($x): float {
    return __pytra_math_sin($x);
}

function cos($x): float {
    return __pytra_math_cos($x);
}

function tan($x): float {
    return __pytra_math_tan($x);
}

function exp($x): float {
    return __pytra_math_exp($x);
}

function log($x): float {
    return __pytra_math_log($x);
}

function log10($x): float {
    return __pytra_math_log10($x);
}

function fabs($x): float {
    return __pytra_math_fabs($x);
}

function floor($x): float {
    return __pytra_math_floor($x);
}

function ceil($x): float {
    return __pytra_math_ceil($x);
}

function pow($x, $y): float {
    return __pytra_math_pow($x, $y);
}
