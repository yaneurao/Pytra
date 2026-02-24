use crate::math;
use crate::time::perf_counter;
use crate::pytra::runtime::gif::save_gif;

// 06: Sample that sweeps Julia-set parameters and outputs a GIF.

fn julia_palette() -> Vec<u8> {
    // Keep index 0 black for points inside the set; build a high-saturation gradient for the rest.
    let mut palette = bytearray((256 * 3));
    palette[0 as usize] = 0;
    palette[1 as usize] = 0;
    palette[2 as usize] = 0;
    let mut i: i64 = 1;
    while i < 256 {
        let t = (((i - 1)) / 254.0);
        let r = (255.0 * ((((9.0 * ((1.0 - t))) * t) * t) * t)) as i64;
        let g = (255.0 * ((((15.0 * ((1.0 - t))) * ((1.0 - t))) * t) * t)) as i64;
        let b = (255.0 * ((((8.5 * ((1.0 - t))) * ((1.0 - t))) * ((1.0 - t))) * t)) as i64;
        palette[((i * 3) + 0) as usize] = r;
        palette[((i * 3) + 1) as usize] = g;
        palette[((i * 3) + 2) as usize] = b;
        i += 1;
    }
    return bytes(palette);
}

fn render_frame(width: i64, height: i64, cr: f64, ci: f64, max_iter: i64, phase: i64) -> Vec<u8> {
    let mut frame = bytearray((width * height));
    let mut y: i64 = 0;
    while y < height {
        let row_base = (y * width);
        let zy0 = ((-1.2) + (2.4 * ((y / ((height - 1))))));
        let mut x: i64 = 0;
        while x < width {
            let mut zx = ((-1.8) + (3.6 * ((x / ((width - 1))))));
            let mut zy = zy0;
            let mut i = 0;
            while i < max_iter {
                let zx2 = (zx * zx);
                let zy2 = (zy * zy);
                if (zx2 + zy2) > 4.0 {
                    py_break;
                }
                zy = (((2.0 * zx) * zy) + ci);
                zx = ((zx2 - zy2) + cr);
                i += 1;
            }
            if i >= max_iter {
                frame[(row_base + x) as usize] = 0;
            } else {
                // Add a small frame phase so colors flow smoothly.
                let color_index = (1 + (((((i * 224) / max_iter) + phase)) % 255));
                frame[(row_base + x) as usize] = color_index;
            }
            x += 1;
        }
        y += 1;
    }
    return bytes(frame);
}

fn run_06_julia_parameter_sweep() {
    let width = 320;
    let height = 240;
    let frames_n = 72;
    let max_iter = 180;
    let out_path = "sample/out/06_julia_parameter_sweep.gif";
    
    let start = perf_counter();
    let mut frames: Vec<Vec<u8>> = vec![];
    // Orbit an ellipse around a known visually good region to reduce flat blown highlights.
    let center_cr = (-0.745);
    let center_ci = 0.186;
    let radius_cr = 0.12;
    let radius_ci = 0.10;
    // Add start and phase offsets so GitHub thumbnails do not appear too dark.
    // Tune it to start in a red-leaning color range.
    let start_offset = 20;
    let phase_offset = 180;
    let mut i: i64 = 0;
    while i < frames_n {
        let t = ((((i + start_offset)) % frames_n) / frames_n);
        let angle = ((2.0 * math.pi) * t);
        let cr = (center_cr + (radius_cr * math.cos(angle)));
        let ci = (center_ci + (radius_ci * math.sin(angle)));
        let phase = (((phase_offset + (i * 5))) % 255);
        frames.push(render_frame(width, height, cr, ci, max_iter, phase));
        i += 1;
    }
    save_gif(out_path, width, height, frames, julia_palette());
    let elapsed = (perf_counter() - start);
    println!("{:?}", ("output:", out_path));
    println!("{:?}", ("frames:", frames_n));
    println!("{:?}", ("elapsed_sec:", elapsed));
}

fn main() {
    run_06_julia_parameter_sweep();
}
