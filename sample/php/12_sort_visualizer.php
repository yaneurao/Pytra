<?php
declare(strict_types=1);

require_once __DIR__ . '/pytra/py_runtime.php';

// 12: Sample that outputs intermediate states of bubble sort as a GIF.
function render($values, $w, $h) {
    $frame = bytearray(($w * $h));
    $n = __pytra_len($values);
    $bar_w = ($w / $n);
    $__hoisted_cast_1 = ((float)($n));
    $__hoisted_cast_2 = ((float)($h));
    for ($i = 0; $i < $n; $i += 1) {
        $x0 = ((int)(($i * $bar_w)));
        $x1 = ((int)((($i + 1) * $bar_w)));
        if (($x1 <= $x0)) {
            $x1 = ($x0 + 1);
        }
        $bh = ((int)((($values[$i] / $__hoisted_cast_1) * $__hoisted_cast_2)));
        $y = ($h - $bh);
        for ($y = $y; $y < $h; $y += 1) {
            for ($x = $x0; $x < $x1; $x += 1) {
                $frame[(($y * $w) + $x)] = 255;
            }
        }
    }
    return bytes($frame);
}

function run_12_sort_visualizer() {
    $w = 320;
    $h = 180;
    $n = 124;
    $out_path = "sample/out/12_sort_visualizer.gif";
    $start = __pytra_perf_counter();
    $values = [];
    for ($i = 0; $i < $n; $i += 1) {
        $values[] = ((($i * 37) + 19) % $n);
    }
    $frames = [render($values, $w, $h)];
    $frame_stride = 16;
    $op = 0;
    for ($i = 0; $i < $n; $i += 1) {
        $swapped = false;
        for ($j = 0; $j < (($n - $i) - 1); $j += 1) {
            if (($values[$j] > $values[($j + 1)])) {
                $_ = [$values[($j + 1)], $values[$j]];
                $swapped = true;
            }
            if ((($op % $frame_stride) == 0)) {
                $frames[] = render($values, $w, $h);
            }
            $op += 1;
        }
        if ((!$swapped)) {
            break;
        }
    }
    __pytra_noop($out_path, $w, $h, $frames, grayscale_palette());
    $elapsed = (__pytra_perf_counter() - $start);
    __pytra_print("output:", $out_path);
    __pytra_print("frames:", __pytra_len($frames));
    __pytra_print("elapsed_sec:", $elapsed);
}

function __pytra_main(): void {
    run_12_sort_visualizer();
}

__pytra_main();
