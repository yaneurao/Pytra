#Requires -Version 5.1

$pytra_runtime = Join-Path $PSScriptRoot "py_runtime.ps1"
if (Test-Path $pytra_runtime) { . $pytra_runtime }

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# import: pytra.std.time

# import: pytra.utils

function render_julia {
    param($width, $height, $max_iter, $cx, $cy)
    $pixels = (__pytra_bytearray 0)
    $__hoisted_cast_1 = __pytra_float ($height - 1)
    $__hoisted_cast_2 = __pytra_float ($width - 1)
    $__hoisted_cast_3 = __pytra_float $max_iter
    for ($y = 0; ($y -lt $height); $y++) {
        $zy0 = ((-1.2) + (2.4 * ($y / $__hoisted_cast_1)))
        for ($x = 0; ($x -lt $width); $x++) {
            $zx = ((-1.8) + (3.6 * ($x / $__hoisted_cast_2)))
            $zy = $zy0
            $i = 0
            while (($i -lt $max_iter)) {
                $zx2 = ($zx * $zx)
                $zy2 = ($zy * $zy)
                if ((($zx2 + $zy2) -gt 4.0)) {
                    break
                }
                $zy = (((2.0 * $zx) * $zy) + $cy)
                $zx = (($zx2 - $zy2) + $cx)
                $i += 1
            }
            $r = 0
            $g = 0
            $b = 0
            if (($i -ge $max_iter)) {
                $r = 0
                $g = 0
                $b = 0
            } else {
                $t = ($i / $__hoisted_cast_3)
                $r = __pytra_int (255.0 * (0.2 + (0.8 * $t)))
                $g = __pytra_int (255.0 * (0.1 + (0.9 * ($t * $t))))
                $b = __pytra_int (255.0 * (1.0 - $t))
            }
            $pixels += @($r)
            $pixels += @($g)
            $pixels += @($b)
        }
    }
    return $pixels
}

function run_julia {
    param()
    $width = 3840
    $height = 2160
    $max_iter = 20000
    $out_path = "sample/out/03_julia_set.png"
    $start = (perf_counter)
    $pixels = (render_julia $width $height $max_iter (-0.8) 0.156)
    $png.write_rgb_png($out_path, $width, $height, $pixels)
    $elapsed = ((perf_counter) - $start)
    __pytra_print "output:" $out_path
    __pytra_print "size:" $width "x" $height
    __pytra_print "max_iter:" $max_iter
    __pytra_print "elapsed_sec:" $elapsed
}

(run_julia)
