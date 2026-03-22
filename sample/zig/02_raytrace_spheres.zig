const std = @import("std");
const pytra = @import("built_in/py_runtime.zig");
const math = @import("std/math.zig");
const png = @import("utils/png.zig");
const time = @import("std/time.zig");
const perf_counter = time.perf_counter;

// 02: Sample that runs a mini sphere-only ray tracer and outputs a PNG image.
// Dependencies are kept minimal (time only) for transpilation compatibility.

fn clamp01(v: f64) f64 {
    if ((v < 0.0)) {
        return 0.0;
    }
    if ((v > 1.0)) {
        return 1.0;
    }
    return v;
}

fn hit_sphere(ox: f64, oy: f64, oz: f64, dx: f64, dy: f64, dz: f64, cx: f64, cy: f64, cz: f64, r: f64) f64 {
    const lx: f64 = (ox - cx);
    const ly: f64 = (oy - cy);
    const lz: f64 = (oz - cz);
    
    const a: f64 = (((dx * dx) + (dy * dy)) + (dz * dz));
    const b: f64 = (2.0 * (((lx * dx) + (ly * dy)) + (lz * dz)));
    const c: f64 = ((((lx * lx) + (ly * ly)) + (lz * lz)) - (r * r));
    
    const d: f64 = ((b * b) - ((4.0 * a) * c));
    if ((d < 0.0)) {
        return -1.0;
    }
    const sd: f64 = math.sqrt(d);
    const t0: f64 = ((-b - sd) / (2.0 * a));
    const t1: f64 = ((-b + sd) / (2.0 * a));
    
    if ((t0 > 0.001)) {
        return t0;
    }
    if ((t1 > 0.001)) {
        return t1;
    }
    return -1.0;
}

fn render(width: i64, height: i64, aa: i64) pytra.Obj {
    const pixels: pytra.Obj = pytra.bytearray(0);
    
    // Camera origin
    const ox: f64 = 0.0;
    const oy: f64 = 0.0;
    const oz: f64 = -3.0;
    
    // Light direction (normalized)
    const lx: f64 = -0.4;
    const ly: f64 = 0.8;
    const lz: f64 = -0.45;
    
    var y: i64 = 0;
    while (y < height) : (y += 1) {
        var x: i64 = 0;
        while (x < width) : (x += 1) {
            var ar: i64 = 0;
            var ag: i64 = 0;
            var ab: i64 = 0;
            
            var ay: i64 = 0;
            while (ay < aa) : (ay += 1) {
                var ax: i64 = 0;
                while (ax < aa) : (ax += 1) {
                    const fy: f64 = ((@as(f64, @floatFromInt(y)) + ((@as(f64, @floatFromInt(ay)) + 0.5) / @as(f64, @floatFromInt(aa)))) / @as(f64, @floatFromInt((height - 1))));
                    const fx: f64 = ((@as(f64, @floatFromInt(x)) + ((@as(f64, @floatFromInt(ax)) + 0.5) / @as(f64, @floatFromInt(aa)))) / @as(f64, @floatFromInt((width - 1))));
                    const sy: f64 = (1.0 - (2.0 * fy));
                    const sx: f64 = (((2.0 * fx) - 1.0) * (@as(f64, @floatFromInt(width)) / @as(f64, @floatFromInt(height))));
                    
                    var dx: f64 = sx;
                    var dy: f64 = sy;
                    var dz: f64 = 1.0;
                    const inv_len: f64 = (1.0 / math.sqrt((((dx * dx) + (dy * dy)) + (dz * dz))));
                    dx *= inv_len;
                    dy *= inv_len;
                    dz *= inv_len;
                    
                    var t_min: f64 = 1e+30;
                    var hit_id: i64 = -1;
                    
                    var t: f64 = hit_sphere(ox, oy, oz, dx, dy, dz, -0.8, -0.2, 2.2, 0.8);
                    if (((t > 0.0) and (t < t_min))) {
                        t_min = t;
                        hit_id = 0;
                    }
                    t = hit_sphere(ox, oy, oz, dx, dy, dz, 0.9, 0.1, 2.9, 0.95);
                    if (((t > 0.0) and (t < t_min))) {
                        t_min = t;
                        hit_id = 1;
                    }
                    t = hit_sphere(ox, oy, oz, dx, dy, dz, 0.0, -1001.0, 3.0, 1000.0);
                    if (((t > 0.0) and (t < t_min))) {
                        t_min = t;
                        hit_id = 2;
                    }
                    var r: i64 = 0;
                    var g: i64 = 0;
                    var b: i64 = 0;
                    
                    if ((hit_id >= 0)) {
                        const px: f64 = (ox + (dx * t_min));
                        const py: f64 = (oy + (dy * t_min));
                        const pz: f64 = (oz + (dz * t_min));
                        
                        var nx: f64 = 0.0;
                        var ny: f64 = 0.0;
                        var nz: f64 = 0.0;
                        
                        if ((hit_id == 0)) {
                            nx = ((px + 0.8) / 0.8);
                            ny = ((py + 0.2) / 0.8);
                            nz = ((pz - 2.2) / 0.8);
                        } else {
                            if ((hit_id == 1)) {
                                nx = ((px - 0.9) / 0.95);
                                ny = ((py - 0.1) / 0.95);
                                nz = ((pz - 2.9) / 0.95);
                            } else {
                                nx = 0.0;
                                ny = 1.0;
                                nz = 0.0;
                            }
                        }
                        var diff: f64 = (((nx * -lx) + (ny * -ly)) + (nz * -lz));
                        diff = clamp01(diff);
                        
                        var base_r: f64 = 0.0;
                        var base_g: f64 = 0.0;
                        var base_b: f64 = 0.0;
                        
                        if ((hit_id == 0)) {
                            base_r = 0.95;
                            base_g = 0.35;
                            base_b = 0.25;
                        } else {
                            if ((hit_id == 1)) {
                                base_r = 0.25;
                                base_g = 0.55;
                                base_b = 0.95;
                            } else {
                                const checker: i64 = (@as(i64, @intFromFloat(((px + 50.0) * 0.8))) + @as(i64, @intFromFloat(((pz + 50.0) * 0.8))));
                                if ((@mod(checker, 2) == 0)) {
                                    base_r = 0.85;
                                    base_g = 0.85;
                                    base_b = 0.85;
                                } else {
                                    base_r = 0.2;
                                    base_g = 0.2;
                                    base_b = 0.2;
                                }
                            }
                        }
                        const shade: f64 = (0.12 + (0.88 * diff));
                        r = @as(i64, @intFromFloat((255.0 * clamp01((base_r * shade)))));
                        g = @as(i64, @intFromFloat((255.0 * clamp01((base_g * shade)))));
                        b = @as(i64, @intFromFloat((255.0 * clamp01((base_b * shade)))));
                    } else {
                        const tsky: f64 = (0.5 * (dy + 1.0));
                        r = @as(i64, @intFromFloat((255.0 * (0.65 + (0.2 * tsky)))));
                        g = @as(i64, @intFromFloat((255.0 * (0.75 + (0.18 * tsky)))));
                        b = @as(i64, @intFromFloat((255.0 * (0.9 + (0.08 * tsky)))));
                    }
                    ar += r;
                    ag += g;
                    ab += b;
                }
            }
            const samples: i64 = (aa * aa);
            pytra.list_append(pixels, u8, @intCast(@divFloor(ar, samples)));
            pytra.list_append(pixels, u8, @intCast(@divFloor(ag, samples)));
            pytra.list_append(pixels, u8, @intCast(@divFloor(ab, samples)));
        }
    }
    return pixels;
}

fn run_raytrace() void {
    const width: i64 = 1600;
    const height: i64 = 900;
    const aa: i64 = 2;
    const out_path: []const u8 = "sample/out/02_raytrace_spheres.png";
    
    const start: f64 = pytra.perf_counter();
    const pixels: pytra.Obj = render(width, height, aa);
    png.write_rgb_png(out_path, width, height, pixels);
    const elapsed: f64 = (pytra.perf_counter() - start);
    
    pytra.print2("output:", out_path);
    pytra.print("size:");
    pytra.print2("elapsed_sec:", elapsed);
}

pub fn main() void {
    run_raytrace();
}
