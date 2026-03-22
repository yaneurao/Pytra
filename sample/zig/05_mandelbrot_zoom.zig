const std = @import("std");
const pytra = @import("built_in/py_runtime.zig");
const time = @import("std/time.zig");
const perf_counter = time.perf_counter;
const gif = @import("utils/gif.zig");
const grayscale_palette = gif.grayscale_palette;
const save_gif = gif.save_gif;

// 05: Sample that outputs a Mandelbrot zoom as an animated GIF.

fn render_frame(width: i64, height: i64, center_x: f64, center_y: f64, scale: f64, max_iter: i64) pytra.Obj {
    const frame: pytra.Obj = pytra.bytearray((width * height));
    var y: i64 = 0;
    while (y < height) : (y += 1) {
        const row_base: i64 = (y * width);
        const cy: f64 = (center_y + ((@as(f64, @floatFromInt(y)) - (@as(f64, @floatFromInt(height)) * 0.5)) * scale));
        var x: i64 = 0;
        while (x < width) : (x += 1) {
            const cx: f64 = (center_x + ((@as(f64, @floatFromInt(x)) - (@as(f64, @floatFromInt(width)) * 0.5)) * scale));
            var zx: f64 = 0.0;
            var zy: f64 = 0.0;
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
            pytra.list_set(frame, u8, (row_base + x), @intCast(@as(i64, @intFromFloat(((255.0 * @as(f64, @floatFromInt(i))) / @as(f64, @floatFromInt(max_iter)))))));
        }
    }
    return frame;
}

fn run_05_mandelbrot_zoom() void {
    const width: i64 = 320;
    const height: i64 = 240;
    const frame_count: i64 = 48;
    const max_iter: i64 = 110;
    const center_x: f64 = -0.743643887037151;
    const center_y: f64 = 0.13182590420533;
    const base_scale: f64 = (3.2 / @as(f64, @floatFromInt(width)));
    const zoom_per_frame: f64 = 0.93;
    const out_path: []const u8 = "sample/out/05_mandelbrot_zoom.gif";
    
    const start: f64 = pytra.perf_counter();
    const frames: pytra.Obj = pytra.list_from(pytra.Obj, &[_]pytra.Obj{  });
    var scale: f64 = base_scale;
    var _unused: i64 = 0;
    while (_unused < frame_count) : (_unused += 1) {
        pytra.list_append(frames, pytra.Obj, render_frame(width, height, center_x, center_y, scale, max_iter));
        scale *= zoom_per_frame;
    }
    save_gif(out_path, width, height, frames, grayscale_palette(), 5, 0);
    const elapsed: f64 = (pytra.perf_counter() - start);
    pytra.print2("output:", out_path);
    pytra.print2("frames:", frame_count);
    pytra.print2("elapsed_sec:", elapsed);
}

pub fn main() void {
    run_05_mandelbrot_zoom();
}
