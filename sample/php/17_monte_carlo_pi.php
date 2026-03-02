<?php
declare(strict_types=1);

require_once __DIR__ . '/pytra/py_runtime.php';

// 17: Sample that scans a large grid using integer arithmetic only and computes a checksum.
// It avoids floating-point error effects, making cross-language comparisons easier.
function run_integer_grid_checksum($width, $height, $seed) {
    $mod_main = 2147483647;
    $mod_out = 1000000007;
    $acc = ($seed % $mod_out);
    for ($y = 0; $y < $height; $y += 1) {
        $row_sum = 0;
        for ($x = 0; $x < $width; $x += 1) {
            $v = (((($x * 37) + ($y * 73)) + $seed) % $mod_main);
            $v = ((($v * 48271) + 1) % $mod_main);
            $row_sum += ($v % 256);
        }
        $acc = (($acc + ($row_sum * ($y + 1))) % $mod_out);
    }
    return $acc;
}

function run_integer_benchmark() {
    $width = 7600;
    $height = 5000;
    $start = __pytra_perf_counter();
    $checksum = run_integer_grid_checksum($width, $height, 123456789);
    $elapsed = (__pytra_perf_counter() - $start);
    __pytra_print("pixels:", ($width * $height));
    __pytra_print("checksum:", $checksum);
    __pytra_print("elapsed_sec:", $elapsed);
}

function __pytra_main(): void {
    run_integer_benchmark();
}

__pytra_main();
