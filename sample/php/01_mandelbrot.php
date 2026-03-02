<?php
declare(strict_types=1);

require_once __DIR__ . '/pytra/py_runtime.php';

// 01: Sample that outputs the Mandelbrot set as a PNG image.
// Syntax is kept straightforward with future transpilation in mind.
function escape_count($cx, $cy, $max_iter) {
    $x = 0.0;
    $y = 0.0;
    for ($i = 0; $i < $max_iter; $i += 1) {
        $x2 = ($x * $x);
        $y2 = ($y * $y);
        if ((($x2 + $y2) > 4.0)) {
            return $i;
        }
        $y = (((2.0 * $x) * $y) + $cy);
        $x = (($x2 - $y2) + $cx);
    }
    return $max_iter;
}

function color_map($iter_count, $max_iter) {
    if (($iter_count >= $max_iter)) {
        return [0, 0, 0];
    }
    $t = ($iter_count / $max_iter);
    $r = ((int)((255.0 * ($t * $t))));
    $g = ((int)((255.0 * $t)));
    $b = ((int)((255.0 * (1.0 - $t))));
    return [$r, $g, $b];
}

function render_mandelbrot($width, $height, $max_iter, $x_min, $x_max, $y_min, $y_max) {
    $pixels = bytearray();
    $__hoisted_cast_1 = ((float)(($height - 1)));
    $__hoisted_cast_2 = ((float)(($width - 1)));
    $__hoisted_cast_3 = ((float)($max_iter));
    for ($y = 0; $y < $height; $y += 1) {
        $py = ($y_min + (($y_max - $y_min) * ($y / $__hoisted_cast_1)));
        for ($x = 0; $x < $width; $x += 1) {
            $px = ($x_min + (($x_max - $x_min) * ($x / $__hoisted_cast_2)));
            $it = escape_count($px, $py, $max_iter);
            $r = null;
            $g = null;
            $b = null;
            if (($it >= $max_iter)) {
                $r = 0;
                $g = 0;
                $b = 0;
            } else {
                $t = ($it / $__hoisted_cast_3);
                $r = ((int)((255.0 * ($t * $t))));
                $g = ((int)((255.0 * $t)));
                $b = ((int)((255.0 * (1.0 - $t))));
            }
            $pixels[] = $r;
            $pixels[] = $g;
            $pixels[] = $b;
        }
    }
    return $pixels;
}

function run_mandelbrot() {
    $width = 1600;
    $height = 1200;
    $max_iter = 1000;
    $out_path = "sample/out/01_mandelbrot.png";
    $start = __pytra_perf_counter();
    $pixels = render_mandelbrot($width, $height, $max_iter, (-2.2), 1.0, (-1.2), 1.2);
    __pytra_noop($out_path, $width, $height, $pixels);
    $elapsed = (__pytra_perf_counter() - $start);
    __pytra_print("output:", $out_path);
    __pytra_print("size:", $width, "x", $height);
    __pytra_print("max_iter:", $max_iter);
    __pytra_print("elapsed_sec:", $elapsed);
}

function __pytra_main(): void {
    run_mandelbrot();
}

__pytra_main();
