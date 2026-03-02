<?php
declare(strict_types=1);

require_once __DIR__ . '/pytra/py_runtime.php';

// 10: Sample that outputs a plasma effect as a GIF.
function run_10_plasma_effect() {
    $w = 320;
    $h = 240;
    $frames_n = 216;
    $out_path = "sample/out/10_plasma_effect.gif";
    $start = __pytra_perf_counter();
    $frames = [];
    for ($t = 0; $t < $frames_n; $t += 1) {
        $frame = bytearray(($w * $h));
        for ($y = 0; $y < $h; $y += 1) {
            $row_base = ($y * $w);
            for ($x = 0; $x < $w; $x += 1) {
                $dx = ($x - 160);
                $dy = ($y - 120);
                $v = (((sin((($x + ($t * 2.0)) * 0.045)) + sin((($y - ($t * 1.2)) * 0.05))) + sin(((($x + $y) + ($t * 1.7)) * 0.03))) + sin(((sqrt((($dx * $dx) + ($dy * $dy))) * 0.07) - ($t * 0.18))));
                $c = ((int)((($v + 4.0) * (255.0 / 8.0))));
                if (($c < 0)) {
                    $c = 0;
                }
                if (($c > 255)) {
                    $c = 255;
                }
                $frame[($row_base + $x)] = $c;
            }
        }
        $frames[] = bytes($frame);
    }
    __pytra_noop($out_path, $w, $h, $frames, grayscale_palette());
    $elapsed = (__pytra_perf_counter() - $start);
    __pytra_print("output:", $out_path);
    __pytra_print("frames:", $frames_n);
    __pytra_print("elapsed_sec:", $elapsed);
}

function __pytra_main(): void {
    run_10_plasma_effect();
}

__pytra_main();
