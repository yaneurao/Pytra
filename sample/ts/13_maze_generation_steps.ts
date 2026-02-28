import { perf_counter } from "./pytra/std/time.js";
import { grayscale_palette } from "./pytra/runtime/gif.js";
import { save_gif } from "./pytra/runtime/gif.js";

// 13: Sample that outputs DFS maze-generation progress as a GIF.

function capture(grid, w, h, scale) {
    let width = w * scale;
    let height = h * scale;
    let frame = (typeof (width * height) === "number" ? new Array(Math.max(0, Math.trunc(Number((width * height))))).fill(0) : (Array.isArray((width * height)) ? (width * height).slice() : Array.from((width * height))));
    const __start_1 = 0;
    for (let y = __start_1; y < h; y += 1) {
        const __start_2 = 0;
        for (let x = __start_2; x < w; x += 1) {
            let v = (grid[(((y) < 0) ? ((grid).length + (y)) : (y))][(((x) < 0) ? ((grid[(((y) < 0) ? ((grid).length + (y)) : (y))]).length + (x)) : (x))] === 0 ? 255 : 40);
            const __start_3 = 0;
            for (let yy = __start_3; yy < scale; yy += 1) {
                let base = (y * scale + yy) * width + x * scale;
                const __start_4 = 0;
                for (let xx = __start_4; xx < scale; xx += 1) {
                    frame[(((base + xx) < 0) ? ((frame).length + (base + xx)) : (base + xx))] = v;
                }
            }
        }
    }
    return (Array.isArray((frame)) ? (frame).slice() : Array.from((frame)));
}

function run_13_maze_generation_steps() {
    // Increase maze size and render resolution to ensure sufficient runtime.
    let cell_w = 89;
    let cell_h = 67;
    let scale = 5;
    let capture_every = 20;
    let out_path = "sample/out/13_maze_generation_steps.gif";
    
    let start = perf_counter();
    let grid = (() => { let __out = []; for (const _ of (() => { const __out = []; const __start = 0; const __stop = cell_h; const __step = 1; if (__step === 0) { return __out; } if (__step > 0) { for (let __i = __start; __i < __stop; __i += __step) { __out.push(__i); } } else { for (let __i = __start; __i > __stop; __i += __step) { __out.push(__i); } } return __out; })()) { __out.push((() => { const __base = ([1]); const __n = Math.max(0, Math.trunc(Number(cell_w))); let __out = []; for (let __i = 0; __i < __n; __i += 1) { for (const __v of __base) { __out.push(__v); } } return __out; })()); } return __out; })();
    let stack = [[1, 1]];
    grid[(((1) < 0) ? ((grid).length + (1)) : (1))][(((1) < 0) ? ((grid[(((1) < 0) ? ((grid).length + (1)) : (1))]).length + (1)) : (1))] = 0;
    
    let dirs = [[2, 0], [-2, 0], [0, 2], [0, -2]];
    let frames = [];
    let step = 0;
    
    while ((stack).length !== 0) {
        const __tmp_5 = stack[(((-1) < 0) ? ((stack).length + (-1)) : (-1))];
        let x = __tmp_5[0];
        let y = __tmp_5[1];
        let candidates = [];
        const __start_6 = 0;
        for (let k = __start_6; k < 4; k += 1) {
            const __tmp_7 = dirs[(((k) < 0) ? ((dirs).length + (k)) : (k))];
            let dx = __tmp_7[0];
            let dy = __tmp_7[1];
            let nx = x + dx;
            let ny = y + dy;
            if (nx >= 1 && nx < cell_w - 1 && ny >= 1 && ny < cell_h - 1 && grid[(((ny) < 0) ? ((grid).length + (ny)) : (ny))][(((nx) < 0) ? ((grid[(((ny) < 0) ? ((grid).length + (ny)) : (ny))]).length + (nx)) : (nx))] === 1) {
                if (dx === 2) {
                    candidates.push([nx, ny, x + 1, y]);
                } else {
                    if (dx === -2) {
                        candidates.push([nx, ny, x - 1, y]);
                    } else {
                        if (dy === 2) {
                            candidates.push([nx, ny, x, y + 1]);
                        } else {
                            candidates.push([nx, ny, x, y - 1]);
                        }
                    }
                }
            }
        }
        if ((candidates).length === 0) {
            stack.pop();
        } else {
            let sel = candidates[((((x * 17 + y * 29 + (stack).length * 13) % (candidates).length) < 0) ? ((candidates).length + ((x * 17 + y * 29 + (stack).length * 13) % (candidates).length)) : ((x * 17 + y * 29 + (stack).length * 13) % (candidates).length))];
            const __tmp_8 = sel;
            let nx = __tmp_8[0];
            let ny = __tmp_8[1];
            let wx = __tmp_8[2];
            let wy = __tmp_8[3];
            grid[(((wy) < 0) ? ((grid).length + (wy)) : (wy))][(((wx) < 0) ? ((grid[(((wy) < 0) ? ((grid).length + (wy)) : (wy))]).length + (wx)) : (wx))] = 0;
            grid[(((ny) < 0) ? ((grid).length + (ny)) : (ny))][(((nx) < 0) ? ((grid[(((ny) < 0) ? ((grid).length + (ny)) : (ny))]).length + (nx)) : (nx))] = 0;
            stack.push([nx, ny]);
        }
        if (step % capture_every === 0) {
            frames.push(capture(grid, cell_w, cell_h, scale));
        }
        step += 1;
    }
    frames.push(capture(grid, cell_w, cell_h, scale));
    save_gif(out_path, cell_w * scale, cell_h * scale, frames, grayscale_palette());
    let elapsed = perf_counter() - start;
    console.log("output:", out_path);
    console.log("frames:", (frames).length);
    console.log("elapsed_sec:", elapsed);
}

run_13_maze_generation_steps();
