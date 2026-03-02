<?php
declare(strict_types=1);

require_once __DIR__ . '/pytra/py_runtime.php';

// 02: Sample that runs a mini sphere-only ray tracer and outputs a PNG image.
// Dependencies are kept minimal (time only) for transpilation compatibility.
function clamp01($v) {
    if (($v < 0.0)) {
        return 0.0;
    }
    if (($v > 1.0)) {
        return 1.0;
    }
    return $v;
}

function hit_sphere($ox, $oy, $oz, $dx, $dy, $dz, $cx, $cy, $cz, $r) {
    $lx = ($ox - $cx);
    $ly = ($oy - $cy);
    $lz = ($oz - $cz);
    $a = ((($dx * $dx) + ($dy * $dy)) + ($dz * $dz));
    $b = (2.0 * ((($lx * $dx) + ($ly * $dy)) + ($lz * $dz)));
    $c = (((($lx * $lx) + ($ly * $ly)) + ($lz * $lz)) - ($r * $r));
    $d = (($b * $b) - ((4.0 * $a) * $c));
    if (($d < 0.0)) {
        return (-1.0);
    }
    $sd = sqrt($d);
    $t0 = (((-$b) - $sd) / (2.0 * $a));
    $t1 = (((-$b) + $sd) / (2.0 * $a));
    if (($t0 > 0.001)) {
        return $t0;
    }
    if (($t1 > 0.001)) {
        return $t1;
    }
    return (-1.0);
}

function render($width, $height, $aa) {
    $pixels = bytearray();
    $ox = 0.0;
    $oy = 0.0;
    $oz = (-3.0);
    $lx = (-0.4);
    $ly = 0.8;
    $lz = (-0.45);
    $__hoisted_cast_1 = ((float)($aa));
    $__hoisted_cast_2 = ((float)(($height - 1)));
    $__hoisted_cast_3 = ((float)(($width - 1)));
    $__hoisted_cast_4 = ((float)($height));
    for ($y = 0; $y < $height; $y += 1) {
        for ($x = 0; $x < $width; $x += 1) {
            $ar = 0;
            $ag = 0;
            $ab = 0;
            for ($ay = 0; $ay < $aa; $ay += 1) {
                for ($ax = 0; $ax < $aa; $ax += 1) {
                    $fy = (($y + (($ay + 0.5) / $__hoisted_cast_1)) / $__hoisted_cast_2);
                    $fx = (($x + (($ax + 0.5) / $__hoisted_cast_1)) / $__hoisted_cast_3);
                    $sy = (1.0 - (2.0 * $fy));
                    $sx = (((2.0 * $fx) - 1.0) * ($width / $__hoisted_cast_4));
                    $dx = $sx;
                    $dy = $sy;
                    $dz = 1.0;
                    $inv_len = (1.0 / sqrt(((($dx * $dx) + ($dy * $dy)) + ($dz * $dz))));
                    $dx *= $inv_len;
                    $dy *= $inv_len;
                    $dz *= $inv_len;
                    $t_min = 1e+30;
                    $hit_id = (-1);
                    $t = hit_sphere($ox, $oy, $oz, $dx, $dy, $dz, (-0.8), (-0.2), 2.2, 0.8);
                    if ((($t > 0.0) && ($t < $t_min))) {
                        $t_min = $t;
                        $hit_id = 0;
                    }
                    $t = hit_sphere($ox, $oy, $oz, $dx, $dy, $dz, 0.9, 0.1, 2.9, 0.95);
                    if ((($t > 0.0) && ($t < $t_min))) {
                        $t_min = $t;
                        $hit_id = 1;
                    }
                    $t = hit_sphere($ox, $oy, $oz, $dx, $dy, $dz, 0.0, (-1001.0), 3.0, 1000.0);
                    if ((($t > 0.0) && ($t < $t_min))) {
                        $t_min = $t;
                        $hit_id = 2;
                    }
                    $r = 0;
                    $g = 0;
                    $b = 0;
                    if (($hit_id >= 0)) {
                        $px = ($ox + ($dx * $t_min));
                        $py = ($oy + ($dy * $t_min));
                        $pz = ($oz + ($dz * $t_min));
                        $nx = 0.0;
                        $ny = 0.0;
                        $nz = 0.0;
                        if (($hit_id == 0)) {
                            $nx = (($px + 0.8) / 0.8);
                            $ny = (($py + 0.2) / 0.8);
                            $nz = (($pz - 2.2) / 0.8);
                        } else {
                            if (($hit_id == 1)) {
                                $nx = (($px - 0.9) / 0.95);
                                $ny = (($py - 0.1) / 0.95);
                                $nz = (($pz - 2.9) / 0.95);
                            } else {
                                $nx = 0.0;
                                $ny = 1.0;
                                $nz = 0.0;
                            }
                        }
                        $diff = ((($nx * (-$lx)) + ($ny * (-$ly))) + ($nz * (-$lz)));
                        $diff = clamp01($diff);
                        $base_r = 0.0;
                        $base_g = 0.0;
                        $base_b = 0.0;
                        if (($hit_id == 0)) {
                            $base_r = 0.95;
                            $base_g = 0.35;
                            $base_b = 0.25;
                        } else {
                            if (($hit_id == 1)) {
                                $base_r = 0.25;
                                $base_g = 0.55;
                                $base_b = 0.95;
                            } else {
                                $checker = (((int)((($px + 50.0) * 0.8))) + ((int)((($pz + 50.0) * 0.8))));
                                if ((($checker % 2) == 0)) {
                                    $base_r = 0.85;
                                    $base_g = 0.85;
                                    $base_b = 0.85;
                                } else {
                                    $base_r = 0.2;
                                    $base_g = 0.2;
                                    $base_b = 0.2;
                                }
                            }
                        }
                        $shade = (0.12 + (0.88 * $diff));
                        $r = ((int)((255.0 * clamp01(($base_r * $shade)))));
                        $g = ((int)((255.0 * clamp01(($base_g * $shade)))));
                        $b = ((int)((255.0 * clamp01(($base_b * $shade)))));
                    } else {
                        $tsky = (0.5 * ($dy + 1.0));
                        $r = ((int)((255.0 * (0.65 + (0.2 * $tsky)))));
                        $g = ((int)((255.0 * (0.75 + (0.18 * $tsky)))));
                        $b = ((int)((255.0 * (0.9 + (0.08 * $tsky)))));
                    }
                    $ar += $r;
                    $ag += $g;
                    $ab += $b;
                }
            }
            $samples = ($aa * $aa);
            $pixels[] = intdiv($ar, $samples);
            $pixels[] = intdiv($ag, $samples);
            $pixels[] = intdiv($ab, $samples);
        }
    }
    return $pixels;
}

function run_raytrace() {
    $width = 1600;
    $height = 900;
    $aa = 2;
    $out_path = "sample/out/02_raytrace_spheres.png";
    $start = __pytra_perf_counter();
    $pixels = render($width, $height, $aa);
    __pytra_noop($out_path, $width, $height, $pixels);
    $elapsed = (__pytra_perf_counter() - $start);
    __pytra_print("output:", $out_path);
    __pytra_print("size:", $width, "x", $height);
    __pytra_print("elapsed_sec:", $elapsed);
}

function __pytra_main(): void {
    run_raytrace();
}

__pytra_main();
