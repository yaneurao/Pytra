const std = @import("std");
const pytra = @import("built_in/py_runtime.zig");
const time = @import("std/time.zig");
const perf_counter = time.perf_counter;
const png = @import("utils/png.zig");
const Tuple0 = struct { _0: i64, _1: i64, _2: i64 };

// 01: Sample that outputs the Mandelbrot set as a PNG image.
// Syntax is kept straightforward with future transpilation in mind.

fn escape_count(cx: f64, cy: f64, max_iter: i64) i64 {
    var x: f64 = 0.0;
    var y: f64 = 0.0;
    var i: i64 = 0;
    while (i < max_iter) : (i += 1) {
        const x2: f64 = (x * x);
        const y2: f64 = (y * y);
        if (((x2 + y2) > 4.0)) {
            return i;
        }
        y = (((2.0 * x) * y) + cy);
        x = ((x2 - y2) + cx);
    }
    return max_iter;
}

fn color_map(iter_count: i64, max_iter: i64) Tuple0 {
    if ((iter_count >= max_iter)) {
        return .{ ._0 = 0, ._1 = 0, ._2 = 0 };
    }
    const t: f64 = (@as(f64, @floatFromInt(iter_count)) / @as(f64, @floatFromInt(max_iter)));
    const r: i64 = @as(i64, @intFromFloat((255.0 * (t * t))));
    const g: i64 = @as(i64, @intFromFloat((255.0 * t)));
    const b: i64 = @as(i64, @intFromFloat((255.0 * (1.0 - t))));
    return .{ ._0 = r, ._1 = g, ._2 = b };
}

fn render_mandelbrot(width: i64, height: i64, max_iter: i64, x_min: f64, x_max: f64, y_min: f64, y_max: f64) pytra.Obj {
    const pixels: pytra.Obj = pytra.bytearray(0);
    
    var y: i64 = 0;
    while (y < height) : (y += 1) {
        const py: f64 = (y_min + ((y_max - y_min) * (@as(f64, @floatFromInt(y)) / @as(f64, @floatFromInt((height - 1))))));
        
        var x: i64 = 0;
        while (x < width) : (x += 1) {
            const px: f64 = (x_min + ((x_max - x_min) * (@as(f64, @floatFromInt(x)) / @as(f64, @floatFromInt((width - 1))))));
            const it: i64 = escape_count(px, py, max_iter);
            var r: i64 = undefined;
            var g: i64 = undefined;
            var b: i64 = undefined;
            if ((it >= max_iter)) {
                r = 0;
                g = 0;
                b = 0;
            } else {
                const t: f64 = (@as(f64, @floatFromInt(it)) / @as(f64, @floatFromInt(max_iter)));
                r = @as(i64, @intFromFloat((255.0 * (t * t))));
                g = @as(i64, @intFromFloat((255.0 * t)));
                b = @as(i64, @intFromFloat((255.0 * (1.0 - t))));
            }
            pytra.list_append(pixels, u8, @intCast(r));
            pytra.list_append(pixels, u8, @intCast(g));
            pytra.list_append(pixels, u8, @intCast(b));
        }
    }
    return pixels;
}

fn run_mandelbrot() void {
    const width: i64 = 1600;
    const height: i64 = 1200;
    const max_iter: i64 = 1000;
    const out_path: []const u8 = "sample/out/01_mandelbrot.png";
    
    const start: f64 = pytra.perf_counter();
    
    const pixels: pytra.Obj = render_mandelbrot(width, height, max_iter, -2.2, 1.0, -1.2, 1.2);
    png.write_rgb_png(out_path, width, height, pixels);
    
    const elapsed: f64 = (pytra.perf_counter() - start);
    pytra.print2("output:", out_path);
    pytra.print("size:");
    pytra.print2("max_iter:", max_iter);
    pytra.print2("elapsed_sec:", elapsed);
}

pub fn main() void {
    run_mandelbrot();
}
