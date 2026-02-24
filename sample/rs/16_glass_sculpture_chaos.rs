use crate::math;
use crate::time::perf_counter;
use crate::pytra::runtime::gif::save_gif;

// 16: Sample that ray-traces chaotic rotation of glass sculptures and outputs a GIF.

fn clamp01(v: f64) -> f64 {
    if v < 0.0 {
        return 0.0;
    }
    if v > 1.0 {
        return 1.0;
    }
    return v;
}

fn dot(ax: f64, ay: f64, az: f64, bx: f64, by: f64, bz: f64) -> f64 {
    return ax * bx + ay * by + az * bz;
}

fn length(x: f64, y: f64, z: f64) -> f64 {
    return math.sqrt(x * x + y * y + z * z);
}

fn normalize(x: f64, y: f64, z: f64) -> (f64, f64, f64) {
    let l = length(x, y, z);
    if l < 1e-9 {
        return (0.0, 0.0, 0.0);
    }
    return (x / l, y / l, z / l);
}

fn reflect(ix: f64, iy: f64, iz: f64, nx: f64, ny: f64, nz: f64) -> (f64, f64, f64) {
    let d = dot(ix, iy, iz, nx, ny, nz) * 2.0;
    return (ix - d * nx, iy - d * ny, iz - d * nz);
}

fn refract(ix: f64, iy: f64, iz: f64, nx: f64, ny: f64, nz: f64, eta: f64) -> (f64, f64, f64) {
    // Simple IOR-based refraction. Return reflection direction on total internal reflection.
    let cosi = (-dot(ix, iy, iz, nx, ny, nz));
    let sint2 = eta * eta * (1.0 - cosi * cosi);
    if sint2 > 1.0 {
        return reflect(ix, iy, iz, nx, ny, nz);
    }
    let cost = math.sqrt(1.0 - sint2);
    let k = eta * cosi - cost;
    return (eta * ix + k * nx, eta * iy + k * ny, eta * iz + k * nz);
}

fn schlick(cos_theta: f64, f0: f64) -> f64 {
    let m = 1.0 - cos_theta;
    return f0 + (1.0 - f0) * m * m * m * m * m;
}

fn sky_color(dx: f64, dy: f64, dz: f64, tphase: f64) -> (f64, f64, f64) {
    // Sky gradient + neon band
    let t = 0.5 * (dy + 1.0);
    let mut r = 0.06 + 0.20 * t;
    let mut g = 0.10 + 0.25 * t;
    let mut b = 0.16 + 0.45 * t;
    let band = 0.5 + 0.5 * math.sin(8.0 * dx + 6.0 * dz + tphase);
    r += 0.08 * band;
    g += 0.05 * band;
    b += 0.12 * band;
    return (clamp01(r), clamp01(g), clamp01(b));
}

fn sphere_intersect(ox: f64, oy: f64, oz: f64, dx: f64, dy: f64, dz: f64, cx: f64, cy: f64, cz: f64, radius: f64) -> f64 {
    let lx = ox - cx;
    let ly = oy - cy;
    let lz = oz - cz;
    let b = lx * dx + ly * dy + lz * dz;
    let c = lx * lx + ly * ly + lz * lz - radius * radius;
    let h = b * b - c;
    if h < 0.0 {
        return (-1.0);
    }
    let s = math.sqrt(h);
    let t0 = (-b) - s;
    if t0 > 1e-4 {
        return t0;
    }
    let t1 = (-b) + s;
    if t1 > 1e-4 {
        return t1;
    }
    return (-1.0);
}

fn palette_332() -> Vec<u8> {
    // 3-3-2 quantized palette. Lightweight quantization that stays fast after transpilation.
    let mut p = bytearray(256 * 3);
    let mut i: i64 = 0;
    while i < 256 {
        let r = i >> 5 & 7;
        let g = i >> 2 & 7;
        let b = i & 3;
        p[i * 3 + 0 as usize] = 255 * r / 7 as i64;
        p[i * 3 + 1 as usize] = 255 * g / 7 as i64;
        p[i * 3 + 2 as usize] = 255 * b / 3 as i64;
        i += 1;
    }
    return bytes(p);
}

fn quantize_332(r: f64, g: f64, b: f64) -> i64 {
    let rr = clamp01(r) * 255.0 as i64;
    let gg = clamp01(g) * 255.0 as i64;
    let bb = clamp01(b) * 255.0 as i64;
    return (rr >> 5 << 5) + (gg >> 5 << 2) + (bb >> 6);
}

fn render_frame(width: i64, height: i64, frame_id: i64, frames_n: i64) -> Vec<u8> {
    let t = frame_id / frames_n;
    let tphase = 2.0 * math.pi * t;
    
    // Camera slowly orbits.
    let cam_r = 3.0;
    let cam_x = cam_r * math.cos(tphase * 0.9);
    let cam_y = 1.1 + 0.25 * math.sin(tphase * 0.6);
    let cam_z = cam_r * math.sin(tphase * 0.9);
    let look_x = 0.0;
    let look_y = 0.35;
    let look_z = 0.0;
    
    (fwd_x, fwd_y, fwd_z) = normalize(look_x - cam_x, look_y - cam_y, look_z - cam_z);
    (right_x, right_y, right_z) = normalize(fwd_z, 0.0, (-fwd_x));
    (up_x, up_y, up_z) = normalize(right_y * fwd_z - right_z * fwd_y, right_z * fwd_x - right_x * fwd_z, right_x * fwd_y - right_y * fwd_x);
    
    // Moving glass sculpture (3 spheres) and an emissive sphere.
    let s0x = 0.9 * math.cos(1.3 * tphase);
    let s0y = 0.15 + 0.35 * math.sin(1.7 * tphase);
    let s0z = 0.9 * math.sin(1.3 * tphase);
    let s1x = 1.2 * math.cos(1.3 * tphase + 2.094);
    let s1y = 0.10 + 0.40 * math.sin(1.1 * tphase + 0.8);
    let s1z = 1.2 * math.sin(1.3 * tphase + 2.094);
    let s2x = 1.0 * math.cos(1.3 * tphase + 4.188);
    let s2y = 0.20 + 0.30 * math.sin(1.5 * tphase + 1.9);
    let s2z = 1.0 * math.sin(1.3 * tphase + 4.188);
    let lr = 0.35;
    let lx = 2.4 * math.cos(tphase * 1.8);
    let ly = 1.8 + 0.8 * math.sin(tphase * 1.2);
    let lz = 2.4 * math.sin(tphase * 1.8);
    
    let mut frame = bytearray(width * height);
    let aspect = width / height;
    let fov = 1.25;
    let mut py: i64 = 0;
    while py < height {
        let row_base = py * width;
        let sy = 1.0 - 2.0 * (py + 0.5) / height;
        let mut px: i64 = 0;
        while px < width {
            let sx = (2.0 * (px + 0.5) / width - 1.0) * aspect;
            let rx = fwd_x + fov * (sx * right_x + sy * up_x);
            let ry = fwd_y + fov * (sx * right_y + sy * up_y);
            let rz = fwd_z + fov * (sx * right_z + sy * up_z);
            (dx, dy, dz) = normalize(rx, ry, rz);
            
            // Search for the nearest hit.
            let mut best_t = 1e9;
            let mut hit_kind = 0;
            let mut r = 0.0;
            let mut g = 0.0;
            let mut b = 0.0;
            
            // Floor plane y=-1.2
            if dy < (-1e-6) {
                let tf = ((-1.2) - cam_y) / dy;
                if (tf > 1e-4) && (tf < best_t) {
                    best_t = tf;
                    hit_kind = 1;
                }
            }
            let t0 = sphere_intersect(cam_x, cam_y, cam_z, dx, dy, dz, s0x, s0y, s0z, 0.65);
            if (t0 > 0.0) && (t0 < best_t) {
                best_t = t0;
                hit_kind = 2;
            }
            let t1 = sphere_intersect(cam_x, cam_y, cam_z, dx, dy, dz, s1x, s1y, s1z, 0.72);
            if (t1 > 0.0) && (t1 < best_t) {
                best_t = t1;
                hit_kind = 3;
            }
            let t2 = sphere_intersect(cam_x, cam_y, cam_z, dx, dy, dz, s2x, s2y, s2z, 0.58);
            if (t2 > 0.0) && (t2 < best_t) {
                best_t = t2;
                hit_kind = 4;
            }
            if hit_kind == 0 {
                (r, g, b) = sky_color(dx, dy, dz, tphase);
            } else {
                if hit_kind == 1 {
                    let mut hx = cam_x + best_t * dx;
                    let mut hz = cam_z + best_t * dz;
                    let mut cx = math.floor(hx * 2.0) as i64;
                    let mut cz = math.floor(hz * 2.0) as i64;
                    let checker = (((cx + cz) % 2 == 0) ? 0 : 1);
                    let base_r = ((checker == 0) ? 0.10 : 0.04);
                    let base_g = ((checker == 0) ? 0.11 : 0.05);
                    let base_b = ((checker == 0) ? 0.13 : 0.08);
                    // Emissive sphere contribution.
                    let mut lxv = lx - hx;
                    let mut lyv = ly - (-1.2);
                    let mut lzv = lz - hz;
                    (ldx, ldy, ldz) = normalize(lxv, lyv, lzv);
                    let mut ndotl = max(ldy, 0.0);
                    let ldist2 = lxv * lxv + lyv * lyv + lzv * lzv;
                    let mut glow = 8.0 / (1.0 + ldist2);
                    r = base_r + 0.8 * glow + 0.20 * ndotl;
                    g = base_g + 0.5 * glow + 0.18 * ndotl;
                    b = base_b + 1.0 * glow + 0.24 * ndotl;
                } else {
                    let mut cx = 0.0;
                    let mut cy = 0.0;
                    let mut cz = 0.0;
                    let mut rad = 1.0;
                    if hit_kind == 2 {
                        cx = s0x;
                        cy = s0y;
                        cz = s0z;
                        rad = 0.65;
                    } else {
                        if hit_kind == 3 {
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
                    let mut hx = cam_x + best_t * dx;
                    let hy = cam_y + best_t * dy;
                    let mut hz = cam_z + best_t * dz;
                    (nx, ny, nz) = normalize((hx - cx) / rad, (hy - cy) / rad, (hz - cz) / rad);
                    
                    // Simple glass shading (reflection + refraction + light highlights).
                    (rdx, rdy, rdz) = reflect(dx, dy, dz, nx, ny, nz);
                    (tdx, tdy, tdz) = refract(dx, dy, dz, nx, ny, nz, 1.0 / 1.45);
                    (sr, sg, sb) = sky_color(rdx, rdy, rdz, tphase);
                    (tr, tg, tb) = sky_color(tdx, tdy, tdz, tphase + 0.8);
                    let cosi = max((-dx * nx + dy * ny + dz * nz), 0.0);
                    let fr = schlick(cosi, 0.04);
                    r = tr * (1.0 - fr) + sr * fr;
                    g = tg * (1.0 - fr) + sg * fr;
                    b = tb * (1.0 - fr) + sb * fr;
                    
                    let mut lxv = lx - hx;
                    let mut lyv = ly - hy;
                    let mut lzv = lz - hz;
                    (ldx, ldy, ldz) = normalize(lxv, lyv, lzv);
                    let mut ndotl = max(nx * ldx + ny * ldy + nz * ldz, 0.0);
                    (hvx, hvy, hvz) = normalize(ldx - dx, ldy - dy, ldz - dz);
                    let ndoth = max(nx * hvx + ny * hvy + nz * hvz, 0.0);
                    let mut spec = ndoth * ndoth;
                    spec = spec * spec;
                    spec = spec * spec;
                    spec = spec * spec;
                    let mut glow = 10.0 / (1.0 + lxv * lxv + lyv * lyv + lzv * lzv);
                    r += 0.20 * ndotl + 0.80 * spec + 0.45 * glow;
                    g += 0.18 * ndotl + 0.60 * spec + 0.35 * glow;
                    b += 0.26 * ndotl + 1.00 * spec + 0.65 * glow;
                    
                    // Slight tint variation per sphere.
                    if hit_kind == 2 {
                        r *= 0.95;
                        g *= 1.05;
                        b *= 1.10;
                    } else {
                        if hit_kind == 3 {
                            r *= 1.08;
                            g *= 0.98;
                            b *= 1.04;
                        } else {
                            r *= 1.02;
                            g *= 1.10;
                            b *= 0.95;
                        }
                    }
                }
            }
            // Slightly stronger tone mapping.
            r = math.sqrt(clamp01(r));
            g = math.sqrt(clamp01(g));
            b = math.sqrt(clamp01(b));
            frame[row_base + px as usize] = quantize_332(r, g, b);
            px += 1;
        }
        py += 1;
    }
    return bytes(frame);
}

fn run_16_glass_sculpture_chaos() {
    let width = 320;
    let height = 240;
    let frames_n = 72;
    let out_path = "sample/out/16_glass_sculpture_chaos.gif";
    
    let start = perf_counter();
    let mut frames: Vec<Vec<u8>> = vec![];
    let mut i: i64 = 0;
    while i < frames_n {
        frames.push(render_frame(width, height, i, frames_n));
        i += 1;
    }
    save_gif(out_path, width, height, frames, palette_332());
    let elapsed = perf_counter() - start;
    println!("{:?}", ("output:", out_path));
    println!("{:?}", ("frames:", frames_n));
    println!("{:?}", ("elapsed_sec:", elapsed));
}

fn main() {
    run_16_glass_sculpture_chaos();
}
