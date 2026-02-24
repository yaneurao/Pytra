use crate::time::perf_counter;
use crate::pytra::runtime::gif::save_gif;

// 09: Sample that outputs a simple fire effect as a GIF.

fn fire_palette() -> Vec<u8> {
    let mut p = bytearray();
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
        p.push(r);
        p.push(g);
        p.push(b);
        i += 1;
    }
    return bytes(p);
}

fn run_09_fire_simulation() {
    let w = 380;
    let h = 260;
    let steps = 420;
    let out_path = "sample/out/09_fire_simulation.gif";
    
    let start = perf_counter();
    let mut heat: Vec<Vec<i64>> = [[0] * w for _ in range(h)];
    let mut frames: Vec<Vec<u8>> = vec![];
    let mut t: i64 = 0;
    while t < steps {
        let mut x: i64 = 0;
        while x < w {
            let val = 170 + (x * 13 + t * 17) % 86;
            heat[h - 1 as usize][x as usize] = val;
            x += 1;
        }
        let mut y: i64 = 1;
        while y < h {
            let mut x: i64 = 0;
            while x < w {
                let a = heat[y as usize][x as usize];
                let b = heat[y as usize][(x - 1 + w) % w as usize];
                let c = heat[y as usize][(x + 1) % w as usize];
                let d = heat[(y + 1) % h as usize][x as usize];
                let v = (a + b + c + d) / 4;
                let cool = 1 + (x + y + t) % 3;
                let nv = v - cool;
                heat[y - 1 as usize][x as usize] = ((nv > 0) ? nv : 0);
                x += 1;
            }
            y += 1;
        }
        let mut frame = bytearray(w * h);
        let mut yy: i64 = 0;
        while yy < h {
            let row_base = yy * w;
            let mut xx: i64 = 0;
            while xx < w {
                frame[row_base + xx as usize] = heat[yy as usize][xx as usize];
                xx += 1;
            }
            yy += 1;
        }
        frames.push(bytes(frame));
        t += 1;
    }
    save_gif(out_path, w, h, frames, fire_palette());
    let elapsed = perf_counter() - start;
    println!("{:?}", ("output:", out_path));
    println!("{:?}", ("frames:", steps));
    println!("{:?}", ("elapsed_sec:", elapsed));
}

fn main() {
    run_09_fire_simulation();
}
