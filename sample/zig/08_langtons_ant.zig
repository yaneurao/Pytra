const std = @import("std");
const pytra = @import("built_in/py_runtime.zig");
const time = @import("std/time.zig");
const perf_counter = time.perf_counter;
const gif = @import("utils/gif.zig");
const grayscale_palette = gif.grayscale_palette;
const save_gif = gif.save_gif;

// 08: Sample that outputs Langton's Ant trajectories as a GIF.

fn capture(grid: pytra.Obj, w: i64, h: i64) pytra.Obj {
    const frame: pytra.Obj = pytra.bytearray((w * h));
    var y: i64 = 0;
    while (y < h) : (y += 1) {
        const row_base: i64 = (y * w);
        var x: i64 = 0;
        while (x < w) : (x += 1) {
            pytra.list_set(frame, u8, (row_base + x), @intCast(if ((pytra.list_get(pytra.list_get(grid, pytra.Obj, y), i64, x) != 0)) @as(i64, 255) else @as(i64, 0)));
        }
    }
    return frame;
}

fn run_08_langtons_ant() void {
    const w: i64 = 420;
    const h: i64 = 420;
    const out_path: []const u8 = "sample/out/08_langtons_ant.gif";
    
    const start: f64 = pytra.perf_counter();
    const grid: pytra.Obj = pytra.list_from(pytra.Obj, &[_]pytra.Obj{  });
    var _unused: i64 = 0;
    while (_unused < h) : (_unused += 1) {
        pytra.list_append(grid, pytra.Obj, __rep_blk_0: { const __rl = pytra.make_list(i64); var __ri: i64 = 0; while (__ri < w) : (__ri += 1) { pytra.list_append(__rl, i64, 0); } break :__rep_blk_0 __rl; });
    }
    var x: i64 = @divFloor(w, 2);
    var y: i64 = @divFloor(h, 2);
    var d: i64 = 0;
    
    const steps_total: i64 = 600000;
    const capture_every: i64 = 3000;
    const frames: pytra.Obj = pytra.list_from(pytra.Obj, &[_]pytra.Obj{  });
    
    var i: i64 = 0;
    while (i < steps_total) : (i += 1) {
        if ((pytra.list_get(pytra.list_get(grid, pytra.Obj, y), i64, x) == 0)) {
            d = @mod((d + 1), 4);
            pytra.list_set(pytra.list_get(grid, pytra.Obj, y), i64, x, @intCast(1));
        } else {
            d = @mod((d + 3), 4);
            pytra.list_set(pytra.list_get(grid, pytra.Obj, y), i64, x, @intCast(0));
        }
        if ((d == 0)) {
            y = @mod(((y - 1) + h), h);
        } else {
            if ((d == 1)) {
                x = @mod((x + 1), w);
            } else {
                if ((d == 2)) {
                    y = @mod((y + 1), h);
                } else {
                    x = @mod(((x - 1) + w), w);
                }
            }
        }
        if ((@mod(i, capture_every) == 0)) {
            pytra.list_append(frames, pytra.Obj, capture(grid, w, h));
        }
    }
    save_gif(out_path, w, h, frames, grayscale_palette(), 5, 0);
    const elapsed: f64 = (pytra.perf_counter() - start);
    pytra.print2("output:", out_path);
    pytra.print2("frames:", pytra.list_len(frames, pytra.Obj));
    pytra.print2("elapsed_sec:", elapsed);
}

pub fn main() void {
    run_08_langtons_ant();
}
