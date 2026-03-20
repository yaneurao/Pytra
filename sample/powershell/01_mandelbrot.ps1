#Requires -Version 5.1

$pytra_runtime = Join-Path $PSScriptRoot "py_runtime.ps1"
if (Test-Path $pytra_runtime) { . $pytra_runtime }

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# import: pytra.std.time

# import: pytra.utils

function escape_count {
    param($cx, $cy, $max_iter)
    $x = 0.0
    $y = 0.0
    for ($i = 0; ($i -lt $max_iter); $i++) {
        $x2 = ($x * $x)
        $y2 = ($y * $y)
        if ((($x2 + $y2) -gt 4.0)) {
            return $i
        }
        $y = (((2.0 * $x) * $y) + $cy)
        $x = (($x2 - $y2) + $cx)
    }
    return $max_iter
}

function color_map {
    param($iter_count, $max_iter)
    if (($iter_count -ge $max_iter)) {
        return @(0, 0, 0)
    }
    $t = ($iter_count / $max_iter)
    $r = __pytra_int (255.0 * ($t * $t))
    $g = __pytra_int (255.0 * $t)
    $b = __pytra_int (255.0 * (1.0 - $t))
    return @($r, $g, $b)
}

function render_mandelbrot {
    param($width, $height, $max_iter, $x_min, $x_max, $y_min, $y_max)
    $pixels = (__pytra_bytearray 0)
    $__hoisted_cast_1 = __pytra_float ($height - 1)
    $__hoisted_cast_2 = __pytra_float ($width - 1)
    $__hoisted_cast_3 = __pytra_float $max_iter
    for ($y = 0; ($y -lt $height); $y++) {
        $py = ($y_min + (($y_max - $y_min) * ($y / $__hoisted_cast_1)))
        for ($x = 0; ($x -lt $width); $x++) {
            $px = ($x_min + (($x_max - $x_min) * ($x / $__hoisted_cast_2)))
            $it = (escape_count $px $py $max_iter)
            $r = $null
            $g = $null
            $b = $null
            if (($it -ge $max_iter)) {
                $r = 0
                $g = 0
                $b = 0
            } else {
                $t = ($it / $__hoisted_cast_3)
                $r = __pytra_int (255.0 * ($t * $t))
                $g = __pytra_int (255.0 * $t)
                $b = __pytra_int (255.0 * (1.0 - $t))
            }
            $pixels += @($r)
            $pixels += @($g)
            $pixels += @($b)
        }
    }
    return $pixels
}

function run_mandelbrot {
    param()
    $width = 1600
    $height = 1200
    $max_iter = 1000
    $out_path = "sample/out/01_mandelbrot.png"
    $start = (perf_counter)
    $pixels = (render_mandelbrot $width $height $max_iter (-2.2) 1.0 (-1.2) 1.2)
    $png.write_rgb_png($out_path, $width, $height, $pixels)
    $elapsed = ((perf_counter) - $start)
    __pytra_print "output:" $out_path
    __pytra_print "size:" $width "x" $height
    __pytra_print "max_iter:" $max_iter
    __pytra_print "elapsed_sec:" $elapsed
}

(run_mandelbrot)
