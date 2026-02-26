import * as math from "./pytra/std/math.js";
import { perf_counter } from "./pytra/std/time.js";
import { save_gif } from "./pytra/runtime/gif.js";

// 16: Sample that ray-traces chaotic rotation of glass sculptures and outputs a GIF.

function clamp01(v) {
    if (v < 0.0) {
        return 0.0;
    }
    if (v > 1.0) {
        return 1.0;
    }
    return v;
}

function dot(ax, ay, az, bx, by, bz) {
    return ax * bx + ay * by + az * bz;
}

function length(x, y, z) {
    return math.sqrt(x * x + y * y + z * z);
}

function normalize(x, y, z) {
    let l = length(x, y, z);
    if (l < 1e-9) {
        return [0.0, 0.0, 0.0];
    }
    return [x / l, y / l, z / l];
}

function reflect(ix, iy, iz, nx, ny, nz) {
    let d = dot(ix, iy, iz, nx, ny, nz) * 2.0;
    return [ix - d * nx, iy - d * ny, iz - d * nz];
}

function refract(ix, iy, iz, nx, ny, nz, eta) {
    // Simple IOR-based refraction. Return reflection direction on total internal reflection.
    let cosi = -dot(ix, iy, iz, nx, ny, nz);
    let sint2 = eta * eta * (1.0 - cosi * cosi);
    if (sint2 > 1.0) {
        return reflect(ix, iy, iz, nx, ny, nz);
    }
    let cost = math.sqrt(1.0 - sint2);
    let k = eta * cosi - cost;
    return [eta * ix + k * nx, eta * iy + k * ny, eta * iz + k * nz];
}

function schlick(cos_theta, f0) {
    let m = 1.0 - cos_theta;
    return f0 + (1.0 - f0) * m * m * m * m * m;
}

function sky_color(dx, dy, dz, tphase) {
    // Sky gradient + neon band
    let t = 0.5 * (dy + 1.0);
    let r = 0.06 + 0.20 * t;
    let g = 0.10 + 0.25 * t;
    let b = 0.16 + 0.45 * t;
    let band = 0.5 + 0.5 * math.sin(8.0 * dx + 6.0 * dz + tphase);
    r += 0.08 * band;
    g += 0.05 * band;
    b += 0.12 * band;
    return [clamp01(r), clamp01(g), clamp01(b)];
}

function sphere_intersect(ox, oy, oz, dx, dy, dz, cx, cy, cz, radius) {
    let lx = ox - cx;
    let ly = oy - cy;
    let lz = oz - cz;
    let b = lx * dx + ly * dy + lz * dz;
    let c = lx * lx + ly * ly + lz * lz - radius * radius;
    let h = b * b - c;
    if (h < 0.0) {
        return -1.0;
    }
    let s = math.sqrt(h);
    let t0 = -b - s;
    if (t0 > 1e-4) {
        return t0;
    }
    let t1 = -b + s;
    if (t1 > 1e-4) {
        return t1;
    }
    return -1.0;
}

function palette_332() {
    // 3-3-2 quantized palette. Lightweight quantization that stays fast after transpilation.
    let p = (typeof (256 * 3) === "number" ? new Array(Math.max(0, Math.trunc(Number((256 * 3))))).fill(0) : (Array.isArray((256 * 3)) ? (256 * 3).slice() : Array.from((256 * 3))));
    const __start_1 = 0;
    for (let i = __start_1; i < 256; i += 1) {
        let r = i >> 5 & 7;
        let g = i >> 2 & 7;
        let b = i & 3;
        p[(((i * 3 + 0) < 0) ? ((p).length + (i * 3 + 0)) : (i * 3 + 0))] = Math.trunc(Number(255 * r / 7));
        p[(((i * 3 + 1) < 0) ? ((p).length + (i * 3 + 1)) : (i * 3 + 1))] = Math.trunc(Number(255 * g / 7));
        p[(((i * 3 + 2) < 0) ? ((p).length + (i * 3 + 2)) : (i * 3 + 2))] = Math.trunc(Number(255 * b / 3));
    }
    return (Array.isArray((p)) ? (p).slice() : Array.from((p)));
}

function quantize_332(r, g, b) {
    let rr = Math.trunc(Number(clamp01(r) * 255.0));
    let gg = Math.trunc(Number(clamp01(g) * 255.0));
    let bb = Math.trunc(Number(clamp01(b) * 255.0));
    return (rr >> 5 << 5) + (gg >> 5 << 2) + (bb >> 6);
}

function render_frame(width, height, frame_id, frames_n) {
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
    
    const __tmp_2 = normalize(look_x - cam_x, look_y - cam_y, look_z - cam_z);
    let fwd_x = __tmp_2[0];
    let fwd_y = __tmp_2[1];
    let fwd_z = __tmp_2[2];
    const __tmp_3 = normalize(fwd_z, 0.0, -fwd_x);
    let right_x = __tmp_3[0];
    let right_y = __tmp_3[1];
    let right_z = __tmp_3[2];
    const __tmp_4 = normalize(right_y * fwd_z - right_z * fwd_y, right_z * fwd_x - right_x * fwd_z, right_x * fwd_y - right_y * fwd_x);
    let up_x = __tmp_4[0];
    let up_y = __tmp_4[1];
    let up_z = __tmp_4[2];
    
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
    
    let frame = (typeof (width * height) === "number" ? new Array(Math.max(0, Math.trunc(Number((width * height))))).fill(0) : (Array.isArray((width * height)) ? (width * height).slice() : Array.from((width * height))));
    let aspect = width / height;
    let fov = 1.25;
    
    const __start_5 = 0;
    for (let py = __start_5; py < height; py += 1) {
        let row_base = py * width;
        let sy = 1.0 - 2.0 * (py + 0.5) / height;
        const __start_6 = 0;
        for (let px = __start_6; px < width; px += 1) {
            let sx = (2.0 * (px + 0.5) / width - 1.0) * aspect;
            let rx = fwd_x + fov * (sx * right_x + sy * up_x);
            let ry = fwd_y + fov * (sx * right_y + sy * up_y);
            let rz = fwd_z + fov * (sx * right_z + sy * up_z);
            const __tmp_7 = normalize(rx, ry, rz);
            let dx = __tmp_7[0];
            let dy = __tmp_7[1];
            let dz = __tmp_7[2];
            
            // Search for the nearest hit.
            let best_t = 1e9;
            let hit_kind = 0;
            let r = 0.0;
            let g = 0.0;
            let b = 0.0;
            
            // Floor plane y=-1.2
            if (dy < -1e-6) {
                let tf = (-1.2 - cam_y) / dy;
                if (tf > 1e-4 && tf < best_t) {
                    best_t = tf;
                    hit_kind = 1;
                }
            }
            let t0 = sphere_intersect(cam_x, cam_y, cam_z, dx, dy, dz, s0x, s0y, s0z, 0.65);
            if (t0 > 0.0 && t0 < best_t) {
                best_t = t0;
                hit_kind = 2;
            }
            let t1 = sphere_intersect(cam_x, cam_y, cam_z, dx, dy, dz, s1x, s1y, s1z, 0.72);
            if (t1 > 0.0 && t1 < best_t) {
                best_t = t1;
                hit_kind = 3;
            }
            let t2 = sphere_intersect(cam_x, cam_y, cam_z, dx, dy, dz, s2x, s2y, s2z, 0.58);
            if (t2 > 0.0 && t2 < best_t) {
                best_t = t2;
                hit_kind = 4;
            }
            if (hit_kind === 0) {
                const __tmp_8 = sky_color(dx, dy, dz, tphase);
                r = __tmp_8[0];
                g = __tmp_8[1];
                b = __tmp_8[2];
            } else {
                if (hit_kind === 1) {
                    let hx = cam_x + best_t * dx;
                    let hz = cam_z + best_t * dz;
                    let cx = Math.trunc(Number(math.floor(hx * 2.0)));
                    let cz = Math.trunc(Number(math.floor(hz * 2.0)));
                    let checker = ((cx + cz) % 2 === 0 ? 0 : 1);
                    let base_r = (checker === 0 ? 0.10 : 0.04);
                    let base_g = (checker === 0 ? 0.11 : 0.05);
                    let base_b = (checker === 0 ? 0.13 : 0.08);
                    // Emissive sphere contribution.
                    let lxv = lx - hx;
                    let lyv = ly - -1.2;
                    let lzv = lz - hz;
                    const __tmp_9 = normalize(lxv, lyv, lzv);
                    let ldx = __tmp_9[0];
                    let ldy = __tmp_9[1];
                    let ldz = __tmp_9[2];
                    let ndotl = Math.max(ldy, 0.0);
                    let ldist2 = lxv * lxv + lyv * lyv + lzv * lzv;
                    let glow = 8.0 / (1.0 + ldist2);
                    r = base_r + 0.8 * glow + 0.20 * ndotl;
                    g = base_g + 0.5 * glow + 0.18 * ndotl;
                    b = base_b + 1.0 * glow + 0.24 * ndotl;
                } else {
                    let cx = 0.0;
                    let cy = 0.0;
                    let cz = 0.0;
                    let rad = 1.0;
                    if (hit_kind === 2) {
                        cx = s0x;
                        cy = s0y;
                        cz = s0z;
                        rad = 0.65;
                    } else {
                        if (hit_kind === 3) {
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
                    let hx = cam_x + best_t * dx;
                    let hy = cam_y + best_t * dy;
                    let hz = cam_z + best_t * dz;
                    const __tmp_10 = normalize((hx - cx) / rad, (hy - cy) / rad, (hz - cz) / rad);
                    let nx = __tmp_10[0];
                    let ny = __tmp_10[1];
                    let nz = __tmp_10[2];
                    
                    // Simple glass shading (reflection + refraction + light highlights).
                    const __tmp_11 = reflect(dx, dy, dz, nx, ny, nz);
                    let rdx = __tmp_11[0];
                    let rdy = __tmp_11[1];
                    let rdz = __tmp_11[2];
                    const __tmp_12 = refract(dx, dy, dz, nx, ny, nz, 1.0 / 1.45);
                    let tdx = __tmp_12[0];
                    let tdy = __tmp_12[1];
                    let tdz = __tmp_12[2];
                    const __tmp_13 = sky_color(rdx, rdy, rdz, tphase);
                    let sr = __tmp_13[0];
                    let sg = __tmp_13[1];
                    let sb = __tmp_13[2];
                    const __tmp_14 = sky_color(tdx, tdy, tdz, tphase + 0.8);
                    let tr = __tmp_14[0];
                    let tg = __tmp_14[1];
                    let tb = __tmp_14[2];
                    let cosi = Math.max(-(dx * nx + dy * ny + dz * nz), 0.0);
                    let fr = schlick(cosi, 0.04);
                    r = tr * (1.0 - fr) + sr * fr;
                    g = tg * (1.0 - fr) + sg * fr;
                    b = tb * (1.0 - fr) + sb * fr;
                    
                    let lxv = lx - hx;
                    let lyv = ly - hy;
                    let lzv = lz - hz;
                    const __tmp_15 = normalize(lxv, lyv, lzv);
                    let ldx = __tmp_15[0];
                    let ldy = __tmp_15[1];
                    let ldz = __tmp_15[2];
                    let ndotl = Math.max(nx * ldx + ny * ldy + nz * ldz, 0.0);
                    const __tmp_16 = normalize(ldx - dx, ldy - dy, ldz - dz);
                    let hvx = __tmp_16[0];
                    let hvy = __tmp_16[1];
                    let hvz = __tmp_16[2];
                    let ndoth = Math.max(nx * hvx + ny * hvy + nz * hvz, 0.0);
                    let spec = ndoth * ndoth;
                    spec = spec * spec;
                    spec = spec * spec;
                    spec = spec * spec;
                    let glow = 10.0 / (1.0 + lxv * lxv + lyv * lyv + lzv * lzv);
                    r += 0.20 * ndotl + 0.80 * spec + 0.45 * glow;
                    g += 0.18 * ndotl + 0.60 * spec + 0.35 * glow;
                    b += 0.26 * ndotl + 1.00 * spec + 0.65 * glow;
                    
                    // Slight tint variation per sphere.
                    if (hit_kind === 2) {
                        r *= 0.95;
                        g *= 1.05;
                        b *= 1.10;
                    } else {
                        if (hit_kind === 3) {
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
            frame[(((row_base + px) < 0) ? ((frame).length + (row_base + px)) : (row_base + px))] = quantize_332(r, g, b);
        }
    }
    return (Array.isArray((frame)) ? (frame).slice() : Array.from((frame)));
}

function run_16_glass_sculpture_chaos() {
    let width = 320;
    let height = 240;
    let frames_n = 72;
    let out_path = "sample/out/16_glass_sculpture_chaos.gif";
    
    let start = perf_counter();
    let frames = [];
    const __start_17 = 0;
    for (let i = __start_17; i < frames_n; i += 1) {
        frames.push(render_frame(width, height, i, frames_n));
    }
    save_gif(out_path, width, height, frames, palette_332());
    let elapsed = perf_counter() - start;
    console.log("output:", out_path);
    console.log("frames:", frames_n);
    console.log("elapsed_sec:", elapsed);
}

// __main__ guard
run_16_glass_sculpture_chaos();
