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
            $v = (($grid[__pytra_index($grid, $y)][__pytra_index($grid[__pytra_index($grid, $y)], $x)] == 0) ? 255 : 40);
            for ($yy = 0; $yy < $scale; $yy += 1) {
                $base = (((($y * $scale) + $yy) * $width) + ($x * $scale));
                for ($xx = 0; $xx < $scale; $xx += 1) {
                    $frame[__pytra_index($frame, ($base + $xx))] = $v;
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
    $grid = [];
    for ($__pytra_lc_i_0 = 0; $__pytra_lc_i_0 < $cell_h; $__pytra_lc_i_0 += 1) {
        $_ = $__pytra_lc_i_0;
        $grid[] = __pytra_list_repeat([1], __pytra_int($cell_w));
    }
    $stack = [[1, 1]];
    $grid[__pytra_index($grid, 1)][__pytra_index($grid[__pytra_index($grid, 1)], 1)] = 0;
    $dirs = [[2, 0], [(-2), 0], [0, 2], [0, (-2)]];
    $frames = [];
    $step = 0;
    while ($stack) {
        $__pytra_unpack_0 = $stack[__pytra_index($stack, (-1))];
        $x = ($__pytra_unpack_0[0] ?? null);
        $y = ($__pytra_unpack_0[1] ?? null);
        $candidates = [];
        for ($k = 0; $k < 4; $k += 1) {
            $__pytra_unpack_0 = $dirs[__pytra_index($dirs, $k)];
            $dx = ($__pytra_unpack_0[0] ?? null);
            $dy = ($__pytra_unpack_0[1] ?? null);
            $nx = ($x + $dx);
            $ny = ($y + $dy);
            if ((($nx >= 1) && ($nx < ($cell_w - 1)) && ($ny >= 1) && ($ny < ($cell_h - 1)) && ($grid[__pytra_index($grid, $ny)][__pytra_index($grid[__pytra_index($grid, $ny)], $nx)] == 1))) {
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
            $sel = $candidates[__pytra_index($candidates, (((($x * 17) + ($y * 29)) + (__pytra_len($stack) * 13)) % __pytra_len($candidates)))];
            $__pytra_unpack_0 = $sel;
            $nx = ($__pytra_unpack_0[0] ?? null);
            $ny = ($__pytra_unpack_0[1] ?? null);
            $wx = ($__pytra_unpack_0[2] ?? null);
            $wy = ($__pytra_unpack_0[3] ?? null);
            $grid[__pytra_index($grid, $wy)][__pytra_index($grid[__pytra_index($grid, $wy)], $wx)] = 0;
            $grid[__pytra_index($grid, $ny)][__pytra_index($grid[__pytra_index($grid, $ny)], $nx)] = 0;
            $stack[] = [$nx, $ny];
        }
        if ((($step % $capture_every) == 0)) {
            $frames[] = capture($grid, $cell_w, $cell_h, $scale);
        }
        $step += 1;
    }
    $frames[] = capture($grid, $cell_w, $cell_h, $scale);
    __pytra_save_gif($out_path, ($cell_w * $scale), ($cell_h * $scale), $frames, grayscale_palette());
    $elapsed = (__pytra_perf_counter() - $start);
    __pytra_print("output:", $out_path);
    __pytra_print("frames:", __pytra_len($frames));
    __pytra_print("elapsed_sec:", $elapsed);
}

function __pytra_main(): void {
    run_13_maze_generation_steps();
}

__pytra_main();
