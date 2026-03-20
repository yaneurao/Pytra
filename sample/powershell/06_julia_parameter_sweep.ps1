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
#   // 06: Sample that sweeps Julia-set parameters and outputs a GIF.
#   
#   function julia_palette() {
#       // Keep index 0 black for points inside the set; build a high-saturation gradient for the rest.
#       let palette = (typeof (256 * 3) === "number" ? new Array(Math.max(0, Math.trunc(Number((256 * 3))))).fill(0) : (Array.isArray((256 * 3)) ? (256 * 3).slice() : Array.from((256 * 3))));
#       palette[(((0) < 0) ? ((palette).length + (0)) : (0))] = 0;
#       palette[(((1) < 0) ? ((palette).length + (1)) : (1))] = 0;
#       palette[(((2) < 0) ? ((palette).length + (2)) : (2))] = 0;
#       for (let i = 1; i < 256; i += 1) {
#           let t = (i - 1) / 254.0;
#           let r = Math.trunc(Number(255.0 * 9.0 * (1.0 - t) * t * t * t));
#           let g = Math.trunc(Number(255.0 * 15.0 * (1.0 - t) * (1.0 - t) * t * t));
#           let b = Math.trunc(Number(255.0 * 8.5 * (1.0 - t) * (1.0 - t) * (1.0 - t) * t));
#           palette[(((i * 3 + 0) < 0) ? ((palette).length + (i * 3 + 0)) : (i * 3 + 0))] = r;
#           palette[(((i * 3 + 1) < 0) ? ((palette).length + (i * 3 + 1)) : (i * 3 + 1))] = g;
#           palette[(((i * 3 + 2) < 0) ? ((palette).length + (i * 3 + 2)) : (i * 3 + 2))] = b;
#       }
#       return (Array.isArray((palette)) ? (palette).slice() : Array.from((palette)));
#   }
#   
#   function render_frame(width, height, cr, ci, max_iter, phase) {
#       let frame = (typeof (width * height) === "number" ? new Array(Math.max(0, Math.trunc(Number((width * height))))).fill(0) : (Array.isArray((width * height)) ? (width * height).slice() : Array.from((width * height))));
#       let __hoisted_cast_1 = Number(height - 1);
#       let __hoisted_cast_2 = Number(width - 1);
#       for (let y = 0; y < height; y += 1) {
#           let row_base = y * width;
#           let zy0 = -1.2 + 2.4 * (y / __hoisted_cast_1);
#           for (let x = 0; x < width; x += 1) {
#               let zx = -1.8 + 3.6 * (x / __hoisted_cast_2);
#               let zy = zy0;
#               let i = 0;
#               while (i < max_iter) {
#                   let zx2 = zx * zx;
#                   let zy2 = zy * zy;
#                   if (zx2 + zy2 > 4.0) {
#                       break;
#                   }
#                   zy = 2.0 * zx * zy + ci;
#                   zx = zx2 - zy2 + cr;
#                   i += 1;
#               }
#               if (i >= max_iter) {
#                   frame[(((row_base + x) < 0) ? ((frame).length + (row_base + x)) : (row_base + x))] = 0;
#               } else {
#                   // Add a small frame phase so colors flow smoothly.
#                   let color_index = 1 + (Math.floor(i * 224 / max_iter) + phase) % 255;
#                   frame[(((row_base + x) < 0) ? ((frame).length + (row_base + x)) : (row_base + x))] = color_index;
#               }
#           }
#       }
#       return (Array.isArray((frame)) ? (frame).slice() : Array.from((frame)));
#   }
#   
#   function run_06_julia_parameter_sweep() {
#       let width = 320;
#       let height = 240;
#       let frames_n = 72;
#       let max_iter = 180;
#       let out_path = "sample/out/06_julia_parameter_sweep.gif";
#       
#       let start = perf_counter();
#       let frames = [];
#       // Orbit an ellipse around a known visually good region to reduce flat blown highlights.
#       let center_cr = -0.745;
#       let center_ci = 0.186;
#       let radius_cr = 0.12;
#       let radius_ci = 0.10;
#       // Add start and phase offsets so GitHub thumbnails do not appear too dark.
#       // Tune it to start in a red-leaning color range.
#       let start_offset = 20;
#       let phase_offset = 180;
#       let __hoisted_cast_3 = Number(frames_n);
#       for (let i = 0; i < frames_n; i += 1) {
#           let t = (i + start_offset) % frames_n / __hoisted_cast_3;
#           let angle = 2.0 * math.pi * t;
#           let cr = center_cr + radius_cr * math.cos(angle);
#           let ci = center_ci + radius_ci * math.sin(angle);
#           let phase = (phase_offset + i * 5) % 255;
#           frames.push(render_frame(width, height, cr, ci, max_iter, phase));
#       }
#       save_gif(out_path, width, height, frames, julia_palette(), 8, 0);
#       let elapsed = perf_counter() - start;
#       console.log("output:", out_path);
#       console.log("frames:", frames_n);
#       console.log("elapsed_sec:", elapsed);
#   }
#   
#   run_06_julia_parameter_sweep();
@'

# PowerShell preview generated from JavaScript pseudo conversion.
    import * as math from "./runtime/js/generated/std/math.js"
    import { perf_counter } from "./runtime/js/generated/std/time.js"
    import { save_gif } from "./runtime/js/generated/utils/gif.js"
    
    # 06: Sample that sweeps Julia-set parameters and outputs a GIF.
    
    function julia_palette {
        param()
        // Keep index 0 black for points inside the set; build a high-saturation gradient for the rest.
        $palette = ($typeof 256 * 3 -$eq "number" ? $Array [Math]::Max(0, Math.trunc(Number((256 * 3)))).fill(0) : ($Array.isArray((256 * 3)) ? (256 * 3).slice() : $Array.from((256 * 3))))
        palette[(((0)  -lt  0) ? ((palette).Length + (0)) : (0))] = 0
        palette[(((1)  -lt  0) ? ((palette).Length + (1)) : (1))] = 0
        palette[(((2)  -lt  0) ? ((palette).Length + (2)) : (2))] = 0
        for ($i = 1; $i  -$lt  256; $i += 1) {
            $t = ($i - 1) / 254.0
            $r = [Math]::$Truncate Number(255.0 * 9.0 * (1.0 - $t * $t * $t * t))
            $g = [Math]::$Truncate Number(255.0 * 15.0 * (1.0 - $t * (1.0 - t) * $t * t))
            $b = [Math]::$Truncate Number(255.0 * 8.5 * (1.0 - $t * (1.0 - t) * (1.0 - t) * t))
            palette[(((i * 3 + 0)  -lt  0) ? ((palette).Length + (i * 3 + 0)) : (i * 3 + 0))] = r
            palette[(((i * 3 + 1)  -lt  0) ? ((palette).Length + (i * 3 + 1)) : (i * 3 + 1))] = g
            palette[(((i * 3 + 2)  -lt  0) ? ((palette).Length + (i * 3 + 2)) : (i * 3 + 2))] = b
        }
        return ($Array.isArray((palette)) ? (palette).slice() : $Array.from((palette)))
    }
    
    function render_frame {
        param($width, $height, $cr, $ci, $max_iter, $phase)
        $frame = ($typeof $width * $height -$eq "number" ? $Array [Math]::Max(0, Math.trunc(Number(($width * height)))).fill(0) : ($Array.isArray(($width * height)) ? ($width * height).slice() : $Array.from(($width * height))))
        $__hoisted_cast_1 = $__pytra_float $height - 1
        $__hoisted_cast_2 = $__pytra_float $width - 1
        for ($y = 0; $y  -$lt  $height; $y += 1) {
            $row_base = $y * $width
            $zy0 = -1.2 + 2.4 * ($y / __hoisted_cast_1)
            for ($x = 0; $x  -$lt  $width; $x += 1) {
                $zx = -1.8 + 3.6 * ($x / __hoisted_cast_2)
                $zy = $zy0
                $i = 0
                while ($i  -$lt  $max_iter) {
                    $zx2 = $zx * $zx
                    $zy2 = $zy * $zy
                    if ($zx2 + $zy2  -$gt  4.0) {
                        break
                    }
                    zy = 2.0 * zx * zy + ci
                    zx = zx2 - zy2 + cr
                    i += 1
                }
                if ($i  -$ge  $max_iter) {
                    frame[(((row_base + x)  -lt  0) ? ((frame).Length + (row_base + x)) : (row_base + x))] = 0
                } else {
                    // Add a small frame phase so colors flow smoothly.
                    $color_index = 1 + ([Math]::$Floor $i * 224 / $max_iter + phase) % 255
                    frame[(((row_base + x)  -lt  0) ? ((frame).Length + (row_base + x)) : (row_base + x))] = color_index
                }
            }
        }
        return ($Array.isArray((frame)) ? (frame).slice() : $Array.from((frame)))
    }
    
    function run_06_julia_parameter_sweep {
        param()
        $width = 320
        $height = 240
        $frames_n = 72
        $max_iter = 180
        $out_path = "sample/out/06_julia_parameter_sweep.gif"
    
        $start = $perf_counter
        $frames = @()
        // Orbit an ellipse around a known visually good region to reduce flat blown highlights.
        $center_cr = -0.745
        $center_ci = 0.186
        $radius_cr = 0.12
        $radius_ci = 0.10
        // Add start and phase offsets so GitHub thumbnails do not appear too dark.
        // Tune it to start in a red-leaning color range.
        $start_offset = 20
        $phase_offset = 180
        $__hoisted_cast_3 = $__pytra_float $frames_n
        for ($i = 0; $i  -$lt  $frames_n; $i += 1) {
            $t = ($i + start_offset) % $frames_n / $__hoisted_cast_3
            $angle = 2.0 * $math.pi * $t
            $cr = $center_cr + $radius_cr * $math.cos(angle)
            $ci = $center_ci + $radius_ci * $math.sin(angle)
            $phase = ($phase_offset + $i * 5) % 255
            frames.push(render_frame width height cr ci max_iter phase)
        }
        save_gif out_path width height frames julia_palette(, 8, 0)
        $elapsed = $perf_counter - $start
        __pytra_print "output:" out_path
        __pytra_print "frames:" frames_n
        __pytra_print "elapsed_sec:" elapsed
    }
    
    run_06_julia_parameter_sweep

if (Get-Command -Name main -ErrorAction SilentlyContinue) {
    main
}
