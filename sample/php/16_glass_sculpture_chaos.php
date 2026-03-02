<?php
declare(strict_types=1);

require_once __DIR__ . '/pytra/py_runtime.php';

// 16: Sample that ray-traces chaotic rotation of glass sculptures and outputs a GIF.
function clamp01($v) {
    if (($v < 0.0)) {
        return 0.0;
    }
    if (($v > 1.0)) {
        return 1.0;
    }
    return $v;
}

function dot($ax, $ay, $az, $bx, $by, $bz) {
    return ((($ax * $bx) + ($ay * $by)) + ($az * $bz));
}

function length($x, $y, $z) {
    return sqrt(((($x * $x) + ($y * $y)) + ($z * $z)));
}

function normalize($x, $y, $z) {
    $l = length($x, $y, $z);
    if (($l < 1e-09)) {
        return [0.0, 0.0, 0.0];
    }
    return [($x / $l), ($y / $l), ($z / $l)];
}

function reflect($ix, $iy, $iz, $nx, $ny, $nz) {
    $d = (dot($ix, $iy, $iz, $nx, $ny, $nz) * 2.0);
    return [($ix - ($d * $nx)), ($iy - ($d * $ny)), ($iz - ($d * $nz))];
}

function refract($ix, $iy, $iz, $nx, $ny, $nz, $eta) {
    $cosi = (-dot($ix, $iy, $iz, $nx, $ny, $nz));
    $sint2 = (($eta * $eta) * (1.0 - ($cosi * $cosi)));
    if (($sint2 > 1.0)) {
        return reflect($ix, $iy, $iz, $nx, $ny, $nz);
    }
    $cost = sqrt((1.0 - $sint2));
    $k = (($eta * $cosi) - $cost);
    return [(($eta * $ix) + ($k * $nx)), (($eta * $iy) + ($k * $ny)), (($eta * $iz) + ($k * $nz))];
}

function schlick($cos_theta, $f0) {
    $m = (1.0 - $cos_theta);
    return ($f0 + ((1.0 - $f0) * (((($m * $m) * $m) * $m) * $m)));
}

function sky_color($dx, $dy, $dz, $tphase) {
    $t = (0.5 * ($dy + 1.0));
    $r = (0.06 + (0.2 * $t));
    $g = (0.1 + (0.25 * $t));
    $b = (0.16 + (0.45 * $t));
    $band = (0.5 + (0.5 * sin((((8.0 * $dx) + (6.0 * $dz)) + $tphase))));
    $r += (0.08 * $band);
    $g += (0.05 * $band);
    $b += (0.12 * $band);
    return [clamp01($r), clamp01($g), clamp01($b)];
}

function sphere_intersect($ox, $oy, $oz, $dx, $dy, $dz, $cx, $cy, $cz, $radius) {
    $lx = ($ox - $cx);
    $ly = ($oy - $cy);
    $lz = ($oz - $cz);
    $b = ((($lx * $dx) + ($ly * $dy)) + ($lz * $dz));
    $c = (((($lx * $lx) + ($ly * $ly)) + ($lz * $lz)) - ($radius * $radius));
    $h = (($b * $b) - $c);
    if (($h < 0.0)) {
        return (-1.0);
    }
    $s = sqrt($h);
    $t0 = ((-$b) - $s);
    if (($t0 > 0.0001)) {
        return $t0;
    }
    $t1 = ((-$b) + $s);
    if (($t1 > 0.0001)) {
        return $t1;
    }
    return (-1.0);
}

function palette_332() {
    $p = bytearray((256 * 3));
    $__hoisted_cast_1 = ((float)(7));
    $__hoisted_cast_2 = ((float)(3));
    for ($i = 0; $i < 256; $i += 1) {
        $r = (($i + 5) + 7);
        $g = (($i + 2) + 7);
        $b = ($i + 3);
        $p[(($i * 3) + 0)] = ((int)(((255 * $r) / $__hoisted_cast_1)));
        $p[(($i * 3) + 1)] = ((int)(((255 * $g) / $__hoisted_cast_1)));
        $p[(($i * 3) + 2)] = ((int)(((255 * $b) / $__hoisted_cast_2)));
    }
    return bytes($p);
}

function quantize_332($r, $g, $b) {
    $rr = ((int)((clamp01($r) * 255.0)));
    $gg = ((int)((clamp01($g) * 255.0)));
    $bb = ((int)((clamp01($b) * 255.0)));
    return (((($rr + 5) + 5) + (($gg + 5) + 2)) + ($bb + 6));
}

function render_frame($width, $height, $frame_id, $frames_n) {
    $t = ($frame_id / $frames_n);
    $tphase = ((2.0 * M_PI) * $t);
    $cam_r = 3.0;
    $cam_x = ($cam_r * cos(($tphase * 0.9)));
    $cam_y = (1.1 + (0.25 * sin(($tphase * 0.6))));
    $cam_z = ($cam_r * sin(($tphase * 0.9)));
    $look_x = 0.0;
    $look_y = 0.35;
    $look_z = 0.0;
    $_ = normalize(($look_x - $cam_x), ($look_y - $cam_y), ($look_z - $cam_z));
    $_ = normalize($fwd_z, 0.0, (-$fwd_x));
    $_ = normalize((($right_y * $fwd_z) - ($right_z * $fwd_y)), (($right_z * $fwd_x) - ($right_x * $fwd_z)), (($right_x * $fwd_y) - ($right_y * $fwd_x)));
    $s0x = (0.9 * cos((1.3 * $tphase)));
    $s0y = (0.15 + (0.35 * sin((1.7 * $tphase))));
    $s0z = (0.9 * sin((1.3 * $tphase)));
    $s1x = (1.2 * cos(((1.3 * $tphase) + 2.094)));
    $s1y = (0.1 + (0.4 * sin(((1.1 * $tphase) + 0.8))));
    $s1z = (1.2 * sin(((1.3 * $tphase) + 2.094)));
    $s2x = (1.0 * cos(((1.3 * $tphase) + 4.188)));
    $s2y = (0.2 + (0.3 * sin(((1.5 * $tphase) + 1.9))));
    $s2z = (1.0 * sin(((1.3 * $tphase) + 4.188)));
    $lr = 0.35;
    $lx = (2.4 * cos(($tphase * 1.8)));
    $ly = (1.8 + (0.8 * sin(($tphase * 1.2))));
    $lz = (2.4 * sin(($tphase * 1.8)));
    $frame = bytearray(($width * $height));
    $aspect = ($width / $height);
    $fov = 1.25;
    $__hoisted_cast_3 = ((float)($height));
    $__hoisted_cast_4 = ((float)($width));
    for ($py = 0; $py < $height; $py += 1) {
        $row_base = ($py * $width);
        $sy = (1.0 - ((2.0 * ($py + 0.5)) / $__hoisted_cast_3));
        for ($px = 0; $px < $width; $px += 1) {
            $sx = ((((2.0 * ($px + 0.5)) / $__hoisted_cast_4) - 1.0) * $aspect);
            $rx = ($fwd_x + ($fov * (($sx * $right_x) + ($sy * $up_x))));
            $ry = ($fwd_y + ($fov * (($sx * $right_y) + ($sy * $up_y))));
            $rz = ($fwd_z + ($fov * (($sx * $right_z) + ($sy * $up_z))));
            $_ = normalize($rx, $ry, $rz);
            $best_t = 1000000000.0;
            $hit_kind = 0;
            $r = 0.0;
            $g = 0.0;
            $b = 0.0;
            if (($dy < (-1e-06))) {
                $tf = (((-1.2) - $cam_y) / $dy);
                if ((($tf > 0.0001) && ($tf < $best_t))) {
                    $best_t = $tf;
                    $hit_kind = 1;
                }
            }
            $t0 = sphere_intersect($cam_x, $cam_y, $cam_z, $dx, $dy, $dz, $s0x, $s0y, $s0z, 0.65);
            if ((($t0 > 0.0) && ($t0 < $best_t))) {
                $best_t = $t0;
                $hit_kind = 2;
            }
            $t1 = sphere_intersect($cam_x, $cam_y, $cam_z, $dx, $dy, $dz, $s1x, $s1y, $s1z, 0.72);
            if ((($t1 > 0.0) && ($t1 < $best_t))) {
                $best_t = $t1;
                $hit_kind = 3;
            }
            $t2 = sphere_intersect($cam_x, $cam_y, $cam_z, $dx, $dy, $dz, $s2x, $s2y, $s2z, 0.58);
            if ((($t2 > 0.0) && ($t2 < $best_t))) {
                $best_t = $t2;
                $hit_kind = 4;
            }
            if (($hit_kind == 0)) {
                $_ = sky_color($dx, $dy, $dz, $tphase);
            } else {
                if (($hit_kind == 1)) {
                    $hx = ($cam_x + ($best_t * $dx));
                    $hz = ($cam_z + ($best_t * $dz));
                    $cx = ((int)(floor(($hx * 2.0))));
                    $cz = ((int)(floor(($hz * 2.0))));
                    $checker = (((($cx + $cz) % 2) == 0) ? 0 : 1);
                    $base_r = (($checker == 0) ? 0.1 : 0.04);
                    $base_g = (($checker == 0) ? 0.11 : 0.05);
                    $base_b = (($checker == 0) ? 0.13 : 0.08);
                    $lxv = ($lx - $hx);
                    $lyv = ($ly - (-1.2));
                    $lzv = ($lz - $hz);
                    $_ = normalize($lxv, $lyv, $lzv);
                    $ndotl = max($ldy, 0.0);
                    $ldist2 = ((($lxv * $lxv) + ($lyv * $lyv)) + ($lzv * $lzv));
                    $glow = (8.0 / (1.0 + $ldist2));
                    $r = (($base_r + (0.8 * $glow)) + (0.2 * $ndotl));
                    $g = (($base_g + (0.5 * $glow)) + (0.18 * $ndotl));
                    $b = (($base_b + (1.0 * $glow)) + (0.24 * $ndotl));
                } else {
                    $cx = 0.0;
                    $cy = 0.0;
                    $cz = 0.0;
                    $rad = 1.0;
                    if (($hit_kind == 2)) {
                        $cx = $s0x;
                        $cy = $s0y;
                        $cz = $s0z;
                        $rad = 0.65;
                    } else {
                        if (($hit_kind == 3)) {
                            $cx = $s1x;
                            $cy = $s1y;
                            $cz = $s1z;
                            $rad = 0.72;
                        } else {
                            $cx = $s2x;
                            $cy = $s2y;
                            $cz = $s2z;
                            $rad = 0.58;
                        }
                    }
                    $hx = ($cam_x + ($best_t * $dx));
                    $hy = ($cam_y + ($best_t * $dy));
                    $hz = ($cam_z + ($best_t * $dz));
                    $_ = normalize((($hx - $cx) / $rad), (($hy - $cy) / $rad), (($hz - $cz) / $rad));
                    $_ = reflect($dx, $dy, $dz, $nx, $ny, $nz);
                    $_ = refract($dx, $dy, $dz, $nx, $ny, $nz, (1.0 / 1.45));
                    $_ = sky_color($rdx, $rdy, $rdz, $tphase);
                    $_ = sky_color($tdx, $tdy, $tdz, ($tphase + 0.8));
                    $cosi = max((-((($dx * $nx) + ($dy * $ny)) + ($dz * $nz))), 0.0);
                    $fr = schlick($cosi, 0.04);
                    $r = (($tr * (1.0 - $fr)) + ($sr * $fr));
                    $g = (($tg * (1.0 - $fr)) + ($sg * $fr));
                    $b = (($tb * (1.0 - $fr)) + ($sb * $fr));
                    $lxv = ($lx - $hx);
                    $lyv = ($ly - $hy);
                    $lzv = ($lz - $hz);
                    $_ = normalize($lxv, $lyv, $lzv);
                    $ndotl = max(((($nx * $ldx) + ($ny * $ldy)) + ($nz * $ldz)), 0.0);
                    $_ = normalize(($ldx - $dx), ($ldy - $dy), ($ldz - $dz));
                    $ndoth = max(((($nx * $hvx) + ($ny * $hvy)) + ($nz * $hvz)), 0.0);
                    $spec = ($ndoth * $ndoth);
                    $spec = ($spec * $spec);
                    $spec = ($spec * $spec);
                    $spec = ($spec * $spec);
                    $glow = (10.0 / (((1.0 + ($lxv * $lxv)) + ($lyv * $lyv)) + ($lzv * $lzv)));
                    $r += (((0.2 * $ndotl) + (0.8 * $spec)) + (0.45 * $glow));
                    $g += (((0.18 * $ndotl) + (0.6 * $spec)) + (0.35 * $glow));
                    $b += (((0.26 * $ndotl) + (1.0 * $spec)) + (0.65 * $glow));
                    if (($hit_kind == 2)) {
                        $r *= 0.95;
                        $g *= 1.05;
                        $b *= 1.1;
                    } else {
                        if (($hit_kind == 3)) {
                            $r *= 1.08;
                            $g *= 0.98;
                            $b *= 1.04;
                        } else {
                            $r *= 1.02;
                            $g *= 1.1;
                            $b *= 0.95;
                        }
                    }
                }
            }
            $r = sqrt(clamp01($r));
            $g = sqrt(clamp01($g));
            $b = sqrt(clamp01($b));
            $frame[($row_base + $px)] = quantize_332($r, $g, $b);
        }
    }
    return bytes($frame);
}

function run_16_glass_sculpture_chaos() {
    $width = 320;
    $height = 240;
    $frames_n = 72;
    $out_path = "sample/out/16_glass_sculpture_chaos.gif";
    $start = __pytra_perf_counter();
    $frames = [];
    for ($i = 0; $i < $frames_n; $i += 1) {
        $frames[] = render_frame($width, $height, $i, $frames_n);
    }
    __pytra_noop($out_path, $width, $height, $frames, palette_332());
    $elapsed = (__pytra_perf_counter() - $start);
    __pytra_print("output:", $out_path);
    __pytra_print("frames:", $frames_n);
    __pytra_print("elapsed_sec:", $elapsed);
}

function __pytra_main(): void {
    run_16_glass_sculpture_chaos();
}

__pytra_main();
