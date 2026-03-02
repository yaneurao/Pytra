<?php
declare(strict_types=1);

require_once __DIR__ . '/pytra/py_runtime.php';

// 15: Sample that renders wave interference animation and writes a GIF.
function run_15_wave_interference_loop() {
    $w = 320;
    $h = 240;
    $frames_n = 96;
    $out_path = "sample/out/15_wave_interference_loop.gif";
    $start = __pytra_perf_counter();
    $frames = [];
    for ($t = 0; $t < $frames_n; $t += 1) {
        $frame = bytearray(($w * $h));
        $phase = ($t * 0.12);
        for ($y = 0; $y < $h; $y += 1) {
            $row_base = ($y * $w);
            for ($x = 0; $x < $w; $x += 1) {
                $dx = ($x - 160);
                $dy = ($y - 120);
                $v = (((sin((($x + ($t * 1.5)) * 0.045)) + sin((($y - ($t * 1.2)) * 0.04))) + sin(((($x + $y) * 0.02) + $phase))) + sin(((sqrt((($dx * $dx) + ($dy * $dy))) * 0.08) - ($phase * 1.3))));
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
    run_15_wave_interference_loop();
}

__pytra_main();
