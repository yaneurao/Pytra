use crate::math;
use crate::time::perf_counter;
use crate::pytra::runtime::gif::save_gif;

// 14: Sample that outputs a moving-light scene in a simple raymarching style as a GIF.

fn palette() -> Vec<u8> {
    let mut p = bytearray();
    let mut i: i64 = 0;
    while i < 256 {
        let r = min(255, 20 + i * 0.9 as i64);
        let g = min(255, 10 + i * 0.7 as i64);
        let b = min(255, 30 + i as i64);
        p.push(r);
        p.push(g);
        p.push(b);
        i += 1;
    }
    return bytes(p);
}

fn scene(x: f64, y: f64, light_x: f64, light_y: f64) -> i64 {
    let x1 = x + 0.45;
    let y1 = y + 0.2;
    let x2 = x - 0.35;
    let y2 = y - 0.15;
    let r1 = math.sqrt(x1 * x1 + y1 * y1);
    let r2 = math.sqrt(x2 * x2 + y2 * y2);
    let blob = math.exp((-7.0) * r1 * r1) + math.exp((-8.0) * r2 * r2);
    
    let lx = x - light_x;
    let ly = y - light_y;
    let l = math.sqrt(lx * lx + ly * ly);
    let lit = 1.0 / (1.0 + 3.5 * l * l);
    
    let v = 255.0 * blob * lit * 5.0 as i64;
    return min(255, max(0, v));
}

fn run_14_raymarching_light_cycle() {
    let w = 320;
    let h = 240;
    let frames_n = 84;
    let out_path = "sample/out/14_raymarching_light_cycle.gif";
    
    let start = perf_counter();
    let mut frames: Vec<Vec<u8>> = vec![];
    let mut t: i64 = 0;
    while t < frames_n {
        let mut frame = bytearray(w * h);
        let a = (t / frames_n) * math.pi * 2.0;
        let light_x = 0.75 * math.cos(a);
        let light_y = 0.55 * math.sin(a * 1.2);
        let mut y: i64 = 0;
        while y < h {
            let row_base = y * w;
            let py = (y / (h - 1)) * 2.0 - 1.0;
            let mut x: i64 = 0;
            while x < w {
                let px = (x / (w - 1)) * 2.0 - 1.0;
                frame[row_base + x as usize] = scene(px, py, light_x, light_y);
                x += 1;
            }
            y += 1;
        }
        frames.push(bytes(frame));
        t += 1;
    }
    save_gif(out_path, w, h, frames, palette());
    let elapsed = perf_counter() - start;
    println!("{:?}", ("output:", out_path));
    println!("{:?}", ("frames:", frames_n));
    println!("{:?}", ("elapsed_sec:", elapsed));
}

fn main() {
    run_14_raymarching_light_cycle();
}
