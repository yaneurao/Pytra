import { perf_counter } from "./pytra/std/time.js";
import { png } from "./pytra/utils.js";

// 04: Sample that renders an orbit-trap Julia set and writes a PNG image.

function render_orbit_trap_julia(width, height, max_iter, cx, cy) {
    let pixels = [];
    let __hoisted_cast_1 = Number(height - 1);
    let __hoisted_cast_2 = Number(width - 1);
    let __hoisted_cast_3 = Number(max_iter);
    
    const __start_1 = 0;
    for (let y = __start_1; y < height; y += 1) {
        let zy0 = -1.3 + 2.6 * (y / __hoisted_cast_1);
        const __start_2 = 0;
        for (let x = __start_2; x < width; x += 1) {
            let zx = -1.9 + 3.8 * (x / __hoisted_cast_2);
            let zy = zy0;
            
            let trap = 1.0e9;
            let i = 0;
            while (i < max_iter) {
                let ax = zx;
                if (ax < 0.0) {
                    ax = -ax;
                }
                let ay = zy;
                if (ay < 0.0) {
                    ay = -ay;
                }
                let dxy = zx - zy;
                if (dxy < 0.0) {
                    dxy = -dxy;
                }
                if (ax < trap) {
                    trap = ax;
                }
                if (ay < trap) {
                    trap = ay;
                }
                if (dxy < trap) {
                    trap = dxy;
                }
                let zx2 = zx * zx;
                let zy2 = zy * zy;
                if (zx2 + zy2 > 4.0) {
                    break;
                }
                zy = 2.0 * zx * zy + cy;
                zx = zx2 - zy2 + cx;
                i += 1;
            }
            let r = 0;
            let g = 0;
            let b = 0;
            if (i >= max_iter) {
                r = 0;
                g = 0;
                b = 0;
            } else {
                let trap_scaled = trap * 3.2;
                if (trap_scaled > 1.0) {
                    trap_scaled = 1.0;
                }
                if (trap_scaled < 0.0) {
                    trap_scaled = 0.0;
                }
                let t = i / __hoisted_cast_3;
                let tone = Math.trunc(Number(255.0 * (1.0 - trap_scaled)));
                r = Math.trunc(Number(tone * (0.35 + 0.65 * t)));
                g = Math.trunc(Number(tone * (0.15 + 0.85 * (1.0 - t))));
                b = Math.trunc(Number(255.0 * (0.25 + 0.75 * t)));
                if (r > 255) {
                    r = 255;
                }
                if (g > 255) {
                    g = 255;
                }
                if (b > 255) {
                    b = 255;
                }
            }
            pixels.push(r);
            pixels.push(g);
            pixels.push(b);
        }
    }
    return pixels;
}

function run_04_orbit_trap_julia() {
    let width = 1920;
    let height = 1080;
    let max_iter = 1400;
    let out_path = "sample/out/04_orbit_trap_julia.png";
    
    let start = perf_counter();
    let pixels = render_orbit_trap_julia(width, height, max_iter, -0.7269, 0.1889);
    png.write_rgb_png(out_path, width, height, pixels);
    let elapsed = perf_counter() - start;
    
    console.log("output:", out_path);
    console.log("size:", width, "x", height);
    console.log("max_iter:", max_iter);
    console.log("elapsed_sec:", elapsed);
}

run_04_orbit_trap_julia();
