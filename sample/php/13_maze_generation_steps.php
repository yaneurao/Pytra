<?php
declare(strict_types=1);

require_once __DIR__ . '/pytra/py_runtime.php';

// 13: Sample that outputs DFS maze-generation progress as a GIF.
function capture($grid, $w, $h, $scale) {
    $width = ($w * $scale);
    $height = ($h * $scale);
    $frame = bytearray(($width * $height));
    for ($y = 0; $y < $h; $y += 1) {
        for ($x = 0; $x < $w; $x += 1) {
            $v = (($grid[$y][$x] == 0) ? 255 : 40);
            for ($yy = 0; $yy < $scale; $yy += 1) {
                $base = (((($y * $scale) + $yy) * $width) + ($x * $scale));
                for ($xx = 0; $xx < $scale; $xx += 1) {
                    $frame[($base + $xx)] = $v;
                }
            }
        }
    }
    return bytes($frame);
}

function run_13_maze_generation_steps() {
    $cell_w = 89;
    $cell_h = 67;
    $scale = 5;
    $capture_every = 20;
    $out_path = "sample/out/13_maze_generation_steps.gif";
    $start = __pytra_perf_counter();
    $grid = null;
    $stack = [[1, 1]];
    $grid[1][1] = 0;
    $dirs = [[2, 0], [(-2), 0], [0, 2], [0, (-2)]];
    $frames = [];
    $step = 0;
    while ($stack) {
        $_ = $stack[(-1)];
        $candidates = [];
        for ($k = 0; $k < 4; $k += 1) {
            $_ = $dirs[$k];
            $nx = ($x + $dx);
            $ny = ($y + $dy);
            if ((($nx >= 1) && ($nx < ($cell_w - 1)) && ($ny >= 1) && ($ny < ($cell_h - 1)) && ($grid[$ny][$nx] == 1))) {
                if (($dx == 2)) {
                    $candidates[] = [$nx, $ny, ($x + 1), $y];
                } else {
                    if (($dx == (-2))) {
                        $candidates[] = [$nx, $ny, ($x - 1), $y];
                    } else {
                        if (($dy == 2)) {
                            $candidates[] = [$nx, $ny, $x, ($y + 1)];
                        } else {
                            $candidates[] = [$nx, $ny, $x, ($y - 1)];
                        }
                    }
                }
            }
        }
        if ((__pytra_len($candidates) == 0)) {
            array_pop($stack);
        } else {
            $sel = $candidates[(((($x * 17) + ($y * 29)) + (__pytra_len($stack) * 13)) % __pytra_len($candidates))];
            $_ = $sel;
            $grid[$wy][$wx] = 0;
            $grid[$ny][$nx] = 0;
            $stack[] = [$nx, $ny];
        }
        if ((($step % $capture_every) == 0)) {
            $frames[] = capture($grid, $cell_w, $cell_h, $scale);
        }
        $step += 1;
    }
    $frames[] = capture($grid, $cell_w, $cell_h, $scale);
    __pytra_noop($out_path, ($cell_w * $scale), ($cell_h * $scale), $frames, grayscale_palette());
    $elapsed = (__pytra_perf_counter() - $start);
    __pytra_print("output:", $out_path);
    __pytra_print("frames:", __pytra_len($frames));
    __pytra_print("elapsed_sec:", $elapsed);
}

function __pytra_main(): void {
    run_13_maze_generation_steps();
}

__pytra_main();
