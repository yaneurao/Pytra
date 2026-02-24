use crate::time::perf_counter;
use crate::pytra::utils::png;

// 04: Sample that renders an orbit-trap Julia set and writes a PNG image.

fn render_orbit_trap_julia(width: i64, height: i64, max_iter: i64, cx: f64, cy: f64) -> Vec<u8> {
    let mut pixels: Vec<u8> = bytearray();
    let mut y: i64 = 0;
    while y < height {
        let zy0: f64 = (-1.3) + 2.6 * (y / (height - 1));
        let mut x: i64 = 0;
        while x < width {
            let mut zx: f64 = (-1.9) + 3.8 * (x / (width - 1));
            let mut zy: f64 = zy0;
            
            let mut trap: f64 = 1.0e9;
            let mut i: i64 = 0;
            while i < max_iter {
                let mut ax: f64 = zx;
                if ax < 0.0 {
                    ax = (-ax);
                }
                let mut ay: f64 = zy;
                if ay < 0.0 {
                    ay = (-ay);
                }
                let mut dxy: f64 = zx - zy;
                if dxy < 0.0 {
                    dxy = (-dxy);
                }
                if ax < trap {
                    trap = ax;
                }
                if ay < trap {
                    trap = ay;
                }
                if dxy < trap {
                    trap = dxy;
                }
                let zx2: f64 = zx * zx;
                let zy2: f64 = zy * zy;
                if zx2 + zy2 > 4.0 {
                    py_break;
                }
                zy = 2.0 * zx * zy + cy;
                zx = zx2 - zy2 + cx;
                i += 1;
            }
            let mut r: i64 = 0;
            let mut g: i64 = 0;
            let mut b: i64 = 0;
            if i >= max_iter {
                r = 0;
                g = 0;
                b = 0;
            } else {
                let mut trap_scaled: f64 = trap * 3.2;
                if trap_scaled > 1.0 {
                    trap_scaled = 1.0;
                }
                if trap_scaled < 0.0 {
                    trap_scaled = 0.0;
                }
                let t: f64 = i / max_iter;
                let tone: i64 = 255.0 * (1.0 - trap_scaled) as i64;
                r = tone * (0.35 + 0.65 * t) as i64;
                g = tone * (0.15 + 0.85 * (1.0 - t)) as i64;
                b = 255.0 * (0.25 + 0.75 * t) as i64;
                if r > 255 {
                    r = 255;
                }
                if g > 255 {
                    g = 255;
                }
                if b > 255 {
                    b = 255;
                }
            }
            pixels.push(r);
            pixels.push(g);
            pixels.push(b);
            x += 1;
        }
        y += 1;
    }
    return pixels;
}

fn run_04_orbit_trap_julia() {
    let width: i64 = 1920;
    let height: i64 = 1080;
    let max_iter: i64 = 1400;
    let out_path: String = "sample/out/04_orbit_trap_julia.png";
    
    let start: f64 = perf_counter();
    let pixels: Vec<u8> = render_orbit_trap_julia(width, height, max_iter, (-0.7269), 0.1889);
    png.write_rgb_png(out_path, width, height, pixels);
    let elapsed: f64 = perf_counter() - start;
    
    println!("{:?}", ("output:", out_path));
    println!("{:?}", ("size:", width, "x", height));
    println!("{:?}", ("max_iter:", max_iter));
    println!("{:?}", ("elapsed_sec:", elapsed));
}

fn main() {
    run_04_orbit_trap_julia();
}
