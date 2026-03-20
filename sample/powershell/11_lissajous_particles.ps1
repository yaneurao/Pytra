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
#   import { save_gif } from "./runtime/js/generated/utils/gif.js";
#   
#   // 11: Sample that outputs Lissajous-motion particles as a GIF.
#   
#   function color_palette() {
#       let p = [];
#       for (let i = 0; i < 256; i += 1) {
#           let r = i;
#           let g = i * 3 % 256;
#           let b = 255 - i;
#           p.push(r);
#           p.push(g);
#           p.push(b);
#       }
#       return (Array.isArray((p)) ? (p).slice() : Array.from((p)));
#   }
#   
#   function run_11_lissajous_particles() {
#       let w = 320;
#       let h = 240;
#       let frames_n = 360;
#       let particles = 48;
#       let out_path = "sample/out/11_lissajous_particles.gif";
#       
#       let start = perf_counter();
#       let frames = [];
#       
#       for (let t = 0; t < frames_n; t += 1) {
#           let frame = (typeof (w * h) === "number" ? new Array(Math.max(0, Math.trunc(Number((w * h))))).fill(0) : (Array.isArray((w * h)) ? (w * h).slice() : Array.from((w * h))));
#           let __hoisted_cast_1 = Number(t);
#           
#           for (let p = 0; p < particles; p += 1) {
#               let phase = p * 0.261799;
#               let x = Math.trunc(Number(w * 0.5 + w * 0.38 * math.sin(0.11 * __hoisted_cast_1 + phase * 2.0)));
#               let y = Math.trunc(Number(h * 0.5 + h * 0.38 * math.sin(0.17 * __hoisted_cast_1 + phase * 3.0)));
#               let color = 30 + p * 9 % 220;
#               
#               for (let dy = -2; dy < 3; dy += 1) {
#                   for (let dx = -2; dx < 3; dx += 1) {
#                       let xx = x + dx;
#                       let yy = y + dy;
#                       if (xx >= 0 && xx < w && yy >= 0 && yy < h) {
#                           let d2 = dx * dx + dy * dy;
#                           if (d2 <= 4) {
#                               let idx = yy * w + xx;
#                               let v = color - d2 * 20;
#                               v = Math.max(0, v);
#                               if (v > frame[(((idx) < 0) ? ((frame).length + (idx)) : (idx))]) {
#                                   frame[(((idx) < 0) ? ((frame).length + (idx)) : (idx))] = v;
#                               }
#                           }
#                       }
#                   }
#               }
#           }
#           frames.push((Array.isArray((frame)) ? (frame).slice() : Array.from((frame))));
#       }
#       save_gif(out_path, w, h, frames, color_palette(), 3, 0);
#       let elapsed = perf_counter() - start;
#       console.log("output:", out_path);
#       console.log("frames:", frames_n);
#       console.log("elapsed_sec:", elapsed);
#   }
#   
#   run_11_lissajous_particles();
@'

# PowerShell preview generated from JavaScript pseudo conversion.
    import * as math from "./runtime/js/generated/std/math.js"
    import { perf_counter } from "./runtime/js/generated/std/time.js"
    import { save_gif } from "./runtime/js/generated/utils/gif.js"
    
    # 11: Sample that outputs Lissajous-motion particles as a GIF.
    
    function color_palette {
        param()
        $p = @()
        for ($i = 0; $i  -$lt  256; $i += 1) {
            $r = $i
            $g = $i * 3 % 256
            $b = 255 - $i
            p.push(r)
            p.push(g)
            p.push(b)
        }
        return ($Array.isArray((p)) ? (p).slice() : $Array.from((p)))
    }
    
    function run_11_lissajous_particles {
        param()
        $w = 320
        $h = 240
        $frames_n = 360
        $particles = 48
        $out_path = "sample/out/11_lissajous_particles.gif"
    
        $start = $perf_counter
        $frames = @()
    
        for ($t = 0; $t  -$lt  $frames_n; $t += 1) {
            $frame = ($typeof $w * $h -$eq "number" ? $Array [Math]::Max(0, Math.trunc(Number(($w * h)))).fill(0) : ($Array.isArray(($w * h)) ? ($w * h).slice() : $Array.from(($w * h))))
            $__hoisted_cast_1 = $__pytra_float $t
    
            for ($p = 0; $p  -$lt  $particles; $p += 1) {
                $phase = $p * 0.261799
                $x = [Math]::$Truncate Number($w * 0.5 + $w * 0.38 * $math.sin(0.11 * $__hoisted_cast_1 + $phase * 2.0))
                $y = [Math]::$Truncate Number($h * 0.5 + $h * 0.38 * $math.sin(0.17 * $__hoisted_cast_1 + $phase * 3.0))
                $color = 30 + $p * 9 % 220
    
                for ($dy = -2; $dy  -$lt  3; $dy += 1) {
                    for ($dx = -2; $dx  -$lt  3; $dx += 1) {
                        $xx = $x + $dx
                        $yy = $y + $dy
                        if ($xx  -$ge  0 -$and $xx  -$lt  $w -$and $yy  -$ge  0 -$and $yy  -$lt  $h) {
                            $d2 = $dx * $dx + $dy * $dy
                            if ($d2  -$le  4) {
                                $idx = $yy * $w + $xx
                                $v = $color - $d2 * 20
                                v = Math.max(0, v)
                                if ($v  -$gt  $frame[(((idx)  -$lt  0) ? ((frame).Length + (idx)) : (idx))]) {
                                    frame[(((idx)  -lt  0) ? ((frame).Length + (idx)) : (idx))] = v
                                }
                            }
                        }
                    }
                }
            }
            frames.push((Array.isArray((frame)) ? (frame).slice() : Array.from((frame))))
        }
        save_gif out_path w h frames color_palette(, 3, 0)
        $elapsed = $perf_counter - $start
        __pytra_print "output:" out_path
        __pytra_print "frames:" frames_n
        __pytra_print "elapsed_sec:" elapsed
    }
    
    run_11_lissajous_particles

if (Get-Command -Name main -ErrorAction SilentlyContinue) {
    main
}
