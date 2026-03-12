<?php
// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/math.py
// generated-by: tools/gen_runtime_from_manifest.py

declare(strict_types=1);

require_once dirname(__DIR__) . '/py_runtime.php';

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
