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
    while i < n {
        let x0 = ((((i) as f64) * bar_w) as i64);
        let mut x1 = (((((i + 1)) as f64) * bar_w) as i64);
        if x1 <= x0 {
            x1 = x0 + 1;
        }
        let bh = (((((values[((if ((i) as i64) < 0 { (values.len() as i64 + ((i) as i64)) } else { ((i) as i64) }) as usize)]) as f64) / __hoisted_cast_1) * __hoisted_cast_2) as i64);
        let mut y = h - bh;
        let mut y: i64 = y;
        while y < h {
            let mut x: i64 = x0;
            while x < x1 {
                let __idx_i64_1 = ((y * w + x) as i64);
                let __idx_2 = if __idx_i64_1 < 0 { (frame.len() as i64 + __idx_i64_1) as usize } else { __idx_i64_1 as usize };
                frame[__idx_2] = ((255) as u8);
                x += 1;
            }
            y += 1;
        }
        i += 1;
    }
    return (frame).clone();
}

fn run_12_sort_visualizer() {
    let w = 320;
    let h = 180;
    let n = 124;
    let out_path = ("sample/out/12_sort_visualizer.gif").to_string();
    
    let start = perf_counter();
    let mut values: Vec<i64> = vec![];
    let mut i: i64 = 0;
    while i < n {
        values.push((i * 37 + 19) % n);
        i += 1;
    }
    let mut frames: Vec<Vec<u8>> = vec![render(&(values), w, h)];
    let frame_stride = 16;
    
    let mut op = 0;
    let mut i: i64 = 0;
    while i < n {
        let mut swapped = false;
        let mut j: i64 = 0;
        while j < n - i - 1 {
            if values[((if ((j) as i64) < 0 { (values.len() as i64 + ((j) as i64)) } else { ((j) as i64) }) as usize)] > values[((if ((j + 1) as i64) < 0 { (values.len() as i64 + ((j + 1) as i64)) } else { ((j + 1) as i64) }) as usize)] {
                let __tmp_3 = (values[((if ((j + 1) as i64) < 0 { (values.len() as i64 + ((j + 1) as i64)) } else { ((j + 1) as i64) }) as usize)], values[((if ((j) as i64) < 0 { (values.len() as i64 + ((j) as i64)) } else { ((j) as i64) }) as usize)]);
                let __idx_i64_4 = ((j) as i64);
                let __idx_5 = if __idx_i64_4 < 0 { (values.len() as i64 + __idx_i64_4) as usize } else { __idx_i64_4 as usize };
                values[__idx_5] = __tmp_3.0;
                let __idx_i64_6 = ((j + 1) as i64);
                let __idx_7 = if __idx_i64_6 < 0 { (values.len() as i64 + __idx_i64_6) as usize } else { __idx_i64_6 as usize };
                values[__idx_7] = __tmp_3.1;
                swapped = true;
            }
            if op % frame_stride == 0 {
                frames.push(render(&(values), w, h));
            }
            op += 1;
            j += 1;
        }
        if !swapped {
            break;
        }
        i += 1;
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
