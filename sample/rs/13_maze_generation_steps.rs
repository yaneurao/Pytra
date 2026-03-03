mod py_runtime;
pub use crate::py_runtime::{math, pytra, time};
use crate::py_runtime::*;

use crate::time::perf_counter;
use crate::pytra::utils::gif::grayscale_palette;
use crate::pytra::utils::gif::save_gif;

// 13: Sample that outputs DFS maze-generation progress as a GIF.

fn capture(grid: &[Vec<i64>], w: i64, h: i64, scale: i64) -> Vec<u8> {
    let width = w * scale;
    let height = h * scale;
    let mut frame = vec![0u8; (width * height) as usize];
    for y in (0)..(h) {
            for x in (0)..(w) {
                    let v = (if grid[((y) as usize)][((x) as usize)] == 0 { 255 } else { 40 });
                    for yy in (0)..(scale) {
                            let base = (y * scale + yy) * width + x * scale;
                            for xx in (0)..(scale) {
                                    let __idx_i64_6 = ((base + xx) as i64);
                                    let __idx_5 = if __idx_i64_6 < 0 { (frame.len() as i64 + __idx_i64_6) as usize } else { __idx_i64_6 as usize };
                                    frame[__idx_5] = ((v) as u8);
                            }
                    }
            }
    }
    return frame;
}

fn run_13_maze_generation_steps() {
    // Increase maze size and render resolution to ensure sufficient runtime.
    let cell_w = 89;
    let cell_h = 67;
    let scale = 5;
    let capture_every = 20;
    let out_path = ("sample/out/13_maze_generation_steps.gif").to_string();
    
    let start = perf_counter();
    let mut grid: Vec<Vec<i64>> = (((0)..(cell_h))).map(|py_underscore| vec![1; ((cell_w) as usize)]).collect::<Vec<_>>();
    let mut stack: Vec<(i64, i64)> = vec![(1, 1)];
    let __idx_7 = ((1) as usize);
    let __idx_8 = ((1) as usize);
    grid[__idx_7][__idx_8] = 0;
    
    let dirs: Vec<(i64, i64)> = vec![(2, 0), (-2, 0), (0, 2), (0, -2)];
    let mut frames: Vec<Vec<u8>> = vec![];
    let mut step = 0;
    
    while stack.len() != 0 {
        let __tmp_9 = (stack[((if ((-1) as i64) < 0 { (stack.len() as i64 + ((-1) as i64)) } else { ((-1) as i64) }) as usize)]).clone();
        let x = __tmp_9.0;
        let y = __tmp_9.1;
        let mut candidates: Vec<(i64, i64, i64, i64)> = vec![];
        for k in (0)..(4) {
                let __tmp_11 = (dirs[((k) as usize)]).clone();
                let dx = __tmp_11.0;
                let dy = __tmp_11.1;
                let mut nx = x + dx;
                let mut ny = y + dy;
                if (nx >= 1) && (nx < cell_w - 1) && (ny >= 1) && (ny < cell_h - 1) && (grid[((if ((ny) as i64) < 0 { (grid.len() as i64 + ((ny) as i64)) } else { ((ny) as i64) }) as usize)][((if ((nx) as i64) < 0 { (grid[((if ((ny) as i64) < 0 { (grid.len() as i64 + ((ny) as i64)) } else { ((ny) as i64) }) as usize)].len() as i64 + ((nx) as i64)) } else { ((nx) as i64) }) as usize)] == 1) {
                    if dx == 2 {
                        candidates.push((nx, ny, x + 1, y));
                    } else if dx == -2 {
                        candidates.push((nx, ny, x - 1, y));
                    } else if dy == 2 {
                        candidates.push((nx, ny, x, y + 1));
                    } else {
                        candidates.push((nx, ny, x, y - 1));
                    }
                }
        }
        if candidates.len() as i64 == 0 {
            stack.pop().unwrap_or_default();
        } else {
            let sel = (candidates[((if (((x * 17 + y * 29 + stack.len() as i64 * 13) % candidates.len() as i64) as i64) < 0 { (candidates.len() as i64 + (((x * 17 + y * 29 + stack.len() as i64 * 13) % candidates.len() as i64) as i64)) } else { (((x * 17 + y * 29 + stack.len() as i64 * 13) % candidates.len() as i64) as i64) }) as usize)]).clone();
            let __tmp_12 = sel;
            let mut nx = __tmp_12.0;
            let mut ny = __tmp_12.1;
            let wx = __tmp_12.2;
            let wy = __tmp_12.3;
            let __idx_i64_14 = ((wy) as i64);
            let __idx_13 = if __idx_i64_14 < 0 { (grid.len() as i64 + __idx_i64_14) as usize } else { __idx_i64_14 as usize };
            let __idx_i64_16 = ((wx) as i64);
            let __idx_15 = if __idx_i64_16 < 0 { (grid[__idx_13].len() as i64 + __idx_i64_16) as usize } else { __idx_i64_16 as usize };
            grid[__idx_13][__idx_15] = 0;
            let __idx_i64_18 = ((ny) as i64);
            let __idx_17 = if __idx_i64_18 < 0 { (grid.len() as i64 + __idx_i64_18) as usize } else { __idx_i64_18 as usize };
            let __idx_i64_20 = ((nx) as i64);
            let __idx_19 = if __idx_i64_20 < 0 { (grid[__idx_17].len() as i64 + __idx_i64_20) as usize } else { __idx_i64_20 as usize };
            grid[__idx_17][__idx_19] = 0;
            stack.push((nx, ny));
        }
        if step % capture_every == 0 {
            frames.push(capture(&(grid), cell_w, cell_h, scale));
        }
        step += 1;
    }
    frames.push(capture(&(grid), cell_w, cell_h, scale));
    save_gif(&(out_path), cell_w * scale, cell_h * scale, &(frames), &(grayscale_palette()), 4, 0);
    let elapsed = perf_counter() - start;
    println!("{} {}", ("output:").to_string(), out_path);
    println!("{} {}", ("frames:").to_string(), frames.len() as i64);
    println!("{} {}", ("elapsed_sec:").to_string(), elapsed);
}

fn main() {
    run_13_maze_generation_steps();
}
