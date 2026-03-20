#Requires -Version 5.1

$pytra_runtime = Join-Path $PSScriptRoot "py_runtime.ps1"
if (Test-Path $pytra_runtime) { . $pytra_runtime }

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# import: pytra.std.time

# import: pytra.utils.gif

function capture {
    param($grid, $w, $h)
    $frame = (__pytra_bytearray ($w * $h))
    for ($y = 0; ($y -lt $h); $y++) {
        $row_base = ($y * $w)
        for ($x = 0; ($x -lt $w); $x++) {
            $frame[($row_base + $x)] = $(if ($grid[$y][$x]) { 255 } else { 0 })
        }
    }
    return (__pytra_bytes $frame)
}

function run_08_langtons_ant {
    param()
    $w = 420
    $h = 420
    $out_path = "sample/out/08_langtons_ant.gif"
    $start = (perf_counter)
    $grid = $null
    $x = [Math]::Floor($w / 2)
    $y = [Math]::Floor($h / 2)
    $d = 0
    $steps_total = 600000
    $capture_every = 3000
    $frames = @()
    for ($i = 0; ($i -lt $steps_total); $i++) {
        if (($grid[$y][$x] -eq 0)) {
            $d = (($d + 1) % 4)
            $grid[$y][$x] = 1
        } else {
            $d = (($d + 3) % 4)
            $grid[$y][$x] = 0
        }
        if (($d -eq 0)) {
            $y = ((($y - 1) + $h) % $h)
        } elseif (($d -eq 1)) {
            $x = (($x + 1) % $w)
        } elseif (($d -eq 2)) {
            $y = (($y + 1) % $h)
        } else {
            $x = ((($x - 1) + $w) % $w)
        }
        if ((($i % $capture_every) -eq 0)) {
            $frames += @((capture $grid $w $h))
        }
    }
    (save_gif $out_path $w $h $frames (grayscale_palette))
    $elapsed = ((perf_counter) - $start)
    __pytra_print "output:" $out_path
    __pytra_print "frames:" __pytra_len $frames
    __pytra_print "elapsed_sec:" $elapsed
}

(run_08_langtons_ant)
