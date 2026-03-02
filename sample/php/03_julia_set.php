<?php
declare(strict_types=1);

require_once __DIR__ . '/pytra/py_runtime.php';

// 03: Sample that outputs a Julia set as a PNG image.
// Implemented with simple loop-centric logic for transpilation compatibility.
function render_julia($width, $height, $max_iter, $cx, $cy) {
    $pixels = bytearray();
    $__hoisted_cast_1 = ((float)(($height - 1)));
    $__hoisted_cast_2 = ((float)(($width - 1)));
    $__hoisted_cast_3 = ((float)($max_iter));
    for ($y = 0; $y < $height; $y += 1) {
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
                $zy = (((2.0 * $zx) * $zy) + $cy);
                $zx = (($zx2 - $zy2) + $cx);
                $i += 1;
            }
            $r = 0;
            $g = 0;
            $b = 0;
            if (($i >= $max_iter)) {
                $r = 0;
                $g = 0;
                $b = 0;
            } else {
                $t = ($i / $__hoisted_cast_3);
                $r = ((int)((255.0 * (0.2 + (0.8 * $t)))));
                $g = ((int)((255.0 * (0.1 + (0.9 * ($t * $t))))));
                $b = ((int)((255.0 * (1.0 - $t))));
            }
            $pixels[] = $r;
            $pixels[] = $g;
            $pixels[] = $b;
        }
    }
    return $pixels;
}

function run_julia() {
    $width = 3840;
    $height = 2160;
    $max_iter = 20000;
    $out_path = "sample/out/03_julia_set.png";
    $start = __pytra_perf_counter();
    $pixels = render_julia($width, $height, $max_iter, (-0.8), 0.156);
    __pytra_noop($out_path, $width, $height, $pixels);
    $elapsed = (__pytra_perf_counter() - $start);
    __pytra_print("output:", $out_path);
    __pytra_print("size:", $width, "x", $height);
    __pytra_print("max_iter:", $max_iter);
    __pytra_print("elapsed_sec:", $elapsed);
}

function __pytra_main(): void {
    run_julia();
}

__pytra_main();
