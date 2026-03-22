const std = @import("std");
const pytra = @import("built_in/py_runtime.zig");
const time = @import("std/time.zig");
const perf_counter = time.perf_counter;
const gif = @import("utils/gif.zig");
const Tuple0 = struct { _0: i64, _1: i64 };
const Tuple1 = struct { _0: i64, _1: i64, _2: i64, _3: i64 };
const grayscale_palette = gif.grayscale_palette;
const save_gif = gif.save_gif;

// 13: Sample that outputs DFS maze-generation progress as a GIF.

fn capture(grid: pytra.Obj, w: i64, h: i64, scale: i64) pytra.Obj {
    const width: i64 = (w * scale);
    const height: i64 = (h * scale);
    const frame: pytra.Obj = pytra.bytearray((width * height));
    var y: i64 = 0;
    while (y < h) : (y += 1) {
        var x: i64 = 0;
        while (x < w) : (x += 1) {
            const v: i64 = if ((pytra.list_get(pytra.list_get(grid, pytra.Obj, y), i64, x) == 0)) @as(i64, 255) else @as(i64, 40);
            var yy: i64 = 0;
            while (yy < scale) : (yy += 1) {
                const base: i64 = ((((y * scale) + yy) * width) + (x * scale));
                var xx: i64 = 0;
                while (xx < scale) : (xx += 1) {
                    pytra.list_set(frame, u8, (base + xx), @intCast(v));
                }
            }
        }
    }
    return frame;
}

fn run_13_maze_generation_steps() void {
    // Increase maze size and render resolution to ensure sufficient runtime.
    const cell_w: i64 = 89;
    const cell_h: i64 = 67;
    const scale: i64 = 5;
    const capture_every: i64 = 20;
    const out_path: []const u8 = "sample/out/13_maze_generation_steps.gif";
    
    const start: f64 = pytra.perf_counter();
    const grid: pytra.Obj = pytra.list_from(pytra.Obj, &[_]pytra.Obj{  });
    var _unused: i64 = 0;
    while (_unused < cell_h) : (_unused += 1) {
        pytra.list_append(grid, pytra.Obj, __rep_blk_0: { const __rl = pytra.make_list(i64); var __ri: i64 = 0; while (__ri < cell_w) : (__ri += 1) { pytra.list_append(__rl, i64, 1); } break :__rep_blk_0 __rl; });
    }
    const stack: pytra.Obj = __list_blk_1: { const __bl = pytra.make_list(Tuple0); pytra.list_append(__bl, Tuple0, .{ ._0 = 1, ._1 = 1 }); break :__list_blk_1 __bl; };
    pytra.list_set(pytra.list_get(grid, pytra.Obj, 1), i64, 1, @intCast(0));
    
    const dirs: pytra.Obj = __list_blk_2: { const __bl = pytra.make_list(Tuple0); pytra.list_append(__bl, Tuple0, .{ ._0 = 2, ._1 = 0 }); pytra.list_append(__bl, Tuple0, .{ ._0 = -2, ._1 = 0 }); pytra.list_append(__bl, Tuple0, .{ ._0 = 0, ._1 = 2 }); pytra.list_append(__bl, Tuple0, .{ ._0 = 0, ._1 = -2 }); break :__list_blk_2 __bl; };
    const frames: pytra.Obj = pytra.list_from(pytra.Obj, &[_]pytra.Obj{  });
    var step: i64 = 0;
    
    while ((pytra.list_len(stack, Tuple0) > 0)) {
        const __tmp_3 = pytra.list_get(stack, Tuple0, -1);
        const x = __tmp_3._0;
        const y = __tmp_3._1;
        const candidates: pytra.Obj = pytra.make_list(Tuple1);
        var nx: pytra.PyObject = undefined;
        var ny: pytra.PyObject = undefined;
        var k: i64 = 0;
        while (k < 4) : (k += 1) {
            const __tmp_4 = pytra.list_get(dirs, Tuple0, k);
            const dx = __tmp_4._0;
            const dy = __tmp_4._1;
            nx = (x + dx);
            ny = (y + dy);
            if (((nx >= 1) and (nx < (cell_w - 1)) and (ny >= 1) and (ny < (cell_h - 1)) and (pytra.list_get(pytra.list_get(grid, pytra.Obj, ny), i64, nx) == 1))) {
                if ((dx == 2)) {
                    pytra.list_append(candidates, Tuple1, .{ ._0 = nx, ._1 = ny, ._2 = (x + 1), ._3 = y });
                } else {
                    if ((dx == -2)) {
                        pytra.list_append(candidates, Tuple1, .{ ._0 = nx, ._1 = ny, ._2 = (x - 1), ._3 = y });
                    } else {
                        if ((dy == 2)) {
                            pytra.list_append(candidates, Tuple1, .{ ._0 = nx, ._1 = ny, ._2 = x, ._3 = (y + 1) });
                        } else {
                            pytra.list_append(candidates, Tuple1, .{ ._0 = nx, ._1 = ny, ._2 = x, ._3 = (y - 1) });
                        }
                    }
                }
            }
        }
        if ((pytra.list_len(candidates, Tuple1) == 0)) {
            _ = pytra.list_pop(stack, Tuple0);
        } else {
            const sel: Tuple1 = pytra.list_get(candidates, Tuple1, @mod((((x * 17) + (y * 29)) + (pytra.list_len(stack, Tuple0) * 13)), pytra.list_len(candidates, Tuple1)));
            const __tmp_5 = sel;
            nx = __tmp_5._0;
            ny = __tmp_5._1;
            const wx = __tmp_5._2;
            const wy = __tmp_5._3;
            pytra.list_set(pytra.list_get(grid, pytra.Obj, wy), i64, wx, @intCast(0));
            pytra.list_set(pytra.list_get(grid, pytra.Obj, ny), i64, nx, @intCast(0));
            pytra.list_append(stack, Tuple0, .{ ._0 = nx, ._1 = ny });
        }
        if ((@mod(step, capture_every) == 0)) {
            pytra.list_append(frames, pytra.Obj, capture(grid, cell_w, cell_h, scale));
        }
        step += 1;
    }
    pytra.list_append(frames, pytra.Obj, capture(grid, cell_w, cell_h, scale));
    save_gif(out_path, (cell_w * scale), (cell_h * scale), frames, grayscale_palette(), 4, 0);
    const elapsed: f64 = (pytra.perf_counter() - start);
    pytra.print2("output:", out_path);
    pytra.print2("frames:", pytra.list_len(frames, pytra.Obj));
    pytra.print2("elapsed_sec:", elapsed);
}

pub fn main() void {
    run_13_maze_generation_steps();
}
