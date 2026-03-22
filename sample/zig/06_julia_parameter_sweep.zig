const std = @import("std");
const pytra = @import("built_in/py_runtime.zig");
const math = @import("std/math.zig");
const time = @import("std/time.zig");
const perf_counter = time.perf_counter;
const gif = @import("utils/gif.zig");
const save_gif = gif.save_gif;

// 06: Sample that sweeps Julia-set parameters and outputs a GIF.

fn julia_palette() pytra.Obj {
    // Keep index 0 black for points inside the set; build a high-saturation gradient for the rest.
    const palette: pytra.Obj = pytra.bytearray((256 * 3));
    pytra.list_set(palette, u8, 0, @intCast(0));
    pytra.list_set(palette, u8, 1, @intCast(0));
    pytra.list_set(palette, u8, 2, @intCast(0));
    var i: i64 = 1;
    while (i < 256) : (i += 1) {
        const t: f64 = (@as(f64, @floatFromInt((i - 1))) / 254.0);
        const r: i64 = @as(i64, @intFromFloat((255.0 * ((((9.0 * (1.0 - t)) * t) * t) * t))));
        const g: i64 = @as(i64, @intFromFloat((255.0 * ((((15.0 * (1.0 - t)) * (1.0 - t)) * t) * t))));
        const b: i64 = @as(i64, @intFromFloat((255.0 * ((((8.5 * (1.0 - t)) * (1.0 - t)) * (1.0 - t)) * t))));
        pytra.list_set(palette, u8, ((i * 3) + 0), @intCast(r));
        pytra.list_set(palette, u8, ((i * 3) + 1), @intCast(g));
        pytra.list_set(palette, u8, ((i * 3) + 2), @intCast(b));
    }
    return palette;
}

fn render_frame(width: i64, height: i64, cr: f64, ci: f64, max_iter: i64, phase: i64) pytra.Obj {
    const frame: pytra.Obj = pytra.bytearray((width * height));
    var y: i64 = 0;
    while (y < height) : (y += 1) {
        const row_base: i64 = (y * width);
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
                zy = (((2.0 * zx) * zy) + ci);
                zx = ((zx2 - zy2) + cr);
                i += 1;
            }
            if ((i >= max_iter)) {
                pytra.list_set(frame, u8, (row_base + x), @intCast(0));
            } else {
                // Add a small frame phase so colors flow smoothly.
                const color_index: i64 = (1 + @mod((@divFloor((i * 224), max_iter) + phase), 255));
                pytra.list_set(frame, u8, (row_base + x), @intCast(color_index));
            }
        }
    }
    return frame;
}

fn run_06_julia_parameter_sweep() void {
    const width: i64 = 320;
    const height: i64 = 240;
    const frames_n: i64 = 72;
    const max_iter: i64 = 180;
    const out_path: []const u8 = "sample/out/06_julia_parameter_sweep.gif";
    
    const start: f64 = pytra.perf_counter();
    const frames: pytra.Obj = pytra.list_from(pytra.Obj, &[_]pytra.Obj{  });
    // Orbit an ellipse around a known visually good region to reduce flat blown highlights.
    const center_cr: f64 = -0.745;
    const center_ci: f64 = 0.186;
    const radius_cr: f64 = 0.12;
    const radius_ci: f64 = 0.1;
    // Add start and phase offsets so GitHub thumbnails do not appear too dark.
    // Tune it to start in a red-leaning color range.
    const start_offset: i64 = 20;
    const phase_offset: i64 = 180;
    var i: i64 = 0;
    while (i < frames_n) : (i += 1) {
        const t: f64 = (@as(f64, @floatFromInt(@mod((i + start_offset), frames_n))) / @as(f64, @floatFromInt(frames_n)));
        const angle: f64 = ((2.0 * math.pi) * t);
        const cr: f64 = (center_cr + (radius_cr * math.cos(angle)));
        const ci: f64 = (center_ci + (radius_ci * math.sin(angle)));
        const phase: i64 = @mod((phase_offset + (i * 5)), 255);
        pytra.list_append(frames, pytra.Obj, render_frame(width, height, cr, ci, max_iter, phase));
    }
    save_gif(out_path, width, height, frames, julia_palette(), 8, 0);
    const elapsed: f64 = (pytra.perf_counter() - start);
    pytra.print2("output:", out_path);
    pytra.print2("frames:", frames_n);
    pytra.print2("elapsed_sec:", elapsed);
}

pub fn main() void {
    run_06_julia_parameter_sweep();
}
