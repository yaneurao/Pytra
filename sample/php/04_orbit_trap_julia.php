<?php
declare(strict_types=1);

require_once __DIR__ . '/pytra/py_runtime.php';

// 04: Sample that renders an orbit-trap Julia set and writes a PNG image.
function render_orbit_trap_julia($width, $height, $max_iter, $cx, $cy) {
    $pixels = bytearray();
    $__hoisted_cast_1 = ((float)(($height - 1)));
    $__hoisted_cast_2 = ((float)(($width - 1)));
    $__hoisted_cast_3 = ((float)($max_iter));
    for ($y = 0; $y < $height; $y += 1) {
        $zy0 = ((-1.3) + (2.6 * ($y / $__hoisted_cast_1)));
        for ($x = 0; $x < $width; $x += 1) {
            $zx = ((-1.9) + (3.8 * ($x / $__hoisted_cast_2)));
            $zy = $zy0;
            $trap = 1000000000.0;
            $i = 0;
            while (($i < $max_iter)) {
                $ax = $zx;
                if (($ax < 0.0)) {
                    $ax = (-$ax);
                }
                $ay = $zy;
                if (($ay < 0.0)) {
                    $ay = (-$ay);
                }
                $dxy = ($zx - $zy);
                if (($dxy < 0.0)) {
                    $dxy = (-$dxy);
                }
                if (($ax < $trap)) {
                    $trap = $ax;
                }
                if (($ay < $trap)) {
                    $trap = $ay;
                }
                if (($dxy < $trap)) {
                    $trap = $dxy;
                }
                $zx2 = ($zx * $zx);
                $zy2 = ($zy * $zy);
                if ((($zx2 + $zy2) > 4.0)) {
                    break;
                }
                $zy = (((2.0 * $zx) * $zy) + $cy);
                $zx = (($zx2 - $zy2) + $cx);
                $i += 1;
            }
            $r = 0;
            $g = 0;
            $b = 0;
            if (($i >= $max_iter)) {
                $r = 0;
                $g = 0;
                $b = 0;
            } else {
                $trap_scaled = ($trap * 3.2);
                if (($trap_scaled > 1.0)) {
                    $trap_scaled = 1.0;
                }
                if (($trap_scaled < 0.0)) {
                    $trap_scaled = 0.0;
                }
                $t = ($i / $__hoisted_cast_3);
                $tone = ((int)((255.0 * (1.0 - $trap_scaled))));
                $r = ((int)(($tone * (0.35 + (0.65 * $t)))));
                $g = ((int)(($tone * (0.15 + (0.85 * (1.0 - $t))))));
                $b = ((int)((255.0 * (0.25 + (0.75 * $t)))));
                if (($r > 255)) {
                    $r = 255;
                }
                if (($g > 255)) {
                    $g = 255;
                }
                if (($b > 255)) {
                    $b = 255;
                }
            }
            $pixels[] = $r;
            $pixels[] = $g;
            $pixels[] = $b;
        }
    }
    return $pixels;
}

function run_04_orbit_trap_julia() {
    $width = 1920;
    $height = 1080;
    $max_iter = 1400;
    $out_path = "sample/out/04_orbit_trap_julia.png";
    $start = __pytra_perf_counter();
    $pixels = render_orbit_trap_julia($width, $height, $max_iter, (-0.7269), 0.1889);
    __pytra_noop($out_path, $width, $height, $pixels);
    $elapsed = (__pytra_perf_counter() - $start);
    __pytra_print("output:", $out_path);
    __pytra_print("size:", $width, "x", $height);
    __pytra_print("max_iter:", $max_iter);
    __pytra_print("elapsed_sec:", $elapsed);
}

function __pytra_main(): void {
    run_04_orbit_trap_julia();
}

__pytra_main();
