#Requires -Version 5.1

$pytra_runtime = Join-Path $PSScriptRoot "py_runtime.ps1"
if (Test-Path $pytra_runtime) { . $pytra_runtime }

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# import: pytra.std.time

# import: pytra.utils

function render_orbit_trap_julia {
    param($width, $height, $max_iter, $cx, $cy)
    $pixels = (__pytra_bytearray 0)
    $__hoisted_cast_1 = __pytra_float ($height - 1)
    $__hoisted_cast_2 = __pytra_float ($width - 1)
    $__hoisted_cast_3 = __pytra_float $max_iter
    for ($y = 0; ($y -lt $height); $y++) {
        $zy0 = ((-1.3) + (2.6 * ($y / $__hoisted_cast_1)))
        for ($x = 0; ($x -lt $width); $x++) {
            $zx = ((-1.9) + (3.8 * ($x / $__hoisted_cast_2)))
            $zy = $zy0
            $trap_ = 1000000000.0
            $i = 0
            while (($i -lt $max_iter)) {
                $ax = $zx
                if (($ax -lt 0.0)) {
                    $ax = (-$ax)
                }
                $ay = $zy
                if (($ay -lt 0.0)) {
                    $ay = (-$ay)
                }
                $dxy = ($zx - $zy)
                if (($dxy -lt 0.0)) {
                    $dxy = (-$dxy)
                }
                if (($ax -lt $trap_)) {
                    $trap_ = $ax
                }
                if (($ay -lt $trap_)) {
                    $trap_ = $ay
                }
                if (($dxy -lt $trap_)) {
                    $trap_ = $dxy
                }
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
                $trap_scaled = ($trap_ * 3.2)
                if (($trap_scaled -gt 1.0)) {
                    $trap_scaled = 1.0
                }
                if (($trap_scaled -lt 0.0)) {
                    $trap_scaled = 0.0
                }
                $t = ($i / $__hoisted_cast_3)
                $tone = __pytra_int (255.0 * (1.0 - $trap_scaled))
                $r = __pytra_int ($tone * (0.35 + (0.65 * $t)))
                $g = __pytra_int ($tone * (0.15 + (0.85 * (1.0 - $t))))
                $b = __pytra_int (255.0 * (0.25 + (0.75 * $t)))
                if (($r -gt 255)) {
                    $r = 255
                }
                if (($g -gt 255)) {
                    $g = 255
                }
                if (($b -gt 255)) {
                    $b = 255
                }
            }
            $pixels += @($r)
            $pixels += @($g)
            $pixels += @($b)
        }
    }
    return $pixels
}

function run_04_orbit_trap_julia {
    param()
    $width = 1920
    $height = 1080
    $max_iter = 1400
    $out_path = "sample/out/04_orbit_trap_julia.png"
    $start = (perf_counter)
    $pixels = (render_orbit_trap_julia $width $height $max_iter (-0.7269) 0.1889)
    $png.write_rgb_png($out_path, $width, $height, $pixels)
    $elapsed = ((perf_counter) - $start)
    __pytra_print "output:" $out_path
    __pytra_print "size:" $width "x" $height
    __pytra_print "max_iter:" $max_iter
    __pytra_print "elapsed_sec:" $elapsed
}

(run_04_orbit_trap_julia)
