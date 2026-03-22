const std = @import("std");
const pytra = @import("built_in/py_runtime.zig");
const time = @import("std/time.zig");
const perf_counter = time.perf_counter;
const gif = @import("utils/gif.zig");
const grayscale_palette = gif.grayscale_palette;
const save_gif = gif.save_gif;

// 12: Sample that outputs intermediate states of bubble sort as a GIF.

fn render(values: pytra.Obj, w: i64, h: i64) pytra.Obj {
    const frame: pytra.Obj = pytra.bytearray((w * h));
    const n: i64 = pytra.list_len(values, i64);
    const bar_w: f64 = (@as(f64, @floatFromInt(w)) / @as(f64, @floatFromInt(n)));
    var i: i64 = 0;
    while (i < n) : (i += 1) {
        const x0: i64 = @as(i64, @intFromFloat((@as(f64, @floatFromInt(i)) * bar_w)));
        var x1: i64 = @as(i64, @intFromFloat((@as(f64, @floatFromInt((i + 1))) * bar_w)));
        if ((x1 <= x0)) {
            x1 = (x0 + 1);
        }
        const bh: i64 = @as(i64, @intFromFloat(((@as(f64, @floatFromInt(pytra.list_get(values, i64, i))) / @as(f64, @floatFromInt(n))) * @as(f64, @floatFromInt(h)))));
        var y: i64 = (h - bh);
        y = y;
        while (y < h) : (y += 1) {
            var x: i64 = x0;
            while (x < x1) : (x += 1) {
                pytra.list_set(frame, u8, ((y * w) + x), @intCast(255));
            }
        }
    }
    return frame;
}

fn run_12_sort_visualizer() void {
    const w: i64 = 320;
    const h: i64 = 180;
    const n: i64 = 124;
    const out_path: []const u8 = "sample/out/12_sort_visualizer.gif";
    
    const start: f64 = pytra.perf_counter();
    const values: pytra.Obj = pytra.list_from(i64, &[_]i64{  });
    var i: i64 = undefined;
    i = 0;
    while (i < n) : (i += 1) {
        pytra.list_append(values, i64, @intCast(@mod(((i * 37) + 19), n)));
    }
    const frames: pytra.Obj = pytra.list_from(pytra.Obj, &[_]pytra.Obj{ render(values, w, h) });
    const frame_stride: i64 = 16;
    
    var op: i64 = 0;
    i = 0;
    while (i < n) : (i += 1) {
        var swapped: bool = false;
        var j: i64 = 0;
        while (j < ((n - i) - 1)) : (j += 1) {
            if ((pytra.list_get(values, i64, j) > pytra.list_get(values, i64, (j + 1)))) {
                const __swap_tmp_0 = pytra.list_get(values, i64, j);
                pytra.list_set(values, i64, j, pytra.list_get(values, i64, (j + 1)));
                pytra.list_set(values, i64, (j + 1), __swap_tmp_0);
                swapped = true;
            }
            if ((@mod(op, frame_stride) == 0)) {
                pytra.list_append(frames, pytra.Obj, render(values, w, h));
            }
            op += 1;
        }
        if (!swapped) {
            break;
        }
    }
    save_gif(out_path, w, h, frames, grayscale_palette(), 3, 0);
    const elapsed: f64 = (pytra.perf_counter() - start);
    pytra.print2("output:", out_path);
    pytra.print2("frames:", pytra.list_len(frames, pytra.Obj));
    pytra.print2("elapsed_sec:", elapsed);
}

pub fn main() void {
    run_12_sort_visualizer();
}
