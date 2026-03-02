<?php
declare(strict_types=1);

require_once __DIR__ . '/pytra/py_runtime.php';

// 05: Sample that outputs a Mandelbrot zoom as an animated GIF.
function render_frame($width, $height, $center_x, $center_y, $scale, $max_iter) {
    $frame = bytearray(($width * $height));
    $__hoisted_cast_1 = ((float)($max_iter));
    for ($y = 0; $y < $height; $y += 1) {
        $row_base = ($y * $width);
        $cy = ($center_y + (($y - ($height * 0.5)) * $scale));
        for ($x = 0; $x < $width; $x += 1) {
            $cx = ($center_x + (($x - ($width * 0.5)) * $scale));
            $zx = 0.0;
            $zy = 0.0;
            $i = 0;
            while (($i < $max_iter)) {
                $zx2 = ($zx * $zx);
                $zy2 = ($zy * $zy);
                if ((($zx2 + $zy2) > 4.0)) {
                    break;
                }
                $zy = (((2.0 * $zx) * $zy) + $cy);
                $zx = (($zx2 - $zy2) + $cx);
                $i += 1;
            }
            $frame[($row_base + $x)] = ((int)(((255.0 * $i) / $__hoisted_cast_1)));
        }
    }
    return bytes($frame);
}

function run_05_mandelbrot_zoom() {
    $width = 320;
    $height = 240;
    $frame_count = 48;
    $max_iter = 110;
    $center_x = (-0.743643887037151);
    $center_y = 0.13182590420533;
    $base_scale = (3.2 / $width);
    $zoom_per_frame = 0.93;
    $out_path = "sample/out/05_mandelbrot_zoom.gif";
    $start = __pytra_perf_counter();
    $frames = [];
    $scale = $base_scale;
    for ($_ = 0; $_ < $frame_count; $_ += 1) {
        $frames[] = render_frame($width, $height, $center_x, $center_y, $scale, $max_iter);
        $scale *= $zoom_per_frame;
    }
    __pytra_noop($out_path, $width, $height, $frames, grayscale_palette());
    $elapsed = (__pytra_perf_counter() - $start);
    __pytra_print("output:", $out_path);
    __pytra_print("frames:", $frame_count);
    __pytra_print("elapsed_sec:", $elapsed);
}

function __pytra_main(): void {
    run_05_mandelbrot_zoom();
}

__pytra_main();
