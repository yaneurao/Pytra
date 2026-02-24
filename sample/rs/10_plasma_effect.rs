use crate::math;
use crate::time::perf_counter;
use crate::pytra::runtime::gif::grayscale_palette;
use crate::pytra::runtime::gif::save_gif;

// 10: Sample that outputs a plasma effect as a GIF.

fn run_10_plasma_effect() {
    let w = 320;
    let h = 240;
    let frames_n = 216;
    let out_path = "sample/out/10_plasma_effect.gif";
    
    let start = perf_counter();
    let mut frames: Vec<Vec<u8>> = vec![];
    let mut t: i64 = 0;
    while t < frames_n {
        let mut frame = bytearray(w * h);
        let mut y: i64 = 0;
        while y < h {
            let row_base = y * w;
            let mut x: i64 = 0;
            while x < w {
                let dx = x - 160;
                let dy = y - 120;
                let v = math.sin((x + t * 2.0) * 0.045) + math.sin((y - t * 1.2) * 0.05) + math.sin((x + y + t * 1.7) * 0.03) + math.sin(math.sqrt(dx * dx + dy * dy) * 0.07 - t * 0.18);
                let mut c = (v + 4.0) * (255.0 / 8.0) as i64;
                if c < 0 {
                    c = 0;
                }
                if c > 255 {
                    c = 255;
                }
                frame[row_base + x as usize] = c;
                x += 1;
            }
            y += 1;
        }
        frames.push(bytes(frame));
        t += 1;
    }
    save_gif(out_path, w, h, frames, grayscale_palette());
    let elapsed = perf_counter() - start;
    println!("{:?}", ("output:", out_path));
    println!("{:?}", ("frames:", frames_n));
    println!("{:?}", ("elapsed_sec:", elapsed));
}

fn main() {
    run_10_plasma_effect();
}
