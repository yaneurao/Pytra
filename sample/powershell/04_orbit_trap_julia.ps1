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
#   // 04: Sample that renders an orbit-trap Julia set and writes a PNG image.
#   
#   function render_orbit_trap_julia(width, height, max_iter, cx, cy) {
#       let pixels = [];
#       let __hoisted_cast_1 = Number(height - 1);
#       let __hoisted_cast_2 = Number(width - 1);
#       let __hoisted_cast_3 = Number(max_iter);
#       
#       for (let y = 0; y < height; y += 1) {
#           let zy0 = -1.3 + 2.6 * (y / __hoisted_cast_1);
#           for (let x = 0; x < width; x += 1) {
#               let zx = -1.9 + 3.8 * (x / __hoisted_cast_2);
#               let zy = zy0;
#               
#               let trap = 1.0e9;
#               let i = 0;
#               while (i < max_iter) {
#                   let ax = zx;
#                   if (ax < 0.0) {
#                       ax = -ax;
#                   }
#                   let ay = zy;
#                   if (ay < 0.0) {
#                       ay = -ay;
#                   }
#                   let dxy = zx - zy;
#                   if (dxy < 0.0) {
#                       dxy = -dxy;
#                   }
#                   if (ax < trap) {
#                       trap = ax;
#                   }
#                   if (ay < trap) {
#                       trap = ay;
#                   }
#                   if (dxy < trap) {
#                       trap = dxy;
#                   }
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
#                   let trap_scaled = trap * 3.2;
#                   if (trap_scaled > 1.0) {
#                       trap_scaled = 1.0;
#                   }
#                   if (trap_scaled < 0.0) {
#                       trap_scaled = 0.0;
#                   }
#                   let t = i / __hoisted_cast_3;
#                   let tone = Math.trunc(Number(255.0 * (1.0 - trap_scaled)));
#                   r = Math.trunc(Number(tone * (0.35 + 0.65 * t)));
#                   g = Math.trunc(Number(tone * (0.15 + 0.85 * (1.0 - t))));
#                   b = Math.trunc(Number(255.0 * (0.25 + 0.75 * t)));
#                   if (r > 255) {
#                       r = 255;
#                   }
#                   if (g > 255) {
#                       g = 255;
#                   }
#                   if (b > 255) {
#                       b = 255;
#                   }
#               }
#               pixels.push(r);
#               pixels.push(g);
#               pixels.push(b);
#           }
#       }
#       return pixels;
#   }
#   
#   function run_04_orbit_trap_julia() {
#       let width = 1920;
#       let height = 1080;
#       let max_iter = 1400;
#       let out_path = "sample/out/04_orbit_trap_julia.png";
#       
#       let start = perf_counter();
#       let pixels = render_orbit_trap_julia(width, height, max_iter, -0.7269, 0.1889);
#       png.write_rgb_png(out_path, width, height, pixels);
#       let elapsed = perf_counter() - start;
#       
#       console.log("output:", out_path);
#       console.log("size:", width, "x", height);
#       console.log("max_iter:", max_iter);
#       console.log("elapsed_sec:", elapsed);
#   }
#   
#   run_04_orbit_trap_julia();
@'

# PowerShell preview generated from JavaScript pseudo conversion.
    import { perf_counter } from "./runtime/js/generated/std/time.js"
    import * as png from "./runtime/js/generated/utils/png.js"
    
    # 04: Sample that renders an orbit-trap Julia set and writes a PNG image.
    
    function render_orbit_trap_julia {
        param($width, $height, $max_iter, $cx, $cy)
        $pixels = @()
        $__hoisted_cast_1 = $__pytra_float $height - 1
        $__hoisted_cast_2 = $__pytra_float $width - 1
        $__hoisted_cast_3 = $__pytra_float $max_iter
    
        for ($y = 0; $y  -$lt  $height; $y += 1) {
            $zy0 = -1.3 + 2.6 * ($y / __hoisted_cast_1)
            for ($x = 0; $x  -$lt  $width; $x += 1) {
                $zx = -1.9 + 3.8 * ($x / __hoisted_cast_2)
                $zy = $zy0
    
                $trap = 1.0$e9
                $i = 0
                while ($i  -$lt  $max_iter) {
                    $ax = $zx
                    if ($ax  -$lt  0.0) {
                        ax = -ax
                    }
                    $ay = $zy
                    if ($ay  -$lt  0.0) {
                        ay = -ay
                    }
                    $dxy = $zx - $zy
                    if ($dxy  -$lt  0.0) {
                        dxy = -dxy
                    }
                    if ($ax  -$lt  $trap) {
                        trap = ax
                    }
                    if ($ay  -$lt  $trap) {
                        trap = ay
                    }
                    if ($dxy  -$lt  $trap) {
                        trap = dxy
                    }
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
                    $trap_scaled = $trap * 3.2
                    if ($trap_scaled  -$gt  1.0) {
                        trap_scaled = 1.0
                    }
                    if ($trap_scaled  -$lt  0.0) {
                        trap_scaled = 0.0
                    }
                    $t = $i / $__hoisted_cast_3
                    $tone = [Math]::$Truncate Number(255.0 * (1.0 - trap_scaled))
                    r = Math.trunc(__pytra_float tone * (0.35 + 0.65 * t))
                    g = Math.trunc(__pytra_float tone * (0.15 + 0.85 * (1.0 - t)))
                    b = Math.trunc(__pytra_float 255.0 * (0.25 + 0.75 * t))
                    if ($r  -$gt  255) {
                        r = 255
                    }
                    if ($g  -$gt  255) {
                        g = 255
                    }
                    if ($b  -$gt  255) {
                        b = 255
                    }
                }
                pixels.push(r)
                pixels.push(g)
                pixels.push(b)
            }
        }
        return $pixels
    }
    
    function run_04_orbit_trap_julia {
        param()
        $width = 1920
        $height = 1080
        $max_iter = 1400
        $out_path = "sample/out/04_orbit_trap_julia.png"
    
        $start = $perf_counter
        $pixels = $render_orbit_trap_julia $width $height $max_iter -0.7269 0.1889
        png.write_rgb_png(out_path, width, height, pixels)
        $elapsed = $perf_counter - $start
    
        __pytra_print "output:" out_path
        __pytra_print "size:" width "x" height
        __pytra_print "max_iter:" max_iter
        __pytra_print "elapsed_sec:" elapsed
    }
    
    run_04_orbit_trap_julia

if (Get-Command -Name main -ErrorAction SilentlyContinue) {
    main
}
