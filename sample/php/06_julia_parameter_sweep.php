<?php
declare(strict_types=1);

require_once __DIR__ . '/pytra/py_runtime.php';

// 06: Sample that sweeps Julia-set parameters and outputs a GIF.
function julia_palette() {
    $palette = bytearray((256 * 3));
    $palette[0] = 0;
    $palette[1] = 0;
    $palette[2] = 0;
    for ($i = 1; $i < 256; $i += 1) {
        $t = (($i - 1) / 254.0);
        $r = ((int)((255.0 * ((((9.0 * (1.0 - $t)) * $t) * $t) * $t))));
        $g = ((int)((255.0 * ((((15.0 * (1.0 - $t)) * (1.0 - $t)) * $t) * $t))));
        $b = ((int)((255.0 * ((((8.5 * (1.0 - $t)) * (1.0 - $t)) * (1.0 - $t)) * $t))));
        $palette[(($i * 3) + 0)] = $r;
        $palette[(($i * 3) + 1)] = $g;
        $palette[(($i * 3) + 2)] = $b;
    }
    return bytes($palette);
}

function render_frame($width, $height, $cr, $ci, $max_iter, $phase) {
    $frame = bytearray(($width * $height));
    $__hoisted_cast_1 = ((float)(($height - 1)));
    $__hoisted_cast_2 = ((float)(($width - 1)));
    for ($y = 0; $y < $height; $y += 1) {
        $row_base = ($y * $width);
        $zy0 = ((-1.2) + (2.4 * ($y / $__hoisted_cast_1)));
        for ($x = 0; $x < $width; $x += 1) {
            $zx = ((-1.8) + (3.6 * ($x / $__hoisted_cast_2)));
            $zy = $zy0;
            $i = 0;
            while (($i < $max_iter)) {
                $zx2 = ($zx * $zx);
                $zy2 = ($zy * $zy);
                if ((($zx2 + $zy2) > 4.0)) {
                    break;
                }
                $zy = (((2.0 * $zx) * $zy) + $ci);
                $zx = (($zx2 - $zy2) + $cr);
                $i += 1;
            }
            if (($i >= $max_iter)) {
                $frame[($row_base + $x)] = 0;
            } else {
                $color_index = (1 + ((intdiv(($i * 224), $max_iter) + $phase) % 255));
                $frame[($row_base + $x)] = $color_index;
            }
        }
    }
    return bytes($frame);
}

function run_06_julia_parameter_sweep() {
    $width = 320;
    $height = 240;
    $frames_n = 72;
    $max_iter = 180;
    $out_path = "sample/out/06_julia_parameter_sweep.gif";
    $start = __pytra_perf_counter();
    $frames = [];
    $center_cr = (-0.745);
    $center_ci = 0.186;
    $radius_cr = 0.12;
    $radius_ci = 0.1;
    $start_offset = 20;
    $phase_offset = 180;
    $__hoisted_cast_3 = ((float)($frames_n));
    for ($i = 0; $i < $frames_n; $i += 1) {
        $t = ((($i + $start_offset) % $frames_n) / $__hoisted_cast_3);
        $angle = ((2.0 * M_PI) * $t);
        $cr = ($center_cr + ($radius_cr * cos($angle)));
        $ci = ($center_ci + ($radius_ci * sin($angle)));
        $phase = (($phase_offset + ($i * 5)) % 255);
        $frames[] = render_frame($width, $height, $cr, $ci, $max_iter, $phase);
    }
    __pytra_noop($out_path, $width, $height, $frames, julia_palette());
    $elapsed = (__pytra_perf_counter() - $start);
    __pytra_print("output:", $out_path);
    __pytra_print("frames:", $frames_n);
    __pytra_print("elapsed_sec:", $elapsed);
}

function __pytra_main(): void {
    run_06_julia_parameter_sweep();
}

__pytra_main();
