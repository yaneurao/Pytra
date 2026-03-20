#Requires -Version 5.1

$pytra_runtime = Join-Path $PSScriptRoot "py_runtime.ps1"
if (Test-Path $pytra_runtime) { . $pytra_runtime }

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# import: pytra.std

# import: pytra.std.time

# import: pytra.utils.gif

function run_15_wave_interference_loop {
    param()
    $w = 320
    $h = 240
    $frames_n = 96
    $out_path = "sample/out/15_wave_interference_loop.gif"
    $start = (perf_counter)
    $frames = @()
    for ($t = 0; ($t -lt $frames_n); $t++) {
        $frame = (__pytra_bytearray ($w * $h))
        $phase = ($t * 0.12)
        for ($y = 0; ($y -lt $h); $y++) {
            $row_base = ($y * $w)
            for ($x = 0; ($x -lt $w); $x++) {
                $dx = ($x - 160)
                $dy = ($y - 120)
                $v = ((([Math]::Sin((($x + ($t * 1.5)) * 0.045)) + [Math]::Sin((($y - ($t * 1.2)) * 0.04))) + [Math]::Sin(((($x + $y) * 0.02) + $phase))) + [Math]::Sin((([Math]::Sqrt((($dx * $dx) + ($dy * $dy))) * 0.08) - ($phase * 1.3))))
                $c = __pytra_int (($v + 4.0) * (255.0 / 8.0))
                if (($c -lt 0)) {
                    $c = 0
                }
                if (($c -gt 255)) {
                    $c = 255
                }
                $frame[($row_base + $x)] = $c
            }
        }
        $frames += @((__pytra_bytes $frame))
    }
    (save_gif $out_path $w $h $frames (grayscale_palette))
    $elapsed = ((perf_counter) - $start)
    __pytra_print "output:" $out_path
    __pytra_print "frames:" $frames_n
    __pytra_print "elapsed_sec:" $elapsed
}

(run_15_wave_interference_loop)
