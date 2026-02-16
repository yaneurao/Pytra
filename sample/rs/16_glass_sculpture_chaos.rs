#[path = "../../src/rs_module/py_runtime.rs"]
mod py_runtime;
use py_runtime::{math_cos, math_exp, math_floor, math_sin, math_sqrt, perf_counter, py_bool, py_grayscale_palette, py_in, py_isalpha, py_isdigit, py_len, py_print, py_save_gif, py_slice, py_write_rgb_png};

// このファイルは自動生成です（native Rust mode）。

fn clamp01(mut v: f64) -> f64 {
    if py_bool(&(((v) < (0.0)))) {
        return 0.0;
    }
    if py_bool(&(((v) > (1.0)))) {
        return 1.0;
    }
    return v;
}

fn dot(mut ax: f64, mut ay: f64, mut az: f64, mut bx: f64, mut by: f64, mut bz: f64) -> f64 {
    return ((((((ax) * (bx))) + (((ay) * (by))))) + (((az) * (bz))));
}

fn length(mut x: f64, mut y: f64, mut z: f64) -> f64 {
    return math_sqrt(((((((((x) * (x))) + (((y) * (y))))) + (((z) * (z))))) as f64));
}

fn normalize(mut x: f64, mut y: f64, mut z: f64) -> (f64, f64, f64) {
    let mut l = length(x, y, z);
    if py_bool(&(((l) < (1e-09)))) {
        return (0.0, 0.0, 0.0);
    }
    return (((( x ) as f64) / (( l ) as f64)), ((( y ) as f64) / (( l ) as f64)), ((( z ) as f64) / (( l ) as f64)));
}

fn reflect(mut ix: f64, mut iy: f64, mut iz: f64, mut nx: f64, mut ny: f64, mut nz: f64) -> (f64, f64, f64) {
    let mut d = ((dot(ix, iy, iz, nx, ny, nz)) * (2.0));
    return (((ix) - (((d) * (nx)))), ((iy) - (((d) * (ny)))), ((iz) - (((d) * (nz)))));
}

fn refract(mut ix: f64, mut iy: f64, mut iz: f64, mut nx: f64, mut ny: f64, mut nz: f64, mut eta: f64) -> (f64, f64, f64) {
    let mut cosi = (-dot(ix, iy, iz, nx, ny, nz));
    let mut sint2 = ((((eta) * (eta))) * (((1.0) - (((cosi) * (cosi))))));
    if py_bool(&(((sint2) > (1.0)))) {
        return reflect(ix, iy, iz, nx, ny, nz);
    }
    let mut cost = math_sqrt(((((1.0) - (sint2))) as f64));
    let mut k = ((((eta) * (cosi))) - (cost));
    return (((((eta) * (ix))) + (((k) * (nx)))), ((((eta) * (iy))) + (((k) * (ny)))), ((((eta) * (iz))) + (((k) * (nz)))));
}

fn schlick(mut cos_theta: f64, mut f0: f64) -> f64 {
    let mut m = ((1.0) - (cos_theta));
    return ((f0) + (((((1.0) - (f0))) * (((((((((m) * (m))) * (m))) * (m))) * (m))))));
}

fn sky_color(mut dx: f64, mut dy: f64, mut dz: f64, mut tphase: f64) -> (f64, f64, f64) {
    let mut t = ((0.5) * (((dy) + (1.0))));
    let mut r = ((0.06) + (((0.2) * (t))));
    let mut g = ((0.1) + (((0.25) * (t))));
    let mut b = ((0.16) + (((0.45) * (t))));
    let mut band = ((0.5) + (((0.5) * (math_sin(((((((((8.0) * (dx))) + (((6.0) * (dz))))) + (tphase))) as f64))))));
    r = r + ((0.08) * (band));
    g = g + ((0.05) * (band));
    b = b + ((0.12) * (band));
    return (clamp01(r), clamp01(g), clamp01(b));
}

fn sphere_intersect(mut ox: f64, mut oy: f64, mut oz: f64, mut dx: f64, mut dy: f64, mut dz: f64, mut cx: f64, mut cy: f64, mut cz: f64, mut radius: f64) -> f64 {
    let mut lx = ((ox) - (cx));
    let mut ly = ((oy) - (cy));
    let mut lz = ((oz) - (cz));
    let mut b = ((((((lx) * (dx))) + (((ly) * (dy))))) + (((lz) * (dz))));
    let mut c = ((((((((lx) * (lx))) + (((ly) * (ly))))) + (((lz) * (lz))))) - (((radius) * (radius))));
    let mut h = ((((b) * (b))) - (c));
    if py_bool(&(((h) < (0.0)))) {
        return (-1.0);
    }
    let mut s = math_sqrt(((h) as f64));
    let mut t0 = (((-b)) - (s));
    if py_bool(&(((t0) > (0.0001)))) {
        return t0;
    }
    let mut t1 = (((-b)) + (s));
    if py_bool(&(((t1) > (0.0001)))) {
        return t1;
    }
    return (-1.0);
}

fn palette_332() -> Vec<u8> {
    let mut p = vec![0u8; (((256) * (3))) as usize];
    for i in (0)..(256) {
        let mut r = ((((i) >> (5))) & (7));
        let mut g = ((((i) >> (2))) & (7));
        let mut b = ((i) & (3));
        (p)[((((i) * (3))) + (0)) as usize] = (((((( ((255) * (r)) ) as f64) / (( 7 ) as f64))) as i64)) as u8;
        (p)[((((i) * (3))) + (1)) as usize] = (((((( ((255) * (g)) ) as f64) / (( 7 ) as f64))) as i64)) as u8;
        (p)[((((i) * (3))) + (2)) as usize] = (((((( ((255) * (b)) ) as f64) / (( 3 ) as f64))) as i64)) as u8;
    }
    return (p).clone();
}

fn quantize_332(mut r: f64, mut g: f64, mut b: f64) -> i64 {
    let mut rr = ((((clamp01(r)) * (255.0))) as i64);
    let mut gg = ((((clamp01(g)) * (255.0))) as i64);
    let mut bb = ((((clamp01(b)) * (255.0))) as i64);
    return ((((((((rr) >> (5))) << (5))) + (((((gg) >> (5))) << (2))))) + (((bb) >> (6))));
}

fn render_frame(mut width: i64, mut height: i64, mut frame_id: i64, mut frames_n: i64) -> Vec<u8> {
    let mut t = ((( frame_id ) as f64) / (( frames_n ) as f64));
    let mut tphase = ((((2.0) * (std::f64::consts::PI))) * (t));
    let mut cam_r = 3.0;
    let mut cam_x = ((cam_r) * (math_cos(((((tphase) * (0.9))) as f64))));
    let mut cam_y = ((1.1) + (((0.25) * (math_sin(((((tphase) * (0.6))) as f64))))));
    let mut cam_z = ((cam_r) * (math_sin(((((tphase) * (0.9))) as f64))));
    let mut look_x = 0.0;
    let mut look_y = 0.35;
    let mut look_z = 0.0;
    let __pytra_tuple_rhs_1 = normalize(((look_x) - (cam_x)), ((look_y) - (cam_y)), ((look_z) - (cam_z)));
    let mut fwd_x = __pytra_tuple_rhs_1.0;
    let mut fwd_y = __pytra_tuple_rhs_1.1;
    let mut fwd_z = __pytra_tuple_rhs_1.2;
    let __pytra_tuple_rhs_2 = normalize(fwd_z, 0.0, (-fwd_x));
    let mut right_x = __pytra_tuple_rhs_2.0;
    let mut right_y = __pytra_tuple_rhs_2.1;
    let mut right_z = __pytra_tuple_rhs_2.2;
    let __pytra_tuple_rhs_3 = normalize(((((right_y) * (fwd_z))) - (((right_z) * (fwd_y)))), ((((right_z) * (fwd_x))) - (((right_x) * (fwd_z)))), ((((right_x) * (fwd_y))) - (((right_y) * (fwd_x)))));
    let mut up_x = __pytra_tuple_rhs_3.0;
    let mut up_y = __pytra_tuple_rhs_3.1;
    let mut up_z = __pytra_tuple_rhs_3.2;
    let mut s0x = ((0.9) * (math_cos(((((1.3) * (tphase))) as f64))));
    let mut s0y = ((0.15) + (((0.35) * (math_sin(((((1.7) * (tphase))) as f64))))));
    let mut s0z = ((0.9) * (math_sin(((((1.3) * (tphase))) as f64))));
    let mut s1x = ((1.2) * (math_cos(((((((1.3) * (tphase))) + (2.094))) as f64))));
    let mut s1y = ((0.1) + (((0.4) * (math_sin(((((((1.1) * (tphase))) + (0.8))) as f64))))));
    let mut s1z = ((1.2) * (math_sin(((((((1.3) * (tphase))) + (2.094))) as f64))));
    let mut s2x = ((1.0) * (math_cos(((((((1.3) * (tphase))) + (4.188))) as f64))));
    let mut s2y = ((0.2) + (((0.3) * (math_sin(((((((1.5) * (tphase))) + (1.9))) as f64))))));
    let mut s2z = ((1.0) * (math_sin(((((((1.3) * (tphase))) + (4.188))) as f64))));
    let mut lr = 0.35;
    let mut lx = ((2.4) * (math_cos(((((tphase) * (1.8))) as f64))));
    let mut ly = ((1.8) + (((0.8) * (math_sin(((((tphase) * (1.2))) as f64))))));
    let mut lz = ((2.4) * (math_sin(((((tphase) * (1.8))) as f64))));
    let mut frame = vec![0u8; (((width) * (height))) as usize];
    let mut aspect = ((( width ) as f64) / (( height ) as f64));
    let mut fov = 1.25;
    let mut i = 0;
    for py in (0)..(height) {
        let mut sy = ((1.0) - (((( ((2.0) * ((((( py ) as f64) + (( 0.5 ) as f64))))) ) as f64) / (( height ) as f64))));
        for px in (0)..(width) {
            let mut sx = ((((((( ((2.0) * ((((( px ) as f64) + (( 0.5 ) as f64))))) ) as f64) / (( width ) as f64))) - (1.0))) * (aspect));
            let mut rx = ((fwd_x) + (((fov) * (((((sx) * (right_x))) + (((sy) * (up_x))))))));
            let mut ry = ((fwd_y) + (((fov) * (((((sx) * (right_y))) + (((sy) * (up_y))))))));
            let mut rz = ((fwd_z) + (((fov) * (((((sx) * (right_z))) + (((sy) * (up_z))))))));
            let __pytra_tuple_rhs_4 = normalize(rx, ry, rz);
            let mut dx = __pytra_tuple_rhs_4.0;
            let mut dy = __pytra_tuple_rhs_4.1;
            let mut dz = __pytra_tuple_rhs_4.2;
            let mut best_t = 1000000000.0;
            let mut hit_kind = 0;
            let mut r = 0.0;
            let mut g = 0.0;
            let mut b = 0.0;
            if py_bool(&(((dy) < ((-1e-06))))) {
                let mut tf = ((( (((-1.2)) - (cam_y)) ) as f64) / (( dy ) as f64));
                if py_bool(&((((tf) > (0.0001)) && ((tf) < (best_t))))) {
                    best_t = tf;
                    hit_kind = 1;
                }
            }
            let mut t0 = sphere_intersect(cam_x, cam_y, cam_z, dx, dy, dz, s0x, s0y, s0z, 0.65);
            if py_bool(&((((t0) > (0.0)) && ((t0) < (best_t))))) {
                best_t = t0;
                hit_kind = 2;
            }
            let mut t1 = sphere_intersect(cam_x, cam_y, cam_z, dx, dy, dz, s1x, s1y, s1z, 0.72);
            if py_bool(&((((t1) > (0.0)) && ((t1) < (best_t))))) {
                best_t = t1;
                hit_kind = 3;
            }
            let mut t2 = sphere_intersect(cam_x, cam_y, cam_z, dx, dy, dz, s2x, s2y, s2z, 0.58);
            if py_bool(&((((t2) > (0.0)) && ((t2) < (best_t))))) {
                best_t = t2;
                hit_kind = 4;
            }
            if py_bool(&(((hit_kind) == (0)))) {
                let __pytra_tuple_rhs_5 = sky_color(dx, dy, dz, tphase);
                r = __pytra_tuple_rhs_5.0;
                g = __pytra_tuple_rhs_5.1;
                b = __pytra_tuple_rhs_5.2;
            } else {
                if py_bool(&(((hit_kind) == (1)))) {
                    let mut hx = ((cam_x) + (((best_t) * (dx))));
                    let mut hz = ((cam_z) + (((best_t) * (dz))));
                    let mut cx = ((math_floor(((((hx) * (2.0))) as f64))) as i64);
                    let mut cz = ((math_floor(((((hz) * (2.0))) as f64))) as i64);
                    let mut checker = (if py_bool(&(((((((cx) + (cz))) % (2))) == (0)))) { 0 } else { 1 });
                    let mut base_r = (if py_bool(&(((checker) == (0)))) { 0.1 } else { 0.04 });
                    let mut base_g = (if py_bool(&(((checker) == (0)))) { 0.11 } else { 0.05 });
                    let mut base_b = (if py_bool(&(((checker) == (0)))) { 0.13 } else { 0.08 });
                    let mut lxv = ((lx) - (hx));
                    let mut lyv = ((ly) - ((-1.2)));
                    let mut lzv = ((lz) - (hz));
                    let __pytra_tuple_rhs_6 = normalize(lxv, lyv, lzv);
                    let mut ldx = __pytra_tuple_rhs_6.0;
                    let mut ldy = __pytra_tuple_rhs_6.1;
                    let mut ldz = __pytra_tuple_rhs_6.2;
                    let mut ndotl = (if (ldy) > (0.0) { ldy } else { 0.0 });
                    let mut ldist2 = ((((((lxv) * (lxv))) + (((lyv) * (lyv))))) + (((lzv) * (lzv))));
                    let mut glow = ((( 8.0 ) as f64) / (( ((1.0) + (ldist2)) ) as f64));
                    r = ((((base_r) + (((0.8) * (glow))))) + (((0.2) * (ndotl))));
                    g = ((((base_g) + (((0.5) * (glow))))) + (((0.18) * (ndotl))));
                    b = ((((base_b) + (((1.0) * (glow))))) + (((0.24) * (ndotl))));
                } else {
                    let mut cx = 0.0;
                    let mut cy = 0.0;
                    let mut cz = 0.0;
                    let mut rad = 1.0;
                    if py_bool(&(((hit_kind) == (2)))) {
                        cx = s0x;
                        cy = s0y;
                        cz = s0z;
                        rad = 0.65;
                    } else {
                        if py_bool(&(((hit_kind) == (3)))) {
                            cx = s1x;
                            cy = s1y;
                            cz = s1z;
                            rad = 0.72;
                        } else {
                            cx = s2x;
                            cy = s2y;
                            cz = s2z;
                            rad = 0.58;
                        }
                    }
                    let mut hx = ((cam_x) + (((best_t) * (dx))));
                    let mut hy = ((cam_y) + (((best_t) * (dy))));
                    let mut hz = ((cam_z) + (((best_t) * (dz))));
                    let __pytra_tuple_rhs_7 = normalize(((( ((hx) - (cx)) ) as f64) / (( rad ) as f64)), ((( ((hy) - (cy)) ) as f64) / (( rad ) as f64)), ((( ((hz) - (cz)) ) as f64) / (( rad ) as f64)));
                    let mut nx = __pytra_tuple_rhs_7.0;
                    let mut ny = __pytra_tuple_rhs_7.1;
                    let mut nz = __pytra_tuple_rhs_7.2;
                    let __pytra_tuple_rhs_8 = reflect(dx, dy, dz, nx, ny, nz);
                    let mut rdx = __pytra_tuple_rhs_8.0;
                    let mut rdy = __pytra_tuple_rhs_8.1;
                    let mut rdz = __pytra_tuple_rhs_8.2;
                    let __pytra_tuple_rhs_9 = refract(dx, dy, dz, nx, ny, nz, ((( 1.0 ) as f64) / (( 1.45 ) as f64)));
                    let mut tdx = __pytra_tuple_rhs_9.0;
                    let mut tdy = __pytra_tuple_rhs_9.1;
                    let mut tdz = __pytra_tuple_rhs_9.2;
                    let __pytra_tuple_rhs_10 = sky_color(rdx, rdy, rdz, tphase);
                    let mut sr = __pytra_tuple_rhs_10.0;
                    let mut sg = __pytra_tuple_rhs_10.1;
                    let mut sb = __pytra_tuple_rhs_10.2;
                    let __pytra_tuple_rhs_11 = sky_color(tdx, tdy, tdz, ((tphase) + (0.8)));
                    let mut tr = __pytra_tuple_rhs_11.0;
                    let mut tg = __pytra_tuple_rhs_11.1;
                    let mut tb = __pytra_tuple_rhs_11.2;
                    let mut cosi = (if ((-((((((dx) * (nx))) + (((dy) * (ny))))) + (((dz) * (nz)))))) > (0.0) { (-((((((dx) * (nx))) + (((dy) * (ny))))) + (((dz) * (nz))))) } else { 0.0 });
                    let mut fr = schlick(cosi, 0.04);
                    r = ((((tr) * (((1.0) - (fr))))) + (((sr) * (fr))));
                    g = ((((tg) * (((1.0) - (fr))))) + (((sg) * (fr))));
                    b = ((((tb) * (((1.0) - (fr))))) + (((sb) * (fr))));
                    let mut lxv = ((lx) - (hx));
                    let mut lyv = ((ly) - (hy));
                    let mut lzv = ((lz) - (hz));
                    let __pytra_tuple_rhs_12 = normalize(lxv, lyv, lzv);
                    let mut ldx = __pytra_tuple_rhs_12.0;
                    let mut ldy = __pytra_tuple_rhs_12.1;
                    let mut ldz = __pytra_tuple_rhs_12.2;
                    let mut ndotl = (if (((((((nx) * (ldx))) + (((ny) * (ldy))))) + (((nz) * (ldz))))) > (0.0) { ((((((nx) * (ldx))) + (((ny) * (ldy))))) + (((nz) * (ldz)))) } else { 0.0 });
                    let __pytra_tuple_rhs_13 = normalize(((ldx) - (dx)), ((ldy) - (dy)), ((ldz) - (dz)));
                    let mut hvx = __pytra_tuple_rhs_13.0;
                    let mut hvy = __pytra_tuple_rhs_13.1;
                    let mut hvz = __pytra_tuple_rhs_13.2;
                    let mut ndoth = (if (((((((nx) * (hvx))) + (((ny) * (hvy))))) + (((nz) * (hvz))))) > (0.0) { ((((((nx) * (hvx))) + (((ny) * (hvy))))) + (((nz) * (hvz)))) } else { 0.0 });
                    let mut spec = ((ndoth) * (ndoth));
                    spec = ((spec) * (spec));
                    spec = ((spec) * (spec));
                    spec = ((spec) * (spec));
                    let mut glow = ((( 10.0 ) as f64) / (( ((((((1.0) + (((lxv) * (lxv))))) + (((lyv) * (lyv))))) + (((lzv) * (lzv)))) ) as f64));
                    r = r + ((((((0.2) * (ndotl))) + (((0.8) * (spec))))) + (((0.45) * (glow))));
                    g = g + ((((((0.18) * (ndotl))) + (((0.6) * (spec))))) + (((0.35) * (glow))));
                    b = b + ((((((0.26) * (ndotl))) + (((1.0) * (spec))))) + (((0.65) * (glow))));
                    if py_bool(&(((hit_kind) == (2)))) {
                        r = r * 0.95;
                        g = g * 1.05;
                        b = b * 1.1;
                    } else {
                        if py_bool(&(((hit_kind) == (3)))) {
                            r = r * 1.08;
                            g = g * 0.98;
                            b = b * 1.04;
                        } else {
                            r = r * 1.02;
                            g = g * 1.1;
                            b = b * 0.95;
                        }
                    }
                }
            }
            r = math_sqrt(((clamp01(r)) as f64));
            g = math_sqrt(((clamp01(g)) as f64));
            b = math_sqrt(((clamp01(b)) as f64));
            (frame)[i as usize] = (quantize_332(r, g, b)) as u8;
            i = i + 1;
        }
    }
    return (frame).clone();
}

fn run_16_glass_sculpture_chaos() -> () {
    let mut width = 320;
    let mut height = 240;
    let mut frames_n = 72;
    let mut out_path = "sample/out/16_glass_sculpture_chaos.gif".to_string();
    let mut start = perf_counter();
    let mut frames: Vec<Vec<u8>> = vec![];
    for i in (0)..(frames_n) {
        frames.push(render_frame(width, height, i, frames_n));
    }
    py_save_gif(&(out_path), width, height, &(frames), &(palette_332()), 6, 0);
    let mut elapsed = ((perf_counter()) - (start));
    println!("{} {}", "output:".to_string(), out_path);
    println!("{} {}", "frames:".to_string(), frames_n);
    println!("{} {}", "elapsed_sec:".to_string(), elapsed);
}

fn main() {
    run_16_glass_sculpture_chaos();
}
