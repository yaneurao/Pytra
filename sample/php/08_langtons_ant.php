<?php
declare(strict_types=1);

require_once __DIR__ . '/pytra/py_runtime.php';

// 08: Sample that outputs Langton's Ant trajectories as a GIF.
function capture($grid, $w, $h) {
    $frame = bytearray(($w * $h));
    for ($y = 0; $y < $h; $y += 1) {
        $row_base = ($y * $w);
        for ($x = 0; $x < $w; $x += 1) {
            $frame[($row_base + $x)] = ($grid[$y][$x] ? 255 : 0);
        }
    }
    return bytes($frame);
}

function run_08_langtons_ant() {
    $w = 420;
    $h = 420;
    $out_path = "sample/out/08_langtons_ant.gif";
    $start = __pytra_perf_counter();
    $grid = null;
    $x = intdiv($w, 2);
    $y = intdiv($h, 2);
    $d = 0;
    $steps_total = 600000;
    $capture_every = 3000;
    $frames = [];
    for ($i = 0; $i < $steps_total; $i += 1) {
        if (($grid[$y][$x] == 0)) {
            $d = (($d + 1) % 4);
            $grid[$y][$x] = 1;
        } else {
            $d = (($d + 3) % 4);
            $grid[$y][$x] = 0;
        }
        if (($d == 0)) {
            $y = ((($y - 1) + $h) % $h);
        } else {
            if (($d == 1)) {
                $x = (($x + 1) % $w);
            } else {
                if (($d == 2)) {
                    $y = (($y + 1) % $h);
                } else {
                    $x = ((($x - 1) + $w) % $w);
                }
            }
        }
        if ((($i % $capture_every) == 0)) {
            $frames[] = capture($grid, $w, $h);
        }
    }
    __pytra_noop($out_path, $w, $h, $frames, grayscale_palette());
    $elapsed = (__pytra_perf_counter() - $start);
    __pytra_print("output:", $out_path);
    __pytra_print("frames:", __pytra_len($frames));
    __pytra_print("elapsed_sec:", $elapsed);
}

function __pytra_main(): void {
    run_08_langtons_ant();
}

__pytra_main();
