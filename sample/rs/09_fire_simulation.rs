#[path = "../../src/runtime/rs/pytra/built_in/py_runtime.rs"]
mod py_runtime;
use py_runtime::{math_cos, math_exp, math_floor, math_sin, math_sqrt, perf_counter, py_bool, py_grayscale_palette, py_in, py_isalpha, py_isdigit, py_len, py_print, py_save_gif, py_slice, py_write_rgb_png};

// このファイルは自動生成です（native Rust mode）。

fn fire_palette() -> Vec<u8> {
    let mut p = Vec::<u8>::new();
    for i in (0)..(256) {
        let mut r = 0;
        let mut g = 0;
        let mut b = 0;
        if py_bool(&(((i) < (85)))) {
            r = ((i) * (3));
            g = 0;
            b = 0;
        } else {
            if py_bool(&(((i) < (170)))) {
                r = 255;
                g = ((((i) - (85))) * (3));
                b = 0;
            } else {
                r = 255;
                g = 255;
                b = ((((i) - (170))) * (3));
            }
        }
        p.push((r) as u8);
        p.push((g) as u8);
        p.push((b) as u8);
    }
    return (p).clone();
}

fn run_09_fire_simulation() -> () {
    let mut w = 380;
    let mut h = 260;
    let mut steps = 420;
    let mut out_path = "sample/out/09_fire_simulation.gif".to_string();
    let mut start = perf_counter();
    let mut heat: Vec<Vec<i64>> = vec![];
    for _ in (0)..(h) {
        let mut row: Vec<i64> = vec![];
        for _ in (0)..(w) {
            row.push(0);
        }
        heat.push(row);
    }
    let mut frames: Vec<Vec<u8>> = vec![];
    for t in (0)..(steps) {
        for x in (0)..(w) {
            let mut val = ((170) + (((((((x) * (13))) + (((t) * (17))))) % (86))));
            ((heat)[((h) - (1)) as usize])[x as usize] = val;
        }
        for y in (1)..(h) {
            for x in (0)..(w) {
                let mut a = ((heat)[y as usize])[x as usize];
                let mut b = ((heat)[y as usize])[((((((x) - (1))) + (w))) % (w)) as usize];
                let mut c = ((heat)[y as usize])[((((x) + (1))) % (w)) as usize];
                let mut d = ((heat)[((((y) + (1))) % (h)) as usize])[x as usize];
                let mut v = ((((((((a) + (b))) + (c))) + (d))) / (4));
                let mut cool = ((1) + (((((((x) + (y))) + (t))) % (3))));
                let mut nv = ((v) - (cool));
                ((heat)[((y) - (1)) as usize])[x as usize] = (if py_bool(&(((nv) > (0)))) { nv } else { 0 });
            }
        }
        let mut frame = vec![0u8; (((w) * (h))) as usize];
        let mut i = 0;
        for yy in (0)..(h) {
            for xx in (0)..(w) {
                (frame)[i as usize] = (((heat)[yy as usize])[xx as usize]) as u8;
                i = i + 1;
            }
        }
        frames.push((frame).clone());
    }
    py_save_gif(&(out_path), w, h, &(frames), &(fire_palette()), 4, 0);
    let mut elapsed = ((perf_counter()) - (start));
    println!("{} {}", "output:".to_string(), out_path);
    println!("{} {}", "frames:".to_string(), steps);
    println!("{} {}", "elapsed_sec:".to_string(), elapsed);
}

fn main() {
    run_09_fire_simulation();
}
