<?php
declare(strict_types=1);

require_once __DIR__ . '/pytra/py_runtime.php';

// 14: Sample that outputs a moving-light scene in a simple raymarching style as a GIF.
function palette() {
    $p = bytearray();
    for ($i = 0; $i < 256; $i += 1) {
        $r = min(255, ((int)((20 + ($i * 0.9)))));
        $g = min(255, ((int)((10 + ($i * 0.7)))));
        $b = min(255, (30 + $i));
        $p[] = $r;
        $p[] = $g;
        $p[] = $b;
    }
    return bytes($p);
}

function scene($x, $y, $light_x, $light_y) {
    $x1 = ($x + 0.45);
    $y1 = ($y + 0.2);
    $x2 = ($x - 0.35);
    $y2 = ($y - 0.15);
    $r1 = sqrt((($x1 * $x1) + ($y1 * $y1)));
    $r2 = sqrt((($x2 * $x2) + ($y2 * $y2)));
    $blob = (exp((((-7.0) * $r1) * $r1)) + exp((((-8.0) * $r2) * $r2)));
    $lx = ($x - $light_x);
    $ly = ($y - $light_y);
    $l = sqrt((($lx * $lx) + ($ly * $ly)));
    $lit = (1.0 / (1.0 + ((3.5 * $l) * $l)));
    $v = ((int)((((255.0 * $blob) * $lit) * 5.0)));
    return min(255, max(0, $v));
}

function run_14_raymarching_light_cycle() {
    $w = 320;
    $h = 240;
    $frames_n = 84;
    $out_path = "sample/out/14_raymarching_light_cycle.gif";
    $start = __pytra_perf_counter();
    $frames = [];
    $__hoisted_cast_1 = ((float)($frames_n));
    $__hoisted_cast_2 = ((float)(($h - 1)));
    $__hoisted_cast_3 = ((float)(($w - 1)));
    for ($t = 0; $t < $frames_n; $t += 1) {
        $frame = bytearray(($w * $h));
        $a = ((($t / $__hoisted_cast_1) * M_PI) * 2.0);
        $light_x = (0.75 * cos($a));
        $light_y = (0.55 * sin(($a * 1.2)));
        for ($y = 0; $y < $h; $y += 1) {
            $row_base = ($y * $w);
            $py = ((($y / $__hoisted_cast_2) * 2.0) - 1.0);
            for ($x = 0; $x < $w; $x += 1) {
                $px = ((($x / $__hoisted_cast_3) * 2.0) - 1.0);
                $frame[($row_base + $x)] = scene($px, $py, $light_x, $light_y);
            }
        }
        $frames[] = bytes($frame);
    }
    __pytra_noop($out_path, $w, $h, $frames, palette());
    $elapsed = (__pytra_perf_counter() - $start);
    __pytra_print("output:", $out_path);
    __pytra_print("frames:", $frames_n);
    __pytra_print("elapsed_sec:", $elapsed);
}

function __pytra_main(): void {
    run_14_raymarching_light_cycle();
}

__pytra_main();
