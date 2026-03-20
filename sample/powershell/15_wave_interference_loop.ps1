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
#   // 15: Sample that renders wave interference animation and writes a GIF.
#   
#   function run_15_wave_interference_loop() {
#       let w = 320;
#       let h = 240;
#       let frames_n = 96;
#       let out_path = "sample/out/15_wave_interference_loop.gif";
#       
#       let start = perf_counter();
#       let frames = [];
#       
#       for (let t = 0; t < frames_n; t += 1) {
#           let frame = (typeof (w * h) === "number" ? new Array(Math.max(0, Math.trunc(Number((w * h))))).fill(0) : (Array.isArray((w * h)) ? (w * h).slice() : Array.from((w * h))));
#           let phase = t * 0.12;
#           for (let y = 0; y < h; y += 1) {
#               let row_base = y * w;
#               for (let x = 0; x < w; x += 1) {
#                   let dx = x - 160;
#                   let dy = y - 120;
#                   let v = math.sin((x + t * 1.5) * 0.045) + math.sin((y - t * 1.2) * 0.04) + math.sin((x + y) * 0.02 + phase) + math.sin(math.sqrt(dx * dx + dy * dy) * 0.08 - phase * 1.3);
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
#       save_gif(out_path, w, h, frames, grayscale_palette(), 4, 0);
#       let elapsed = perf_counter() - start;
#       console.log("output:", out_path);
#       console.log("frames:", frames_n);
#       console.log("elapsed_sec:", elapsed);
#   }
#   
#   run_15_wave_interference_loop();
@'

# PowerShell preview generated from JavaScript pseudo conversion.
    import * as math from "./runtime/js/generated/std/math.js"
    import { perf_counter } from "./runtime/js/generated/std/time.js"
    import { grayscale_palette } from "./runtime/js/generated/utils/gif.js"
    import { save_gif } from "./runtime/js/generated/utils/gif.js"
    
    # 15: Sample that renders wave interference animation and writes a GIF.
    
    function run_15_wave_interference_loop {
        param()
        $w = 320
        $h = 240
        $frames_n = 96
        $out_path = "sample/out/15_wave_interference_loop.gif"
    
        $start = $perf_counter
        $frames = @()
    
        for ($t = 0; $t  -$lt  $frames_n; $t += 1) {
            $frame = ($typeof $w * $h -$eq "number" ? $Array [Math]::Max(0, Math.trunc(Number(($w * h)))).fill(0) : ($Array.isArray(($w * h)) ? ($w * h).slice() : $Array.from(($w * h))))
            $phase = $t * 0.12
            for ($y = 0; $y  -$lt  $h; $y += 1) {
                $row_base = $y * $w
                for ($x = 0; $x  -$lt  $w; $x += 1) {
                    $dx = $x - 160
                    $dy = $y - 120
                    $v = $math.sin(($x + $t * 1.5) * 0.045) + $math.sin(($y - $t * 1.2) * 0.04) + $math.sin(($x + y) * 0.02 + phase) + $math.sin($math.sqrt($dx * $dx + $dy * dy) * 0.08 - $phase * 1.3)
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
        save_gif out_path w h frames grayscale_palette(, 4, 0)
        $elapsed = $perf_counter - $start
        __pytra_print "output:" out_path
        __pytra_print "frames:" frames_n
        __pytra_print "elapsed_sec:" elapsed
    }
    
    run_15_wave_interference_loop

if (Get-Command -Name main -ErrorAction SilentlyContinue) {
    main
}
