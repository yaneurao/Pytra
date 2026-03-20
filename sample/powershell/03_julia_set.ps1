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
#   import * as png from "./runtime/js/generated/utils/png.js";
#   
#   // 03: Sample that outputs a Julia set as a PNG image.
#   // Implemented with simple loop-centric logic for transpilation compatibility.
#   
#   function render_julia(width, height, max_iter, cx, cy) {
#       let pixels = [];
#       let __hoisted_cast_1 = Number(height - 1);
#       let __hoisted_cast_2 = Number(width - 1);
#       let __hoisted_cast_3 = Number(max_iter);
#       
#       for (let y = 0; y < height; y += 1) {
#           let zy0 = -1.2 + 2.4 * (y / __hoisted_cast_1);
#           
#           for (let x = 0; x < width; x += 1) {
#               let zx = -1.8 + 3.6 * (x / __hoisted_cast_2);
#               let zy = zy0;
#               
#               let i = 0;
#               while (i < max_iter) {
#                   let zx2 = zx * zx;
#                   let zy2 = zy * zy;
#                   if (zx2 + zy2 > 4.0) {
#                       break;
#                   }
#                   zy = 2.0 * zx * zy + cy;
#                   zx = zx2 - zy2 + cx;
#                   i += 1;
#               }
#               let r = 0;
#               let g = 0;
#               let b = 0;
#               if (i >= max_iter) {
#                   r = 0;
#                   g = 0;
#                   b = 0;
#               } else {
#                   let t = i / __hoisted_cast_3;
#                   r = Math.trunc(Number(255.0 * (0.2 + 0.8 * t)));
#                   g = Math.trunc(Number(255.0 * (0.1 + 0.9 * t * t)));
#                   b = Math.trunc(Number(255.0 * (1.0 - t)));
#               }
#               pixels.push(r);
#               pixels.push(g);
#               pixels.push(b);
#           }
#       }
#       return pixels;
#   }
#   
#   function run_julia() {
#       let width = 3840;
#       let height = 2160;
#       let max_iter = 20000;
#       let out_path = "sample/out/03_julia_set.png";
#       
#       let start = perf_counter();
#       let pixels = render_julia(width, height, max_iter, -0.8, 0.156);
#       png.write_rgb_png(out_path, width, height, pixels);
#       let elapsed = perf_counter() - start;
#       
#       console.log("output:", out_path);
#       console.log("size:", width, "x", height);
#       console.log("max_iter:", max_iter);
#       console.log("elapsed_sec:", elapsed);
#   }
#   
#   run_julia();
@'

# PowerShell preview generated from JavaScript pseudo conversion.
    import { perf_counter } from "./runtime/js/generated/std/time.js"
    import * as png from "./runtime/js/generated/utils/png.js"
    
    # 03: Sample that outputs a Julia set as a PNG image.
    # Implemented with simple loop-centric logic for transpilation compatibility.
    
    function render_julia {
        param($width, $height, $max_iter, $cx, $cy)
        $pixels = @()
        $__hoisted_cast_1 = $__pytra_float $height - 1
        $__hoisted_cast_2 = $__pytra_float $width - 1
        $__hoisted_cast_3 = $__pytra_float $max_iter
    
        for ($y = 0; $y  -$lt  $height; $y += 1) {
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
                    zy = 2.0 * zx * zy + cy
                    zx = zx2 - zy2 + cx
                    i += 1
                }
                $r = 0
                $g = 0
                $b = 0
                if ($i  -$ge  $max_iter) {
                    r = 0
                    g = 0
                    b = 0
                } else {
                    $t = $i / $__hoisted_cast_3
                    r = Math.trunc(__pytra_float 255.0 * (0.2 + 0.8 * t))
                    g = Math.trunc(__pytra_float 255.0 * (0.1 + 0.9 * t * t))
                    b = Math.trunc(__pytra_float 255.0 * (1.0 - t))
                }
                pixels.push(r)
                pixels.push(g)
                pixels.push(b)
            }
        }
        return $pixels
    }
    
    function run_julia {
        param()
        $width = 3840
        $height = 2160
        $max_iter = 20000
        $out_path = "sample/out/03_julia_set.png"
    
        $start = $perf_counter
        $pixels = $render_julia $width $height $max_iter -0.8 0.156
        png.write_rgb_png(out_path, width, height, pixels)
        $elapsed = $perf_counter - $start
    
        __pytra_print "output:" out_path
        __pytra_print "size:" width "x" height
        __pytra_print "max_iter:" max_iter
        __pytra_print "elapsed_sec:" elapsed
    }
    
    run_julia

if (Get-Command -Name main -ErrorAction SilentlyContinue) {
    main
}
