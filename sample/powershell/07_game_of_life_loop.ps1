#Requires -Version 5.1

$pytra_runtime = Join-Path $PSScriptRoot "py_runtime.ps1"
if (Test-Path $pytra_runtime) { . $pytra_runtime }

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# import: pytra.std.time

# import: pytra.utils.gif

function next_state {
    param($grid, $w, $h)
    $nxt = @()
    for ($y = 0; ($y -lt $h); $y++) {
        $row = @()
        for ($x = 0; ($x -lt $w); $x++) {
            $cnt = 0
            for ($dy = 0; ($dy -lt 2); $dy++) {
                for ($dx = 0; ($dx -lt 2); $dx++) {
                    if ((($dx -ne 0) -or ($dy -ne 0))) {
                        $nx = ((($x + $dx) + $w) % $w)
                        $ny = ((($y + $dy) + $h) % $h)
                        $cnt += $grid[$ny][$nx]
                    }
                }
            }
            $alive = $grid[$y][$x]
            if ((($alive -eq 1) -and (($cnt -eq 2) -or ($cnt -eq 3)))) {
                $row += @(1)
            } elseif ((($alive -eq 0) -and ($cnt -eq 3))) {
                $row += @(1)
            } else {
                $row += @(0)
            }
        }
        $nxt += @($row)
    }
    return $nxt
}

function render {
    param($grid, $w, $h, $cell)
    $width = ($w * $cell)
    $height = ($h * $cell)
    $frame = (__pytra_bytearray ($width * $height))
    for ($y = 0; ($y -lt $h); $y++) {
        for ($x = 0; ($x -lt $w); $x++) {
            $v = $(if ($grid[$y][$x]) { 255 } else { 0 })
            for ($yy = 0; ($yy -lt $cell); $yy++) {
                $base = (((($y * $cell) + $yy) * $width) + ($x * $cell))
                for ($xx = 0; ($xx -lt $cell); $xx++) {
                    $frame[($base + $xx)] = $v
                }
            }
        }
    }
    return (__pytra_bytes $frame)
}

function run_07_game_of_life_loop {
    param()
    $w = 144
    $h = 108
    $cell = 4
    $steps = 105
    $out_path = "sample/out/07_game_of_life_loop.gif"
    $start = (perf_counter)
    $grid = $null
    for ($y = 0; ($y -lt $h); $y++) {
        for ($x = 0; ($x -lt $w); $x++) {
            $noise = ((((($x * 37) + ($y * 73)) + (($x * $y) % 19)) + (($x + $y) % 11)) % 97)
            if (($noise -lt 3)) {
                $grid[$y][$x] = 1
            }
        }
    }
    $glider = @(@(0, 1, 0), @(0, 0, 1), @(1, 1, 1))
    $r_pentomino = @(@(0, 1, 1), @(1, 1, 0), @(0, 1, 0))
    $lwss = @(@(0, 1, 1, 1, 1), @(1, 0, 0, 0, 1), @(0, 0, 0, 0, 1), @(1, 0, 0, 1, 0))
    for ($gy = 0; ($gy -lt ($h - 8)); $gy++) {
        for ($gx = 0; ($gx -lt ($w - 8)); $gx++) {
            $kind = ((($gx * 7) + ($gy * 11)) % 3)
            if (($kind -eq 0)) {
                $ph = __pytra_len $glider
                for ($py = 0; ($py -lt $ph); $py++) {
                    $pw = __pytra_len $glider[$py]
                    for ($px = 0; ($px -lt $pw); $px++) {
                        if (($glider[$py][$px] -eq 1)) {
                            $grid[(($gy + $py) % $h)][(($gx + $px) % $w)] = 1
                        }
                    }
                }
            } elseif (($kind -eq 1)) {
                $ph = __pytra_len $r_pentomino
                for ($py = 0; ($py -lt $ph); $py++) {
                    $pw = __pytra_len $r_pentomino[$py]
                    for ($px = 0; ($px -lt $pw); $px++) {
                        if (($r_pentomino[$py][$px] -eq 1)) {
                            $grid[(($gy + $py) % $h)][(($gx + $px) % $w)] = 1
                        }
                    }
                }
            } else {
                $ph = __pytra_len $lwss
                for ($py = 0; ($py -lt $ph); $py++) {
                    $pw = __pytra_len $lwss[$py]
                    for ($px = 0; ($px -lt $pw); $px++) {
                        if (($lwss[$py][$px] -eq 1)) {
                            $grid[(($gy + $py) % $h)][(($gx + $px) % $w)] = 1
                        }
                    }
                }
            }
        }
    }
    $frames = @()
    for ($_ = 0; ($_ -lt $steps); $_++) {
        $frames += @((render $grid $w $h $cell))
        $grid = (next_state $grid $w $h)
    }
    (save_gif $out_path ($w * $cell) ($h * $cell) $frames (grayscale_palette))
    $elapsed = ((perf_counter) - $start)
    __pytra_print "output:" $out_path
    __pytra_print "frames:" $steps
    __pytra_print "elapsed_sec:" $elapsed
}

(run_07_game_of_life_loop)
