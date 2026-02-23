// このファイルは自動生成です（Python -> JavaScript native mode）。

const __pytra_root = process.cwd();
const py_runtime = require(__pytra_root + '/src/js_module/py_runtime.js');
const py_math = require(__pytra_root + '/src/js_module/math.js');
const py_time = require(__pytra_root + '/src/js_module/time.js');
const { pyPrint, pyLen, pyBool, pyRange, pyFloorDiv, pyMod, pyIn, pySlice, pyOrd, pyChr, pyBytearray, pyBytes, pyIsDigit, pyIsAlpha } = py_runtime;
const { perfCounter } = py_time;
const math = require(__pytra_root + '/src/js_module/math.js');
const png_helper = require(__pytra_root + '/src/js_module/png_helper.js');
const perf_counter = perfCounter;

function clamp01(v) {
    if (pyBool(((v) < (0.0)))) {
        return 0.0;
    }
    if (pyBool(((v) > (1.0)))) {
        return 1.0;
    }
    return v;
}
function hit_sphere(ox, oy, oz, dx, dy, dz, cx, cy, cz, r) {
    let lx = ((ox) - (cx));
    let ly = ((oy) - (cy));
    let lz = ((oz) - (cz));
    let a = ((((((dx) * (dx))) + (((dy) * (dy))))) + (((dz) * (dz))));
    let b = ((2.0) * (((((((lx) * (dx))) + (((ly) * (dy))))) + (((lz) * (dz))))));
    let c = ((((((((lx) * (lx))) + (((ly) * (ly))))) + (((lz) * (lz))))) - (((r) * (r))));
    let d = ((((b) * (b))) - (((((4.0) * (a))) * (c))));
    if (pyBool(((d) < (0.0)))) {
        return (-(1.0));
    }
    let sd = math.sqrt(d);
    let t0 = (((((-(b))) - (sd))) / (((2.0) * (a))));
    let t1 = (((((-(b))) + (sd))) / (((2.0) * (a))));
    if (pyBool(((t0) > (0.001)))) {
        return t0;
    }
    if (pyBool(((t1) > (0.001)))) {
        return t1;
    }
    return (-(1.0));
}
function render(width, height, aa) {
    let pixels = pyBytearray();
    let ox = 0.0;
    let oy = 0.0;
    let oz = (-(3.0));
    let lx = (-(0.4));
    let ly = 0.8;
    let lz = (-(0.45));
    let y;
    for (let __pytra_i_1 = 0; __pytra_i_1 < height; __pytra_i_1 += 1) {
        y = __pytra_i_1;
        let x;
        for (let __pytra_i_2 = 0; __pytra_i_2 < width; __pytra_i_2 += 1) {
            x = __pytra_i_2;
            let ar = 0;
            let ag = 0;
            let ab = 0;
            let ay;
            for (let __pytra_i_3 = 0; __pytra_i_3 < aa; __pytra_i_3 += 1) {
                ay = __pytra_i_3;
                let ax;
                for (let __pytra_i_4 = 0; __pytra_i_4 < aa; __pytra_i_4 += 1) {
                    ax = __pytra_i_4;
                    let fy = ((((y) + (((((ay) + (0.5))) / (aa))))) / (((height) - (1))));
                    let fx = ((((x) + (((((ax) + (0.5))) / (aa))))) / (((width) - (1))));
                    let sy = ((1.0) - (((2.0) * (fy))));
                    let sx = ((((((2.0) * (fx))) - (1.0))) * (((width) / (height))));
                    let dx = sx;
                    let dy = sy;
                    let dz = 1.0;
                    let inv_len = ((1.0) / (math.sqrt(((((((dx) * (dx))) + (((dy) * (dy))))) + (((dz) * (dz)))))));
                    dx = dx * inv_len;
                    dy = dy * inv_len;
                    dz = dz * inv_len;
                    let t_min = 1e+30;
                    let hit_id = (-(1));
                    let t = hit_sphere(ox, oy, oz, dx, dy, dz, (-(0.8)), (-(0.2)), 2.2, 0.8);
                    if (pyBool((((t) > (0.0)) && ((t) < (t_min))))) {
                        t_min = t;
                        hit_id = 0;
                    }
                    t = hit_sphere(ox, oy, oz, dx, dy, dz, 0.9, 0.1, 2.9, 0.95);
                    if (pyBool((((t) > (0.0)) && ((t) < (t_min))))) {
                        t_min = t;
                        hit_id = 1;
                    }
                    t = hit_sphere(ox, oy, oz, dx, dy, dz, 0.0, (-(1001.0)), 3.0, 1000.0);
                    if (pyBool((((t) > (0.0)) && ((t) < (t_min))))) {
                        t_min = t;
                        hit_id = 2;
                    }
                    let r = 0;
                    let g = 0;
                    let b = 0;
                    if (pyBool(((hit_id) >= (0)))) {
                        let px = ((ox) + (((dx) * (t_min))));
                        let py = ((oy) + (((dy) * (t_min))));
                        let pz = ((oz) + (((dz) * (t_min))));
                        let nx = 0.0;
                        let ny = 0.0;
                        let nz = 0.0;
                        if (pyBool(((hit_id) === (0)))) {
                            nx = ((((px) + (0.8))) / (0.8));
                            ny = ((((py) + (0.2))) / (0.8));
                            nz = ((((pz) - (2.2))) / (0.8));
                        } else {
                            if (pyBool(((hit_id) === (1)))) {
                                nx = ((((px) - (0.9))) / (0.95));
                                ny = ((((py) - (0.1))) / (0.95));
                                nz = ((((pz) - (2.9))) / (0.95));
                            } else {
                                nx = 0.0;
                                ny = 1.0;
                                nz = 0.0;
                            }
                        }
                        let diff = ((((((nx) * ((-(lx))))) + (((ny) * ((-(ly))))))) + (((nz) * ((-(lz))))));
                        diff = clamp01(diff);
                        let base_r = 0.0;
                        let base_g = 0.0;
                        let base_b = 0.0;
                        if (pyBool(((hit_id) === (0)))) {
                            base_r = 0.95;
                            base_g = 0.35;
                            base_b = 0.25;
                        } else {
                            if (pyBool(((hit_id) === (1)))) {
                                base_r = 0.25;
                                base_g = 0.55;
                                base_b = 0.95;
                            } else {
                                let checker = ((Math.trunc(Number(((((px) + (50.0))) * (0.8))))) + (Math.trunc(Number(((((pz) + (50.0))) * (0.8))))));
                                if (pyBool(((pyMod(checker, 2)) === (0)))) {
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
                        let shade = ((0.12) + (((0.88) * (diff))));
                        r = Math.trunc(Number(((255.0) * (clamp01(((base_r) * (shade)))))));
                        g = Math.trunc(Number(((255.0) * (clamp01(((base_g) * (shade)))))));
                        b = Math.trunc(Number(((255.0) * (clamp01(((base_b) * (shade)))))));
                    } else {
                        let tsky = ((0.5) * (((dy) + (1.0))));
                        r = Math.trunc(Number(((255.0) * (((0.65) + (((0.2) * (tsky))))))));
                        g = Math.trunc(Number(((255.0) * (((0.75) + (((0.18) * (tsky))))))));
                        b = Math.trunc(Number(((255.0) * (((0.9) + (((0.08) * (tsky))))))));
                    }
                    ar = ar + r;
                    ag = ag + g;
                    ab = ab + b;
                }
            }
            let samples = ((aa) * (aa));
            pixels.push(pyFloorDiv(ar, samples));
            pixels.push(pyFloorDiv(ag, samples));
            pixels.push(pyFloorDiv(ab, samples));
        }
    }
    return pixels;
}
function run_raytrace() {
    let width = 1600;
    let height = 900;
    let aa = 2;
    let out_path = 'sample/out/02_raytrace_spheres.png';
    let start = perf_counter();
    let pixels = render(width, height, aa);
    png_helper.write_rgb_png(out_path, width, height, pixels);
    let elapsed = ((perf_counter()) - (start));
    pyPrint('output:', out_path);
    pyPrint('size:', width, 'x', height);
    pyPrint('elapsed_sec:', elapsed);
}
run_raytrace();
