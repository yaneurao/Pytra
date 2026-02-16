// このファイルは自動生成です（Python -> TypeScript native mode）。

const __pytra_root = process.cwd();
const py_runtime = require(__pytra_root + '/src/ts_module/py_runtime.ts');
const py_math = require(__pytra_root + '/src/ts_module/math.ts');
const py_time = require(__pytra_root + '/src/ts_module/time.ts');
const { pyPrint, pyLen, pyBool, pyRange, pyFloorDiv, pyMod, pyIn, pySlice, pyOrd, pyChr, pyBytearray, pyBytes, pyIsDigit, pyIsAlpha } = py_runtime;
const { perfCounter } = py_time;
const math = require(__pytra_root + '/src/ts_module/math.ts');
const perf_counter = perfCounter;
const { save_gif } = require(__pytra_root + '/src/ts_module/gif_helper.ts');

function clamp01(v) {
    if (pyBool(((v) < (0.0)))) {
        return 0.0;
    }
    if (pyBool(((v) > (1.0)))) {
        return 1.0;
    }
    return v;
}
function dot(ax, ay, az, bx, by, bz) {
    return ((((((ax) * (bx))) + (((ay) * (by))))) + (((az) * (bz))));
}
function length(x, y, z) {
    return math.sqrt(((((((x) * (x))) + (((y) * (y))))) + (((z) * (z)))));
}
function normalize(x, y, z) {
    let l = length(x, y, z);
    if (pyBool(((l) < (1e-09)))) {
        return [0.0, 0.0, 0.0];
    }
    return [((x) / (l)), ((y) / (l)), ((z) / (l))];
}
function reflect(ix, iy, iz, nx, ny, nz) {
    let d = ((dot(ix, iy, iz, nx, ny, nz)) * (2.0));
    return [((ix) - (((d) * (nx)))), ((iy) - (((d) * (ny)))), ((iz) - (((d) * (nz))))];
}
function refract(ix, iy, iz, nx, ny, nz, eta) {
    let cosi = (-(dot(ix, iy, iz, nx, ny, nz)));
    let sint2 = ((((eta) * (eta))) * (((1.0) - (((cosi) * (cosi))))));
    if (pyBool(((sint2) > (1.0)))) {
        return reflect(ix, iy, iz, nx, ny, nz);
    }
    let cost = math.sqrt(((1.0) - (sint2)));
    let k = ((((eta) * (cosi))) - (cost));
    return [((((eta) * (ix))) + (((k) * (nx)))), ((((eta) * (iy))) + (((k) * (ny)))), ((((eta) * (iz))) + (((k) * (nz))))];
}
function schlick(cos_theta, f0) {
    let m = ((1.0) - (cos_theta));
    return ((f0) + (((((1.0) - (f0))) * (((((((((m) * (m))) * (m))) * (m))) * (m))))));
}
function sky_color(dx, dy, dz, tphase) {
    let t = ((0.5) * (((dy) + (1.0))));
    let r = ((0.06) + (((0.2) * (t))));
    let g = ((0.1) + (((0.25) * (t))));
    let b = ((0.16) + (((0.45) * (t))));
    let band = ((0.5) + (((0.5) * (math.sin(((((((8.0) * (dx))) + (((6.0) * (dz))))) + (tphase)))))));
    r = r + ((0.08) * (band));
    g = g + ((0.05) * (band));
    b = b + ((0.12) * (band));
    return [clamp01(r), clamp01(g), clamp01(b)];
}
function sphere_intersect(ox, oy, oz, dx, dy, dz, cx, cy, cz, radius) {
    let lx = ((ox) - (cx));
    let ly = ((oy) - (cy));
    let lz = ((oz) - (cz));
    let b = ((((((lx) * (dx))) + (((ly) * (dy))))) + (((lz) * (dz))));
    let c = ((((((((lx) * (lx))) + (((ly) * (ly))))) + (((lz) * (lz))))) - (((radius) * (radius))));
    let h = ((((b) * (b))) - (c));
    if (pyBool(((h) < (0.0)))) {
        return (-(1.0));
    }
    let s = math.sqrt(h);
    let t0 = (((-(b))) - (s));
    if (pyBool(((t0) > (0.0001)))) {
        return t0;
    }
    let t1 = (((-(b))) + (s));
    if (pyBool(((t1) > (0.0001)))) {
        return t1;
    }
    return (-(1.0));
}
function palette_332() {
    let p = pyBytearray(((256) * (3)));
    let i;
    for (let __pytra_i_1 = 0; __pytra_i_1 < 256; __pytra_i_1 += 1) {
        i = __pytra_i_1;
        let r = ((((i) >> (5))) & (7));
        let g = ((((i) >> (2))) & (7));
        let b = ((i) & (3));
        p[((((i) * (3))) + (0))] = Math.trunc(Number(((((255) * (r))) / (7))));
        p[((((i) * (3))) + (1))] = Math.trunc(Number(((((255) * (g))) / (7))));
        p[((((i) * (3))) + (2))] = Math.trunc(Number(((((255) * (b))) / (3))));
    }
    return pyBytes(p);
}
function quantize_332(r, g, b) {
    let rr = Math.trunc(Number(((clamp01(r)) * (255.0))));
    let gg = Math.trunc(Number(((clamp01(g)) * (255.0))));
    let bb = Math.trunc(Number(((clamp01(b)) * (255.0))));
    return ((((((((rr) >> (5))) << (5))) + (((((gg) >> (5))) << (2))))) + (((bb) >> (6))));
}
function render_frame(width, height, frame_id, frames_n) {
    let t = ((frame_id) / (frames_n));
    let tphase = ((((2.0) * (math.pi))) * (t));
    let cam_r = 3.0;
    let cam_x = ((cam_r) * (math.cos(((tphase) * (0.9)))));
    let cam_y = ((1.1) + (((0.25) * (math.sin(((tphase) * (0.6)))))));
    let cam_z = ((cam_r) * (math.sin(((tphase) * (0.9)))));
    let look_x = 0.0;
    let look_y = 0.35;
    let look_z = 0.0;
    const __pytra_tuple_2 = normalize(((look_x) - (cam_x)), ((look_y) - (cam_y)), ((look_z) - (cam_z)));
    let fwd_x = __pytra_tuple_2[0];
    let fwd_y = __pytra_tuple_2[1];
    let fwd_z = __pytra_tuple_2[2];
    const __pytra_tuple_3 = normalize(fwd_z, 0.0, (-(fwd_x)));
    let right_x = __pytra_tuple_3[0];
    let right_y = __pytra_tuple_3[1];
    let right_z = __pytra_tuple_3[2];
    const __pytra_tuple_4 = normalize(((((right_y) * (fwd_z))) - (((right_z) * (fwd_y)))), ((((right_z) * (fwd_x))) - (((right_x) * (fwd_z)))), ((((right_x) * (fwd_y))) - (((right_y) * (fwd_x)))));
    let up_x = __pytra_tuple_4[0];
    let up_y = __pytra_tuple_4[1];
    let up_z = __pytra_tuple_4[2];
    let s0x = ((0.9) * (math.cos(((1.3) * (tphase)))));
    let s0y = ((0.15) + (((0.35) * (math.sin(((1.7) * (tphase)))))));
    let s0z = ((0.9) * (math.sin(((1.3) * (tphase)))));
    let s1x = ((1.2) * (math.cos(((((1.3) * (tphase))) + (2.094)))));
    let s1y = ((0.1) + (((0.4) * (math.sin(((((1.1) * (tphase))) + (0.8)))))));
    let s1z = ((1.2) * (math.sin(((((1.3) * (tphase))) + (2.094)))));
    let s2x = ((1.0) * (math.cos(((((1.3) * (tphase))) + (4.188)))));
    let s2y = ((0.2) + (((0.3) * (math.sin(((((1.5) * (tphase))) + (1.9)))))));
    let s2z = ((1.0) * (math.sin(((((1.3) * (tphase))) + (4.188)))));
    let lr = 0.35;
    let lx = ((2.4) * (math.cos(((tphase) * (1.8)))));
    let ly = ((1.8) + (((0.8) * (math.sin(((tphase) * (1.2)))))));
    let lz = ((2.4) * (math.sin(((tphase) * (1.8)))));
    let frame = pyBytearray(((width) * (height)));
    let aspect = ((width) / (height));
    let fov = 1.25;
    let i = 0;
    let py;
    for (let __pytra_i_5 = 0; __pytra_i_5 < height; __pytra_i_5 += 1) {
        py = __pytra_i_5;
        let sy = ((1.0) - (((((2.0) * (((py) + (0.5))))) / (height))));
        let px;
        for (let __pytra_i_6 = 0; __pytra_i_6 < width; __pytra_i_6 += 1) {
            px = __pytra_i_6;
            let sx = ((((((((2.0) * (((px) + (0.5))))) / (width))) - (1.0))) * (aspect));
            let rx = ((fwd_x) + (((fov) * (((((sx) * (right_x))) + (((sy) * (up_x))))))));
            let ry = ((fwd_y) + (((fov) * (((((sx) * (right_y))) + (((sy) * (up_y))))))));
            let rz = ((fwd_z) + (((fov) * (((((sx) * (right_z))) + (((sy) * (up_z))))))));
            const __pytra_tuple_7 = normalize(rx, ry, rz);
            let dx = __pytra_tuple_7[0];
            let dy = __pytra_tuple_7[1];
            let dz = __pytra_tuple_7[2];
            let best_t = 1000000000.0;
            let hit_kind = 0;
            let r = 0.0;
            let g = 0.0;
            let b = 0.0;
            if (pyBool(((dy) < ((-(1e-06)))))) {
                let tf = (((((-(1.2))) - (cam_y))) / (dy));
                if (pyBool((((tf) > (0.0001)) && ((tf) < (best_t))))) {
                    best_t = tf;
                    hit_kind = 1;
                }
            }
            let t0 = sphere_intersect(cam_x, cam_y, cam_z, dx, dy, dz, s0x, s0y, s0z, 0.65);
            if (pyBool((((t0) > (0.0)) && ((t0) < (best_t))))) {
                best_t = t0;
                hit_kind = 2;
            }
            let t1 = sphere_intersect(cam_x, cam_y, cam_z, dx, dy, dz, s1x, s1y, s1z, 0.72);
            if (pyBool((((t1) > (0.0)) && ((t1) < (best_t))))) {
                best_t = t1;
                hit_kind = 3;
            }
            let t2 = sphere_intersect(cam_x, cam_y, cam_z, dx, dy, dz, s2x, s2y, s2z, 0.58);
            if (pyBool((((t2) > (0.0)) && ((t2) < (best_t))))) {
                best_t = t2;
                hit_kind = 4;
            }
            if (pyBool(((hit_kind) === (0)))) {
                const __pytra_tuple_8 = sky_color(dx, dy, dz, tphase);
                r = __pytra_tuple_8[0];
                g = __pytra_tuple_8[1];
                b = __pytra_tuple_8[2];
            } else {
                if (pyBool(((hit_kind) === (1)))) {
                    let hx = ((cam_x) + (((best_t) * (dx))));
                    let hz = ((cam_z) + (((best_t) * (dz))));
                    let cx = Math.trunc(Number(math.floor(((hx) * (2.0)))));
                    let cz = Math.trunc(Number(math.floor(((hz) * (2.0)))));
                    let checker = (pyBool(((pyMod(((cx) + (cz)), 2)) === (0))) ? 0 : 1);
                    let base_r = (pyBool(((checker) === (0))) ? 0.1 : 0.04);
                    let base_g = (pyBool(((checker) === (0))) ? 0.11 : 0.05);
                    let base_b = (pyBool(((checker) === (0))) ? 0.13 : 0.08);
                    let lxv = ((lx) - (hx));
                    let lyv = ((ly) - ((-(1.2))));
                    let lzv = ((lz) - (hz));
                    const __pytra_tuple_9 = normalize(lxv, lyv, lzv);
                    let ldx = __pytra_tuple_9[0];
                    let ldy = __pytra_tuple_9[1];
                    let ldz = __pytra_tuple_9[2];
                    let ndotl = Math.max(ldy, 0.0);
                    let ldist2 = ((((((lxv) * (lxv))) + (((lyv) * (lyv))))) + (((lzv) * (lzv))));
                    let glow = ((8.0) / (((1.0) + (ldist2))));
                    r = ((((base_r) + (((0.8) * (glow))))) + (((0.2) * (ndotl))));
                    g = ((((base_g) + (((0.5) * (glow))))) + (((0.18) * (ndotl))));
                    b = ((((base_b) + (((1.0) * (glow))))) + (((0.24) * (ndotl))));
                } else {
                    let cx = 0.0;
                    let cy = 0.0;
                    let cz = 0.0;
                    let rad = 1.0;
                    if (pyBool(((hit_kind) === (2)))) {
                        cx = s0x;
                        cy = s0y;
                        cz = s0z;
                        rad = 0.65;
                    } else {
                        if (pyBool(((hit_kind) === (3)))) {
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
                    let hx = ((cam_x) + (((best_t) * (dx))));
                    let hy = ((cam_y) + (((best_t) * (dy))));
                    let hz = ((cam_z) + (((best_t) * (dz))));
                    const __pytra_tuple_10 = normalize(((((hx) - (cx))) / (rad)), ((((hy) - (cy))) / (rad)), ((((hz) - (cz))) / (rad)));
                    let nx = __pytra_tuple_10[0];
                    let ny = __pytra_tuple_10[1];
                    let nz = __pytra_tuple_10[2];
                    const __pytra_tuple_11 = reflect(dx, dy, dz, nx, ny, nz);
                    let rdx = __pytra_tuple_11[0];
                    let rdy = __pytra_tuple_11[1];
                    let rdz = __pytra_tuple_11[2];
                    const __pytra_tuple_12 = refract(dx, dy, dz, nx, ny, nz, ((1.0) / (1.45)));
                    let tdx = __pytra_tuple_12[0];
                    let tdy = __pytra_tuple_12[1];
                    let tdz = __pytra_tuple_12[2];
                    const __pytra_tuple_13 = sky_color(rdx, rdy, rdz, tphase);
                    let sr = __pytra_tuple_13[0];
                    let sg = __pytra_tuple_13[1];
                    let sb = __pytra_tuple_13[2];
                    const __pytra_tuple_14 = sky_color(tdx, tdy, tdz, ((tphase) + (0.8)));
                    let tr = __pytra_tuple_14[0];
                    let tg = __pytra_tuple_14[1];
                    let tb = __pytra_tuple_14[2];
                    let cosi = Math.max((-(((((((dx) * (nx))) + (((dy) * (ny))))) + (((dz) * (nz)))))), 0.0);
                    let fr = schlick(cosi, 0.04);
                    r = ((((tr) * (((1.0) - (fr))))) + (((sr) * (fr))));
                    g = ((((tg) * (((1.0) - (fr))))) + (((sg) * (fr))));
                    b = ((((tb) * (((1.0) - (fr))))) + (((sb) * (fr))));
                    let lxv = ((lx) - (hx));
                    let lyv = ((ly) - (hy));
                    let lzv = ((lz) - (hz));
                    const __pytra_tuple_15 = normalize(lxv, lyv, lzv);
                    let ldx = __pytra_tuple_15[0];
                    let ldy = __pytra_tuple_15[1];
                    let ldz = __pytra_tuple_15[2];
                    let ndotl = Math.max(((((((nx) * (ldx))) + (((ny) * (ldy))))) + (((nz) * (ldz)))), 0.0);
                    const __pytra_tuple_16 = normalize(((ldx) - (dx)), ((ldy) - (dy)), ((ldz) - (dz)));
                    let hvx = __pytra_tuple_16[0];
                    let hvy = __pytra_tuple_16[1];
                    let hvz = __pytra_tuple_16[2];
                    let ndoth = Math.max(((((((nx) * (hvx))) + (((ny) * (hvy))))) + (((nz) * (hvz)))), 0.0);
                    let spec = ((ndoth) * (ndoth));
                    spec = ((spec) * (spec));
                    spec = ((spec) * (spec));
                    spec = ((spec) * (spec));
                    let glow = ((10.0) / (((((((1.0) + (((lxv) * (lxv))))) + (((lyv) * (lyv))))) + (((lzv) * (lzv))))));
                    r = r + ((((((0.2) * (ndotl))) + (((0.8) * (spec))))) + (((0.45) * (glow))));
                    g = g + ((((((0.18) * (ndotl))) + (((0.6) * (spec))))) + (((0.35) * (glow))));
                    b = b + ((((((0.26) * (ndotl))) + (((1.0) * (spec))))) + (((0.65) * (glow))));
                    if (pyBool(((hit_kind) === (2)))) {
                        r = r * 0.95;
                        g = g * 1.05;
                        b = b * 1.1;
                    } else {
                        if (pyBool(((hit_kind) === (3)))) {
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
            r = math.sqrt(clamp01(r));
            g = math.sqrt(clamp01(g));
            b = math.sqrt(clamp01(b));
            frame[i] = quantize_332(r, g, b);
            i = i + 1;
        }
    }
    return pyBytes(frame);
}
function run_16_glass_sculpture_chaos() {
    let width = 320;
    let height = 240;
    let frames_n = 72;
    let out_path = 'sample/out/16_glass_sculpture_chaos.gif';
    let start = perf_counter();
    let frames = [];
    let i;
    for (let __pytra_i_17 = 0; __pytra_i_17 < frames_n; __pytra_i_17 += 1) {
        i = __pytra_i_17;
        frames.push(render_frame(width, height, i, frames_n));
    }
    save_gif(out_path, width, height, frames, palette_332(), 6, 0);
    let elapsed = ((perf_counter()) - (start));
    pyPrint('output:', out_path);
    pyPrint('frames:', frames_n);
    pyPrint('elapsed_sec:', elapsed);
}
run_16_glass_sculpture_chaos();
