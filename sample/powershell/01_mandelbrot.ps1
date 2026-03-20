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
#   // 01: Sample that outputs the Mandelbrot set as a PNG image.
#   // Syntax is kept straightforward with future transpilation in mind.
#   
#   function escape_count(cx, cy, max_iter) {
#       let x = 0.0;
#       let y = 0.0;
#       for (let i = 0; i < max_iter; i += 1) {
#           let x2 = x * x;
#           let y2 = y * y;
#           if (x2 + y2 > 4.0) {
#               return i;
#           }
#           y = 2.0 * x * y + cy;
#           x = x2 - y2 + cx;
#       }
#       return max_iter;
#   }
#   
#   function color_map(iter_count, max_iter) {
#       if (iter_count >= max_iter) {
#           return [0, 0, 0];
#       }
#       let t = iter_count / max_iter;
#       let r = Math.trunc(Number(255.0 * t * t));
#       let g = Math.trunc(Number(255.0 * t));
#       let b = Math.trunc(Number(255.0 * (1.0 - t)));
#       return [r, g, b];
#   }
#   
#   function render_mandelbrot(width, height, max_iter, x_min, x_max, y_min, y_max) {
#       let pixels = [];
#       let __hoisted_cast_1 = Number(height - 1);
#       let __hoisted_cast_2 = Number(width - 1);
#       let __hoisted_cast_3 = Number(max_iter);
#       
#       for (let y = 0; y < height; y += 1) {
#           let py = y_min + (y_max - y_min) * (y / __hoisted_cast_1);
#           
#           for (let x = 0; x < width; x += 1) {
#               let px = x_min + (x_max - x_min) * (x / __hoisted_cast_2);
#               let it = escape_count(px, py, max_iter);
#               let r;
#               let g;
#               let b;
#               if (it >= max_iter) {
#                   r = 0;
#                   g = 0;
#                   b = 0;
#               } else {
#                   let t = it / __hoisted_cast_3;
#                   r = Math.trunc(Number(255.0 * t * t));
#                   g = Math.trunc(Number(255.0 * t));
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
#   function run_mandelbrot() {
#       let width = 1600;
#       let height = 1200;
#       let max_iter = 1000;
#       let out_path = "sample/out/01_mandelbrot.png";
#       
#       let start = perf_counter();
#       
#       let pixels = render_mandelbrot(width, height, max_iter, -2.2, 1.0, -1.2, 1.2);
#       png.write_rgb_png(out_path, width, height, pixels);
#       
#       let elapsed = perf_counter() - start;
#       console.log("output:", out_path);
#       console.log("size:", width, "x", height);
#       console.log("max_iter:", max_iter);
#       console.log("elapsed_sec:", elapsed);
#   }
#   
#   run_mandelbrot();
@'

# PowerShell preview generated from JavaScript pseudo conversion.
    import { perf_counter } from "./runtime/js/generated/std/time.js"
    import * as png from "./runtime/js/generated/utils/png.js"
    
    # 01: Sample that outputs the Mandelbrot set as a PNG image.
    # Syntax is kept straightforward with future transpilation in mind.
    
    function escape_count {
        param($cx, $cy, $max_iter)
        $x = 0.0
        $y = 0.0
        for ($i = 0; $i  -$lt  $max_iter; $i += 1) {
            $x2 = $x * $x
            $y2 = $y * $y
            if ($x2 + $y2  -$gt  4.0) {
                return $i
            }
            y = 2.0 * x * y + cy
            x = x2 - y2 + cx
        }
        return $max_iter
    }
    
    function color_map {
        param($iter_count, $max_iter)
        if ($iter_count  -$ge  $max_iter) {
            return [0, 0, 0]
        }
        $t = $iter_count / $max_iter
        $r = [Math]::$Truncate Number(255.0 * $t * t)
        $g = [Math]::$Truncate Number(255.0 * t)
        $b = [Math]::$Truncate Number(255.0 * (1.0 - t))
        return [$r, $g, $b]
    }
    
    function render_mandelbrot {
        param($width, $height, $max_iter, $x_min, $x_max, $y_min, $y_max)
        $pixels = @()
        $__hoisted_cast_1 = $__pytra_float $height - 1
        $__hoisted_cast_2 = $__pytra_float $width - 1
        $__hoisted_cast_3 = $__pytra_float $max_iter
    
        for ($y = 0; $y  -$lt  $height; $y += 1) {
            $py = $y_min + ($y_max - y_min) * ($y / __hoisted_cast_1)
    
            for ($x = 0; $x  -$lt  $width; $x += 1) {
                $px = $x_min + ($x_max - x_min) * ($x / __hoisted_cast_2)
                $it = $escape_count $px $py $max_iter
                $r = $null
                $g = $null
                $b = $null
                if ($it  -$ge  $max_iter) {
                    r = 0
                    g = 0
                    b = 0
                } else {
                    $t = $it / $__hoisted_cast_3
                    r = Math.trunc(__pytra_float 255.0 * t * t)
                    g = Math.trunc(__pytra_float 255.0 * t)
                    b = Math.trunc(__pytra_float 255.0 * (1.0 - t))
                }
                pixels.push(r)
                pixels.push(g)
                pixels.push(b)
            }
        }
        return $pixels
    }
    
    function run_mandelbrot {
        param()
        $width = 1600
        $height = 1200
        $max_iter = 1000
        $out_path = "sample/out/01_mandelbrot.png"
    
        $start = $perf_counter
    
        $pixels = $render_mandelbrot $width $height $max_iter -2.2 1.0 -1.2 1.2
        png.write_rgb_png(out_path, width, height, pixels)
    
        $elapsed = $perf_counter - $start
        __pytra_print "output:" out_path
        __pytra_print "size:" width "x" height
        __pytra_print "max_iter:" max_iter
        __pytra_print "elapsed_sec:" elapsed
    }
    
    run_mandelbrot

if (Get-Command -Name main -ErrorAction SilentlyContinue) {
    main
}
