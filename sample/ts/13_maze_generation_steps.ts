// このファイルは EAST ベース TypeScript プレビュー出力です。
// TODO: 専用 TSEmitter 実装へ段階移行する。
import { perf_counter } from "./time.js";
import { grayscale_palette } from "./pytra/runtime/gif.js";
import { save_gif } from "./pytra/runtime/gif.js";

// 13: Sample that outputs DFS maze-generation progress as a GIF.

function capture(grid, w, h, scale) {
    let width = w * scale;
    let height = h * scale;
    let frame = bytearray(width * height);
    for (let y = 0; y < h; y += 1) {
        for (let x = 0; x < w; x += 1) {
            let v = (grid[y][x] === 0 ? 255 : 40);
            for (let yy = 0; yy < scale; yy += 1) {
                let base = (y * scale + yy) * width + x * scale;
                for (let xx = 0; xx < scale; xx += 1) {
                    frame[base + xx] = v;
                }
            }
        }
    }
    return bytes(frame);
}

function run_13_maze_generation_steps() {
    // Increase maze size and render resolution to ensure sufficient runtime.
    let cell_w = 89;
    let cell_h = 67;
    let scale = 5;
    let capture_every = 20;
    let out_path = "sample/out/13_maze_generation_steps.gif";
    
    let start = perf_counter();
    let grid = [];
    for (let _y = 0; _y < cell_h; _y += 1) {
        grid.push(Array(cell_w).fill(1));
    }
    let stack = [];
    grid[1][1] = 0;
    
    let dirs = [];
    let frames = [];
    let step = 0;
    
    while ((stack).length !== 0) {
        const __tmp_1 = stack[-1];
        x = __tmp_1[0];
        y = __tmp_1[1];
        let candidates = [];
        for (let k = 0; k < 4; k += 1) {
            const __tmp_2 = dirs[k];
            dx = __tmp_2[0];
            dy = __tmp_2[1];
            let nx = x + dx;
            let ny = y + dy;
            if (nx >= 1 && nx < cell_w - 1 && ny >= 1 && ny < cell_h - 1 && grid[ny][nx] === 1) {
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
            let sel = candidates[(x * 17 + y * 29 + (stack).length * 13) % (candidates).length];
            [nx, ny, wx, wy] = sel;
            grid[wy][wx] = 0;
            grid[ny][nx] = 0;
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

// __main__ guard
run_13_maze_generation_steps();
