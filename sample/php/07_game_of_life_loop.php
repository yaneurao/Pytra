<?php
declare(strict_types=1);

require_once __DIR__ . '/pytra/py_runtime.php';

// 07: Sample that outputs Game of Life evolution as a GIF.
function next_state($grid, $w, $h) {
    $nxt = [];
    for ($y = 0; $y < $h; $y += 1) {
        $row = [];
        for ($x = 0; $x < $w; $x += 1) {
            $cnt = 0;
            for ($dy = (-1); $dy < 2; $dy += 1) {
                for ($dx = (-1); $dx < 2; $dx += 1) {
                    if ((($dx != 0) || ($dy != 0))) {
                        $nx = ((($x + $dx) + $w) % $w);
                        $ny = ((($y + $dy) + $h) % $h);
                        $cnt += $grid[$ny][$nx];
                    }
                }
            }
            $alive = $grid[$y][$x];
            if ((($alive == 1) && (($cnt == 2) || ($cnt == 3)))) {
                $row[] = 1;
            } else {
                if ((($alive == 0) && ($cnt == 3))) {
                    $row[] = 1;
                } else {
                    $row[] = 0;
                }
            }
        }
        $nxt[] = $row;
    }
    return $nxt;
}

function render($grid, $w, $h, $cell) {
    $width = ($w * $cell);
    $height = ($h * $cell);
    $frame = bytearray(($width * $height));
    for ($y = 0; $y < $h; $y += 1) {
        for ($x = 0; $x < $w; $x += 1) {
            $v = ($grid[$y][$x] ? 255 : 0);
            for ($yy = 0; $yy < $cell; $yy += 1) {
                $base = (((($y * $cell) + $yy) * $width) + ($x * $cell));
                for ($xx = 0; $xx < $cell; $xx += 1) {
                    $frame[($base + $xx)] = $v;
                }
            }
        }
    }
    return bytes($frame);
}

function run_07_game_of_life_loop() {
    $w = 144;
    $h = 108;
    $cell = 4;
    $steps = 105;
    $out_path = "sample/out/07_game_of_life_loop.gif";
    $start = __pytra_perf_counter();
    $grid = null;
    for ($y = 0; $y < $h; $y += 1) {
        for ($x = 0; $x < $w; $x += 1) {
            $noise = ((((($x * 37) + ($y * 73)) + (($x * $y) % 19)) + (($x + $y) % 11)) % 97);
            if (($noise < 3)) {
                $grid[$y][$x] = 1;
            }
        }
    }
    $glider = [[0, 1, 0], [0, 0, 1], [1, 1, 1]];
    $r_pentomino = [[0, 1, 1], [1, 1, 0], [0, 1, 0]];
    $lwss = [[0, 1, 1, 1, 1], [1, 0, 0, 0, 1], [0, 0, 0, 0, 1], [1, 0, 0, 1, 0]];
    for ($gy = 8; $gy < ($h - 8); $gy += 18) {
        for ($gx = 8; $gx < ($w - 8); $gx += 22) {
            $kind = ((($gx * 7) + ($gy * 11)) % 3);
            if (($kind == 0)) {
                $ph = __pytra_len($glider);
                for ($py = 0; $py < $ph; $py += 1) {
                    $pw = __pytra_len($glider[$py]);
                    for ($px = 0; $px < $pw; $px += 1) {
                        if (($glider[$py][$px] == 1)) {
                            $grid[(($gy + $py) % $h)][(($gx + $px) % $w)] = 1;
                        }
                    }
                }
            } else {
                if (($kind == 1)) {
                    $ph = __pytra_len($r_pentomino);
                    for ($py = 0; $py < $ph; $py += 1) {
                        $pw = __pytra_len($r_pentomino[$py]);
                        for ($px = 0; $px < $pw; $px += 1) {
                            if (($r_pentomino[$py][$px] == 1)) {
                                $grid[(($gy + $py) % $h)][(($gx + $px) % $w)] = 1;
                            }
                        }
                    }
                } else {
                    $ph = __pytra_len($lwss);
                    for ($py = 0; $py < $ph; $py += 1) {
                        $pw = __pytra_len($lwss[$py]);
                        for ($px = 0; $px < $pw; $px += 1) {
                            if (($lwss[$py][$px] == 1)) {
                                $grid[(($gy + $py) % $h)][(($gx + $px) % $w)] = 1;
                            }
                        }
                    }
                }
            }
        }
    }
    $frames = [];
    for ($_ = 0; $_ < $steps; $_ += 1) {
        $frames[] = render($grid, $w, $h, $cell);
        $grid = next_state($grid, $w, $h);
    }
    __pytra_noop($out_path, ($w * $cell), ($h * $cell), $frames, grayscale_palette());
    $elapsed = (__pytra_perf_counter() - $start);
    __pytra_print("output:", $out_path);
    __pytra_print("frames:", $steps);
    __pytra_print("elapsed_sec:", $elapsed);
}

function __pytra_main(): void {
    run_07_game_of_life_loop();
}

__pytra_main();
