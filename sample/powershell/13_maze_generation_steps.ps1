#Requires -Version 5.1

$pytra_runtime = Join-Path $PSScriptRoot "py_runtime.ps1"
if (Test-Path $pytra_runtime) { . $pytra_runtime }

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# import: pytra.std.time

# import: pytra.utils.gif

function capture {
    param($grid, $w, $h, $scale)
    $width = ($w * $scale)
    $height = ($h * $scale)
    $frame = (__pytra_bytearray ($width * $height))
    for ($y = 0; ($y -lt $h); $y++) {
        for ($x = 0; ($x -lt $w); $x++) {
            $v = $(if (($grid[$y][$x] -eq 0)) { 255 } else { 40 })
            for ($yy = 0; ($yy -lt $scale); $yy++) {
                $base = (((($y * $scale) + $yy) * $width) + ($x * $scale))
                for ($xx = 0; ($xx -lt $scale); $xx++) {
                    $frame[($base + $xx)] = $v
                }
            }
        }
    }
    return (__pytra_bytes $frame)
}

function run_13_maze_generation_steps {
    param()
    $cell_w = 89
    $cell_h = 67
    $scale = 5
    $capture_every = 20
    $out_path = "sample/out/13_maze_generation_steps.gif"
    $start = (perf_counter)
    $grid = $null
    $stack = @(@(1, 1))
    $grid[1][1] = 0
    $dirs = @(@(2, 0), @((-2), 0), @(0, 2), @(0, (-2)))
    $frames = @()
    $step = 0
    while ($stack) {
        $__tuple_tmp = $stack[(-1)]
        $x = $__tuple_tmp[0]
        $y = $__tuple_tmp[1]
        $candidates = @()
        for ($k = 0; ($k -lt 4); $k++) {
            $__tuple_tmp = $dirs[$k]
            $dx = $__tuple_tmp[0]
            $dy = $__tuple_tmp[1]
            $nx = ($x + $dx)
            $ny = ($y + $dy)
            if ((($nx -ge 1) -and ($nx -lt ($cell_w - 1)) -and ($ny -ge 1) -and ($ny -lt ($cell_h - 1)) -and ($grid[$ny][$nx] -eq 1))) {
                if (($dx -eq 2)) {
                    $candidates += @(@($nx, $ny, ($x + 1), $y))
                } elseif (($dx -eq (-2))) {
                    $candidates += @(@($nx, $ny, ($x - 1), $y))
                } elseif (($dy -eq 2)) {
                    $candidates += @(@($nx, $ny, $x, ($y + 1)))
                } else {
                    $candidates += @(@($nx, $ny, $x, ($y - 1)))
                }
            }
        }
        if ((__pytra_len $candidates -eq 0)) {
            $stack[-1]; $stack = $stack[0..($stack.Length - 2)]
        } else {
            $sel = $candidates[(((($x * 17) + ($y * 29)) + (__pytra_len $stack * 13)) % __pytra_len $candidates)]
            $__tuple_tmp = $sel
            $nx = $__tuple_tmp[0]
            $ny = $__tuple_tmp[1]
            $wx = $__tuple_tmp[2]
            $wy = $__tuple_tmp[3]
            $grid[$wy][$wx] = 0
            $grid[$ny][$nx] = 0
            $stack += @(@($nx, $ny))
        }
        if ((($step % $capture_every) -eq 0)) {
            $frames += @((capture $grid $cell_w $cell_h $scale))
        }
        $step += 1
    }
    $frames += @((capture $grid $cell_w $cell_h $scale))
    (save_gif $out_path ($cell_w * $scale) ($cell_h * $scale) $frames (grayscale_palette))
    $elapsed = ((perf_counter) - $start)
    __pytra_print "output:" $out_path
    __pytra_print "frames:" __pytra_len $frames
    __pytra_print "elapsed_sec:" $elapsed
}

(run_13_maze_generation_steps)
