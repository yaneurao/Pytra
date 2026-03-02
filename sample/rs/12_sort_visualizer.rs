mod py_runtime;
pub use crate::py_runtime::{math, pytra, time};
use crate::py_runtime::*;

use crate::time::perf_counter;
use crate::pytra::utils::gif::grayscale_palette;
use crate::pytra::utils::gif::save_gif;

// 12: Sample that outputs intermediate states of bubble sort as a GIF.

fn render(values: &Vec<i64>, w: i64, h: i64) -> Vec<u8> {
    let mut frame = vec![0u8; (w * h) as usize];
    let n = values.len() as i64;
    let bar_w = ((w) as f64) / ((n) as f64);
    let __hoisted_cast_1: f64 = ((n) as f64);
    let __hoisted_cast_2: f64 = ((h) as f64);
    let mut i: i64 = 0;
    for __for_i_1 in (0)..(n) {
        i = __for_i_1;
            let x0 = ((((i) as f64) * bar_w) as i64);
            let mut x1 = (((((i + 1)) as f64) * bar_w) as i64);
            if x1 <= x0 {
                x1 = x0 + 1;
            }
            let bh = (((((values[((i) as usize)]) as f64) / __hoisted_cast_1) * __hoisted_cast_2) as i64);
            let mut y = h - bh;
            let mut y: i64 = y;
            for __for_i_2 in (y)..(h) {
                y = __for_i_2;
                    let mut x: i64 = x0;
                    for __for_i_3 in (x0)..(x1) {
                        x = __for_i_3;
                            let __idx_i64_5 = ((y * w + x) as i64);
                            let __idx_4 = if __idx_i64_5 < 0 { (frame.len() as i64 + __idx_i64_5) as usize } else { __idx_i64_5 as usize };
                            frame[__idx_4] = ((255) as u8);
                    }
            }
    }
    return frame;
}

fn run_12_sort_visualizer() {
    let w = 320;
    let h = 180;
    let n = 124;
    let out_path = ("sample/out/12_sort_visualizer.gif").to_string();
    
    let start = perf_counter();
    let mut values: Vec<i64> = vec![];
    let mut i: i64 = 0;
    for __for_i_6 in (0)..(n) {
        i = __for_i_6;
            values.push((i * 37 + 19) % n);
    }
    let mut frames: Vec<Vec<u8>> = vec![render(&(values), w, h)];
    let frame_stride = 16;
    
    let mut op = 0;
    let mut i: i64 = 0;
    for __for_i_7 in (0)..(n) {
        i = __for_i_7;
            let mut swapped = false;
            let mut j: i64 = 0;
            for __for_i_8 in (0)..(n - i - 1) {
                j = __for_i_8;
                    if values[((j) as usize)] > values[((j + 1) as usize)] {
                        let __tmp_9 = (values[((j + 1) as usize)], values[((j) as usize)]);
                        let __idx_10 = ((j) as usize);
                        values[__idx_10] = __tmp_9.0;
                        let __idx_11 = ((j + 1) as usize);
                        values[__idx_11] = __tmp_9.1;
                        swapped = true;
                    }
                    if op % frame_stride == 0 {
                        frames.push(render(&(values), w, h));
                    }
                    op += 1;
            }
            if !swapped {
                break;
            }
    }
    save_gif(&(out_path), w, h, &(frames), &(grayscale_palette()), 3, 0);
    let elapsed = perf_counter() - start;
    println!("{} {}", ("output:").to_string(), out_path);
    println!("{} {}", ("frames:").to_string(), frames.len() as i64);
    println!("{} {}", ("elapsed_sec:").to_string(), elapsed);
}

fn main() {
    run_12_sort_visualizer();
}
