const std = @import("std");
const pytra = @import("built_in/py_runtime.zig");
const time = @import("std/time.zig");
const perf_counter = time.perf_counter;
const gif = @import("utils/gif.zig");
const grayscale_palette = gif.grayscale_palette;
const save_gif = gif.save_gif;

// 07: Sample that outputs Game of Life evolution as a GIF.

fn next_state(grid: pytra.Obj, w: i64, h: i64) pytra.Obj {
    const nxt: pytra.Obj = pytra.list_from(pytra.Obj, &[_]pytra.Obj{  });
    var y: i64 = 0;
    while (y < h) : (y += 1) {
        const row: pytra.Obj = pytra.list_from(i64, &[_]i64{  });
        var x: i64 = 0;
        while (x < w) : (x += 1) {
            var cnt: i64 = 0;
            var dy: i64 = -1;
            while (dy < 2) : (dy += 1) {
                var dx: i64 = -1;
                while (dx < 2) : (dx += 1) {
                    if (((dx != 0) or (dy != 0))) {
                        const nx: i64 = @mod(((x + dx) + w), w);
                        const ny: i64 = @mod(((y + dy) + h), h);
                        cnt += pytra.list_get(pytra.list_get(grid, pytra.Obj, ny), i64, nx);
                    }
                }
            }
            const alive: i64 = pytra.list_get(pytra.list_get(grid, pytra.Obj, y), i64, x);
            if (((alive == 1) and ((cnt == 2) or (cnt == 3)))) {
                pytra.list_append(row, i64, @intCast(1));
            } else {
                if (((alive == 0) and (cnt == 3))) {
                    pytra.list_append(row, i64, @intCast(1));
                } else {
                    pytra.list_append(row, i64, @intCast(0));
                }
            }
        }
        pytra.list_append(nxt, pytra.Obj, row);
    }
    return nxt;
}

fn render(grid: pytra.Obj, w: i64, h: i64, cell: i64) pytra.Obj {
    const width: i64 = (w * cell);
    const height: i64 = (h * cell);
    const frame: pytra.Obj = pytra.bytearray((width * height));
    var y: i64 = 0;
    while (y < h) : (y += 1) {
        var x: i64 = 0;
        while (x < w) : (x += 1) {
            const v: i64 = if ((pytra.list_get(pytra.list_get(grid, pytra.Obj, y), i64, x) != 0)) @as(i64, 255) else @as(i64, 0);
            var yy: i64 = 0;
            while (yy < cell) : (yy += 1) {
                const base: i64 = ((((y * cell) + yy) * width) + (x * cell));
                var xx: i64 = 0;
                while (xx < cell) : (xx += 1) {
                    pytra.list_set(frame, u8, (base + xx), @intCast(v));
                }
            }
        }
    }
    return frame;
}

fn run_07_game_of_life_loop() void {
    const w: i64 = 144;
    const h: i64 = 108;
    const cell: i64 = 4;
    const steps: i64 = 105;
    const out_path: []const u8 = "sample/out/07_game_of_life_loop.gif";
    
    const start: f64 = pytra.perf_counter();
    var grid: pytra.Obj = pytra.list_from(pytra.Obj, &[_]pytra.Obj{  });
    var _unused: i64 = 0;
    while (_unused < h) : (_unused += 1) {
        pytra.list_append(grid, pytra.Obj, __rep_blk_0: { const __rl = pytra.make_list(i64); var __ri: i64 = 0; while (__ri < w) : (__ri += 1) { pytra.list_append(__rl, i64, 0); } break :__rep_blk_0 __rl; });
    }
    
    // Lay down sparse noise so the whole field is less likely to stabilize too early.
    // Avoid large integer literals so all transpilers handle the expression consistently.
    var y: i64 = 0;
    while (y < h) : (y += 1) {
        var x: i64 = 0;
        while (x < w) : (x += 1) {
            const noise: i64 = @mod(((((x * 37) + (y * 73)) + @mod((x * y), 19)) + @mod((x + y), 11)), 97);
            if ((noise < 3)) {
                pytra.list_set(pytra.list_get(grid, pytra.Obj, y), i64, x, @intCast(1));
            }
        }
    }
    // Place multiple well-known long-lived patterns.
    const glider: pytra.Obj = pytra.list_from(pytra.Obj, &[_]pytra.Obj{ pytra.list_from(i64, &[_]i64{ 0, 1, 0 }), pytra.list_from(i64, &[_]i64{ 0, 0, 1 }), pytra.list_from(i64, &[_]i64{ 1, 1, 1 }) });
    const r_pentomino: pytra.Obj = pytra.list_from(pytra.Obj, &[_]pytra.Obj{ pytra.list_from(i64, &[_]i64{ 0, 1, 1 }), pytra.list_from(i64, &[_]i64{ 1, 1, 0 }), pytra.list_from(i64, &[_]i64{ 0, 1, 0 }) });
    const lwss: pytra.Obj = pytra.list_from(pytra.Obj, &[_]pytra.Obj{ pytra.list_from(i64, &[_]i64{ 0, 1, 1, 1, 1 }), pytra.list_from(i64, &[_]i64{ 1, 0, 0, 0, 1 }), pytra.list_from(i64, &[_]i64{ 0, 0, 0, 0, 1 }), pytra.list_from(i64, &[_]i64{ 1, 0, 0, 1, 0 }) });
    
    var gy: i64 = 8;
    while (gy < (h - 8)) : (gy += 18) {
        var gx: i64 = 8;
        while (gx < (w - 8)) : (gx += 22) {
            const kind: i64 = @mod(((gx * 7) + (gy * 11)), 3);
            var ph: i64 = undefined;
            var pw: i64 = undefined;
            var px: i64 = undefined;
            var py: i64 = undefined;
            if ((kind == 0)) {
                ph = pytra.list_len(glider, pytra.Obj);
                py = 0;
                while (py < ph) : (py += 1) {
                    pw = pytra.list_len(pytra.list_get(glider, pytra.Obj, py), i64);
                    px = 0;
                    while (px < pw) : (px += 1) {
                        if ((pytra.list_get(pytra.list_get(glider, pytra.Obj, py), i64, px) == 1)) {
                            pytra.list_set(pytra.list_get(grid, pytra.Obj, @mod((gy + py), h)), i64, @mod((gx + px), w), @intCast(1));
                        }
                    }
                }
            } else {
                if ((kind == 1)) {
                    ph = pytra.list_len(r_pentomino, pytra.Obj);
                    py = 0;
                    while (py < ph) : (py += 1) {
                        pw = pytra.list_len(pytra.list_get(r_pentomino, pytra.Obj, py), i64);
                        px = 0;
                        while (px < pw) : (px += 1) {
                            if ((pytra.list_get(pytra.list_get(r_pentomino, pytra.Obj, py), i64, px) == 1)) {
                                pytra.list_set(pytra.list_get(grid, pytra.Obj, @mod((gy + py), h)), i64, @mod((gx + px), w), @intCast(1));
                            }
                        }
                    }
                } else {
                    ph = pytra.list_len(lwss, pytra.Obj);
                    py = 0;
                    while (py < ph) : (py += 1) {
                        pw = pytra.list_len(pytra.list_get(lwss, pytra.Obj, py), i64);
                        px = 0;
                        while (px < pw) : (px += 1) {
                            if ((pytra.list_get(pytra.list_get(lwss, pytra.Obj, py), i64, px) == 1)) {
                                pytra.list_set(pytra.list_get(grid, pytra.Obj, @mod((gy + py), h)), i64, @mod((gx + px), w), @intCast(1));
                            }
                        }
                    }
                }
            }
        }
    }
    const frames: pytra.Obj = pytra.list_from(pytra.Obj, &[_]pytra.Obj{  });
    _unused = 0;
    while (_unused < steps) : (_unused += 1) {
        pytra.list_append(frames, pytra.Obj, render(grid, w, h, cell));
        grid = next_state(grid, w, h);
    }
    save_gif(out_path, (w * cell), (h * cell), frames, grayscale_palette(), 4, 0);
    const elapsed: f64 = (pytra.perf_counter() - start);
    pytra.print2("output:", out_path);
    pytra.print2("frames:", steps);
    pytra.print2("elapsed_sec:", elapsed);
}

pub fn main() void {
    run_07_game_of_life_loop();
}
