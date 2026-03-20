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
#   // 12: Sample that outputs intermediate states of bubble sort as a GIF.
#   
#   function render(values, w, h) {
#       let frame = (typeof (w * h) === "number" ? new Array(Math.max(0, Math.trunc(Number((w * h))))).fill(0) : (Array.isArray((w * h)) ? (w * h).slice() : Array.from((w * h))));
#       let n = (values).length;
#       let bar_w = w / n;
#       let __hoisted_cast_1 = Number(n);
#       let __hoisted_cast_2 = Number(h);
#       for (let i = 0; i < n; i += 1) {
#           let x0 = Math.trunc(Number(i * bar_w));
#           let x1 = Math.trunc(Number((i + 1) * bar_w));
#           if (x1 <= x0) {
#               x1 = x0 + 1;
#           }
#           let bh = Math.trunc(Number((values[(((i) < 0) ? ((values).length + (i)) : (i))] / __hoisted_cast_1) * __hoisted_cast_2));
#           let y = h - bh;
#           const __start_1 = y;
#           for (let y = __start_1; y < h; y += 1) {
#               for (let x = x0; x < x1; x += 1) {
#                   frame[(((y * w + x) < 0) ? ((frame).length + (y * w + x)) : (y * w + x))] = 255;
#               }
#           }
#       }
#       return (Array.isArray((frame)) ? (frame).slice() : Array.from((frame)));
#   }
#   
#   function run_12_sort_visualizer() {
#       let w = 320;
#       let h = 180;
#       let n = 124;
#       let out_path = "sample/out/12_sort_visualizer.gif";
#       
#       let start = perf_counter();
#       let values = [];
#       for (let i = 0; i < n; i += 1) {
#           values.push((i * 37 + 19) % n);
#       }
#       let frames = [render(values, w, h)];
#       let frame_stride = 16;
#       
#       let op = 0;
#       for (let i = 0; i < n; i += 1) {
#           let swapped = false;
#           for (let j = 0; j < n - i - 1; j += 1) {
#               if (values[(((j) < 0) ? ((values).length + (j)) : (j))] > values[(((j + 1) < 0) ? ((values).length + (j + 1)) : (j + 1))]) {
#                   const __tmp_2 = [values[(((j + 1) < 0) ? ((values).length + (j + 1)) : (j + 1))], values[(((j) < 0) ? ((values).length + (j)) : (j))]];
#                   values[(((j) < 0) ? ((values).length + (j)) : (j))] = __tmp_2[0];
#                   values[(((j + 1) < 0) ? ((values).length + (j + 1)) : (j + 1))] = __tmp_2[1];
#                   swapped = true;
#               }
#               if (op % frame_stride === 0) {
#                   frames.push(render(values, w, h));
#               }
#               op += 1;
#           }
#           if (!swapped) {
#               break;
#           }
#       }
#       save_gif(out_path, w, h, frames, grayscale_palette(), 3, 0);
#       let elapsed = perf_counter() - start;
#       console.log("output:", out_path);
#       console.log("frames:", (frames).length);
#       console.log("elapsed_sec:", elapsed);
#   }
#   
#   run_12_sort_visualizer();
@'

# PowerShell preview generated from JavaScript pseudo conversion.
    import { perf_counter } from "./runtime/js/generated/std/time.js"
    import { grayscale_palette } from "./runtime/js/generated/utils/gif.js"
    import { save_gif } from "./runtime/js/generated/utils/gif.js"
    
    # 12: Sample that outputs intermediate states of bubble sort as a GIF.
    
    function render {
        param($values, $w, $h)
        $frame = ($typeof $w * $h -$eq "number" ? $Array [Math]::Max(0, Math.trunc(Number(($w * h)))).fill(0) : ($Array.isArray(($w * h)) ? ($w * h).slice() : $Array.from(($w * h))))
        $n = (values).Length
        $bar_w = $w / $n
        $__hoisted_cast_1 = $__pytra_float $n
        $__hoisted_cast_2 = $__pytra_float $h
        for ($i = 0; $i  -$lt  $n; $i += 1) {
            $x0 = [Math]::$Truncate Number($i * bar_w)
            $x1 = [Math]::$Truncate Number(($i + 1 * bar_w))
            if ($x1  -$le  $x0) {
                x1 = x0 + 1
            }
            $bh = [Math]::$Truncate Number(($values[((($i  -$lt  0) ? ((values).Length + (i)) : (i))] / __hoisted_cast_1) * __hoisted_cast_2))
            $y = $h - $bh
            $__start_1 = $y
            for ($y = $__start_1; $y  -$lt  $h; $y += 1) {
                for ($x = $x0; $x  -$lt  $x1; $x += 1) {
                    frame[(((y * w + x)  -lt  0) ? ((frame).Length + (y * w + x)) : (y * w + x))] = 255
                }
            }
        }
        return ($Array.isArray((frame)) ? (frame).slice() : $Array.from((frame)))
    }
    
    function run_12_sort_visualizer {
        param()
        $w = 320
        $h = 180
        $n = 124
        $out_path = "sample/out/12_sort_visualizer.gif"
    
        $start = $perf_counter
        $values = @()
        for ($i = 0; $i  -$lt  $n; $i += 1) {
            values.push((i * 37 + 19) % n)
        }
        $frames = @($render $values $w $h)
        $frame_stride = 16
    
        $op = 0
        for ($i = 0; $i  -$lt  $n; $i += 1) {
            $swapped = $false
            for ($j = 0; $j  -$lt  $n - $i - 1; $j += 1) {
                if ($values[(((j)  -$lt  0) ? ((values).Length + (j)) : (j))]  -$gt  $values[((($j + 1)  -$lt  0) ? ((values).Length + ($j + 1)) : ($j + 1))]) {
                    $__tmp_2 = @($values[((($j + 1)  -$lt  0) ? ((values).Length + ($j + 1)) : ($j + 1))], $values[(((j)  -$lt  0) ? ((values).Length + (j)) : (j))])
                    values[(((j)  -lt  0) ? ((values).Length + (j)) : (j))] = __tmp_2[0]
                    values[(((j + 1)  -lt  0) ? ((values).Length + (j + 1)) : (j + 1))] = __tmp_2[1]
                    swapped = $true
                }
                if ($op % $frame_stride -$eq 0) {
                    frames.push(render values w h)
                }
                op += 1
            }
            if (-$not $swapped) {
                break
            }
        }
        save_gif out_path w h frames grayscale_palette(, 3, 0)
        $elapsed = $perf_counter - $start
        __pytra_print "output:" out_path
        __pytra_print "frames:" (frames).Length
        __pytra_print "elapsed_sec:" elapsed
    }
    
    run_12_sort_visualizer

if (Get-Command -Name main -ErrorAction SilentlyContinue) {
    main
}
