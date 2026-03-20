#Requires -Version 5.1

$pytra_runtime = Join-Path $PSScriptRoot "py_runtime.ps1"
if (Test-Path $pytra_runtime) { . $pytra_runtime }

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# import: pytra.std.time

# import: pytra.utils.gif

function fire_palette {
    param()
    $p = (__pytra_bytearray 0)
    for ($i = 0; ($i -lt 256); $i++) {
        $r = 0
        $g = 0
        $b = 0
        if (($i -lt 85)) {
            $r = ($i * 3)
            $g = 0
            $b = 0
        } elseif (($i -lt 170)) {
            $r = 255
            $g = (($i - 85) * 3)
            $b = 0
        } else {
            $r = 255
            $g = 255
            $b = (($i - 170) * 3)
        }
        $p += @($r)
        $p += @($g)
        $p += @($b)
    }
    return (__pytra_bytes $p)
}

function run_09_fire_simulation {
    param()
    $w = 380
    $h = 260
    $steps = 420
    $out_path = "sample/out/09_fire_simulation.gif"
    $start = (perf_counter)
    $heat = $null
    $frames = @()
    for ($t = 0; ($t -lt $steps); $t++) {
        for ($x = 0; ($x -lt $w); $x++) {
            $val = (170 + ((($x * 13) + ($t * 17)) % 86))
            $heat[($h - 1)][$x] = $val
        }
        for ($y = 0; ($y -lt $h); $y++) {
            for ($x = 0; ($x -lt $w); $x++) {
                $a = $heat[$y][$x]
                $b = $heat[$y][((($x - 1) + $w) % $w)]
                $c = $heat[$y][(($x + 1) % $w)]
                $d = $heat[(($y + 1) % $h)][$x]
                $v = [Math]::Floor(((($a + $b) + $c) + $d) / 4)
                $cool = (1 + ((($x + $y) + $t) % 3))
                $nv = ($v - $cool)
                $heat[($y - 1)][$x] = $(if (($nv -gt 0)) { $nv } else { 0 })
            }
        }
        $frame = (__pytra_bytearray ($w * $h))
        for ($yy = 0; ($yy -lt $h); $yy++) {
            $row_base = ($yy * $w)
            for ($xx = 0; ($xx -lt $w); $xx++) {
                $frame[($row_base + $xx)] = $heat[$yy][$xx]
            }
        }
        $frames += @((__pytra_bytes $frame))
    }
    (save_gif $out_path $w $h $frames (fire_palette))
    $elapsed = ((perf_counter) - $start)
    __pytra_print "output:" $out_path
    __pytra_print "frames:" $steps
    __pytra_print "elapsed_sec:" $elapsed
}

(run_09_fire_simulation)
