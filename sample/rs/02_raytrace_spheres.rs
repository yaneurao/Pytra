use crate::math;
use crate::pytra::runtime::png;
use crate::time::perf_counter;

// 02: Sample that runs a mini sphere-only ray tracer and outputs a PNG image.
// Dependencies are kept minimal (time only) for transpilation compatibility.

fn clamp01(v: f64) -> f64 {
    if v < 0.0 {
        return 0.0;
    }
    if v > 1.0 {
        return 1.0;
    }
    return v;
}

fn hit_sphere(ox: f64, oy: f64, oz: f64, dx: f64, dy: f64, dz: f64, cx: f64, cy: f64, cz: f64, r: f64) -> f64 {
    let lx: f64 = (ox - cx);
    let ly: f64 = (oy - cy);
    let lz: f64 = (oz - cz);
    
    let a: f64 = (((dx * dx) + (dy * dy)) + (dz * dz));
    let b: f64 = (2.0 * ((((lx * dx) + (ly * dy)) + (lz * dz))));
    let c: f64 = ((((lx * lx) + (ly * ly)) + (lz * lz)) - (r * r));
    
    let d: f64 = ((b * b) - ((4.0 * a) * c));
    if d < 0.0 {
        return (-1.0);
    }
    let sd: f64 = math.sqrt(d);
    let t0: f64 = ((((-b) - sd)) / ((2.0 * a)));
    let t1: f64 = ((((-b) + sd)) / ((2.0 * a)));
    
    if t0 > 0.001 {
        return t0;
    }
    if t1 > 0.001 {
        return t1;
    }
    return (-1.0);
}

fn render(width: i64, height: i64, aa: i64) -> Vec<u8> {
    let mut pixels: Vec<u8> = bytearray();
    
    // Camera origin
    let ox: f64 = 0.0;
    let oy: f64 = 0.0;
    let oz: f64 = (-3.0);
    
    // Light direction (normalized)
    let lx: f64 = (-0.4);
    let ly: f64 = 0.8;
    let lz: f64 = (-0.45);
    
    let mut y: i64 = 0;
    while y < height {
        let mut x: i64 = 0;
        while x < width {
            let mut ar: i64 = 0;
            let mut ag: i64 = 0;
            let mut ab: i64 = 0;
            
            let mut ay: i64 = 0;
            while ay < aa {
                let mut ax: i64 = 0;
                while ax < aa {
                    let fy = (((y + (((ay + 0.5)) / aa))) / ((height - 1)));
                    let fx = (((x + (((ax + 0.5)) / aa))) / ((width - 1)));
                    let sy: f64 = (1.0 - (2.0 * fy));
                    let sx: f64 = ((((2.0 * fx) - 1.0)) * ((width / height)));
                    
                    let mut dx: f64 = sx;
                    let mut dy: f64 = sy;
                    let mut dz: f64 = 1.0;
                    let inv_len: f64 = (1.0 / math.sqrt((((dx * dx) + (dy * dy)) + (dz * dz))));
                    dx *= inv_len;
                    dy *= inv_len;
                    dz *= inv_len;
                    
                    let mut t_min: f64 = 1.0e30;
                    let mut hit_id: i64 = (-1);
                    
                    let mut t: f64 = hit_sphere(ox, oy, oz, dx, dy, dz, (-0.8), (-0.2), 2.2, 0.8);
                    if (t > 0.0) && (t < t_min) {
                        t_min = t;
                        hit_id = 0;
                    }
                    t = hit_sphere(ox, oy, oz, dx, dy, dz, 0.9, 0.1, 2.9, 0.95);
                    if (t > 0.0) && (t < t_min) {
                        t_min = t;
                        hit_id = 1;
                    }
                    t = hit_sphere(ox, oy, oz, dx, dy, dz, 0.0, (-1001.0), 3.0, 1000.0);
                    if (t > 0.0) && (t < t_min) {
                        t_min = t;
                        hit_id = 2;
                    }
                    let mut r: i64 = 0;
                    let mut g: i64 = 0;
                    let mut b: i64 = 0;
                    
                    if hit_id >= 0 {
                        let px: f64 = (ox + (dx * t_min));
                        let py: f64 = (oy + (dy * t_min));
                        let pz: f64 = (oz + (dz * t_min));
                        
                        let mut nx: f64 = 0.0;
                        let mut ny: f64 = 0.0;
                        let mut nz: f64 = 0.0;
                        
                        if hit_id == 0 {
                            nx = (((px + 0.8)) / 0.8);
                            ny = (((py + 0.2)) / 0.8);
                            nz = (((pz - 2.2)) / 0.8);
                        } else {
                            if hit_id == 1 {
                                nx = (((px - 0.9)) / 0.95);
                                ny = (((py - 0.1)) / 0.95);
                                nz = (((pz - 2.9)) / 0.95);
                            } else {
                                nx = 0.0;
                                ny = 1.0;
                                nz = 0.0;
                            }
                        }
                        let mut diff: f64 = (((nx * (-lx)) + (ny * (-ly))) + (nz * (-lz)));
                        diff = clamp01(diff);
                        
                        let mut base_r: f64 = 0.0;
                        let mut base_g: f64 = 0.0;
                        let mut base_b: f64 = 0.0;
                        
                        if hit_id == 0 {
                            base_r = 0.95;
                            base_g = 0.35;
                            base_b = 0.25;
                        } else {
                            if hit_id == 1 {
                                base_r = 0.25;
                                base_g = 0.55;
                                base_b = 0.95;
                            } else {
                                let checker: i64 = ((((px + 50.0)) * 0.8) as i64 + (((pz + 50.0)) * 0.8) as i64);
                                if (checker % 2) == 0 {
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
                        let shade: f64 = (0.12 + (0.88 * diff));
                        r = (255.0 * clamp01((base_r * shade))) as i64;
                        g = (255.0 * clamp01((base_g * shade))) as i64;
                        b = (255.0 * clamp01((base_b * shade))) as i64;
                    } else {
                        let tsky: f64 = (0.5 * ((dy + 1.0)));
                        r = (255.0 * ((0.65 + (0.20 * tsky)))) as i64;
                        g = (255.0 * ((0.75 + (0.18 * tsky)))) as i64;
                        b = (255.0 * ((0.90 + (0.08 * tsky)))) as i64;
                    }
                    ar += r;
                    ag += g;
                    ab += b;
                    ax += 1;
                }
                ay += 1;
            }
            let samples = (aa * aa);
            pixels.push((ar / samples));
            pixels.push((ag / samples));
            pixels.push((ab / samples));
            x += 1;
        }
        y += 1;
    }
    return pixels;
}

fn run_raytrace() {
    let width: i64 = 1600;
    let height: i64 = 900;
    let aa: i64 = 2;
    let out_path: String = "sample/out/02_raytrace_spheres.png";
    
    let start: f64 = perf_counter();
    let pixels: Vec<u8> = render(width, height, aa);
    png.write_rgb_png(out_path, width, height, pixels);
    let elapsed: f64 = (perf_counter() - start);
    
    println!("{:?}", ("output:", out_path));
    println!("{:?}", ("size:", width, "x", height));
    println!("{:?}", ("elapsed_sec:", elapsed));
}

fn main() {
    run_raytrace();
}
