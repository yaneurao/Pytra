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
#   // 13: Sample that outputs DFS maze-generation progress as a GIF.
#   
#   function capture(grid, w, h, scale) {
#       let width = w * scale;
#       let height = h * scale;
#       let frame = (typeof (width * height) === "number" ? new Array(Math.max(0, Math.trunc(Number((width * height))))).fill(0) : (Array.isArray((width * height)) ? (width * height).slice() : Array.from((width * height))));
#       for (let y = 0; y < h; y += 1) {
#           for (let x = 0; x < w; x += 1) {
#               let v = (grid[(((y) < 0) ? ((grid).length + (y)) : (y))][(((x) < 0) ? ((grid[(((y) < 0) ? ((grid).length + (y)) : (y))]).length + (x)) : (x))] === 0 ? 255 : 40);
#               for (let yy = 0; yy < scale; yy += 1) {
#                   let base = (y * scale + yy) * width + x * scale;
#                   for (let xx = 0; xx < scale; xx += 1) {
#                       frame[(((base + xx) < 0) ? ((frame).length + (base + xx)) : (base + xx))] = v;
#                   }
#               }
#           }
#       }
#       return (Array.isArray((frame)) ? (frame).slice() : Array.from((frame)));
#   }
#   
#   function run_13_maze_generation_steps() {
#       // Increase maze size and render resolution to ensure sufficient runtime.
#       let cell_w = 89;
#       let cell_h = 67;
#       let scale = 5;
#       let capture_every = 20;
#       let out_path = "sample/out/13_maze_generation_steps.gif";
#       
#       let start = perf_counter();
#       let grid = (() => { let __out = []; for (const _ of (() => { const __out = []; const __start = 0; const __stop = cell_h; const __step = 1; if (__step === 0) { return __out; } if (__step > 0) { for (let __i = __start; __i < __stop; __i += __step) { __out.push(__i); } } else { for (let __i = __start; __i > __stop; __i += __step) { __out.push(__i); } } return __out; })()) { __out.push((() => { const __base = ([1]); const __n = Math.max(0, Math.trunc(Number(cell_w))); let __out = []; for (let __i = 0; __i < __n; __i += 1) { for (const __v of __base) { __out.push(__v); } } return __out; })()); } return __out; })();
#       let stack = [[1, 1]];
#       grid[(((1) < 0) ? ((grid).length + (1)) : (1))][(((1) < 0) ? ((grid[(((1) < 0) ? ((grid).length + (1)) : (1))]).length + (1)) : (1))] = 0;
#       
#       let dirs = [[2, 0], [-2, 0], [0, 2], [0, -2]];
#       let frames = [];
#       let step = 0;
#       
#       while ((stack).length !== 0) {
#           const __tmp_1 = stack[(((-1) < 0) ? ((stack).length + (-1)) : (-1))];
#           let x = __tmp_1[0];
#           let y = __tmp_1[1];
#           let candidates = [];
#           for (let k = 0; k < 4; k += 1) {
#               const __tmp_2 = dirs[(((k) < 0) ? ((dirs).length + (k)) : (k))];
#               let dx = __tmp_2[0];
#               let dy = __tmp_2[1];
#               let nx = x + dx;
#               let ny = y + dy;
#               if (nx >= 1 && nx < cell_w - 1 && ny >= 1 && ny < cell_h - 1 && grid[(((ny) < 0) ? ((grid).length + (ny)) : (ny))][(((nx) < 0) ? ((grid[(((ny) < 0) ? ((grid).length + (ny)) : (ny))]).length + (nx)) : (nx))] === 1) {
#                   if (dx === 2) {
#                       candidates.push([nx, ny, x + 1, y]);
#                   } else {
#                       if (dx === -2) {
#                           candidates.push([nx, ny, x - 1, y]);
#                       } else {
#                           if (dy === 2) {
#                               candidates.push([nx, ny, x, y + 1]);
#                           } else {
#                               candidates.push([nx, ny, x, y - 1]);
#                           }
#                       }
#                   }
#               }
#           }
#           if ((candidates).length === 0) {
#               stack.pop();
#           } else {
#               let sel = candidates[((((x * 17 + y * 29 + (stack).length * 13) % (candidates).length) < 0) ? ((candidates).length + ((x * 17 + y * 29 + (stack).length * 13) % (candidates).length)) : ((x * 17 + y * 29 + (stack).length * 13) % (candidates).length))];
#               const __tmp_3 = sel;
#               let nx = __tmp_3[0];
#               let ny = __tmp_3[1];
#               let wx = __tmp_3[2];
#               let wy = __tmp_3[3];
#               grid[(((wy) < 0) ? ((grid).length + (wy)) : (wy))][(((wx) < 0) ? ((grid[(((wy) < 0) ? ((grid).length + (wy)) : (wy))]).length + (wx)) : (wx))] = 0;
#               grid[(((ny) < 0) ? ((grid).length + (ny)) : (ny))][(((nx) < 0) ? ((grid[(((ny) < 0) ? ((grid).length + (ny)) : (ny))]).length + (nx)) : (nx))] = 0;
#               stack.push([nx, ny]);
#           }
#           if (step % capture_every === 0) {
#               frames.push(capture(grid, cell_w, cell_h, scale));
#           }
#           step += 1;
#       }
#       frames.push(capture(grid, cell_w, cell_h, scale));
#       save_gif(out_path, cell_w * scale, cell_h * scale, frames, grayscale_palette(), 4, 0);
#       let elapsed = perf_counter() - start;
#       console.log("output:", out_path);
#       console.log("frames:", (frames).length);
#       console.log("elapsed_sec:", elapsed);
#   }
#   
#   run_13_maze_generation_steps();
@'

# PowerShell preview generated from JavaScript pseudo conversion.
    import { perf_counter } from "./runtime/js/generated/std/time.js"
    import { grayscale_palette } from "./runtime/js/generated/utils/gif.js"
    import { save_gif } from "./runtime/js/generated/utils/gif.js"
    
    # 13: Sample that outputs DFS maze-generation progress as a GIF.
    
    function capture {
        param($grid, $w, $h, $scale)
        $width = $w * $scale
        $height = $h * $scale
        $frame = ($typeof $width * $height -$eq "number" ? $Array [Math]::Max(0, Math.trunc(Number(($width * height)))).fill(0) : ($Array.isArray(($width * height)) ? ($width * height).slice() : $Array.from(($width * height))))
        for ($y = 0; $y  -$lt  $h; $y += 1) {
            for ($x = 0; $x  -$lt  $w; $x += 1) {
                $v = ($grid[(((y)  -$lt  0) ? ((grid).Length + (y)) : (y))][(((x)  -$lt  0) ? (($grid[(((y)  -$lt  0) ? ((grid).Length + (y)) : (y))]).Length + (x)) : (x))] -$eq 0 ? 255 : 40)
                for ($yy = 0; $yy  -$lt  $scale; $yy += 1) {
                    $base = ($y * $scale + yy) * $width + $x * $scale
                    for ($xx = 0; $xx  -$lt  $scale; $xx += 1) {
                        frame[(((base + xx)  -lt  0) ? ((frame).Length + (base + xx)) : (base + xx))] = v
                    }
                }
            }
        }
        return ($Array.isArray((frame)) ? (frame).slice() : $Array.from((frame)))
    }
    
    function run_13_maze_generation_steps {
        param()
        // Increase maze size and render resolution to ensure sufficient runtime.
        $cell_w = 89
        $cell_h = 67
        $scale = 5
        $capture_every = 20
        $out_path = "sample/out/13_maze_generation_steps.gif"
    
        $start = $perf_counter
        $grid = (() = -$gt  { $let $__out = []; for ($const $_ of (() = -$gt  { $const $__out = []; $const $__start = 0; $const $__stop = $cell_h; $const $__step = 1; if ($__step -$eq 0) { return $__out; } if ($__step  -$gt  0) { for ($let $__i = $__start; $__i  -$lt  $__stop; $__i += __step) { $__out.push(__i); } } else { for ($let $__i = $__start; $__i  -$gt  $__stop; $__i += __step) { $__out.push(__i); } } return $__out; })()) { $__out.push((() = -$gt  { $const $__base = ([1]); $const $__n = [Math]::$Max 0 Math.trunc(Number(cell_w)); $let $__out = []; for ($let $__i = 0; $__i  -$lt  $__n; $__i += 1) { for ($const $__v $of __base) { $__out.push(__v); } } return $__out; })()); } return $__out; })()
        $stack = @(@(1, 1))
        grid[(((1)  -lt  0) ? ((grid).Length + (1)) : (1))][(((1)  -lt  0) ? ((grid[(((1)  -lt  0) ? ((grid).Length + (1)) : (1))]).Length + (1)) : (1))] = 0
    
        $dirs = @(@(2, 0), @(-2, 0), @(0, 2), @(0, -2))
        $frames = @()
        $step = 0
    
        while ((stack).Length -$ne 0) {
            $__tmp_1 = $stack[(((-1)  -$lt  0) ? ((stack).Length + (-1)) : (-1))]
            $x = $__tmp_1[0]
            $y = $__tmp_1[1]
            $candidates = @()
            for ($k = 0; $k  -$lt  4; $k += 1) {
                $__tmp_2 = $dirs[(((k)  -$lt  0) ? ((dirs).Length + (k)) : (k))]
                $dx = $__tmp_2[0]
                $dy = $__tmp_2[1]
                $nx = $x + $dx
                $ny = $y + $dy
                if ($nx  -$ge  1 -$and $nx  -$lt  $cell_w - 1 -$and $ny  -$ge  1 -$and $ny  -$lt  $cell_h - 1 -$and $grid[(((ny)  -$lt  0) ? ((grid).Length + (ny)) : (ny))][(((nx)  -$lt  0) ? (($grid[(((ny)  -$lt  0) ? ((grid).Length + (ny)) : (ny))]).Length + (nx)) : (nx))] -$eq 1) {
                    if ($dx -$eq 2) {
                        candidates.push([nx, ny, x + 1, y])
                    } else {
                        if ($dx -$eq -2) {
                            candidates.push([nx, ny, x - 1, y])
                        } else {
                            if ($dy -$eq 2) {
                                candidates.push([nx, ny, x, y + 1])
                            } else {
                                candidates.push([nx, ny, x, y - 1])
                            }
                        }
                    }
                }
            }
            if ((candidates).Length -$eq 0) {
                stack.pop()
            } else {
                $sel = $candidates[(((($x * 17 + $y * 29 + (stack).Length * 13) % (candidates).Length)  -$lt  0) ? ((candidates).Length + (($x * 17 + $y * 29 + (stack).Length * 13) % (candidates).Length)) : (($x * 17 + $y * 29 + (stack).Length * 13) % (candidates).Length))]
                $__tmp_3 = $sel
                $nx = $__tmp_3[0]
                $ny = $__tmp_3[1]
                $wx = $__tmp_3[2]
                $wy = $__tmp_3[3]
                grid[(((wy)  -lt  0) ? ((grid).Length + (wy)) : (wy))][(((wx)  -lt  0) ? ((grid[(((wy)  -lt  0) ? ((grid).Length + (wy)) : (wy))]).Length + (wx)) : (wx))] = 0
                grid[(((ny)  -lt  0) ? ((grid).Length + (ny)) : (ny))][(((nx)  -lt  0) ? ((grid[(((ny)  -lt  0) ? ((grid).Length + (ny)) : (ny))]).Length + (nx)) : (nx))] = 0
                stack.push([nx, ny])
            }
            if ($step % $capture_every -$eq 0) {
                frames.push(capture grid cell_w cell_h scale)
            }
            step += 1
        }
        frames.push(capture grid cell_w cell_h scale)
        save_gif out_path cell_w * scale cell_h * scale frames grayscale_palette(, 4, 0)
        $elapsed = $perf_counter - $start
        __pytra_print "output:" out_path
        __pytra_print "frames:" (frames).Length
        __pytra_print "elapsed_sec:" elapsed
    }
    
    run_13_maze_generation_steps

if (Get-Command -Name main -ErrorAction SilentlyContinue) {
    main
}
