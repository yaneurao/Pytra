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
            let __idx_i64_2 = ((row_base + x) as i64);
            let __idx_1 = if __idx_i64_2 < 0 { (frame.len() as i64 + __idx_i64_2) as usize } else { __idx_i64_2 as usize };
            frame[__idx_1] = (((if grid[((y) as usize)][((x) as usize)] != 0 { 255 } else { 0 })) as u8);
            x += 1;
        }
        y += 1;
    }
    return frame;
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
        if grid[((y) as usize)][((x) as usize)] == 0 {
            d = (d + 1) % 4;
            let __idx_3 = ((y) as usize);
            let __idx_4 = ((x) as usize);
            grid[__idx_3][__idx_4] = 1;
        } else {
            d = (d + 3) % 4;
            let __idx_5 = ((y) as usize);
            let __idx_6 = ((x) as usize);
            grid[__idx_5][__idx_6] = 0;
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
