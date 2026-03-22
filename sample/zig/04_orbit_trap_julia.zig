const std = @import("std");
const pytra = @import("built_in/py_runtime.zig");
const time = @import("std/time.zig");
const perf_counter = time.perf_counter;
const png = @import("utils/png.zig");

// 04: Sample that renders an orbit-trap Julia set and writes a PNG image.

fn render_orbit_trap_julia(width: i64, height: i64, max_iter: i64, cx: f64, cy: f64) pytra.Obj {
    const pixels: pytra.Obj = pytra.bytearray(0);
    
    var y: i64 = 0;
    while (y < height) : (y += 1) {
        const zy0: f64 = (-1.3 + (2.6 * (@as(f64, @floatFromInt(y)) / @as(f64, @floatFromInt((height - 1))))));
        var x: i64 = 0;
        while (x < width) : (x += 1) {
            var zx: f64 = (-1.9 + (3.8 * (@as(f64, @floatFromInt(x)) / @as(f64, @floatFromInt((width - 1))))));
            var zy: f64 = zy0;
            
            var trap: f64 = 1000000000.0;
            var i: i64 = 0;
            while ((i < max_iter)) {
                var ax: f64 = zx;
                if ((ax < 0.0)) {
                    ax = -ax;
                }
                var ay: f64 = zy;
                if ((ay < 0.0)) {
                    ay = -ay;
                }
                var dxy: f64 = (zx - zy);
                if ((dxy < 0.0)) {
                    dxy = -dxy;
                }
                if ((ax < trap)) {
                    trap = ax;
                }
                if ((ay < trap)) {
                    trap = ay;
                }
                if ((dxy < trap)) {
                    trap = dxy;
                }
                const zx2: f64 = (zx * zx);
                const zy2: f64 = (zy * zy);
                if (((zx2 + zy2) > 4.0)) {
                    break;
                }
                zy = (((2.0 * zx) * zy) + cy);
                zx = ((zx2 - zy2) + cx);
                i += 1;
            }
            var r: i64 = 0;
            var g: i64 = 0;
            var b: i64 = 0;
            if ((i >= max_iter)) {
                r = 0;
                g = 0;
                b = 0;
            } else {
                var trap_scaled: f64 = (trap * 3.2);
                if ((trap_scaled > 1.0)) {
                    trap_scaled = 1.0;
                }
                if ((trap_scaled < 0.0)) {
                    trap_scaled = 0.0;
                }
                const t: f64 = (@as(f64, @floatFromInt(i)) / @as(f64, @floatFromInt(max_iter)));
                const tone: i64 = @as(i64, @intFromFloat((255.0 * (1.0 - trap_scaled))));
                r = @as(i64, @intFromFloat((@as(f64, @floatFromInt(tone)) * (0.35 + (0.65 * t)))));
                g = @as(i64, @intFromFloat((@as(f64, @floatFromInt(tone)) * (0.15 + (0.85 * (1.0 - t))))));
                b = @as(i64, @intFromFloat((255.0 * (0.25 + (0.75 * t)))));
                if ((r > 255)) {
                    r = 255;
                }
                if ((g > 255)) {
                    g = 255;
                }
                if ((b > 255)) {
                    b = 255;
                }
            }
            pytra.list_append(pixels, u8, @intCast(r));
            pytra.list_append(pixels, u8, @intCast(g));
            pytra.list_append(pixels, u8, @intCast(b));
        }
    }
    return pixels;
}

fn run_04_orbit_trap_julia() void {
    const width: i64 = 1920;
    const height: i64 = 1080;
    const max_iter: i64 = 1400;
    const out_path: []const u8 = "sample/out/04_orbit_trap_julia.png";
    
    const start: f64 = pytra.perf_counter();
    const pixels: pytra.Obj = render_orbit_trap_julia(width, height, max_iter, -0.7269, 0.1889);
    png.write_rgb_png(out_path, width, height, pixels);
    const elapsed: f64 = (pytra.perf_counter() - start);
    
    pytra.print2("output:", out_path);
    pytra.print("size:");
    pytra.print2("max_iter:", max_iter);
    pytra.print2("elapsed_sec:", elapsed);
}

pub fn main() void {
    run_04_orbit_trap_julia();
}
