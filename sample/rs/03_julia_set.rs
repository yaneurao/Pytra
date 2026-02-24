use crate::time::perf_counter;
use crate::pytra::runtime::png;

// 03: Sample that outputs a Julia set as a PNG image.
// Implemented with simple loop-centric logic for transpilation compatibility.

fn render_julia(width: i64, height: i64, max_iter: i64, cx: f64, cy: f64) -> Vec<u8> {
    let mut pixels: Vec<u8> = bytearray();
    let mut y: i64 = 0;
    while y < height {
        let zy0: f64 = (-1.2) + 2.4 * (y / (height - 1));
        let mut x: i64 = 0;
        while x < width {
            let mut zx: f64 = (-1.8) + 3.6 * (x / (width - 1));
            let mut zy: f64 = zy0;
            
            let mut i: i64 = 0;
            while i < max_iter {
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
                let t: f64 = i / max_iter;
                r = 255.0 * (0.2 + 0.8 * t) as i64;
                g = 255.0 * (0.1 + 0.9 * t * t) as i64;
                b = 255.0 * (1.0 - t) as i64;
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

fn run_julia() {
    let width: i64 = 3840;
    let height: i64 = 2160;
    let max_iter: i64 = 20000;
    let out_path: String = "sample/out/03_julia_set.png";
    
    let start: f64 = perf_counter();
    let pixels: Vec<u8> = render_julia(width, height, max_iter, (-0.8), 0.156);
    png.write_rgb_png(out_path, width, height, pixels);
    let elapsed: f64 = perf_counter() - start;
    
    println!("{:?}", ("output:", out_path));
    println!("{:?}", ("size:", width, "x", height));
    println!("{:?}", ("max_iter:", max_iter));
    println!("{:?}", ("elapsed_sec:", elapsed));
}

fn main() {
    run_julia();
}
