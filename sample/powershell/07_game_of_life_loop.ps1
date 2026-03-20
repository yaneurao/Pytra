#Requires -Version 5.1
#
# WARNING: Experimental PowerShell backend
# This output intentionally emits a best-effort PowerShell preview.
# Do not treat this as production-ready PowerShell code.

$pytra_runtime = Join-Path $PSScriptRoot "py_runtime.ps1"
if (Test-Path $pytra_runtime) { . $pytra_runtime }

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$pytra_program = @'
# Preview of generated payload.
#   import { perf_counter } from "./runtime/js/generated/std/time.js";
#   import { grayscale_palette } from "./runtime/js/generated/utils/gif.js";
#   import { save_gif } from "./runtime/js/generated/utils/gif.js";
#   
#   // 07: Sample that outputs Game of Life evolution as a GIF.
#   
#   function next_state(grid, w, h) {
#       let nxt = [];
#       for (let y = 0; y < h; y += 1) {
#           let row = [];
#           for (let x = 0; x < w; x += 1) {
#               let cnt = 0;
#               for (let dy = -1; dy < 2; dy += 1) {
#                   for (let dx = -1; dx < 2; dx += 1) {
#                       if (dx !== 0 || dy !== 0) {
#                           let nx = (x + dx + w) % w;
#                           let ny = (y + dy + h) % h;
#                           cnt += grid[(((ny) < 0) ? ((grid).length + (ny)) : (ny))][(((nx) < 0) ? ((grid[(((ny) < 0) ? ((grid).length + (ny)) : (ny))]).length + (nx)) : (nx))];
#                       }
#                   }
#               }
#               let alive = grid[(((y) < 0) ? ((grid).length + (y)) : (y))][(((x) < 0) ? ((grid[(((y) < 0) ? ((grid).length + (y)) : (y))]).length + (x)) : (x))];
#               if (alive === 1 && cnt === 2 || cnt === 3) {
#                   row.push(1);
#               } else {
#                   if (alive === 0 && cnt === 3) {
#                       row.push(1);
#                   } else {
#                       row.push(0);
#                   }
#               }
#           }
#           nxt.push(row);
#       }
#       return nxt;
#   }
#   
#   function render(grid, w, h, cell) {
#       let width = w * cell;
#       let height = h * cell;
#       let frame = (typeof (width * height) === "number" ? new Array(Math.max(0, Math.trunc(Number((width * height))))).fill(0) : (Array.isArray((width * height)) ? (width * height).slice() : Array.from((width * height))));
#       for (let y = 0; y < h; y += 1) {
#           for (let x = 0; x < w; x += 1) {
#               let v = (grid[(((y) < 0) ? ((grid).length + (y)) : (y))][(((x) < 0) ? ((grid[(((y) < 0) ? ((grid).length + (y)) : (y))]).length + (x)) : (x))] ? 255 : 0);
#               for (let yy = 0; yy < cell; yy += 1) {
#                   let base = (y * cell + yy) * width + x * cell;
#                   for (let xx = 0; xx < cell; xx += 1) {
#                       frame[(((base + xx) < 0) ? ((frame).length + (base + xx)) : (base + xx))] = v;
#                   }
#               }
#           }
#       }
#       return (Array.isArray((frame)) ? (frame).slice() : Array.from((frame)));
#   }
#   
#   function run_07_game_of_life_loop() {
#       let w = 144;
#       let h = 108;
#       let cell = 4;
#       let steps = 105;
#       let out_path = "sample/out/07_game_of_life_loop.gif";
#       
#       let start = perf_counter();
#       let grid = (() => { let __out = []; for (const _ of (() => { const __out = []; const __start = 0; const __stop = h; const __step = 1; if (__step === 0) { return __out; } if (__step > 0) { for (let __i = __start; __i < __stop; __i += __step) { __out.push(__i); } } else { for (let __i = __start; __i > __stop; __i += __step) { __out.push(__i); } } return __out; })()) { __out.push((() => { const __base = ([0]); const __n = Math.max(0, Math.trunc(Number(w))); let __out = []; for (let __i = 0; __i < __n; __i += 1) { for (const __v of __base) { __out.push(__v); } } return __out; })()); } return __out; })();
#       
#       // Lay down sparse noise so the whole field is less likely to stabilize too early.
#       // Avoid large integer literals so all transpilers handle the expression consistently.
#       for (let y = 0; y < h; y += 1) {
#           for (let x = 0; x < w; x += 1) {
#               let noise = (x * 37 + y * 73 + x * y % 19 + (x + y) % 11) % 97;
#               if (noise < 3) {
#                   grid[(((y) < 0) ? ((grid).length + (y)) : (y))][(((x) < 0) ? ((grid[(((y) < 0) ? ((grid).length + (y)) : (y))]).length + (x)) : (x))] = 1;
#               }
#           }
#       }
#       // Place multiple well-known long-lived patterns.
#       let glider = [[0, 1, 0], [0, 0, 1], [1, 1, 1]];
#       let r_pentomino = [[0, 1, 1], [1, 1, 0], [0, 1, 0]];
#       let lwss = [[0, 1, 1, 1, 1], [1, 0, 0, 0, 1], [0, 0, 0, 0, 1], [1, 0, 0, 1, 0]];
#       
#       for (let gy = 8; gy < h - 8; gy += 18) {
#           for (let gx = 8; gx < w - 8; gx += 22) {
#               let kind = (gx * 7 + gy * 11) % 3;
#               if (kind === 0) {
#                   let ph = (glider).length;
#                   for (let py = 0; py < ph; py += 1) {
#                       let pw = (glider[(((py) < 0) ? ((glider).length + (py)) : (py))]).length;
#                       for (let px = 0; px < pw; px += 1) {
#                           if (glider[(((py) < 0) ? ((glider).length + (py)) : (py))][(((px) < 0) ? ((glider[(((py) < 0) ? ((glider).length + (py)) : (py))]).length + (px)) : (px))] === 1) {
#                               grid[((((gy + py) % h) < 0) ? ((grid).length + ((gy + py) % h)) : ((gy + py) % h))][((((gx + px) % w) < 0) ? ((grid[((((gy + py) % h) < 0) ? ((grid).length + ((gy + py) % h)) : ((gy + py) % h))]).length + ((gx + px) % w)) : ((gx + px) % w))] = 1;
#                           }
#                       }
#                   }
#               } else {
#                   if (kind === 1) {
#                       let ph = (r_pentomino).length;
#                       for (let py = 0; py < ph; py += 1) {
#                           let pw = (r_pentomino[(((py) < 0) ? ((r_pentomino).length + (py)) : (py))]).length;
#                           for (let px = 0; px < pw; px += 1) {
#                               if (r_pentomino[(((py) < 0) ? ((r_pentomino).length + (py)) : (py))][(((px) < 0) ? ((r_pentomino[(((py) < 0) ? ((r_pentomino).length + (py)) : (py))]).length + (px)) : (px))] === 1) {
#                                   grid[((((gy + py) % h) < 0) ? ((grid).length + ((gy + py) % h)) : ((gy + py) % h))][((((gx + px) % w) < 0) ? ((grid[((((gy + py) % h) < 0) ? ((grid).length + ((gy + py) % h)) : ((gy + py) % h))]).length + ((gx + px) % w)) : ((gx + px) % w))] = 1;
#                               }
#                           }
#                       }
#                   } else {
#                       let ph = (lwss).length;
#                       for (let py = 0; py < ph; py += 1) {
#                           let pw = (lwss[(((py) < 0) ? ((lwss).length + (py)) : (py))]).length;
#                           for (let px = 0; px < pw; px += 1) {
#                               if (lwss[(((py) < 0) ? ((lwss).length + (py)) : (py))][(((px) < 0) ? ((lwss[(((py) < 0) ? ((lwss).length + (py)) : (py))]).length + (px)) : (px))] === 1) {
#                                   grid[((((gy + py) % h) < 0) ? ((grid).length + ((gy + py) % h)) : ((gy + py) % h))][((((gx + px) % w) < 0) ? ((grid[((((gy + py) % h) < 0) ? ((grid).length + ((gy + py) % h)) : ((gy + py) % h))]).length + ((gx + px) % w)) : ((gx + px) % w))] = 1;
#                               }
#                           }
#                       }
#                   }
#               }
#           }
#       }
#       let frames = [];
#       for (let _ = 0; _ < steps; _ += 1) {
#           frames.push(render(grid, w, h, cell));
#           grid = next_state(grid, w, h);
#       }
#       save_gif(out_path, w * cell, h * cell, frames, grayscale_palette(), 4, 0);
#       let elapsed = perf_counter() - start;
#       console.log("output:", out_path);
#       console.log("frames:", steps);
#       console.log("elapsed_sec:", elapsed);
#   }
#   
#   run_07_game_of_life_loop();
@'

# PowerShell preview generated from JavaScript pseudo conversion.
    import { perf_counter } from "./runtime/js/generated/std/time.js"
    import { grayscale_palette } from "./runtime/js/generated/utils/gif.js"
    import { save_gif } from "./runtime/js/generated/utils/gif.js"
    
    # 07: Sample that outputs Game of Life evolution as a GIF.
    
    function next_state {
        param($grid, $w, $h)
        $nxt = @()
        for ($y = 0; $y  -$lt  $h; $y += 1) {
            $row = @()
            for ($x = 0; $x  -$lt  $w; $x += 1) {
                $cnt = 0
                for ($dy = -1; $dy  -$lt  2; $dy += 1) {
                    for ($dx = -1; $dx  -$lt  2; $dx += 1) {
                        if ($dx -$ne 0 -$or $dy -$ne 0) {
                            $nx = ($x + $dx + w) % $w
                            $ny = ($y + $dy + h) % $h
                            cnt += grid[(((ny)  -lt  0) ? ((grid).Length + (ny)) : (ny))][(((nx)  -lt  0) ? ((grid[(((ny)  -lt  0) ? ((grid).Length + (ny)) : (ny))]).Length + (nx)) : (nx))]
                        }
                    }
                }
                $alive = $grid[(((y)  -$lt  0) ? ((grid).Length + (y)) : (y))][(((x)  -$lt  0) ? (($grid[(((y)  -$lt  0) ? ((grid).Length + (y)) : (y))]).Length + (x)) : (x))]
                if ($alive -$eq 1 -$and $cnt -$eq 2 -$or $cnt -$eq 3) {
                    row.push(1)
                } else {
                    if ($alive -$eq 0 -$and $cnt -$eq 3) {
                        row.push(1)
                    } else {
                        row.push(0)
                    }
                }
            }
            nxt.push(row)
        }
        return $nxt
    }
    
    function render {
        param($grid, $w, $h, $cell)
        $width = $w * $cell
        $height = $h * $cell
        $frame = ($typeof $width * $height -$eq "number" ? $Array [Math]::Max(0, Math.trunc(Number(($width * height)))).fill(0) : ($Array.isArray(($width * height)) ? ($width * height).slice() : $Array.from(($width * height))))
        for ($y = 0; $y  -$lt  $h; $y += 1) {
            for ($x = 0; $x  -$lt  $w; $x += 1) {
                $v = ($grid[(((y)  -$lt  0) ? ((grid).Length + (y)) : (y))][(((x)  -$lt  0) ? (($grid[(((y)  -$lt  0) ? ((grid).Length + (y)) : (y))]).Length + (x)) : (x))] ? 255 : 0)
                for ($yy = 0; $yy  -$lt  $cell; $yy += 1) {
                    $base = ($y * $cell + yy) * $width + $x * $cell
                    for ($xx = 0; $xx  -$lt  $cell; $xx += 1) {
                        frame[(((base + xx)  -lt  0) ? ((frame).Length + (base + xx)) : (base + xx))] = v
                    }
                }
            }
        }
        return ($Array.isArray((frame)) ? (frame).slice() : $Array.from((frame)))
    }
    
    function run_07_game_of_life_loop {
        param()
        $w = 144
        $h = 108
        $cell = 4
        $steps = 105
        $out_path = "sample/out/07_game_of_life_loop.gif"
    
        $start = $perf_counter
        $grid = (() = -$gt  { $let $__out = []; for ($const $_ of (() = -$gt  { $const $__out = []; $const $__start = 0; $const $__stop = $h; $const $__step = 1; if ($__step -$eq 0) { return $__out; } if ($__step  -$gt  0) { for ($let $__i = $__start; $__i  -$lt  $__stop; $__i += __step) { $__out.push(__i); } } else { for ($let $__i = $__start; $__i  -$gt  $__stop; $__i += __step) { $__out.push(__i); } } return $__out; })()) { $__out.push((() = -$gt  { $const $__base = ([0]); $const $__n = [Math]::$Max 0 Math.trunc(Number(w)); $let $__out = []; for ($let $__i = 0; $__i  -$lt  $__n; $__i += 1) { for ($const $__v $of __base) { $__out.push(__v); } } return $__out; })()); } return $__out; })()
    
        // Lay down sparse noise so the whole field is less likely to stabilize too early.
        // Avoid large integer literals so all transpilers handle the expression consistently.
        for ($y = 0; $y  -$lt  $h; $y += 1) {
            for ($x = 0; $x  -$lt  $w; $x += 1) {
                $noise = ($x * 37 + $y * 73 + $x * $y % 19 + ($x + y) % 11) % 97
                if ($noise  -$lt  3) {
                    grid[(((y)  -lt  0) ? ((grid).Length + (y)) : (y))][(((x)  -lt  0) ? ((grid[(((y)  -lt  0) ? ((grid).Length + (y)) : (y))]).Length + (x)) : (x))] = 1
                }
            }
        }
        // Place multiple well-known long-lived patterns.
        $glider = @(@(0, 1, 0), @(0, 0, 1), @(1, 1, 1))
        $r_pentomino = @(@(0, 1, 1), @(1, 1, 0), @(0, 1, 0))
        $lwss = @(@(0, 1, 1, 1, 1), @(1, 0, 0, 0, 1), @(0, 0, 0, 0, 1), @(1, 0, 0, 1, 0))
    
        for ($gy = 8; $gy  -$lt  $h - 8; $gy += 18) {
            for ($gx = 8; $gx  -$lt  $w - 8; $gx += 22) {
                $kind = ($gx * 7 + $gy * 11) % 3
                if ($kind -$eq 0) {
                    $ph = (glider).Length
                    for ($py = 0; $py  -$lt  $ph; $py += 1) {
                        $pw = ($glider[(((py)  -$lt  0) ? ((glider).Length + (py)) : (py))]).Length
                        for ($px = 0; $px  -$lt  $pw; $px += 1) {
                            if ($glider[(((py)  -$lt  0) ? ((glider).Length + (py)) : (py))][(((px)  -$lt  0) ? (($glider[(((py)  -$lt  0) ? ((glider).Length + (py)) : (py))]).Length + (px)) : (px))] -$eq 1) {
                                grid[((((gy + py) % h)  -lt  0) ? ((grid).Length + ((gy + py) % h)) : ((gy + py) % h))][((((gx + px) % w)  -lt  0) ? ((grid[((((gy + py) % h)  -lt  0) ? ((grid).Length + ((gy + py) % h)) : ((gy + py) % h))]).Length + ((gx + px) % w)) : ((gx + px) % w))] = 1
                            }
                        }
                    }
                } else {
                    if ($kind -$eq 1) {
                        $ph = (r_pentomino).Length
                        for ($py = 0; $py  -$lt  $ph; $py += 1) {
                            $pw = ($r_pentomino[(((py)  -$lt  0) ? ((r_pentomino).Length + (py)) : (py))]).Length
                            for ($px = 0; $px  -$lt  $pw; $px += 1) {
                                if ($r_pentomino[(((py)  -$lt  0) ? ((r_pentomino).Length + (py)) : (py))][(((px)  -$lt  0) ? (($r_pentomino[(((py)  -$lt  0) ? ((r_pentomino).Length + (py)) : (py))]).Length + (px)) : (px))] -$eq 1) {
                                    grid[((((gy + py) % h)  -lt  0) ? ((grid).Length + ((gy + py) % h)) : ((gy + py) % h))][((((gx + px) % w)  -lt  0) ? ((grid[((((gy + py) % h)  -lt  0) ? ((grid).Length + ((gy + py) % h)) : ((gy + py) % h))]).Length + ((gx + px) % w)) : ((gx + px) % w))] = 1
                                }
                            }
                        }
                    } else {
                        $ph = (lwss).Length
                        for ($py = 0; $py  -$lt  $ph; $py += 1) {
                            $pw = ($lwss[(((py)  -$lt  0) ? ((lwss).Length + (py)) : (py))]).Length
                            for ($px = 0; $px  -$lt  $pw; $px += 1) {
                                if ($lwss[(((py)  -$lt  0) ? ((lwss).Length + (py)) : (py))][(((px)  -$lt  0) ? (($lwss[(((py)  -$lt  0) ? ((lwss).Length + (py)) : (py))]).Length + (px)) : (px))] -$eq 1) {
                                    grid[((((gy + py) % h)  -lt  0) ? ((grid).Length + ((gy + py) % h)) : ((gy + py) % h))][((((gx + px) % w)  -lt  0) ? ((grid[((((gy + py) % h)  -lt  0) ? ((grid).Length + ((gy + py) % h)) : ((gy + py) % h))]).Length + ((gx + px) % w)) : ((gx + px) % w))] = 1
                                }
                            }
                        }
                    }
                }
            }
        }
        $frames = @()
        for ($_ = 0; $_  -$lt  $steps; $_ += 1) {
            frames.push(render grid w h cell)
            grid = next_state grid w h
        }
        save_gif out_path w * cell h * cell frames grayscale_palette(, 4, 0)
        $elapsed = $perf_counter - $start
        __pytra_print "output:" out_path
        __pytra_print "frames:" steps
        __pytra_print "elapsed_sec:" elapsed
    }
    
    run_07_game_of_life_loop

if (Get-Command -Name main -ErrorAction SilentlyContinue) {
    main
}
