use crate::math;
use crate::time::perf_counter;
use crate::pytra::utils::gif::grayscale_palette;
use crate::pytra::utils::gif::save_gif;

// 15: Sample that renders wave interference animation and writes a GIF.

fn run_15_wave_interference_loop() {
    let mut w = 320;
    let mut h = 240;
    let mut frames_n = 96;
    let mut out_path = "sample/out/15_wave_interference_loop.gif";
    
    let mut start = perf_counter();
    let mut frames: Vec<Vec<u8>> = vec![];
    
    let mut t: i64 = 0;
    while t < frames_n {
        let mut frame = bytearray((w * h));
        let mut phase = (t * 0.12);
        let mut y: i64 = 0;
        while y < h {
            let mut row_base = (y * w);
            let mut x: i64 = 0;
            while x < w {
                let mut dx = (x - 160);
                let mut dy = (y - 120);
                let mut v = (((math.sin((((x + (t * 1.5))) * 0.045)) + math.sin((((y - (t * 1.2))) * 0.04))) + math.sin(((((x + y)) * 0.02) + phase))) + math.sin(((math.sqrt(((dx * dx) + (dy * dy))) * 0.08) - (phase * 1.3))));
                let mut c = (((v + 4.0)) * ((255.0 / 8.0))) as i64;
                if c < 0 {
                    c = 0;
                }
                if c > 255 {
                    c = 255;
                }
                frame[(row_base + x) as usize] = c;
                x += 1;
            }
            y += 1;
        }
        frames.push(bytes(frame));
        t += 1;
    }
    save_gif(out_path, w, h, frames, grayscale_palette());
    let mut elapsed = (perf_counter() - start);
    println!("{:?}", ("output:", out_path));
    println!("{:?}", ("frames:", frames_n));
    println!("{:?}", ("elapsed_sec:", elapsed));
}

fn main() {
    run_15_wave_interference_loop();
}
