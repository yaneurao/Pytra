const std = @import("std");
const pytra = @import("built_in/py_runtime.zig");
const math = @import("std/math.zig");
const time = @import("std/time.zig");
const perf_counter = time.perf_counter;
const gif = @import("utils/gif.zig");
const save_gif = gif.save_gif;

// 14: Sample that outputs a moving-light scene in a simple raymarching style as a GIF.

fn palette() pytra.Obj {
    const p: pytra.Obj = pytra.bytearray(0);
    var i: i64 = 0;
    while (i < 256) : (i += 1) {
        const r: i64 = @min(255, @as(i64, @intFromFloat((@as(f64, @floatFromInt(20)) + (@as(f64, @floatFromInt(i)) * 0.9)))));
        const g: i64 = @min(255, @as(i64, @intFromFloat((@as(f64, @floatFromInt(10)) + (@as(f64, @floatFromInt(i)) * 0.7)))));
        const b: i64 = @min(255, (30 + i));
        pytra.list_append(p, u8, @intCast(r));
        pytra.list_append(p, u8, @intCast(g));
        pytra.list_append(p, u8, @intCast(b));
    }
    return p;
}

fn scene(x: f64, y: f64, light_x: f64, light_y: f64) i64 {
    const x1: f64 = (x + 0.45);
    const y1: f64 = (y + 0.2);
    const x2: f64 = (x - 0.35);
    const y2: f64 = (y - 0.15);
    const r1: f64 = math.sqrt(((x1 * x1) + (y1 * y1)));
    const r2: f64 = math.sqrt(((x2 * x2) + (y2 * y2)));
    const blob: f64 = (math.exp(((-7.0 * r1) * r1)) + math.exp(((-8.0 * r2) * r2)));
    
    const lx: f64 = (x - light_x);
    const ly: f64 = (y - light_y);
    const l: f64 = math.sqrt(((lx * lx) + (ly * ly)));
    const lit: f64 = (1.0 / (1.0 + ((3.5 * l) * l)));
    
    const v: i64 = @as(i64, @intFromFloat((((255.0 * blob) * lit) * 5.0)));
    return @min(255, @max(0, v));
}

fn run_14_raymarching_light_cycle() void {
    const w: i64 = 320;
    const h: i64 = 240;
    const frames_n: i64 = 84;
    const out_path: []const u8 = "sample/out/14_raymarching_light_cycle.gif";
    
    const start: f64 = pytra.perf_counter();
    const frames: pytra.Obj = pytra.list_from(pytra.Obj, &[_]pytra.Obj{  });
    
    var t: i64 = 0;
    while (t < frames_n) : (t += 1) {
        const frame: pytra.Obj = pytra.bytearray((w * h));
        const a: f64 = (((@as(f64, @floatFromInt(t)) / @as(f64, @floatFromInt(frames_n))) * math.pi) * 2.0);
        const light_x: f64 = (0.75 * math.cos(a));
        const light_y: f64 = (0.55 * math.sin((a * 1.2)));
        
        var y: i64 = 0;
        while (y < h) : (y += 1) {
            const row_base: i64 = (y * w);
            const py: f64 = (((@as(f64, @floatFromInt(y)) / @as(f64, @floatFromInt((h - 1)))) * 2.0) - 1.0);
            var x: i64 = 0;
            while (x < w) : (x += 1) {
                const px: f64 = (((@as(f64, @floatFromInt(x)) / @as(f64, @floatFromInt((w - 1)))) * 2.0) - 1.0);
                pytra.list_set(frame, u8, (row_base + x), @intCast(scene(px, py, light_x, light_y)));
            }
        }
        pytra.list_append(frames, pytra.Obj, frame);
    }
    save_gif(out_path, w, h, frames, palette(), 3, 0);
    const elapsed: f64 = (pytra.perf_counter() - start);
    pytra.print2("output:", out_path);
    pytra.print2("frames:", frames_n);
    pytra.print2("elapsed_sec:", elapsed);
}

pub fn main() void {
    run_14_raymarching_light_cycle();
}
