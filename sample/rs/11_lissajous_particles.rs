use crate::math;
use crate::time::perf_counter;
use crate::pytra::runtime::gif::save_gif;

// 11: Sample that outputs Lissajous-motion particles as a GIF.

fn color_palette() -> Vec<u8> {
    let mut p = bytearray();
    let mut i: i64 = 0;
    while i < 256 {
        let r = i;
        let g = ((i * 3) % 256);
        let b = (255 - i);
        p.push(r);
        p.push(g);
        p.push(b);
        i += 1;
    }
    return bytes(p);
}

fn run_11_lissajous_particles() {
    let w = 320;
    let h = 240;
    let frames_n = 360;
    let particles = 48;
    let out_path = "sample/out/11_lissajous_particles.gif";
    
    let start = perf_counter();
    let mut frames: Vec<Vec<u8>> = vec![];
    
    let mut t: i64 = 0;
    while t < frames_n {
        let mut frame = bytearray((w * h));
        
        let mut p: i64 = 0;
        while p < particles {
            let phase = (p * 0.261799);
            let x = ((w * 0.5) + ((w * 0.38) * math.sin(((0.11 * t) + (phase * 2.0))))) as i64;
            let y = ((h * 0.5) + ((h * 0.38) * math.sin(((0.17 * t) + (phase * 3.0))))) as i64;
            let color = (30 + ((p * 9) % 220));
            
            let mut dy: i64 = (-2);
            while dy < 3 {
                let mut dx: i64 = (-2);
                while dx < 3 {
                    let xx = (x + dx);
                    let yy = (y + dy);
                    if (xx >= 0) && (xx < w) && (yy >= 0) && (yy < h) {
                        let d2 = ((dx * dx) + (dy * dy));
                        if d2 <= 4 {
                            let idx = ((yy * w) + xx);
                            let mut v = (color - (d2 * 20));
                            v = max(0, v);
                            if v > frame[idx as usize] {
                                frame[idx as usize] = v;
                            }
                        }
                    }
                    dx += 1;
                }
                dy += 1;
            }
            p += 1;
        }
        frames.push(bytes(frame));
        t += 1;
    }
    save_gif(out_path, w, h, frames, color_palette());
    let elapsed = (perf_counter() - start);
    println!("{:?}", ("output:", out_path));
    println!("{:?}", ("frames:", frames_n));
    println!("{:?}", ("elapsed_sec:", elapsed));
}

fn main() {
    run_11_lissajous_particles();
}
