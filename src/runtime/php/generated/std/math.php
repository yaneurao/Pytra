<?php
// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/math.py
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

$pi = pyMathPi();
$e = pyMathE();

function sqrt($x): float {
    return pyMathSqrt($x);
}

function sin($x): float {
    return pyMathSin($x);
}

function cos($x): float {
    return pyMathCos($x);
}

function tan($x): float {
    return pyMathTan($x);
}

function exp($x): float {
    return pyMathExp($x);
}

function log($x): float {
    return pyMathLog($x);
}

function log10($x): float {
    return pyMathLog10($x);
}

function fabs($x): float {
    return pyMathFabs($x);
}

function floor($x): float {
    return pyMathFloor($x);
}

function ceil($x): float {
    return pyMathCeil($x);
}

function pow($x, $y): float {
    return pyMathPow($x, $y);
}
