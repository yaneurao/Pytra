#Requires -Version 5.1

$pytra_runtime = Join-Path $PSScriptRoot "py_runtime.ps1"
if (Test-Path $pytra_runtime) { . $pytra_runtime }

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# import: pytra.std

# import: pytra.std.time

# import: pytra.utils.gif

function julia_palette {
    param()
    $palette = (__pytra_bytearray (256 * 3))
    $palette[0] = 0
    $palette[1] = 0
    $palette[2] = 0
    for ($i = 0; ($i -lt 256); $i++) {
        $t = (($i - 1) / 254.0)
        $r = __pytra_int (255.0 * ((((9.0 * (1.0 - $t)) * $t) * $t) * $t))
        $g = __pytra_int (255.0 * ((((15.0 * (1.0 - $t)) * (1.0 - $t)) * $t) * $t))
        $b = __pytra_int (255.0 * ((((8.5 * (1.0 - $t)) * (1.0 - $t)) * (1.0 - $t)) * $t))
        $palette[(($i * 3) + 0)] = $r
        $palette[(($i * 3) + 1)] = $g
        $palette[(($i * 3) + 2)] = $b
    }
    return (__pytra_bytes $palette)
}

function render_frame {
    param($width, $height, $cr, $ci, $max_iter, $phase)
    $frame = (__pytra_bytearray ($width * $height))
    $__hoisted_cast_1 = __pytra_float ($height - 1)
    $__hoisted_cast_2 = __pytra_float ($width - 1)
    for ($y = 0; ($y -lt $height); $y++) {
        $row_base = ($y * $width)
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
                $zy = (((2.0 * $zx) * $zy) + $ci)
                $zx = (($zx2 - $zy2) + $cr)
                $i += 1
            }
            if (($i -ge $max_iter)) {
                $frame[($row_base + $x)] = 0
            } else {
                $color_index = (1 + (([Math]::Floor(($i * 224) / $max_iter) + $phase) % 255))
                $frame[($row_base + $x)] = $color_index
            }
        }
    }
    return (__pytra_bytes $frame)
}

function run_06_julia_parameter_sweep {
    param()
    $width = 320
    $height = 240
    $frames_n = 72
    $max_iter = 180
    $out_path = "sample/out/06_julia_parameter_sweep.gif"
    $start = (perf_counter)
    $frames = @()
    $center_cr = (-0.745)
    $center_ci = 0.186
    $radius_cr = 0.12
    $radius_ci = 0.1
    $start_offset = 20
    $phase_offset = 180
    $__hoisted_cast_3 = __pytra_float $frames_n
    for ($i = 0; ($i -lt $frames_n); $i++) {
        $t = ((($i + $start_offset) % $frames_n) / $__hoisted_cast_3)
        $angle = ((2.0 * $math.pi) * $t)
        $cr = ($center_cr + ($radius_cr * [Math]::Cos($angle)))
        $ci = ($center_ci + ($radius_ci * [Math]::Sin($angle)))
        $phase = (($phase_offset + ($i * 5)) % 255)
        $frames += @((render_frame $width $height $cr $ci $max_iter $phase))
    }
    (save_gif $out_path $width $height $frames (julia_palette))
    $elapsed = ((perf_counter) - $start)
    __pytra_print "output:" $out_path
    __pytra_print "frames:" $frames_n
    __pytra_print "elapsed_sec:" $elapsed
}

(run_06_julia_parameter_sweep)
