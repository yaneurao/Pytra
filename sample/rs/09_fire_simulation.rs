mod py_runtime;
pub use crate::py_runtime::{math, pytra, time};
use crate::py_runtime::*;

use crate::time::perf_counter;
use crate::pytra::runtime::gif::save_gif;

// 09: Sample that outputs a simple fire effect as a GIF.

fn fire_palette() -> Vec<u8> {
    let mut p = Vec::<u8>::new();
    let mut i: i64 = 0;
    while i < 256 {
        let mut r = 0;
        let mut g = 0;
        let mut b = 0;
        if i < 85 {
            r = i * 3;
            g = 0;
            b = 0;
        } else {
            if i < 170 {
                r = 255;
                g = (i - 85) * 3;
                b = 0;
            } else {
                r = 255;
                g = 255;
                b = (i - 170) * 3;
            }
        }
        p.push(((r) as u8));
        p.push(((g) as u8));
        p.push(((b) as u8));
        i += 1;
    }
    return (p).clone();
}

fn run_09_fire_simulation() {
    let w = 380;
    let h = 260;
    let steps = 420;
    let out_path = ("sample/out/09_fire_simulation.gif").to_string();
    
    let start = perf_counter();
    let mut heat: Vec<Vec<i64>> = (((0)..(h))).map(|py_underscore| vec![0; ((w) as usize)]).collect::<Vec<_>>();
    let mut frames: Vec<Vec<u8>> = vec![];
    
    let mut t: i64 = 0;
    while t < steps {
        let mut x: i64 = 0;
        while x < w {
            let val = 170 + (x * 13 + t * 17) % 86;
            let __idx_i64_1 = ((h - 1) as i64);
            let __idx_2 = if __idx_i64_1 < 0 { (heat.len() as i64 + __idx_i64_1) as usize } else { __idx_i64_1 as usize };
            let __idx_i64_3 = ((x) as i64);
            let __idx_4 = if __idx_i64_3 < 0 { (heat[__idx_2].len() as i64 + __idx_i64_3) as usize } else { __idx_i64_3 as usize };
            heat[__idx_2][__idx_4] = val;
            x += 1;
        }
        let mut y: i64 = 1;
        while y < h {
            let mut x: i64 = 0;
            while x < w {
                let a = heat[((if ((y) as i64) < 0 { (heat.len() as i64 + ((y) as i64)) } else { ((y) as i64) }) as usize)][((if ((x) as i64) < 0 { (heat[((if ((y) as i64) < 0 { (heat.len() as i64 + ((y) as i64)) } else { ((y) as i64) }) as usize)].len() as i64 + ((x) as i64)) } else { ((x) as i64) }) as usize)];
                let b = heat[((if ((y) as i64) < 0 { (heat.len() as i64 + ((y) as i64)) } else { ((y) as i64) }) as usize)][((if (((x - 1 + w) % w) as i64) < 0 { (heat[((if ((y) as i64) < 0 { (heat.len() as i64 + ((y) as i64)) } else { ((y) as i64) }) as usize)].len() as i64 + (((x - 1 + w) % w) as i64)) } else { (((x - 1 + w) % w) as i64) }) as usize)];
                let c = heat[((if ((y) as i64) < 0 { (heat.len() as i64 + ((y) as i64)) } else { ((y) as i64) }) as usize)][((if (((x + 1) % w) as i64) < 0 { (heat[((if ((y) as i64) < 0 { (heat.len() as i64 + ((y) as i64)) } else { ((y) as i64) }) as usize)].len() as i64 + (((x + 1) % w) as i64)) } else { (((x + 1) % w) as i64) }) as usize)];
                let d = heat[((if (((y + 1) % h) as i64) < 0 { (heat.len() as i64 + (((y + 1) % h) as i64)) } else { (((y + 1) % h) as i64) }) as usize)][((if ((x) as i64) < 0 { (heat[((if (((y + 1) % h) as i64) < 0 { (heat.len() as i64 + (((y + 1) % h) as i64)) } else { (((y + 1) % h) as i64) }) as usize)].len() as i64 + ((x) as i64)) } else { ((x) as i64) }) as usize)];
                let v = (a + b + c + d) / 4;
                let cool = 1 + (x + y + t) % 3;
                let nv = v - cool;
                let __idx_i64_5 = ((y - 1) as i64);
                let __idx_6 = if __idx_i64_5 < 0 { (heat.len() as i64 + __idx_i64_5) as usize } else { __idx_i64_5 as usize };
                let __idx_i64_7 = ((x) as i64);
                let __idx_8 = if __idx_i64_7 < 0 { (heat[__idx_6].len() as i64 + __idx_i64_7) as usize } else { __idx_i64_7 as usize };
                heat[__idx_6][__idx_8] = (if nv > 0 { nv } else { 0 });
                x += 1;
            }
            y += 1;
        }
        let mut frame = vec![0u8; (w * h) as usize];
        let mut yy: i64 = 0;
        while yy < h {
            let row_base = yy * w;
            let mut xx: i64 = 0;
            while xx < w {
                let __idx_i64_9 = ((row_base + xx) as i64);
                let __idx_10 = if __idx_i64_9 < 0 { (frame.len() as i64 + __idx_i64_9) as usize } else { __idx_i64_9 as usize };
                frame[__idx_10] = ((heat[((if ((yy) as i64) < 0 { (heat.len() as i64 + ((yy) as i64)) } else { ((yy) as i64) }) as usize)][((if ((xx) as i64) < 0 { (heat[((if ((yy) as i64) < 0 { (heat.len() as i64 + ((yy) as i64)) } else { ((yy) as i64) }) as usize)].len() as i64 + ((xx) as i64)) } else { ((xx) as i64) }) as usize)]) as u8);
                xx += 1;
            }
            yy += 1;
        }
        frames.push((frame).clone());
        t += 1;
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
