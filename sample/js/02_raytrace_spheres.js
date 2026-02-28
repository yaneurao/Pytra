import * as math from "./pytra/std/math.js";
import { png } from "./pytra/runtime.js";
import { perf_counter } from "./pytra/std/time.js";

// 02: Sample that runs a mini sphere-only ray tracer and outputs a PNG image.
// Dependencies are kept minimal (time only) for transpilation compatibility.

function clamp01(v) {
    if (v < 0.0) {
        return 0.0;
    }
    if (v > 1.0) {
        return 1.0;
    }
    return v;
}

function hit_sphere(ox, oy, oz, dx, dy, dz, cx, cy, cz, r) {
    let lx = ox - cx;
    let ly = oy - cy;
    let lz = oz - cz;
    
    let a = dx * dx + dy * dy + dz * dz;
    let b = 2.0 * (lx * dx + ly * dy + lz * dz);
    let c = lx * lx + ly * ly + lz * lz - r * r;
    
    let d = b * b - 4.0 * a * c;
    if (d < 0.0) {
        return -1.0;
    }
    let sd = math.sqrt(d);
    let t0 = (-b - sd) / (2.0 * a);
    let t1 = (-b + sd) / (2.0 * a);
    
    if (t0 > 0.001) {
        return t0;
    }
    if (t1 > 0.001) {
        return t1;
    }
    return -1.0;
}

function render(width, height, aa) {
    let pixels = [];
    
    // Camera origin
    let ox = 0.0;
    let oy = 0.0;
    let oz = -3.0;
    
    // Light direction (normalized)
    let lx = -0.4;
    let ly = 0.8;
    let lz = -0.45;
    let __hoisted_cast_1 = Number(aa);
    let __hoisted_cast_2 = Number(height - 1);
    let __hoisted_cast_3 = Number(width - 1);
    let __hoisted_cast_4 = Number(height);
    
    const __start_1 = 0;
    for (let y = __start_1; y < height; y += 1) {
        const __start_2 = 0;
        for (let x = __start_2; x < width; x += 1) {
            let ar = 0;
            let ag = 0;
            let ab = 0;
            
            const __start_3 = 0;
            for (let ay = __start_3; ay < aa; ay += 1) {
                const __start_4 = 0;
                for (let ax = __start_4; ax < aa; ax += 1) {
                    let fy = (y + (ay + 0.5) / __hoisted_cast_1) / __hoisted_cast_2;
                    let fx = (x + (ax + 0.5) / __hoisted_cast_1) / __hoisted_cast_3;
                    let sy = 1.0 - 2.0 * fy;
                    let sx = (2.0 * fx - 1.0) * (width / __hoisted_cast_4);
                    
                    let dx = sx;
                    let dy = sy;
                    let dz = 1.0;
                    let inv_len = 1.0 / math.sqrt(dx * dx + dy * dy + dz * dz);
                    dx *= inv_len;
                    dy *= inv_len;
                    dz *= inv_len;
                    
                    let t_min = 1.0e30;
                    let hit_id = -1;
                    
                    let t = hit_sphere(ox, oy, oz, dx, dy, dz, -0.8, -0.2, 2.2, 0.8);
                    if (t > 0.0 && t < t_min) {
                        t_min = t;
                        hit_id = 0;
                    }
                    t = hit_sphere(ox, oy, oz, dx, dy, dz, 0.9, 0.1, 2.9, 0.95);
                    if (t > 0.0 && t < t_min) {
                        t_min = t;
                        hit_id = 1;
                    }
                    t = hit_sphere(ox, oy, oz, dx, dy, dz, 0.0, -1001.0, 3.0, 1000.0);
                    if (t > 0.0 && t < t_min) {
                        t_min = t;
                        hit_id = 2;
                    }
                    let r = 0;
                    let g = 0;
                    let b = 0;
                    
                    if (hit_id >= 0) {
                        let px = ox + dx * t_min;
                        let py = oy + dy * t_min;
                        let pz = oz + dz * t_min;
                        
                        let nx = 0.0;
                        let ny = 0.0;
                        let nz = 0.0;
                        
                        if (hit_id === 0) {
                            nx = (px + 0.8) / 0.8;
                            ny = (py + 0.2) / 0.8;
                            nz = (pz - 2.2) / 0.8;
                        } else {
                            if (hit_id === 1) {
                                nx = (px - 0.9) / 0.95;
                                ny = (py - 0.1) / 0.95;
                                nz = (pz - 2.9) / 0.95;
                            } else {
                                nx = 0.0;
                                ny = 1.0;
                                nz = 0.0;
                            }
                        }
                        let diff = nx * -lx + ny * -ly + nz * -lz;
                        diff = clamp01(diff);
                        
                        let base_r = 0.0;
                        let base_g = 0.0;
                        let base_b = 0.0;
                        
                        if (hit_id === 0) {
                            base_r = 0.95;
                            base_g = 0.35;
                            base_b = 0.25;
                        } else {
                            if (hit_id === 1) {
                                base_r = 0.25;
                                base_g = 0.55;
                                base_b = 0.95;
                            } else {
                                let checker = Math.trunc(Number((px + 50.0) * 0.8)) + Math.trunc(Number((pz + 50.0) * 0.8));
                                if (checker % 2 === 0) {
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
                        let shade = 0.12 + 0.88 * diff;
                        r = Math.trunc(Number(255.0 * clamp01(base_r * shade)));
                        g = Math.trunc(Number(255.0 * clamp01(base_g * shade)));
                        b = Math.trunc(Number(255.0 * clamp01(base_b * shade)));
                    } else {
                        let tsky = 0.5 * (dy + 1.0);
                        r = Math.trunc(Number(255.0 * (0.65 + 0.20 * tsky)));
                        g = Math.trunc(Number(255.0 * (0.75 + 0.18 * tsky)));
                        b = Math.trunc(Number(255.0 * (0.90 + 0.08 * tsky)));
                    }
                    ar += r;
                    ag += g;
                    ab += b;
                }
            }
            let samples = aa * aa;
            pixels.push(Math.floor(ar / samples));
            pixels.push(Math.floor(ag / samples));
            pixels.push(Math.floor(ab / samples));
        }
    }
    return pixels;
}

function run_raytrace() {
    let width = 1600;
    let height = 900;
    let aa = 2;
    let out_path = "sample/out/02_raytrace_spheres.png";
    
    let start = perf_counter();
    let pixels = render(width, height, aa);
    png.write_rgb_png(out_path, width, height, pixels);
    let elapsed = perf_counter() - start;
    
    console.log("output:", out_path);
    console.log("size:", width, "x", height);
    console.log("elapsed_sec:", elapsed);
}

run_raytrace();
