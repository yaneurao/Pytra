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
#   import * as math from "./runtime/js/generated/std/math.js";
#   import { perf_counter } from "./runtime/js/generated/std/time.js";
#   import { grayscale_palette } from "./runtime/js/generated/utils/gif.js";
#   import { save_gif } from "./runtime/js/generated/utils/gif.js";
#   
#   // 10: Sample that outputs a plasma effect as a GIF.
#   
#   function run_10_plasma_effect() {
#       let w = 320;
#       let h = 240;
#       let frames_n = 216;
#       let out_path = "sample/out/10_plasma_effect.gif";
#       
#       let start = perf_counter();
#       let frames = [];
#       
#       for (let t = 0; t < frames_n; t += 1) {
#           let frame = (typeof (w * h) === "number" ? new Array(Math.max(0, Math.trunc(Number((w * h))))).fill(0) : (Array.isArray((w * h)) ? (w * h).slice() : Array.from((w * h))));
#           for (let y = 0; y < h; y += 1) {
#               let row_base = y * w;
#               for (let x = 0; x < w; x += 1) {
#                   let dx = x - 160;
#                   let dy = y - 120;
#                   let v = math.sin((x + t * 2.0) * 0.045) + math.sin((y - t * 1.2) * 0.05) + math.sin((x + y + t * 1.7) * 0.03) + math.sin(math.sqrt(dx * dx + dy * dy) * 0.07 - t * 0.18);
#                   let c = Math.trunc(Number((v + 4.0) * (255.0 / 8.0)));
#                   if (c < 0) {
#                       c = 0;
#                   }
#                   if (c > 255) {
#                       c = 255;
#                   }
#                   frame[(((row_base + x) < 0) ? ((frame).length + (row_base + x)) : (row_base + x))] = c;
#               }
#           }
#           frames.push((Array.isArray((frame)) ? (frame).slice() : Array.from((frame))));
#       }
#       save_gif(out_path, w, h, frames, grayscale_palette(), 3, 0);
#       let elapsed = perf_counter() - start;
#       console.log("output:", out_path);
#       console.log("frames:", frames_n);
#       console.log("elapsed_sec:", elapsed);
#   }
#   
#   run_10_plasma_effect();
@'

# PowerShell preview generated from JavaScript pseudo conversion.
    import * as math from "./runtime/js/generated/std/math.js"
    import { perf_counter } from "./runtime/js/generated/std/time.js"
    import { grayscale_palette } from "./runtime/js/generated/utils/gif.js"
    import { save_gif } from "./runtime/js/generated/utils/gif.js"
    
    # 10: Sample that outputs a plasma effect as a GIF.
    
    function run_10_plasma_effect {
        param()
        $w = 320
        $h = 240
        $frames_n = 216
        $out_path = "sample/out/10_plasma_effect.gif"
    
        $start = $perf_counter
        $frames = @()
    
        for ($t = 0; $t  -$lt  $frames_n; $t += 1) {
            $frame = ($typeof $w * $h -$eq "number" ? $Array [Math]::Max(0, Math.trunc(Number(($w * h)))).fill(0) : ($Array.isArray(($w * h)) ? ($w * h).slice() : $Array.from(($w * h))))
            for ($y = 0; $y  -$lt  $h; $y += 1) {
                $row_base = $y * $w
                for ($x = 0; $x  -$lt  $w; $x += 1) {
                    $dx = $x - 160
                    $dy = $y - 120
                    $v = $math.sin(($x + $t * 2.0) * 0.045) + $math.sin(($y - $t * 1.2) * 0.05) + $math.sin(($x + $y + $t * 1.7) * 0.03) + $math.sin($math.sqrt($dx * $dx + $dy * dy) * 0.07 - $t * 0.18)
                    $c = [Math]::$Truncate Number(($v + 4.0 * (255.0 / 8.0)))
                    if ($c  -$lt  0) {
                        c = 0
                    }
                    if ($c  -$gt  255) {
                        c = 255
                    }
                    frame[(((row_base + x)  -lt  0) ? ((frame).Length + (row_base + x)) : (row_base + x))] = c
                }
            }
            frames.push((Array.isArray((frame)) ? (frame).slice() : Array.from((frame))))
        }
        save_gif out_path w h frames grayscale_palette(, 3, 0)
        $elapsed = $perf_counter - $start
        __pytra_print "output:" out_path
        __pytra_print "frames:" frames_n
        __pytra_print "elapsed_sec:" elapsed
    }
    
    run_10_plasma_effect

if (Get-Command -Name main -ErrorAction SilentlyContinue) {
    main
}
