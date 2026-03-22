const std = @import("std");
const pytra = @import("built_in/py_runtime.zig");
const time = @import("std/time.zig");
const perf_counter = time.perf_counter;
const png = @import("utils/png.zig");

// 03: Sample that outputs a Julia set as a PNG image.
// Implemented with simple loop-centric logic for transpilation compatibility.

fn render_julia(width: i64, height: i64, max_iter: i64, cx: f64, cy: f64) pytra.Obj {
    const pixels: pytra.Obj = pytra.bytearray(0);
    
    var y: i64 = 0;
    while (y < height) : (y += 1) {
        const zy0: f64 = (-1.2 + (2.4 * (@as(f64, @floatFromInt(y)) / @as(f64, @floatFromInt((height - 1))))));
        
        var x: i64 = 0;
        while (x < width) : (x += 1) {
            var zx: f64 = (-1.8 + (3.6 * (@as(f64, @floatFromInt(x)) / @as(f64, @floatFromInt((width - 1))))));
            var zy: f64 = zy0;
            
            var i: i64 = 0;
            while ((i < max_iter)) {
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
                const t: f64 = (@as(f64, @floatFromInt(i)) / @as(f64, @floatFromInt(max_iter)));
                r = @as(i64, @intFromFloat((255.0 * (0.2 + (0.8 * t)))));
                g = @as(i64, @intFromFloat((255.0 * (0.1 + (0.9 * (t * t))))));
                b = @as(i64, @intFromFloat((255.0 * (1.0 - t))));
            }
            pytra.list_append(pixels, u8, @intCast(r));
            pytra.list_append(pixels, u8, @intCast(g));
            pytra.list_append(pixels, u8, @intCast(b));
        }
    }
    return pixels;
}

fn run_julia() void {
    const width: i64 = 3840;
    const height: i64 = 2160;
    const max_iter: i64 = 20000;
    const out_path: []const u8 = "sample/out/03_julia_set.png";
    
    const start: f64 = pytra.perf_counter();
    const pixels: pytra.Obj = render_julia(width, height, max_iter, -0.8, 0.156);
    png.write_rgb_png(out_path, width, height, pixels);
    const elapsed: f64 = (pytra.perf_counter() - start);
    
    pytra.print2("output:", out_path);
    pytra.print("size:");
    pytra.print2("max_iter:", max_iter);
    pytra.print2("elapsed_sec:", elapsed);
}

pub fn main() void {
    run_julia();
}
