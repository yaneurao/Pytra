<?php
declare(strict_types=1);

require_once __DIR__ . '/pytra/py_runtime.php';

// 09: Sample that outputs a simple fire effect as a GIF.
function fire_palette() {
    $p = bytearray();
    for ($i = 0; $i < 256; $i += 1) {
        $r = 0;
        $g = 0;
        $b = 0;
        if (($i < 85)) {
            $r = ($i * 3);
            $g = 0;
            $b = 0;
        } else {
            if (($i < 170)) {
                $r = 255;
                $g = (($i - 85) * 3);
                $b = 0;
            } else {
                $r = 255;
                $g = 255;
                $b = (($i - 170) * 3);
            }
        }
        $p[] = $r;
        $p[] = $g;
        $p[] = $b;
    }
    return bytes($p);
}

function run_09_fire_simulation() {
    $w = 380;
    $h = 260;
    $steps = 420;
    $out_path = "sample/out/09_fire_simulation.gif";
    $start = __pytra_perf_counter();
    $heat = null;
    $frames = [];
    for ($t = 0; $t < $steps; $t += 1) {
        for ($x = 0; $x < $w; $x += 1) {
            $val = (170 + ((($x * 13) + ($t * 17)) % 86));
            $heat[($h - 1)][$x] = $val;
        }
        for ($y = 1; $y < $h; $y += 1) {
            for ($x = 0; $x < $w; $x += 1) {
                $a = $heat[$y][$x];
                $b = $heat[$y][((($x - 1) + $w) % $w)];
                $c = $heat[$y][(($x + 1) % $w)];
                $d = $heat[(($y + 1) % $h)][$x];
                $v = intdiv(((($a + $b) + $c) + $d), 4);
                $cool = (1 + ((($x + $y) + $t) % 3));
                $nv = ($v - $cool);
                $heat[($y - 1)][$x] = (($nv > 0) ? $nv : 0);
            }
        }
        $frame = bytearray(($w * $h));
        for ($yy = 0; $yy < $h; $yy += 1) {
            $row_base = ($yy * $w);
            for ($xx = 0; $xx < $w; $xx += 1) {
                $frame[($row_base + $xx)] = $heat[$yy][$xx];
            }
        }
        $frames[] = bytes($frame);
    }
    __pytra_noop($out_path, $w, $h, $frames, fire_palette());
    $elapsed = (__pytra_perf_counter() - $start);
    __pytra_print("output:", $out_path);
    __pytra_print("frames:", $steps);
    __pytra_print("elapsed_sec:", $elapsed);
}

function __pytra_main(): void {
    run_09_fire_simulation();
}

__pytra_main();
