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
#   import * as png from "./runtime/js/generated/utils/png.js";
#   import { perf_counter } from "./runtime/js/generated/std/time.js";
#   
#   // 02: Sample that runs a mini sphere-only ray tracer and outputs a PNG image.
#   // Dependencies are kept minimal (time only) for transpilation compatibility.
#   
#   function clamp01(v) {
#       if (v < 0.0) {
#           return 0.0;
#       }
#       if (v > 1.0) {
#           return 1.0;
#       }
#       return v;
#   }
#   
#   function hit_sphere(ox, oy, oz, dx, dy, dz, cx, cy, cz, r) {
#       let lx = ox - cx;
#       let ly = oy - cy;
#       let lz = oz - cz;
#       
#       let a = dx * dx + dy * dy + dz * dz;
#       let b = 2.0 * (lx * dx + ly * dy + lz * dz);
#       let c = lx * lx + ly * ly + lz * lz - r * r;
#       
#       let d = b * b - 4.0 * a * c;
#       if (d < 0.0) {
#           return -1.0;
#       }
#       let sd = math.sqrt(d);
#       let t0 = (-b - sd) / (2.0 * a);
#       let t1 = (-b + sd) / (2.0 * a);
#       
#       if (t0 > 0.001) {
#           return t0;
#       }
#       if (t1 > 0.001) {
#           return t1;
#       }
#       return -1.0;
#   }
#   
#   function render(width, height, aa) {
#       let pixels = [];
#       
#       // Camera origin
#       let ox = 0.0;
#       let oy = 0.0;
#       let oz = -3.0;
#       
#       // Light direction (normalized)
#       let lx = -0.4;
#       let ly = 0.8;
#       let lz = -0.45;
#       let __hoisted_cast_1 = Number(aa);
#       let __hoisted_cast_2 = Number(height - 1);
#       let __hoisted_cast_3 = Number(width - 1);
#       let __hoisted_cast_4 = Number(height);
#       
#       for (let y = 0; y < height; y += 1) {
#           for (let x = 0; x < width; x += 1) {
#               let ar = 0;
#               let ag = 0;
#               let ab = 0;
#               
#               for (let ay = 0; ay < aa; ay += 1) {
#                   for (let ax = 0; ax < aa; ax += 1) {
#                       let fy = (y + (ay + 0.5) / __hoisted_cast_1) / __hoisted_cast_2;
#                       let fx = (x + (ax + 0.5) / __hoisted_cast_1) / __hoisted_cast_3;
#                       let sy = 1.0 - 2.0 * fy;
#                       let sx = (2.0 * fx - 1.0) * (width / __hoisted_cast_4);
#                       
#                       let dx = sx;
#                       let dy = sy;
#                       let dz = 1.0;
#                       let inv_len = 1.0 / math.sqrt(dx * dx + dy * dy + dz * dz);
#                       dx *= inv_len;
#                       dy *= inv_len;
#                       dz *= inv_len;
#                       
#                       let t_min = 1.0e30;
#                       let hit_id = -1;
#                       
#                       let t = hit_sphere(ox, oy, oz, dx, dy, dz, -0.8, -0.2, 2.2, 0.8);
#                       if (t > 0.0 && t < t_min) {
#                           t_min = t;
#                           hit_id = 0;
#                       }
#                       t = hit_sphere(ox, oy, oz, dx, dy, dz, 0.9, 0.1, 2.9, 0.95);
#                       if (t > 0.0 && t < t_min) {
#                           t_min = t;
#                           hit_id = 1;
#                       }
#                       t = hit_sphere(ox, oy, oz, dx, dy, dz, 0.0, -1001.0, 3.0, 1000.0);
#                       if (t > 0.0 && t < t_min) {
#                           t_min = t;
#                           hit_id = 2;
#                       }
#                       let r = 0;
#                       let g = 0;
#                       let b = 0;
#                       
#                       if (hit_id >= 0) {
#                           let px = ox + dx * t_min;
#                           let py = oy + dy * t_min;
#                           let pz = oz + dz * t_min;
#                           
#                           let nx = 0.0;
#                           let ny = 0.0;
#                           let nz = 0.0;
#                           
#                           if (hit_id === 0) {
#                               nx = (px + 0.8) / 0.8;
#                               ny = (py + 0.2) / 0.8;
#                               nz = (pz - 2.2) / 0.8;
#                           } else {
#                               if (hit_id === 1) {
#                                   nx = (px - 0.9) / 0.95;
#                                   ny = (py - 0.1) / 0.95;
#                                   nz = (pz - 2.9) / 0.95;
#                               } else {
#                                   nx = 0.0;
#                                   ny = 1.0;
#                                   nz = 0.0;
#                               }
#                           }
#                           let diff = nx * -lx + ny * -ly + nz * -lz;
#                           diff = clamp01(diff);
#                           
#                           let base_r = 0.0;
#                           let base_g = 0.0;
#                           let base_b = 0.0;
#                           
#                           if (hit_id === 0) {
#                               base_r = 0.95;
#                               base_g = 0.35;
#                               base_b = 0.25;
#                           } else {
#                               if (hit_id === 1) {
#                                   base_r = 0.25;
#                                   base_g = 0.55;
#                                   base_b = 0.95;
#                               } else {
#                                   let checker = Math.trunc(Number((px + 50.0) * 0.8)) + Math.trunc(Number((pz + 50.0) * 0.8));
#                                   if (checker % 2 === 0) {
#                                       base_r = 0.85;
#                                       base_g = 0.85;
#                                       base_b = 0.85;
#                                   } else {
#                                       base_r = 0.2;
#                                       base_g = 0.2;
#                                       base_b = 0.2;
#                                   }
#                               }
#                           }
#                           let shade = 0.12 + 0.88 * diff;
#                           r = Math.trunc(Number(255.0 * clamp01(base_r * shade)));
#                           g = Math.trunc(Number(255.0 * clamp01(base_g * shade)));
#                           b = Math.trunc(Number(255.0 * clamp01(base_b * shade)));
#                       } else {
#                           let tsky = 0.5 * (dy + 1.0);
#                           r = Math.trunc(Number(255.0 * (0.65 + 0.20 * tsky)));
#                           g = Math.trunc(Number(255.0 * (0.75 + 0.18 * tsky)));
#                           b = Math.trunc(Number(255.0 * (0.90 + 0.08 * tsky)));
#                       }
#                       ar += r;
#                       ag += g;
#                       ab += b;
#                   }
#               }
#               let samples = aa * aa;
#               pixels.push(Math.floor(ar / samples));
#               pixels.push(Math.floor(ag / samples));
#               pixels.push(Math.floor(ab / samples));
#           }
#       }
#       return pixels;
#   }
#   
#   function run_raytrace() {
#       let width = 1600;
#       let height = 900;
#       let aa = 2;
#       let out_path = "sample/out/02_raytrace_spheres.png";
#       
#       let start = perf_counter();
#       let pixels = render(width, height, aa);
#       png.write_rgb_png(out_path, width, height, pixels);
#       let elapsed = perf_counter() - start;
#       
#       console.log("output:", out_path);
#       console.log("size:", width, "x", height);
#       console.log("elapsed_sec:", elapsed);
#   }
#   
#   run_raytrace();
@'

# PowerShell preview generated from JavaScript pseudo conversion.
    import * as math from "./runtime/js/generated/std/math.js"
    import * as png from "./runtime/js/generated/utils/png.js"
    import { perf_counter } from "./runtime/js/generated/std/time.js"
    
    # 02: Sample that runs a mini sphere-only ray tracer and outputs a PNG image.
    # Dependencies are kept minimal (time only) for transpilation compatibility.
    
    function clamp01 {
        param($v)
        if ($v  -$lt  0.0) {
            return 0.0
        }
        if ($v  -$gt  1.0) {
            return 1.0
        }
        return $v
    }
    
    function hit_sphere {
        param($ox, $oy, $oz, $dx, $dy, $dz, $cx, $cy, $cz, $r)
        $lx = $ox - $cx
        $ly = $oy - $cy
        $lz = $oz - $cz
    
        $a = $dx * $dx + $dy * $dy + $dz * $dz
        $b = 2.0 * ($lx * $dx + $ly * $dy + $lz * dz)
        $c = $lx * $lx + $ly * $ly + $lz * $lz - $r * $r
    
        $d = $b * $b - 4.0 * $a * $c
        if ($d  -$lt  0.0) {
            return -1.0
        }
        $sd = $math.sqrt(d)
        $t0 = (-$b - sd) / (2.0 * a)
        $t1 = (-$b + sd) / (2.0 * a)
    
        if ($t0  -$gt  0.001) {
            return $t0
        }
        if ($t1  -$gt  0.001) {
            return $t1
        }
        return -1.0
    }
    
    function render {
        param($width, $height, $aa)
        $pixels = @()
    
        // Camera origin
        $ox = 0.0
        $oy = 0.0
        $oz = -3.0
    
        // Light direction normalized
        $lx = -0.4
        $ly = 0.8
        $lz = -0.45
        $__hoisted_cast_1 = $__pytra_float $aa
        $__hoisted_cast_2 = $__pytra_float $height - 1
        $__hoisted_cast_3 = $__pytra_float $width - 1
        $__hoisted_cast_4 = $__pytra_float $height
    
        for ($y = 0; $y  -$lt  $height; $y += 1) {
            for ($x = 0; $x  -$lt  $width; $x += 1) {
                $ar = 0
                $ag = 0
                $ab = 0
    
                for ($ay = 0; $ay  -$lt  $aa; $ay += 1) {
                    for ($ax = 0; $ax  -$lt  $aa; $ax += 1) {
                        $fy = ($y + ($ay + 0.5) / __hoisted_cast_1) / $__hoisted_cast_2
                        $fx = ($x + ($ax + 0.5) / __hoisted_cast_1) / $__hoisted_cast_3
                        $sy = 1.0 - 2.0 * $fy
                        $sx = (2.0 * $fx - 1.0) * ($width / __hoisted_cast_4)
    
                        $dx = $sx
                        $dy = $sy
                        $dz = 1.0
                        $inv_len = 1.0 / $math.sqrt($dx * $dx + $dy * $dy + $dz * dz)
                        dx *= inv_len
                        dy *= inv_len
                        dz *= inv_len
    
                        $t_min = 1.0$e30
                        $hit_id = -1
    
                        $t = $hit_sphere $ox $oy $oz $dx $dy $dz -0.8 -0.2 2.2 0.8
                        if ($t  -$gt  0.0 -$and $t  -$lt  $t_min) {
                            t_min = t
                            hit_id = 0
                        }
                        t = hit_sphere ox oy oz dx dy dz 0.9 0.1 2.9 0.95
                        if ($t  -$gt  0.0 -$and $t  -$lt  $t_min) {
                            t_min = t
                            hit_id = 1
                        }
                        t = hit_sphere ox oy oz dx dy dz 0.0 -1001.0 3.0 1000.0
                        if ($t  -$gt  0.0 -$and $t  -$lt  $t_min) {
                            t_min = t
                            hit_id = 2
                        }
                        $r = 0
                        $g = 0
                        $b = 0
    
                        if ($hit_id  -$ge  0) {
                            $px = $ox + $dx * $t_min
                            $py = $oy + $dy * $t_min
                            $pz = $oz + $dz * $t_min
    
                            $nx = 0.0
                            $ny = 0.0
                            $nz = 0.0
    
                            if ($hit_id -$eq 0) {
                                nx = (px + 0.8) / 0.8
                                ny = (py + 0.2) / 0.8
                                nz = (pz - 2.2) / 0.8
                            } else {
                                if ($hit_id -$eq 1) {
                                    nx = (px - 0.9) / 0.95
                                    ny = (py - 0.1) / 0.95
                                    nz = (pz - 2.9) / 0.95
                                } else {
                                    nx = 0.0
                                    ny = 1.0
                                    nz = 0.0
                                }
                            }
                            $diff = $nx * -$lx + $ny * -$ly + $nz * -$lz
                            diff = clamp01 diff
    
                            $base_r = 0.0
                            $base_g = 0.0
                            $base_b = 0.0
    
                            if ($hit_id -$eq 0) {
                                base_r = 0.95
                                base_g = 0.35
                                base_b = 0.25
                            } else {
                                if ($hit_id -$eq 1) {
                                    base_r = 0.25
                                    base_g = 0.55
                                    base_b = 0.95
                                } else {
                                    $checker = [Math]::$Truncate Number(($px + 50.0 * 0.8)) + Math.trunc(__pytra_float ($pz + 50.0 * 0.8))
                                    if ($checker % 2 -$eq 0) {
                                        base_r = 0.85
                                        base_g = 0.85
                                        base_b = 0.85
                                    } else {
                                        base_r = 0.2
                                        base_g = 0.2
                                        base_b = 0.2
                                    }
                                }
                            }
                            $shade = 0.12 + 0.88 * $diff
                            r = Math.trunc(__pytra_float 255.0 * clamp01(base_r * shade))
                            g = Math.trunc(__pytra_float 255.0 * clamp01(base_g * shade))
                            b = Math.trunc(__pytra_float 255.0 * clamp01(base_b * shade))
                        } else {
                            $tsky = 0.5 * ($dy + 1.0)
                            r = Math.trunc(__pytra_float 255.0 * (0.65 + 0.20 * tsky))
                            g = Math.trunc(__pytra_float 255.0 * (0.75 + 0.18 * tsky))
                            b = Math.trunc(__pytra_float 255.0 * (0.90 + 0.08 * tsky))
                        }
                        ar += r
                        ag += g
                        ab += b
                    }
                }
                $samples = $aa * $aa
                pixels.push(Math.floor(ar / samples))
                pixels.push(Math.floor(ag / samples))
                pixels.push(Math.floor(ab / samples))
            }
        }
        return $pixels
    }
    
    function run_raytrace {
        param()
        $width = 1600
        $height = 900
        $aa = 2
        $out_path = "sample/out/02_raytrace_spheres.png"
    
        $start = $perf_counter
        $pixels = $render $width $height $aa
        png.write_rgb_png(out_path, width, height, pixels)
        $elapsed = $perf_counter - $start
    
        __pytra_print "output:" out_path
        __pytra_print "size:" width "x" height
        __pytra_print "elapsed_sec:" elapsed
    }
    
    run_raytrace

if (Get-Command -Name main -ErrorAction SilentlyContinue) {
    main
}
