<?php
// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/random.py
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

function seed($value) {
    $v = ($value & 2147483647);
    if (($v == 0)) {
        $v = 1;
    }
    $_state_box[0] = $v;
    $_gauss_has_spare[0] = 0;
}

function _next_u31() {
    $s = $_state_box[0];
    $s = (((1103515245 * $s) + 12345) & 2147483647);
    $_state_box[0] = $s;
    return $s;
}

function random() {
    return (_next_u31() / 2147483648.0);
}

function randint($a, $b) {
    $lo = $a;
    $hi = $b;
    if (($hi < $lo)) {
        $__pytra_swap_0 = $lo;
        $lo = $hi;
        $hi = $__pytra_swap_0;
    }
    $span = (($hi - $lo) + 1);
    return ($lo + ((int)((random() * $span))));
}

function choices($population, $weights, $k) {
    $n = __pytra_len($population);
    if (($n <= 0)) {
        return [];
    }
    $draws = $k;
    if (($draws < 0)) {
        $draws = 0;
    }
    $weight_vals = [];
    foreach ($weights as $w) {
        $weight_vals[] = $w;
    }
    $out = [];
    if ((__pytra_len($weight_vals) == $n)) {
        $total = 0.0;
        foreach ($weight_vals as $w) {
            if (($w > 0.0)) {
                $total += $w;
            }
        }
        if (($total > 0.0)) {
            for ($_ = 0; $_ < $draws; $_ += 1) {
                $r = (random() * $total);
                $acc = 0.0;
                $picked_i = ($n - 1);
                for ($i = 0; $i < $n; $i += 1) {
                    $w = $weight_vals[__pytra_index($weight_vals, $i)];
                    if (($w > 0.0)) {
                        $acc += $w;
                    }
                    if (($r < $acc)) {
                        $picked_i = $i;
                        break;
                    }
                }
                $out[] = $population[__pytra_index($population, $picked_i)];
            }
            return $out;
        }
    }
    for ($_ = 0; $_ < $draws; $_ += 1) {
        $out[] = $population[__pytra_index($population, randint(0, ($n - 1)))];
    }
    return $out;
}

function gauss($mu, $sigma) {
    if (($_gauss_has_spare[0] != 0)) {
        $_gauss_has_spare[0] = 0;
        return ($mu + ($sigma * $_gauss_spare[0]));
    }
    $u1 = 0.0;
    while (($u1 <= 1e-12)) {
        $u1 = random();
    }
    $u2 = random();
    $mag = pyMathSqrt(((-2.0) * pyMathLog($u1)));
    $z0 = ($mag * pyMathCos(((2.0 * pyMathPi()) * $u2)));
    $z1 = ($mag * pyMathSin(((2.0 * pyMathPi()) * $u2)));
    $_gauss_spare[0] = $z1;
    $_gauss_has_spare[0] = 1;
    return ($mu + ($sigma * $z0));
}

function shuffle($xs) {
    $i = (__pytra_len($xs) - 1);
    while (($i > 0)) {
        $j = randint(0, $i);
        if (($j != $i)) {
            $tmp = $xs[__pytra_index($xs, $i)];
            $xs[__pytra_index($xs, $i)] = $xs[__pytra_index($xs, $j)];
            $xs[__pytra_index($xs, $j)] = $tmp;
        }
        $i -= 1;
    }
}
