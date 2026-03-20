#Requires -Version 5.1

$pytra_runtime = Join-Path $PSScriptRoot "py_runtime.ps1"
if (Test-Path $pytra_runtime) { . $pytra_runtime }

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# import: pytra.std.time

# import: pytra.utils.gif

function render {
    param($values, $w, $h)
    $frame = (__pytra_bytearray ($w * $h))
    $n = __pytra_len $values
    $bar_w = ($w / $n)
    $__hoisted_cast_1 = __pytra_float $n
    $__hoisted_cast_2 = __pytra_float $h
    for ($i = 0; ($i -lt $n); $i++) {
        $x0 = __pytra_int ($i * $bar_w)
        $x1 = __pytra_int (($i + 1) * $bar_w)
        if (($x1 -le $x0)) {
            $x1 = ($x0 + 1)
        }
        $bh = __pytra_int (($values[$i] / $__hoisted_cast_1) * $__hoisted_cast_2)
        $y = ($h - $bh)
        for ($y = 0; ($y -lt $h); $y++) {
            for ($x = 0; ($x -lt $x1); $x++) {
                $frame[(($y * $w) + $x)] = 255
            }
        }
    }
    return (__pytra_bytes $frame)
}

function run_12_sort_visualizer {
    param()
    $w = 320
    $h = 180
    $n = 124
    $out_path = "sample/out/12_sort_visualizer.gif"
    $start = (perf_counter)
    $values = @()
    for ($i = 0; ($i -lt $n); $i++) {
        $values += @(((($i * 37) + 19) % $n))
    }
    $frames = @((render $values $w $h))
    $frame_stride = 16
    $op = 0
    for ($i = 0; ($i -lt $n); $i++) {
        $swapped = $false
        for ($j = 0; ($j -lt (($n - $i) - 1)); $j++) {
            if (($values[$j] -gt $values[($j + 1)])) {
                $__tuple_tmp = @($values[($j + 1)], $values[$j])
                $values[$j] = $__tuple_tmp[0]
                $values[($j + 1)] = $__tuple_tmp[1]
                $swapped = $true
            }
            if ((($op % $frame_stride) -eq 0)) {
                $frames += @((render $values $w $h))
            }
            $op += 1
        }
        if ((-not $swapped)) {
            break
        }
    }
    (save_gif $out_path $w $h $frames (grayscale_palette))
    $elapsed = ((perf_counter) - $start)
    __pytra_print "output:" $out_path
    __pytra_print "frames:" __pytra_len $frames
    __pytra_print "elapsed_sec:" $elapsed
}

(run_12_sort_visualizer)
