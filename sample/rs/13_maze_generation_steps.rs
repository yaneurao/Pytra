mod py_runtime;
pub use crate::py_runtime::{math, pytra, time};
use crate::py_runtime::*;

use crate::time::perf_counter;
use crate::pytra::runtime::gif::grayscale_palette;
use crate::pytra::runtime::gif::save_gif;

// 13: Sample that outputs DFS maze-generation progress as a GIF.

fn capture(grid: &Vec<Vec<i64>>, w: i64, h: i64, scale: i64) -> Vec<u8> {
    let width = w * scale;
    let height = h * scale;
    let mut frame = vec![0u8; (width * height) as usize];
    let mut y: i64 = 0;
    while y < h {
        let mut x: i64 = 0;
        while x < w {
            let v = (if grid[((if ((y) as i64) < 0 { (grid.len() as i64 + ((y) as i64)) } else { ((y) as i64) }) as usize)][((if ((x) as i64) < 0 { (grid[((if ((y) as i64) < 0 { (grid.len() as i64 + ((y) as i64)) } else { ((y) as i64) }) as usize)].len() as i64 + ((x) as i64)) } else { ((x) as i64) }) as usize)] == 0 { 255 } else { 40 });
            let mut yy: i64 = 0;
            while yy < scale {
                let base = (y * scale + yy) * width + x * scale;
                let mut xx: i64 = 0;
                while xx < scale {
                    let __idx_i64_1 = ((base + xx) as i64);
                    let __idx_2 = if __idx_i64_1 < 0 { (frame.len() as i64 + __idx_i64_1) as usize } else { __idx_i64_1 as usize };
                    frame[__idx_2] = ((v) as u8);
                    xx += 1;
                }
                yy += 1;
            }
            x += 1;
        }
        y += 1;
    }
    return (frame).clone();
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
    let __idx_i64_3 = ((1) as i64);
    let __idx_4 = if __idx_i64_3 < 0 { (grid.len() as i64 + __idx_i64_3) as usize } else { __idx_i64_3 as usize };
    let __idx_i64_5 = ((1) as i64);
    let __idx_6 = if __idx_i64_5 < 0 { (grid[__idx_4].len() as i64 + __idx_i64_5) as usize } else { __idx_i64_5 as usize };
    grid[__idx_4][__idx_6] = 0;
    
    let dirs: Vec<(i64, i64)> = vec![(2, 0), (-2, 0), (0, 2), (0, -2)];
    let mut frames: Vec<Vec<u8>> = vec![];
    let mut step = 0;
    
    while stack.len() != 0 {
        let __tmp_7 = (stack[((if ((-1) as i64) < 0 { (stack.len() as i64 + ((-1) as i64)) } else { ((-1) as i64) }) as usize)]).clone();
        let x = __tmp_7.0;
        let y = __tmp_7.1;
        let mut candidates: Vec<(i64, i64, i64, i64)> = vec![];
        let mut k: i64 = 0;
        while k < 4 {
            let __tmp_8 = (dirs[((if ((k) as i64) < 0 { (dirs.len() as i64 + ((k) as i64)) } else { ((k) as i64) }) as usize)]).clone();
            let dx = __tmp_8.0;
            let dy = __tmp_8.1;
            let mut nx = x + dx;
            let mut ny = y + dy;
            if (nx >= 1) && (nx < cell_w - 1) && (ny >= 1) && (ny < cell_h - 1) && (grid[((if ((ny) as i64) < 0 { (grid.len() as i64 + ((ny) as i64)) } else { ((ny) as i64) }) as usize)][((if ((nx) as i64) < 0 { (grid[((if ((ny) as i64) < 0 { (grid.len() as i64 + ((ny) as i64)) } else { ((ny) as i64) }) as usize)].len() as i64 + ((nx) as i64)) } else { ((nx) as i64) }) as usize)] == 1) {
                if dx == 2 {
                    candidates.push((nx, ny, x + 1, y));
                } else {
                    if dx == -2 {
                        candidates.push((nx, ny, x - 1, y));
                    } else {
                        if dy == 2 {
                            candidates.push((nx, ny, x, y + 1));
                        } else {
                            candidates.push((nx, ny, x, y - 1));
                        }
                    }
                }
            }
            k += 1;
        }
        if candidates.len() as i64 == 0 {
            stack.pop().unwrap_or_default();
        } else {
            let sel = (candidates[((if (((x * 17 + y * 29 + stack.len() as i64 * 13) % candidates.len() as i64) as i64) < 0 { (candidates.len() as i64 + (((x * 17 + y * 29 + stack.len() as i64 * 13) % candidates.len() as i64) as i64)) } else { (((x * 17 + y * 29 + stack.len() as i64 * 13) % candidates.len() as i64) as i64) }) as usize)]).clone();
            let __tmp_9 = sel;
            let mut nx = __tmp_9.0;
            let mut ny = __tmp_9.1;
            let wx = __tmp_9.2;
            let wy = __tmp_9.3;
            let __idx_i64_10 = ((wy) as i64);
            let __idx_11 = if __idx_i64_10 < 0 { (grid.len() as i64 + __idx_i64_10) as usize } else { __idx_i64_10 as usize };
            let __idx_i64_12 = ((wx) as i64);
            let __idx_13 = if __idx_i64_12 < 0 { (grid[__idx_11].len() as i64 + __idx_i64_12) as usize } else { __idx_i64_12 as usize };
            grid[__idx_11][__idx_13] = 0;
            let __idx_i64_14 = ((ny) as i64);
            let __idx_15 = if __idx_i64_14 < 0 { (grid.len() as i64 + __idx_i64_14) as usize } else { __idx_i64_14 as usize };
            let __idx_i64_16 = ((nx) as i64);
            let __idx_17 = if __idx_i64_16 < 0 { (grid[__idx_15].len() as i64 + __idx_i64_16) as usize } else { __idx_i64_16 as usize };
            grid[__idx_15][__idx_17] = 0;
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
