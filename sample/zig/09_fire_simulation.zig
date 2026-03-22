const std = @import("std");
const pytra = @import("built_in/py_runtime.zig");
const time = @import("std/time.zig");
const perf_counter = time.perf_counter;
const gif = @import("utils/gif.zig");
const save_gif = gif.save_gif;

// 09: Sample that outputs a simple fire effect as a GIF.

fn fire_palette() pytra.Obj {
    const p: pytra.Obj = pytra.bytearray(0);
    var i: i64 = 0;
    while (i < 256) : (i += 1) {
        var r: i64 = 0;
        var g: i64 = 0;
        var b: i64 = 0;
        if ((i < 85)) {
            r = (i * 3);
            g = 0;
            b = 0;
        } else {
            if ((i < 170)) {
                r = 255;
                g = ((i - 85) * 3);
                b = 0;
            } else {
                r = 255;
                g = 255;
                b = ((i - 170) * 3);
            }
        }
        pytra.list_append(p, u8, @intCast(r));
        pytra.list_append(p, u8, @intCast(g));
        pytra.list_append(p, u8, @intCast(b));
    }
    return p;
}

fn run_09_fire_simulation() void {
    const w: i64 = 380;
    const h: i64 = 260;
    const steps: i64 = 420;
    const out_path: []const u8 = "sample/out/09_fire_simulation.gif";
    
    const start: f64 = pytra.perf_counter();
    const heat: pytra.Obj = pytra.list_from(pytra.Obj, &[_]pytra.Obj{  });
    var _unused: i64 = 0;
    while (_unused < h) : (_unused += 1) {
        pytra.list_append(heat, pytra.Obj, __rep_blk_0: { const __rl = pytra.make_list(i64); var __ri: i64 = 0; while (__ri < w) : (__ri += 1) { pytra.list_append(__rl, i64, 0); } break :__rep_blk_0 __rl; });
    }
    const frames: pytra.Obj = pytra.list_from(pytra.Obj, &[_]pytra.Obj{  });
    
    var t: i64 = 0;
    while (t < steps) : (t += 1) {
        var x: i64 = undefined;
        x = 0;
        while (x < w) : (x += 1) {
            const val: i64 = (170 + @mod(((x * 13) + (t * 17)), 86));
            pytra.list_set(pytra.list_get(heat, pytra.Obj, (h - 1)), i64, x, @intCast(val));
        }
        var y: i64 = 1;
        while (y < h) : (y += 1) {
            x = 0;
            while (x < w) : (x += 1) {
                const a: i64 = pytra.list_get(pytra.list_get(heat, pytra.Obj, y), i64, x);
                const b: i64 = pytra.list_get(pytra.list_get(heat, pytra.Obj, y), i64, @mod(((x - 1) + w), w));
                const c: i64 = pytra.list_get(pytra.list_get(heat, pytra.Obj, y), i64, @mod((x + 1), w));
                const d: i64 = pytra.list_get(pytra.list_get(heat, pytra.Obj, @mod((y + 1), h)), i64, x);
                const v: i64 = @divFloor((((a + b) + c) + d), 4);
                const cool: i64 = (1 + @mod(((x + y) + t), 3));
                const nv: i64 = (v - cool);
                pytra.list_set(pytra.list_get(heat, pytra.Obj, (y - 1)), i64, x, @intCast(if ((nv > 0)) nv else @as(i64, 0)));
            }
        }
        const frame: pytra.Obj = pytra.bytearray((w * h));
        var yy: i64 = 0;
        while (yy < h) : (yy += 1) {
            const row_base: i64 = (yy * w);
            var xx: i64 = 0;
            while (xx < w) : (xx += 1) {
                pytra.list_set(frame, u8, (row_base + xx), @intCast(pytra.list_get(pytra.list_get(heat, pytra.Obj, yy), i64, xx)));
            }
        }
        pytra.list_append(frames, pytra.Obj, frame);
    }
    save_gif(out_path, w, h, frames, fire_palette(), 4, 0);
    const elapsed: f64 = (pytra.perf_counter() - start);
    pytra.print2("output:", out_path);
    pytra.print2("frames:", steps);
    pytra.print2("elapsed_sec:", elapsed);
}

pub fn main() void {
    run_09_fire_simulation();
}
