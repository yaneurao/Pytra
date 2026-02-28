mod py_runtime;
pub use crate::py_runtime::{math, pytra, time};
use crate::py_runtime::*;

use crate::time::perf_counter;
use crate::pytra::runtime::gif::save_gif;

// 14: Sample that outputs a moving-light scene in a simple raymarching style as a GIF.

fn palette() -> Vec<u8> {
    let mut p = Vec::<u8>::new();
    let mut i: i64 = 0;
    while i < 256 {
        let r = (if 255 < ((((20) as f64) + ((i) as f64) * 0.9) as i64) { 255 } else { ((((20) as f64) + ((i) as f64) * 0.9) as i64) });
        let g = (if 255 < ((((10) as f64) + ((i) as f64) * 0.7) as i64) { 255 } else { ((((10) as f64) + ((i) as f64) * 0.7) as i64) });
        let b = (if 255 < 30 + i { 255 } else { 30 + i });
        p.push(((r) as u8));
        p.push(((g) as u8));
        p.push(((b) as u8));
        i += 1;
    }
    return (p).clone();
}

fn scene(x: f64, y: f64, light_x: f64, light_y: f64) -> i64 {
    let x1 = x + 0.45;
    let y1 = y + 0.2;
    let x2 = x - 0.35;
    let y2 = y - 0.15;
    let r1 = math::sqrt(x1 * x1 + y1 * y1);
    let r2 = math::sqrt(x2 * x2 + y2 * y2);
    let blob = math::exp(-7.0 * r1 * r1) + math::exp(-8.0 * r2 * r2);
    
    let lx = x - light_x;
    let ly = y - light_y;
    let l = math::sqrt(lx * lx + ly * ly);
    let lit = 1.0 / (1.0 + 3.5 * l * l);
    
    let v = ((255.0 * blob * lit * 5.0) as i64);
    return (if 255 < (if 0 > v { 0 } else { v }) { 255 } else { (if 0 > v { 0 } else { v }) });
}

fn run_14_raymarching_light_cycle() {
    let w = 320;
    let h = 240;
    let frames_n = 84;
    let out_path = ("sample/out/14_raymarching_light_cycle.gif").to_string();
    
    let start = perf_counter();
    let mut frames: Vec<Vec<u8>> = vec![];
    let __hoisted_cast_1: f64 = ((frames_n) as f64);
    let __hoisted_cast_2: f64 = ((h - 1) as f64);
    let __hoisted_cast_3: f64 = ((w - 1) as f64);
    
    let mut t: i64 = 0;
    while t < frames_n {
        let mut frame = vec![0u8; (w * h) as usize];
        let a = (((t) as f64) / __hoisted_cast_1) * math::pi * 2.0;
        let light_x = 0.75 * math::cos(a);
        let light_y = 0.55 * math::sin(a * 1.2);
        
        let mut y: i64 = 0;
        while y < h {
            let row_base = y * w;
            let py = (((y) as f64) / __hoisted_cast_2) * 2.0 - 1.0;
            let mut x: i64 = 0;
            while x < w {
                let px = (((x) as f64) / __hoisted_cast_3) * 2.0 - 1.0;
                let __idx_i64_1 = ((row_base + x) as i64);
                let __idx_2 = if __idx_i64_1 < 0 { (frame.len() as i64 + __idx_i64_1) as usize } else { __idx_i64_1 as usize };
                frame[__idx_2] = ((scene(px, py, light_x, light_y)) as u8);
                x += 1;
            }
            y += 1;
        }
        frames.push((frame).clone());
        t += 1;
    }
    save_gif(&(out_path), w, h, &(frames), &(palette()), 3, 0);
    let elapsed = perf_counter() - start;
    println!("{} {}", ("output:").to_string(), out_path);
    println!("{} {}", ("frames:").to_string(), frames_n);
    println!("{} {}", ("elapsed_sec:").to_string(), elapsed);
}

fn main() {
    run_14_raymarching_light_cycle();
}
