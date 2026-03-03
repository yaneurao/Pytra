mod py_runtime;
pub use crate::py_runtime::{math, pytra, time};
use crate::py_runtime::*;

use crate::time::perf_counter;
use crate::pytra::utils::gif::save_gif;

// 09: Sample that outputs a simple fire effect as a GIF.

fn fire_palette() -> Vec<u8> {
    let mut p = Vec::<u8>::new();
    for i in (0)..(256) {
            let mut r = 0;
            let mut g = 0;
            let mut b = 0;
            if i < 85 {
                r = i * 3;
                g = 0;
                b = 0;
            } else if i < 170 {
                r = 255;
                g = (i - 85) * 3;
                b = 0;
            } else {
                r = 255;
                g = 255;
                b = (i - 170) * 3;
            }
            p.push(((r) as u8));
            p.push(((g) as u8));
            p.push(((b) as u8));
    }
    return p;
}

fn run_09_fire_simulation() {
    let w = 380;
    let h = 260;
    let steps = 420;
    let out_path = ("sample/out/09_fire_simulation.gif").to_string();
    
    let start = perf_counter();
    let mut heat: Vec<Vec<i64>> = (((0)..(h))).map(|py_underscore| vec![0; ((w) as usize)]).collect::<Vec<_>>();
    let mut frames: Vec<Vec<u8>> = vec![];
    
    for t in (0)..(steps) {
            let mut x: i64 = 0;
            for __for_i_4 in (0)..(w) {
                x = __for_i_4;
                    let val = 170 + (x * 13 + t * 17) % 86;
                    let __idx_5 = ((h - 1) as usize);
                    let __idx_6 = ((x) as usize);
                    heat[__idx_5][__idx_6] = val;
            }
            for y in (1)..(h) {
                    for x in (0)..(w) {
                            let a = heat[((y) as usize)][((x) as usize)];
                            let b = heat[((y) as usize)][(((x - 1 + w) % w) as usize)];
                            let c = heat[((y) as usize)][(((x + 1) % w) as usize)];
                            let d = heat[(((y + 1) % h) as usize)][((x) as usize)];
                            let v = (a + b + c + d) / 4;
                            let cool = 1 + (x + y + t) % 3;
                            let nv = v - cool;
                            let __idx_i64_9 = ((y - 1) as i64);
                            let __idx_8 = if __idx_i64_9 < 0 { (heat.len() as i64 + __idx_i64_9) as usize } else { __idx_i64_9 as usize };
                            let __idx_10 = ((x) as usize);
                            heat[__idx_8][__idx_10] = (if nv > 0 { nv } else { 0 });
                    }
            }
            let mut frame = vec![0u8; (w * h) as usize];
            for yy in (0)..(h) {
                    let row_base = yy * w;
                    for xx in (0)..(w) {
                            let __idx_13 = ((row_base + xx) as usize);
                            frame[__idx_13] = ((heat[((yy) as usize)][((xx) as usize)]) as u8);
                    }
            }
            frames.push((frame).clone());
    }
    save_gif(&(out_path), w, h, &(frames), &(fire_palette()), 4, 0);
    let elapsed = perf_counter() - start;
    println!("{} {}", ("output:").to_string(), out_path);
    println!("{} {}", ("frames:").to_string(), steps);
    println!("{} {}", ("elapsed_sec:").to_string(), elapsed);
}

fn main() {
    run_09_fire_simulation();
}
