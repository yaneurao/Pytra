mod py_runtime;
pub use crate::py_runtime::{math, pytra, time};
use crate::py_runtime::*;

use crate::time::perf_counter;
use crate::pytra::utils::gif::grayscale_palette;
use crate::pytra::utils::gif::save_gif;

// 08: Sample that outputs Langton's Ant trajectories as a GIF.

fn capture(grid: &[Vec<i64>], w: i64, h: i64) -> Vec<u8> {
    let mut frame = vec![0u8; (w * h) as usize];
    for y in (0)..(h) {
            let row_base = y * w;
            for x in (0)..(w) {
                    let __idx_i64_4 = ((row_base + x) as i64);
                    let __idx_3 = if __idx_i64_4 < 0 { (frame.len() as i64 + __idx_i64_4) as usize } else { __idx_i64_4 as usize };
                    frame[__idx_3] = (((if grid[((y) as usize)][((x) as usize)] != 0 { 255 } else { 0 })) as u8);
            }
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
    
    frames.reserve(((if (steps_total) <= 0 { 0 } else { ((steps_total) + (capture_every) - 1) / (capture_every) })) as usize);
    let mut __next_capture_5: i64 = 0;
    for i in (0)..(steps_total) {
            if grid[((y) as usize)][((x) as usize)] == 0 {
                d = (d + 1) % 4;
                let __idx_6 = ((y) as usize);
                let __idx_7 = ((x) as usize);
                grid[__idx_6][__idx_7] = 1;
            } else {
                d = (d + 3) % 4;
                let __idx_8 = ((y) as usize);
                let __idx_9 = ((x) as usize);
                grid[__idx_8][__idx_9] = 0;
            }
            if d == 0 {
                y = (y - 1 + h) % h;
            } else if d == 1 {
                x = (x + 1) % w;
            } else if d == 2 {
                y = (y + 1) % h;
            } else {
                x = (x - 1 + w) % w;
            }
            if i == __next_capture_5 {
                frames.push(capture(&(grid), w, h));
            __next_capture_5 += capture_every;
            }
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
