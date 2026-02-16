#[path = "../../src/rs_module/py_runtime.rs"]
mod py_runtime;
use py_runtime::{math_cos, math_exp, math_sin, math_sqrt, perf_counter, py_bool, py_grayscale_palette, py_in, py_len, py_print, py_save_gif, py_slice, py_write_rgb_png};

// このファイルは自動生成です（native Rust mode）。

fn clamp01(v: f64) -> f64 {
    if py_bool(&(((v) < (0.0)))) {
        return 0.0;
    }
    if py_bool(&(((v) > (1.0)))) {
        return 1.0;
    }
    return v;
}

fn hit_sphere(ox: f64, oy: f64, oz: f64, dx: f64, dy: f64, dz: f64, cx: f64, cy: f64, cz: f64, r: f64) -> f64 {
    let mut lx: f64 = ((ox) - (cx));
    let mut ly: f64 = ((oy) - (cy));
    let mut lz: f64 = ((oz) - (cz));
    let mut a: f64 = ((((((dx) * (dx))) + (((dy) * (dy))))) + (((dz) * (dz))));
    let mut b: f64 = ((2.0) * (((((((lx) * (dx))) + (((ly) * (dy))))) + (((lz) * (dz))))));
    let mut c: f64 = ((((((((lx) * (lx))) + (((ly) * (ly))))) + (((lz) * (lz))))) - (((r) * (r))));
    let mut d: f64 = ((((b) * (b))) - (((((4.0) * (a))) * (c))));
    if py_bool(&(((d) < (0.0)))) {
        return (-1.0);
    }
    let mut sd: f64 = math_sqrt(((d) as f64));
    let mut t0: f64 = ((( (((-b)) - (sd)) ) as f64) / (( ((2.0) * (a)) ) as f64));
    let mut t1: f64 = ((( (((-b)) + (sd)) ) as f64) / (( ((2.0) * (a)) ) as f64));
    if py_bool(&(((t0) > (0.001)))) {
        return t0;
    }
    if py_bool(&(((t1) > (0.001)))) {
        return t1;
    }
    return (-1.0);
}

fn render(width: i64, height: i64) -> Vec<u8> {
    let mut pixels: Vec<u8> = Vec::<u8>::new();
    let mut ox: f64 = 0.0;
    let mut oy: f64 = 0.0;
    let mut oz: f64 = (-3.0);
    let mut lx: f64 = (-0.4);
    let mut ly: f64 = 0.8;
    let mut lz: f64 = (-0.45);
    for y in (0)..(height) {
        let mut sy: f64 = ((1.0) - (((2.0) * (((( y ) as f64) / (( ((height) - (1)) ) as f64))))));
        for x in (0)..(width) {
            let mut sx: f64 = ((((2.0) * (((( x ) as f64) / (( ((width) - (1)) ) as f64))))) - (1.0));
            sx = sx * ((( width ) as f64) / (( height ) as f64));
            let mut dx: f64 = sx;
            let mut dy: f64 = sy;
            let mut dz: f64 = 1.0;
            let mut inv_len: f64 = ((( 1.0 ) as f64) / (( math_sqrt(((((((((dx) * (dx))) + (((dy) * (dy))))) + (((dz) * (dz))))) as f64)) ) as f64));
            dx = dx * inv_len;
            dy = dy * inv_len;
            dz = dz * inv_len;
            let mut t_min: f64 = 1e+30;
            let mut hit_id: i64 = (-1);
            let mut t: f64 = hit_sphere(ox, oy, oz, dx, dy, dz, (-0.8), (-0.2), 2.2, 0.8);
            if py_bool(&((((t) > (0.0)) && ((t) < (t_min))))) {
                t_min = t;
                hit_id = 0;
            }
            t = hit_sphere(ox, oy, oz, dx, dy, dz, 0.9, 0.1, 2.9, 0.95);
            if py_bool(&((((t) > (0.0)) && ((t) < (t_min))))) {
                t_min = t;
                hit_id = 1;
            }
            t = hit_sphere(ox, oy, oz, dx, dy, dz, 0.0, (-1001.0), 3.0, 1000.0);
            if py_bool(&((((t) > (0.0)) && ((t) < (t_min))))) {
                t_min = t;
                hit_id = 2;
            }
            let mut r: i64 = 0;
            let mut g: i64 = 0;
            let mut b: i64 = 0;
            if py_bool(&(((hit_id) >= (0)))) {
                let mut px: f64 = ((ox) + (((dx) * (t_min))));
                let mut py: f64 = ((oy) + (((dy) * (t_min))));
                let mut pz: f64 = ((oz) + (((dz) * (t_min))));
                let mut nx: f64 = 0.0;
                let mut ny: f64 = 0.0;
                let mut nz: f64 = 0.0;
                if py_bool(&(((hit_id) == (0)))) {
                    nx = ((( ((px) + (0.8)) ) as f64) / (( 0.8 ) as f64));
                    ny = ((( ((py) + (0.2)) ) as f64) / (( 0.8 ) as f64));
                    nz = ((( ((pz) - (2.2)) ) as f64) / (( 0.8 ) as f64));
                } else {
                    if py_bool(&(((hit_id) == (1)))) {
                        nx = ((( ((px) - (0.9)) ) as f64) / (( 0.95 ) as f64));
                        ny = ((( ((py) - (0.1)) ) as f64) / (( 0.95 ) as f64));
                        nz = ((( ((pz) - (2.9)) ) as f64) / (( 0.95 ) as f64));
                    } else {
                        nx = 0.0;
                        ny = 1.0;
                        nz = 0.0;
                    }
                }
                let mut diff: f64 = ((((((nx) * ((-lx)))) + (((ny) * ((-ly)))))) + (((nz) * ((-lz)))));
                diff = clamp01(diff);
                let mut base_r: f64 = 0.0;
                let mut base_g: f64 = 0.0;
                let mut base_b: f64 = 0.0;
                if py_bool(&(((hit_id) == (0)))) {
                    base_r = 0.95;
                    base_g = 0.35;
                    base_b = 0.25;
                } else {
                    if py_bool(&(((hit_id) == (1)))) {
                        base_r = 0.25;
                        base_g = 0.55;
                        base_b = 0.95;
                    } else {
                        let mut checker: i64 = ((((((((px) + (50.0))) * (0.8))) as i64)) + (((((((pz) + (50.0))) * (0.8))) as i64)));
                        if py_bool(&(((((checker) % (2))) == (0)))) {
                            base_r = 0.85;
                            base_g = 0.85;
                            base_b = 0.85;
                        } else {
                            base_r = 0.2;
                            base_g = 0.2;
                            base_b = 0.2;
                        }
                    }
                }
                let mut shade: f64 = ((0.12) + (((0.88) * (diff))));
                r = ((((255.0) * (clamp01(((base_r) * (shade)))))) as i64);
                g = ((((255.0) * (clamp01(((base_g) * (shade)))))) as i64);
                b = ((((255.0) * (clamp01(((base_b) * (shade)))))) as i64);
            } else {
                let mut tsky: f64 = ((0.5) * (((dy) + (1.0))));
                r = ((((255.0) * (((0.65) + (((0.2) * (tsky))))))) as i64);
                g = ((((255.0) * (((0.75) + (((0.18) * (tsky))))))) as i64);
                b = ((((255.0) * (((0.9) + (((0.08) * (tsky))))))) as i64);
            }
            pixels.push((r) as u8);
            pixels.push((g) as u8);
            pixels.push((b) as u8);
        }
    }
    return pixels;
}

fn run_raytrace() -> () {
    let mut width: i64 = 960;
    let mut height: i64 = 540;
    let mut out_path: String = "sample/out/raytrace_02.png".to_string();
    let mut start: f64 = perf_counter();
    let mut pixels: Vec<u8> = render(width, height);
    py_write_rgb_png(&(out_path), width, height, &(pixels));
    let mut elapsed: f64 = ((perf_counter()) - (start));
    println!("{} {}", "output:".to_string(), out_path);
    println!("{} {} {} {}", "size:".to_string(), width, "x".to_string(), height);
    println!("{} {}", "elapsed_sec:".to_string(), elapsed);
}

fn main() {
    run_raytrace();
}
