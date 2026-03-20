#Requires -Version 5.1

$pytra_runtime = Join-Path $PSScriptRoot "py_runtime.ps1"
if (Test-Path $pytra_runtime) { . $pytra_runtime }

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# import: pytra.std

# import: pytra.std.time

# import: pytra.utils.gif

function color_palette {
    param()
    $p = (__pytra_bytearray 0)
    for ($i = 0; ($i -lt 256); $i++) {
        $r = $i
        $g = (($i * 3) % 256)
        $b = (255 - $i)
        $p += @($r)
        $p += @($g)
        $p += @($b)
    }
    return (__pytra_bytes $p)
}

function run_11_lissajous_particles {
    param()
    $w = 320
    $h = 240
    $frames_n = 360
    $particles = 48
    $out_path = "sample/out/11_lissajous_particles.gif"
    $start = (perf_counter)
    $frames = @()
    for ($t = 0; ($t -lt $frames_n); $t++) {
        $frame = (__pytra_bytearray ($w * $h))
        $__hoisted_cast_1 = __pytra_float $t
        for ($p = 0; ($p -lt $particles); $p++) {
            $phase = ($p * 0.261799)
            $x = __pytra_int (($w * 0.5) + (($w * 0.38) * [Math]::Sin(((0.11 * $__hoisted_cast_1) + ($phase * 2.0)))))
            $y = __pytra_int (($h * 0.5) + (($h * 0.38) * [Math]::Sin(((0.17 * $__hoisted_cast_1) + ($phase * 3.0)))))
            $color = (30 + (($p * 9) % 220))
            for ($dy = 0; ($dy -lt 3); $dy++) {
                for ($dx = 0; ($dx -lt 3); $dx++) {
                    $xx = ($x + $dx)
                    $yy = ($y + $dy)
                    if ((($xx -ge 0) -and ($xx -lt $w) -and ($yy -ge 0) -and ($yy -lt $h))) {
                        $d2 = (($dx * $dx) + ($dy * $dy))
                        if (($d2 -le 4)) {
                            $idx = (($yy * $w) + $xx)
                            $v = ($color - ($d2 * 20))
                            $v = [Math]::Max(0, $v)
                            if (($v -gt $frame[$idx])) {
                                $frame[$idx] = $v
                            }
                        }
                    }
                }
            }
        }
        $frames += @((__pytra_bytes $frame))
    }
    (save_gif $out_path $w $h $frames (color_palette))
    $elapsed = ((perf_counter) - $start)
    __pytra_print "output:" $out_path
    __pytra_print "frames:" $frames_n
    __pytra_print "elapsed_sec:" $elapsed
}

(run_11_lissajous_particles)
