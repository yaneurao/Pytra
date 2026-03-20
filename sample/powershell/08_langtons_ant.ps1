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
#   // 08: Sample that outputs Langton's Ant trajectories as a GIF.
#   
#   function capture(grid, w, h) {
#       let frame = (typeof (w * h) === "number" ? new Array(Math.max(0, Math.trunc(Number((w * h))))).fill(0) : (Array.isArray((w * h)) ? (w * h).slice() : Array.from((w * h))));
#       for (let y = 0; y < h; y += 1) {
#           let row_base = y * w;
#           for (let x = 0; x < w; x += 1) {
#               frame[(((row_base + x) < 0) ? ((frame).length + (row_base + x)) : (row_base + x))] = (grid[(((y) < 0) ? ((grid).length + (y)) : (y))][(((x) < 0) ? ((grid[(((y) < 0) ? ((grid).length + (y)) : (y))]).length + (x)) : (x))] ? 255 : 0);
#           }
#       }
#       return (Array.isArray((frame)) ? (frame).slice() : Array.from((frame)));
#   }
#   
#   function run_08_langtons_ant() {
#       let w = 420;
#       let h = 420;
#       let out_path = "sample/out/08_langtons_ant.gif";
#       
#       let start = perf_counter();
#       
#       let grid = (() => { let __out = []; for (const _ of (() => { const __out = []; const __start = 0; const __stop = h; const __step = 1; if (__step === 0) { return __out; } if (__step > 0) { for (let __i = __start; __i < __stop; __i += __step) { __out.push(__i); } } else { for (let __i = __start; __i > __stop; __i += __step) { __out.push(__i); } } return __out; })()) { __out.push((() => { const __base = ([0]); const __n = Math.max(0, Math.trunc(Number(w))); let __out = []; for (let __i = 0; __i < __n; __i += 1) { for (const __v of __base) { __out.push(__v); } } return __out; })()); } return __out; })();
#       let x = Math.floor(w / 2);
#       let y = Math.floor(h / 2);
#       let d = 0;
#       
#       let steps_total = 600000;
#       let capture_every = 3000;
#       let frames = [];
#       
#       for (let i = 0; i < steps_total; i += 1) {
#           if (grid[(((y) < 0) ? ((grid).length + (y)) : (y))][(((x) < 0) ? ((grid[(((y) < 0) ? ((grid).length + (y)) : (y))]).length + (x)) : (x))] === 0) {
#               d = (d + 1) % 4;
#               grid[(((y) < 0) ? ((grid).length + (y)) : (y))][(((x) < 0) ? ((grid[(((y) < 0) ? ((grid).length + (y)) : (y))]).length + (x)) : (x))] = 1;
#           } else {
#               d = (d + 3) % 4;
#               grid[(((y) < 0) ? ((grid).length + (y)) : (y))][(((x) < 0) ? ((grid[(((y) < 0) ? ((grid).length + (y)) : (y))]).length + (x)) : (x))] = 0;
#           }
#           if (d === 0) {
#               y = (y - 1 + h) % h;
#           } else {
#               if (d === 1) {
#                   x = (x + 1) % w;
#               } else {
#                   if (d === 2) {
#                       y = (y + 1) % h;
#                   } else {
#                       x = (x - 1 + w) % w;
#                   }
#               }
#           }
#           if (i % capture_every === 0) {
#               frames.push(capture(grid, w, h));
#           }
#       }
#       save_gif(out_path, w, h, frames, grayscale_palette(), 5, 0);
#       let elapsed = perf_counter() - start;
#       console.log("output:", out_path);
#       console.log("frames:", (frames).length);
#       console.log("elapsed_sec:", elapsed);
#   }
#   
#   run_08_langtons_ant();
@'

# PowerShell preview generated from JavaScript pseudo conversion.
    import { perf_counter } from "./runtime/js/generated/std/time.js"
    import { grayscale_palette } from "./runtime/js/generated/utils/gif.js"
    import { save_gif } from "./runtime/js/generated/utils/gif.js"
    
    # 08: Sample that outputs Langton's Ant trajectories as a GIF.
    
    function capture {
        param($grid, $w, $h)
        $frame = ($typeof $w * $h -$eq "number" ? $Array [Math]::Max(0, Math.trunc(Number(($w * h)))).fill(0) : ($Array.isArray(($w * h)) ? ($w * h).slice() : $Array.from(($w * h))))
        for ($y = 0; $y  -$lt  $h; $y += 1) {
            $row_base = $y * $w
            for ($x = 0; $x  -$lt  $w; $x += 1) {
                frame[(((row_base + x)  -lt  0) ? ((frame).Length + (row_base + x)) : (row_base + x))] = (grid[(((y)  -lt  0) ? ((grid).Length + (y)) : (y))][(((x)  -lt  0) ? ((grid[(((y)  -lt  0) ? ((grid).Length + (y)) : (y))]).Length + (x)) : (x))] ? 255 : 0)
            }
        }
        return ($Array.isArray((frame)) ? (frame).slice() : $Array.from((frame)))
    }
    
    function run_08_langtons_ant {
        param()
        $w = 420
        $h = 420
        $out_path = "sample/out/08_langtons_ant.gif"
    
        $start = $perf_counter
    
        $grid = (() = -$gt  { $let $__out = []; for ($const $_ of (() = -$gt  { $const $__out = []; $const $__start = 0; $const $__stop = $h; $const $__step = 1; if ($__step -$eq 0) { return $__out; } if ($__step  -$gt  0) { for ($let $__i = $__start; $__i  -$lt  $__stop; $__i += __step) { $__out.push(__i); } } else { for ($let $__i = $__start; $__i  -$gt  $__stop; $__i += __step) { $__out.push(__i); } } return $__out; })()) { $__out.push((() = -$gt  { $const $__base = ([0]); $const $__n = [Math]::$Max 0 Math.trunc(Number(w)); $let $__out = []; for ($let $__i = 0; $__i  -$lt  $__n; $__i += 1) { for ($const $__v $of __base) { $__out.push(__v); } } return $__out; })()); } return $__out; })()
        $x = [Math]::$Floor $w / 2
        $y = [Math]::$Floor $h / 2
        $d = 0
    
        $steps_total = 600000
        $capture_every = 3000
        $frames = @()
    
        for ($i = 0; $i  -$lt  $steps_total; $i += 1) {
            if ($grid[(((y)  -$lt  0) ? ((grid).Length + (y)) : (y))][(((x)  -$lt  0) ? (($grid[(((y)  -$lt  0) ? ((grid).Length + (y)) : (y))]).Length + (x)) : (x))] -$eq 0) {
                d = (d + 1) % 4
                grid[(((y)  -lt  0) ? ((grid).Length + (y)) : (y))][(((x)  -lt  0) ? ((grid[(((y)  -lt  0) ? ((grid).Length + (y)) : (y))]).Length + (x)) : (x))] = 1
            } else {
                d = (d + 3) % 4
                grid[(((y)  -lt  0) ? ((grid).Length + (y)) : (y))][(((x)  -lt  0) ? ((grid[(((y)  -lt  0) ? ((grid).Length + (y)) : (y))]).Length + (x)) : (x))] = 0
            }
            if ($d -$eq 0) {
                y = (y - 1 + h) % h
            } else {
                if ($d -$eq 1) {
                    x = (x + 1) % w
                } else {
                    if ($d -$eq 2) {
                        y = (y + 1) % h
                    } else {
                        x = (x - 1 + w) % w
                    }
                }
            }
            if ($i % $capture_every -$eq 0) {
                frames.push(capture grid w h)
            }
        }
        save_gif out_path w h frames grayscale_palette(, 5, 0)
        $elapsed = $perf_counter - $start
        __pytra_print "output:" out_path
        __pytra_print "frames:" (frames).Length
        __pytra_print "elapsed_sec:" elapsed
    }
    
    run_08_langtons_ant

if (Get-Command -Name main -ErrorAction SilentlyContinue) {
    main
}
