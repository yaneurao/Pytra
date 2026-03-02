<?php
declare(strict_types=1);

require_once __DIR__ . '/pytra/py_runtime.php';

// 11: Sample that outputs Lissajous-motion particles as a GIF.
function color_palette() {
    $p = bytearray();
    for ($i = 0; $i < 256; $i += 1) {
        $r = $i;
        $g = (($i * 3) % 256);
        $b = (255 - $i);
        $p[] = $r;
        $p[] = $g;
        $p[] = $b;
    }
    return bytes($p);
}

function run_11_lissajous_particles() {
    $w = 320;
    $h = 240;
    $frames_n = 360;
    $particles = 48;
    $out_path = "sample/out/11_lissajous_particles.gif";
    $start = __pytra_perf_counter();
    $frames = [];
    for ($t = 0; $t < $frames_n; $t += 1) {
        $frame = bytearray(($w * $h));
        $__hoisted_cast_1 = ((float)($t));
        for ($p = 0; $p < $particles; $p += 1) {
            $phase = ($p * 0.261799);
            $x = ((int)((($w * 0.5) + (($w * 0.38) * sin(((0.11 * $__hoisted_cast_1) + ($phase * 2.0)))))));
            $y = ((int)((($h * 0.5) + (($h * 0.38) * sin(((0.17 * $__hoisted_cast_1) + ($phase * 3.0)))))));
            $color = (30 + (($p * 9) % 220));
            for ($dy = (-2); $dy < 3; $dy += 1) {
                for ($dx = (-2); $dx < 3; $dx += 1) {
                    $xx = ($x + $dx);
                    $yy = ($y + $dy);
                    if ((($xx >= 0) && ($xx < $w) && ($yy >= 0) && ($yy < $h))) {
                        $d2 = (($dx * $dx) + ($dy * $dy));
                        if (($d2 <= 4)) {
                            $idx = (($yy * $w) + $xx);
                            $v = ($color - ($d2 * 20));
                            $v = max(0, $v);
                            if (($v > $frame[$idx])) {
                                $frame[$idx] = $v;
                            }
                        }
                    }
                }
            }
        }
        $frames[] = bytes($frame);
    }
    __pytra_noop($out_path, $w, $h, $frames, color_palette());
    $elapsed = (__pytra_perf_counter() - $start);
    __pytra_print("output:", $out_path);
    __pytra_print("frames:", $frames_n);
    __pytra_print("elapsed_sec:", $elapsed);
}

function __pytra_main(): void {
    run_11_lissajous_particles();
}

__pytra_main();
