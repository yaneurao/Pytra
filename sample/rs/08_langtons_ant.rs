mod py_runtime;
pub use crate::py_runtime::{math, pytra, time};
use crate::py_runtime::*;

use crate::time::perf_counter;
use crate::pytra::runtime::gif::grayscale_palette;
use crate::pytra::runtime::gif::save_gif;

// 08: Sample that outputs Langton's Ant trajectories as a GIF.

fn capture(grid: &Vec<Vec<i64>>, w: i64, h: i64) -> Vec<u8> {
    let mut frame = vec![0u8; (w * h) as usize];
    let mut y: i64 = 0;
    while y < h {
        let row_base = y * w;
        let mut x: i64 = 0;
        while x < w {
            let __idx_i64_1 = ((row_base + x) as i64);
            let __idx_2 = if __idx_i64_1 < 0 { (frame.len() as i64 + __idx_i64_1) as usize } else { __idx_i64_1 as usize };
            frame[__idx_2] = (((if grid[((if ((y) as i64) < 0 { (grid.len() as i64 + ((y) as i64)) } else { ((y) as i64) }) as usize)][((if ((x) as i64) < 0 { (grid[((if ((y) as i64) < 0 { (grid.len() as i64 + ((y) as i64)) } else { ((y) as i64) }) as usize)].len() as i64 + ((x) as i64)) } else { ((x) as i64) }) as usize)] != 0 { 255 } else { 0 })) as u8);
            x += 1;
        }
        y += 1;
    }
    return (frame).clone();
}

fn run_08_langtons_ant() {
    let w = 420;
    let h = 420;
    let out_path = ("sample/out/08_langtons_ant.gif").to_string();
    
    let start = perf_counter();
    
    let mut grid: Vec<Vec<i64>> = (((0)..(h))).map(|py_underscore| vec![0; ((w) as usize)]).collect::<Vec<_>>();
    let mut x = w / 2;
    let mut y = h / 2;
    let mut d = 0;
    
    let steps_total = 600000;
    let capture_every = 3000;
    let mut frames: Vec<Vec<u8>> = vec![];
    
    let mut i: i64 = 0;
    while i < steps_total {
        if grid[((if ((y) as i64) < 0 { (grid.len() as i64 + ((y) as i64)) } else { ((y) as i64) }) as usize)][((if ((x) as i64) < 0 { (grid[((if ((y) as i64) < 0 { (grid.len() as i64 + ((y) as i64)) } else { ((y) as i64) }) as usize)].len() as i64 + ((x) as i64)) } else { ((x) as i64) }) as usize)] == 0 {
            d = (d + 1) % 4;
            let __idx_i64_3 = ((y) as i64);
            let __idx_4 = if __idx_i64_3 < 0 { (grid.len() as i64 + __idx_i64_3) as usize } else { __idx_i64_3 as usize };
            let __idx_i64_5 = ((x) as i64);
            let __idx_6 = if __idx_i64_5 < 0 { (grid[__idx_4].len() as i64 + __idx_i64_5) as usize } else { __idx_i64_5 as usize };
            grid[__idx_4][__idx_6] = 1;
        } else {
            d = (d + 3) % 4;
            let __idx_i64_7 = ((y) as i64);
            let __idx_8 = if __idx_i64_7 < 0 { (grid.len() as i64 + __idx_i64_7) as usize } else { __idx_i64_7 as usize };
            let __idx_i64_9 = ((x) as i64);
            let __idx_10 = if __idx_i64_9 < 0 { (grid[__idx_8].len() as i64 + __idx_i64_9) as usize } else { __idx_i64_9 as usize };
            grid[__idx_8][__idx_10] = 0;
        }
        if d == 0 {
            y = (y - 1 + h) % h;
        } else {
            if d == 1 {
                x = (x + 1) % w;
            } else {
                if d == 2 {
                    y = (y + 1) % h;
                } else {
                    x = (x - 1 + w) % w;
                }
            }
        }
        if i % capture_every == 0 {
            frames.push(capture(&(grid), w, h));
        }
        i += 1;
    }
    save_gif(&(out_path), w, h, &(frames), &(grayscale_palette()), 5, 0);
    let elapsed = perf_counter() - start;
    println!("{} {}", ("output:").to_string(), out_path);
    println!("{} {}", ("frames:").to_string(), frames.len() as i64);
    println!("{} {}", ("elapsed_sec:").to_string(), elapsed);
}

fn main() {
    run_08_langtons_ant();
}
