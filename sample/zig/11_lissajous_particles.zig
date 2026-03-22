const std = @import("std");
const pytra = @import("built_in/py_runtime.zig");
const math = @import("std/math.zig");
const time = @import("std/time.zig");
const perf_counter = time.perf_counter;
const gif = @import("utils/gif.zig");
const save_gif = gif.save_gif;

// 11: Sample that outputs Lissajous-motion particles as a GIF.

fn color_palette() pytra.Obj {
    const p: pytra.Obj = pytra.bytearray(0);
    var i: i64 = 0;
    while (i < 256) : (i += 1) {
        const r: i64 = i;
        const g: i64 = @mod((i * 3), 256);
        const b: i64 = (255 - i);
        pytra.list_append(p, u8, @intCast(r));
        pytra.list_append(p, u8, @intCast(g));
        pytra.list_append(p, u8, @intCast(b));
    }
    return p;
}

fn run_11_lissajous_particles() void {
    const w: i64 = 320;
    const h: i64 = 240;
    const frames_n: i64 = 360;
    const particles: i64 = 48;
    const out_path: []const u8 = "sample/out/11_lissajous_particles.gif";
    
    const start: f64 = pytra.perf_counter();
    const frames: pytra.Obj = pytra.list_from(pytra.Obj, &[_]pytra.Obj{  });
    
    var t: i64 = 0;
    while (t < frames_n) : (t += 1) {
        const frame: pytra.Obj = pytra.bytearray((w * h));
        
        var p: i64 = 0;
        while (p < particles) : (p += 1) {
            const phase: f64 = (@as(f64, @floatFromInt(p)) * 0.261799);
            const x: i64 = @as(i64, @intFromFloat(((@as(f64, @floatFromInt(w)) * 0.5) + ((@as(f64, @floatFromInt(w)) * 0.38) * math.sin(((0.11 * @as(f64, @floatFromInt(t))) + (phase * 2.0)))))));
            const y: i64 = @as(i64, @intFromFloat(((@as(f64, @floatFromInt(h)) * 0.5) + ((@as(f64, @floatFromInt(h)) * 0.38) * math.sin(((0.17 * @as(f64, @floatFromInt(t))) + (phase * 3.0)))))));
            const color: i64 = (30 + @mod((p * 9), 220));
            
            var dy: i64 = -2;
            while (dy < 3) : (dy += 1) {
                var dx: i64 = -2;
                while (dx < 3) : (dx += 1) {
                    const xx: i64 = (x + dx);
                    const yy: i64 = (y + dy);
                    if (((xx >= 0) and (xx < w) and (yy >= 0) and (yy < h))) {
                        const d2: i64 = ((dx * dx) + (dy * dy));
                        if ((d2 <= 4)) {
                            const idx: i64 = ((yy * w) + xx);
                            var v: i64 = (color - (d2 * 20));
                            v = @max(0, v);
                            if ((v > pytra.list_get(frame, u8, idx))) {
                                pytra.list_set(frame, u8, idx, @intCast(v));
                            }
                        }
                    }
                }
            }
        }
        pytra.list_append(frames, pytra.Obj, frame);
    }
    save_gif(out_path, w, h, frames, color_palette(), 3, 0);
    const elapsed: f64 = (pytra.perf_counter() - start);
    pytra.print2("output:", out_path);
    pytra.print2("frames:", frames_n);
    pytra.print2("elapsed_sec:", elapsed);
}

pub fn main() void {
    run_11_lissajous_particles();
}
