const std = @import("std");
const pytra = @import("built_in/py_runtime.zig");
const math = @import("std/math.zig");
const time = @import("std/time.zig");
const perf_counter = time.perf_counter;
const gif = @import("utils/gif.zig");
const Tuple0 = struct { _0: f64, _1: f64, _2: f64 };
const save_gif = gif.save_gif;

// 16: Sample that ray-traces chaotic rotation of glass sculptures and outputs a GIF.

fn clamp01(v: f64) f64 {
    if ((v < 0.0)) {
        return 0.0;
    }
    if ((v > 1.0)) {
        return 1.0;
    }
    return v;
}

fn dot(ax: f64, ay: f64, az: f64, bx: f64, by: f64, bz: f64) f64 {
    return (((ax * bx) + (ay * by)) + (az * bz));
}

fn length(x: f64, y: f64, z: f64) f64 {
    return math.sqrt((((x * x) + (y * y)) + (z * z)));
}

fn normalize(x: f64, y: f64, z: f64) Tuple0 {
    const l: f64 = length(x, y, z);
    if ((l < 1e-09)) {
        return .{ ._0 = 0.0, ._1 = 0.0, ._2 = 0.0 };
    }
    return .{ ._0 = (x / l), ._1 = (y / l), ._2 = (z / l) };
}

fn reflect(ix: f64, iy: f64, iz: f64, nx: f64, ny: f64, nz: f64) Tuple0 {
    const d: f64 = (dot(ix, iy, iz, nx, ny, nz) * 2.0);
    return .{ ._0 = (ix - (d * nx)), ._1 = (iy - (d * ny)), ._2 = (iz - (d * nz)) };
}

fn refract(ix: f64, iy: f64, iz: f64, nx: f64, ny: f64, nz: f64, eta: f64) Tuple0 {
    // Simple IOR-based refraction. Return reflection direction on total internal reflection.
    const cosi: f64 = -dot(ix, iy, iz, nx, ny, nz);
    const sint2: f64 = ((eta * eta) * (1.0 - (cosi * cosi)));
    if ((sint2 > 1.0)) {
        return reflect(ix, iy, iz, nx, ny, nz);
    }
    const cost: f64 = math.sqrt((1.0 - sint2));
    const k: f64 = ((eta * cosi) - cost);
    return .{ ._0 = ((eta * ix) + (k * nx)), ._1 = ((eta * iy) + (k * ny)), ._2 = ((eta * iz) + (k * nz)) };
}

fn schlick(cos_theta: f64, f0: f64) f64 {
    const m: f64 = (1.0 - cos_theta);
    return (f0 + ((1.0 - f0) * ((((m * m) * m) * m) * m)));
}

fn sky_color(dx: f64, dy: f64, dz: f64, tphase: f64) Tuple0 {
    // Sky gradient + neon band
    const t: f64 = (0.5 * (dy + 1.0));
    var r: f64 = (0.06 + (0.2 * t));
    var g: f64 = (0.1 + (0.25 * t));
    var b: f64 = (0.16 + (0.45 * t));
    const band: f64 = (0.5 + (0.5 * math.sin((((8.0 * dx) + (6.0 * dz)) + tphase))));
    r += (0.08 * band);
    g += (0.05 * band);
    b += (0.12 * band);
    return .{ ._0 = clamp01(r), ._1 = clamp01(g), ._2 = clamp01(b) };
}

fn sphere_intersect(ox: f64, oy: f64, oz: f64, dx: f64, dy: f64, dz: f64, cx: f64, cy: f64, cz: f64, radius: f64) f64 {
    const lx: f64 = (ox - cx);
    const ly: f64 = (oy - cy);
    const lz: f64 = (oz - cz);
    const b: f64 = (((lx * dx) + (ly * dy)) + (lz * dz));
    const c: f64 = ((((lx * lx) + (ly * ly)) + (lz * lz)) - (radius * radius));
    const h: f64 = ((b * b) - c);
    if ((h < 0.0)) {
        return -1.0;
    }
    const s: f64 = math.sqrt(h);
    const t0: f64 = (-b - s);
    if ((t0 > 0.0001)) {
        return t0;
    }
    const t1: f64 = (-b + s);
    if ((t1 > 0.0001)) {
        return t1;
    }
    return -1.0;
}

fn palette_332() pytra.Obj {
    // 3-3-2 quantized palette. Lightweight quantization that stays fast after transpilation.
    const p: pytra.Obj = pytra.bytearray((256 * 3));
    var i: i64 = 0;
    while (i < 256) : (i += 1) {
        const r: i64 = ((@as(i64, i) >> @intCast(5)) & 7);
        const g: i64 = ((@as(i64, i) >> @intCast(2)) & 7);
        const b: i64 = (i & 3);
        pytra.list_set(p, u8, ((i * 3) + 0), @intCast(@as(i64, @intFromFloat((@as(f64, @floatFromInt((255 * r))) / @as(f64, @floatFromInt(7)))))));
        pytra.list_set(p, u8, ((i * 3) + 1), @intCast(@as(i64, @intFromFloat((@as(f64, @floatFromInt((255 * g))) / @as(f64, @floatFromInt(7)))))));
        pytra.list_set(p, u8, ((i * 3) + 2), @intCast(@as(i64, @intFromFloat((@as(f64, @floatFromInt((255 * b))) / @as(f64, @floatFromInt(3)))))));
    }
    return p;
}

fn quantize_332(r: f64, g: f64, b: f64) i64 {
    const rr: i64 = @as(i64, @intFromFloat((clamp01(r) * 255.0)));
    const gg: i64 = @as(i64, @intFromFloat((clamp01(g) * 255.0)));
    const bb: i64 = @as(i64, @intFromFloat((clamp01(b) * 255.0)));
    return (((@as(i64, (@as(i64, rr) >> @intCast(5))) << @intCast(5)) + (@as(i64, (@as(i64, gg) >> @intCast(5))) << @intCast(2))) + (@as(i64, bb) >> @intCast(6)));
}

fn render_frame(width: i64, height: i64, frame_id: i64, frames_n: i64) pytra.Obj {
    const t: f64 = (@as(f64, @floatFromInt(frame_id)) / @as(f64, @floatFromInt(frames_n)));
    const tphase: f64 = ((2.0 * math.pi) * t);
    
    // Camera slowly orbits.
    const cam_r: f64 = 3.0;
    const cam_x: f64 = (cam_r * math.cos((tphase * 0.9)));
    const cam_y: f64 = (1.1 + (0.25 * math.sin((tphase * 0.6))));
    const cam_z: f64 = (cam_r * math.sin((tphase * 0.9)));
    const look_x: f64 = 0.0;
    const look_y: f64 = 0.35;
    const look_z: f64 = 0.0;
    
    const __tmp_0 = normalize((look_x - cam_x), (look_y - cam_y), (look_z - cam_z));
    const fwd_x = __tmp_0._0;
    const fwd_y = __tmp_0._1;
    const fwd_z = __tmp_0._2;
    const __tmp_1 = normalize(fwd_z, 0.0, -fwd_x);
    const right_x = __tmp_1._0;
    const right_y = __tmp_1._1;
    const right_z = __tmp_1._2;
    const __tmp_2 = normalize(((right_y * fwd_z) - (right_z * fwd_y)), ((right_z * fwd_x) - (right_x * fwd_z)), ((right_x * fwd_y) - (right_y * fwd_x)));
    const up_x = __tmp_2._0;
    const up_y = __tmp_2._1;
    const up_z = __tmp_2._2;
    
    // Moving glass sculpture (3 spheres) and an emissive sphere.
    const s0x: f64 = (0.9 * math.cos((1.3 * tphase)));
    const s0y: f64 = (0.15 + (0.35 * math.sin((1.7 * tphase))));
    const s0z: f64 = (0.9 * math.sin((1.3 * tphase)));
    const s1x: f64 = (1.2 * math.cos(((1.3 * tphase) + 2.094)));
    const s1y: f64 = (0.1 + (0.4 * math.sin(((1.1 * tphase) + 0.8))));
    const s1z: f64 = (1.2 * math.sin(((1.3 * tphase) + 2.094)));
    const s2x: f64 = (1.0 * math.cos(((1.3 * tphase) + 4.188)));
    const s2y: f64 = (0.2 + (0.3 * math.sin(((1.5 * tphase) + 1.9))));
    const s2z: f64 = (1.0 * math.sin(((1.3 * tphase) + 4.188)));
    const lr: f64 = 0.35;
    _ = lr;
    const lx: f64 = (2.4 * math.cos((tphase * 1.8)));
    const ly: f64 = (1.8 + (0.8 * math.sin((tphase * 1.2))));
    const lz: f64 = (2.4 * math.sin((tphase * 1.8)));
    
    const frame: pytra.Obj = pytra.bytearray((width * height));
    const aspect: f64 = (@as(f64, @floatFromInt(width)) / @as(f64, @floatFromInt(height)));
    const fov: f64 = 1.25;
    
    var py: i64 = 0;
    while (py < height) : (py += 1) {
        const row_base: i64 = (py * width);
        const sy: f64 = (1.0 - ((2.0 * (@as(f64, @floatFromInt(py)) + 0.5)) / @as(f64, @floatFromInt(height))));
        var px: i64 = 0;
        while (px < width) : (px += 1) {
            const sx: f64 = ((((2.0 * (@as(f64, @floatFromInt(px)) + 0.5)) / @as(f64, @floatFromInt(width))) - 1.0) * aspect);
            const rx: f64 = (fwd_x + (fov * ((sx * right_x) + (sy * up_x))));
            const ry: f64 = (fwd_y + (fov * ((sx * right_y) + (sy * up_y))));
            const rz: f64 = (fwd_z + (fov * ((sx * right_z) + (sy * up_z))));
            const __tmp_3 = normalize(rx, ry, rz);
            const dx = __tmp_3._0;
            const dy = __tmp_3._1;
            const dz = __tmp_3._2;
            
            // Search for the nearest hit.
            var best_t: f64 = 1000000000.0;
            var hit_kind: i64 = 0;
            var r: f64 = 0.0;
            var g: f64 = 0.0;
            var b: f64 = 0.0;
            
            // Floor plane y=-1.2
            if ((dy < -1e-06)) {
                const tf: f64 = ((-1.2 - cam_y) / dy);
                if (((tf > 0.0001) and (tf < best_t))) {
                    best_t = tf;
                    hit_kind = 1;
                }
            }
            const t0: f64 = sphere_intersect(cam_x, cam_y, cam_z, dx, dy, dz, s0x, s0y, s0z, 0.65);
            if (((t0 > 0.0) and (t0 < best_t))) {
                best_t = t0;
                hit_kind = 2;
            }
            const t1: f64 = sphere_intersect(cam_x, cam_y, cam_z, dx, dy, dz, s1x, s1y, s1z, 0.72);
            if (((t1 > 0.0) and (t1 < best_t))) {
                best_t = t1;
                hit_kind = 3;
            }
            const t2: f64 = sphere_intersect(cam_x, cam_y, cam_z, dx, dy, dz, s2x, s2y, s2z, 0.58);
            if (((t2 > 0.0) and (t2 < best_t))) {
                best_t = t2;
                hit_kind = 4;
            }
            var glow: f64 = undefined;
            var hx: f64 = undefined;
            var hz: f64 = undefined;
            var ldx: f64 = undefined;
            var ldy: f64 = undefined;
            var ldz: f64 = undefined;
            var lxv: f64 = undefined;
            var lyv: f64 = undefined;
            var lzv: f64 = undefined;
            var ndotl: f64 = undefined;
            if ((hit_kind == 0)) {
                const __tmp_4 = sky_color(dx, dy, dz, tphase);
                r = __tmp_4._0;
                g = __tmp_4._1;
                b = __tmp_4._2;
            } else {
                if ((hit_kind == 1)) {
                    hx = (cam_x + (best_t * dx));
                    hz = (cam_z + (best_t * dz));
                    const cx_i: i64 = @as(i64, @intFromFloat(math.floor((hx * 2.0))));
                    const cz_i: i64 = @as(i64, @intFromFloat(math.floor((hz * 2.0))));
                    const checker: i64 = if ((@mod((cx_i + cz_i), 2) == 0)) @as(i64, 0) else @as(i64, 1);
                    const base_r: f64 = if ((checker == 0)) 0.1 else 0.04;
                    const base_g: f64 = if ((checker == 0)) 0.11 else 0.05;
                    const base_b: f64 = if ((checker == 0)) 0.13 else 0.08;
                    // Emissive sphere contribution.
                    lxv = (lx - hx);
                    lyv = (ly - -1.2);
                    lzv = (lz - hz);
                    const __tmp_5 = normalize(lxv, lyv, lzv);
                    ldx = __tmp_5._0;
                    ldy = __tmp_5._1;
                    ldz = __tmp_5._2;
                    ndotl = @max(ldy, 0.0);
                    const ldist2: f64 = (((lxv * lxv) + (lyv * lyv)) + (lzv * lzv));
                    glow = (8.0 / (1.0 + ldist2));
                    r = ((base_r + (0.8 * glow)) + (0.2 * ndotl));
                    g = ((base_g + (0.5 * glow)) + (0.18 * ndotl));
                    b = ((base_b + (1.0 * glow)) + (0.24 * ndotl));
                } else {
                    var cx: f64 = 0.0;
                    var cy: f64 = 0.0;
                    var cz: f64 = 0.0;
                    var rad: f64 = 1.0;
                    if ((hit_kind == 2)) {
                        cx = s0x;
                        cy = s0y;
                        cz = s0z;
                        rad = 0.65;
                    } else {
                        if ((hit_kind == 3)) {
                            cx = s1x;
                            cy = s1y;
                            cz = s1z;
                            rad = 0.72;
                        } else {
                            cx = s2x;
                            cy = s2y;
                            cz = s2z;
                            rad = 0.58;
                        }
                    }
                    hx = (cam_x + (best_t * dx));
                    const hy: f64 = (cam_y + (best_t * dy));
                    hz = (cam_z + (best_t * dz));
                    const __tmp_6 = normalize(((hx - cx) / rad), ((hy - cy) / rad), ((hz - cz) / rad));
                    const nx = __tmp_6._0;
                    const ny = __tmp_6._1;
                    const nz = __tmp_6._2;
                    
                    // Simple glass shading (reflection + refraction + light highlights).
                    const __tmp_7 = reflect(dx, dy, dz, nx, ny, nz);
                    const rdx = __tmp_7._0;
                    const rdy = __tmp_7._1;
                    const rdz = __tmp_7._2;
                    const __tmp_8 = refract(dx, dy, dz, nx, ny, nz, (1.0 / 1.45));
                    const tdx = __tmp_8._0;
                    const tdy = __tmp_8._1;
                    const tdz = __tmp_8._2;
                    const __tmp_9 = sky_color(rdx, rdy, rdz, tphase);
                    const sr = __tmp_9._0;
                    const sg = __tmp_9._1;
                    const sb = __tmp_9._2;
                    const __tmp_10 = sky_color(tdx, tdy, tdz, (tphase + 0.8));
                    const tr = __tmp_10._0;
                    const tg = __tmp_10._1;
                    const tb = __tmp_10._2;
                    const cosi: f64 = @max(-(((dx * nx) + (dy * ny)) + (dz * nz)), 0.0);
                    const fr: f64 = schlick(cosi, 0.04);
                    r = ((tr * (1.0 - fr)) + (sr * fr));
                    g = ((tg * (1.0 - fr)) + (sg * fr));
                    b = ((tb * (1.0 - fr)) + (sb * fr));
                    
                    lxv = (lx - hx);
                    lyv = (ly - hy);
                    lzv = (lz - hz);
                    const __tmp_11 = normalize(lxv, lyv, lzv);
                    ldx = __tmp_11._0;
                    ldy = __tmp_11._1;
                    ldz = __tmp_11._2;
                    ndotl = @max((((nx * ldx) + (ny * ldy)) + (nz * ldz)), 0.0);
                    const __tmp_12 = normalize((ldx - dx), (ldy - dy), (ldz - dz));
                    const hvx = __tmp_12._0;
                    const hvy = __tmp_12._1;
                    const hvz = __tmp_12._2;
                    const ndoth: f64 = @max((((nx * hvx) + (ny * hvy)) + (nz * hvz)), 0.0);
                    var spec: f64 = (ndoth * ndoth);
                    spec = (spec * spec);
                    spec = (spec * spec);
                    spec = (spec * spec);
                    glow = (10.0 / (((1.0 + (lxv * lxv)) + (lyv * lyv)) + (lzv * lzv)));
                    r += (((0.2 * ndotl) + (0.8 * spec)) + (0.45 * glow));
                    g += (((0.18 * ndotl) + (0.6 * spec)) + (0.35 * glow));
                    b += (((0.26 * ndotl) + (1.0 * spec)) + (0.65 * glow));
                    
                    // Slight tint variation per sphere.
                    if ((hit_kind == 2)) {
                        r *= 0.95;
                        g *= 1.05;
                        b *= 1.1;
                    } else {
                        if ((hit_kind == 3)) {
                            r *= 1.08;
                            g *= 0.98;
                            b *= 1.04;
                        } else {
                            r *= 1.02;
                            g *= 1.1;
                            b *= 0.95;
                        }
                    }
                }
            }
            // Slightly stronger tone mapping.
            r = math.sqrt(clamp01(r));
            g = math.sqrt(clamp01(g));
            b = math.sqrt(clamp01(b));
            pytra.list_set(frame, u8, (row_base + px), @intCast(quantize_332(r, g, b)));
        }
    }
    return frame;
}

fn run_16_glass_sculpture_chaos() void {
    const width: i64 = 320;
    const height: i64 = 240;
    const frames_n: i64 = 72;
    const out_path: []const u8 = "sample/out/16_glass_sculpture_chaos.gif";
    
    const start: f64 = pytra.perf_counter();
    const frames: pytra.Obj = pytra.list_from(pytra.Obj, &[_]pytra.Obj{  });
    var i: i64 = 0;
    while (i < frames_n) : (i += 1) {
        pytra.list_append(frames, pytra.Obj, render_frame(width, height, i, frames_n));
    }
    save_gif(out_path, width, height, frames, palette_332(), 6, 0);
    const elapsed: f64 = (pytra.perf_counter() - start);
    pytra.print2("output:", out_path);
    pytra.print2("frames:", frames_n);
    pytra.print2("elapsed_sec:", elapsed);
}

pub fn main() void {
    run_16_glass_sculpture_chaos();
}
