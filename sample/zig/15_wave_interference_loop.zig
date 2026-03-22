const std = @import("std");
const pytra = @import("built_in/py_runtime.zig");
const math = @import("std/math.zig");
const time = @import("std/time.zig");
const perf_counter = time.perf_counter;
const gif = @import("utils/gif.zig");
const grayscale_palette = gif.grayscale_palette;
const save_gif = gif.save_gif;

// 15: Sample that renders wave interference animation and writes a GIF.

fn run_15_wave_interference_loop() void {
    const w: i64 = 320;
    const h: i64 = 240;
    const frames_n: i64 = 96;
    const out_path: []const u8 = "sample/out/15_wave_interference_loop.gif";
    
    const start: f64 = pytra.perf_counter();
    const frames: pytra.Obj = pytra.list_from(pytra.Obj, &[_]pytra.Obj{  });
    
    var t: i64 = 0;
    while (t < frames_n) : (t += 1) {
        const frame: pytra.Obj = pytra.bytearray((w * h));
        const phase: f64 = (@as(f64, @floatFromInt(t)) * 0.12);
        var y: i64 = 0;
        while (y < h) : (y += 1) {
            const row_base: i64 = (y * w);
            var x: i64 = 0;
            while (x < w) : (x += 1) {
                const dx: i64 = (x - 160);
                const dy: i64 = (y - 120);
                const v: f64 = (((math.sin(((@as(f64, @floatFromInt(x)) + (@as(f64, @floatFromInt(t)) * 1.5)) * 0.045)) + math.sin(((@as(f64, @floatFromInt(y)) - (@as(f64, @floatFromInt(t)) * 1.2)) * 0.04))) + math.sin(((@as(f64, @floatFromInt((x + y))) * 0.02) + phase))) + math.sin(((math.sqrt(@as(f64, @floatFromInt(((dx * dx) + (dy * dy))))) * 0.08) - (phase * 1.3))));
                var c: i64 = @as(i64, @intFromFloat(((v + 4.0) * (255.0 / 8.0))));
                if ((c < 0)) {
                    c = 0;
                }
                if ((c > 255)) {
                    c = 255;
                }
                pytra.list_set(frame, u8, (row_base + x), @intCast(c));
            }
        }
        pytra.list_append(frames, pytra.Obj, frame);
    }
    save_gif(out_path, w, h, frames, grayscale_palette(), 4, 0);
    const elapsed: f64 = (pytra.perf_counter() - start);
    pytra.print2("output:", out_path);
    pytra.print2("frames:", frames_n);
    pytra.print2("elapsed_sec:", elapsed);
}

pub fn main() void {
    run_15_wave_interference_loop();
}
