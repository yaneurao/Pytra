<?php
declare(strict_types=1);

if (!function_exists('__pytra_time_perf_counter')) {
    function __pytra_time_perf_counter(): float {
        return microtime(true);
    }
}
