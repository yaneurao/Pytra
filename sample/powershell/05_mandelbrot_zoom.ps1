#Requires -Version 5.1

$pytra_runtime = Join-Path $PSScriptRoot "py_runtime.ps1"
if (Test-Path $pytra_runtime) { . $pytra_runtime }

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# import: pytra.std.time

# import: pytra.utils.gif

function render_frame {
    param($width, $height, $center_x, $center_y, $scale, $max_iter)
    $frame = (__pytra_bytearray ($width * $height))
    $__hoisted_cast_1 = __pytra_float $max_iter
    for ($y = 0; ($y -lt $height); $y++) {
        $row_base = ($y * $width)
        $cy = ($center_y + (($y - ($height * 0.5)) * $scale))
        for ($x = 0; ($x -lt $width); $x++) {
            $cx = ($center_x + (($x - ($width * 0.5)) * $scale))
            $zx = 0.0
            $zy = 0.0
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
            $frame[($row_base + $x)] = __pytra_int ((255.0 * $i) / $__hoisted_cast_1)
        }
    }
    return (__pytra_bytes $frame)
}

function run_05_mandelbrot_zoom {
    param()
    $width = 320
    $height = 240
    $frame_count = 48
    $max_iter = 110
    $center_x = (-0.743643887037151)
    $center_y = 0.13182590420533
    $base_scale = (3.2 / $width)
    $zoom_per_frame = 0.93
    $out_path = "sample/out/05_mandelbrot_zoom.gif"
    $start = (perf_counter)
    $frames = @()
    $scale = $base_scale
    for ($_ = 0; ($_ -lt $frame_count); $_++) {
        $frames += @((render_frame $width $height $center_x $center_y $scale $max_iter))
        $scale *= $zoom_per_frame
    }
    (save_gif $out_path $width $height $frames (grayscale_palette))
    $elapsed = ((perf_counter) - $start)
    __pytra_print "output:" $out_path
    __pytra_print "frames:" $frame_count
    __pytra_print "elapsed_sec:" $elapsed
}

(run_05_mandelbrot_zoom)
