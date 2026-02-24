import { perf_counter } from "./time.js";
import { grayscale_palette } from "./pytra/runtime/gif.js";
import { save_gif } from "./pytra/runtime/gif.js";

// 08: Sample that outputs Langton's Ant trajectories as a GIF.

function capture(grid, w, h) {
    let frame = bytearray(w * h);
    for (let y = 0; y < h; y += 1) {
        let row_base = y * w;
        for (let x = 0; x < w; x += 1) {
            frame[row_base + x] = (grid[y][x] ? 255 : 0);
        }
    }
    return bytes(frame);
}

function run_08_langtons_ant() {
    let w = 420;
    let h = 420;
    let out_path = "sample/out/08_langtons_ant.gif";
    
    let start = perf_counter();
    
    let grid = [[0] * w for _ in range(h)];
    let x = Math.floor(w / 2);
    let y = Math.floor(h / 2);
    let d = 0;
    
    let steps_total = 600000;
    let capture_every = 3000;
    let frames = [];
    
    for (let i = 0; i < steps_total; i += 1) {
        if (grid[y][x] === 0) {
            d = (d + 1) % 4;
            grid[y][x] = 1;
        } else {
            d = (d + 3) % 4;
            grid[y][x] = 0;
        }
        if (d === 0) {
            y = (y - 1 + h) % h;
        } else {
            if (d === 1) {
                x = (x + 1) % w;
            } else {
                if (d === 2) {
                    y = (y + 1) % h;
                } else {
                    x = (x - 1 + w) % w;
                }
            }
        }
        if (i % capture_every === 0) {
            frames.push(capture(grid, w, h));
        }
    }
    save_gif(out_path, w, h, frames, grayscale_palette());
    let elapsed = perf_counter() - start;
    console.log("output:", out_path);
    console.log("frames:", (frames).length);
    console.log("elapsed_sec:", elapsed);
}

// __main__ guard
run_08_langtons_ant();
