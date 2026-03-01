import kotlin.math.*


// 16: Sample that ray-traces chaotic rotation of glass sculptures and outputs a GIF.

fun clamp01(v: Double): Double {
    if ((__pytra_float(v) < __pytra_float(0.0))) {
        return __pytra_float(0.0)
    }
    if ((__pytra_float(v) > __pytra_float(1.0))) {
        return __pytra_float(1.0)
    }
    return __pytra_float(v)
}

fun dot(ax: Double, ay: Double, az: Double, bx: Double, by: Double, bz: Double): Double {
    return __pytra_float((__pytra_float((__pytra_float((__pytra_float(ax) * __pytra_float(bx))) + __pytra_float((__pytra_float(ay) * __pytra_float(by))))) + __pytra_float((__pytra_float(az) * __pytra_float(bz)))))
}

fun length(x: Double, y: Double, z: Double): Double {
    return __pytra_float(kotlin.math.sqrt(__pytra_float((__pytra_float((__pytra_float((__pytra_float(x) * __pytra_float(x))) + __pytra_float((__pytra_float(y) * __pytra_float(y))))) + __pytra_float((__pytra_float(z) * __pytra_float(z)))))))
}

fun normalize(x: Double, y: Double, z: Double): MutableList<Any?> {
    var l: Double = __pytra_float(length(x, y, z))
    if ((__pytra_float(l) < __pytra_float(1e-09))) {
        return __pytra_as_list(mutableListOf(0.0, 0.0, 0.0))
    }
    return __pytra_as_list(mutableListOf((__pytra_float(x) / __pytra_float(l)), (__pytra_float(y) / __pytra_float(l)), (__pytra_float(z) / __pytra_float(l))))
}

fun reflect(ix: Double, iy: Double, iz: Double, nx: Double, ny: Double, nz: Double): MutableList<Any?> {
    var d: Double = __pytra_float((__pytra_float(dot(ix, iy, iz, nx, ny, nz)) * __pytra_float(2.0)))
    return __pytra_as_list(mutableListOf((__pytra_float(ix) - __pytra_float((__pytra_float(d) * __pytra_float(nx)))), (__pytra_float(iy) - __pytra_float((__pytra_float(d) * __pytra_float(ny)))), (__pytra_float(iz) - __pytra_float((__pytra_float(d) * __pytra_float(nz))))))
}

fun refract(ix: Double, iy: Double, iz: Double, nx: Double, ny: Double, nz: Double, eta: Double): MutableList<Any?> {
    var cosi: Double = __pytra_float((-dot(ix, iy, iz, nx, ny, nz)))
    var sint2: Double = __pytra_float((__pytra_float((__pytra_float(eta) * __pytra_float(eta))) * __pytra_float((__pytra_float(1.0) - __pytra_float((__pytra_float(cosi) * __pytra_float(cosi)))))))
    if ((__pytra_float(sint2) > __pytra_float(1.0))) {
        return __pytra_as_list(reflect(ix, iy, iz, nx, ny, nz))
    }
    var cost: Double = __pytra_float(kotlin.math.sqrt(__pytra_float((__pytra_float(1.0) - __pytra_float(sint2)))))
    var k: Double = __pytra_float(((__pytra_float(eta) * __pytra_float(cosi)) - cost))
    return __pytra_as_list(mutableListOf(((__pytra_float(eta) * __pytra_float(ix)) + (k * nx)), ((__pytra_float(eta) * __pytra_float(iy)) + (k * ny)), ((__pytra_float(eta) * __pytra_float(iz)) + (k * nz))))
}

fun schlick(cos_theta: Double, f0: Double): Double {
    var m: Double = __pytra_float((__pytra_float(1.0) - __pytra_float(cos_theta)))
    return __pytra_float((__pytra_float(f0) + __pytra_float((__pytra_float((__pytra_float(1.0) - __pytra_float(f0))) * __pytra_float((__pytra_float((__pytra_float((__pytra_float((__pytra_float(m) * __pytra_float(m))) * __pytra_float(m))) * __pytra_float(m))) * __pytra_float(m)))))))
}

fun sky_color(dx: Double, dy: Double, dz: Double, tphase: Double): MutableList<Any?> {
    var t: Double = __pytra_float((__pytra_float(0.5) * __pytra_float((__pytra_float(dy) + __pytra_float(1.0)))))
    var r: Double = __pytra_float((__pytra_float(0.06) + __pytra_float((__pytra_float(0.2) * __pytra_float(t)))))
    var g: Double = __pytra_float((__pytra_float(0.1) + __pytra_float((__pytra_float(0.25) * __pytra_float(t)))))
    var b: Double = __pytra_float((__pytra_float(0.16) + __pytra_float((__pytra_float(0.45) * __pytra_float(t)))))
    var band: Double = __pytra_float((0.5 + (0.5 * kotlin.math.sin(__pytra_float((__pytra_float((__pytra_float((__pytra_float(8.0) * __pytra_float(dx))) + __pytra_float((__pytra_float(6.0) * __pytra_float(dz))))) + __pytra_float(tphase)))))))
    r += (0.08 * band)
    g += (0.05 * band)
    b += (0.12 * band)
    return __pytra_as_list(mutableListOf(clamp01(r), clamp01(g), clamp01(b)))
}

fun sphere_intersect(ox: Double, oy: Double, oz: Double, dx: Double, dy: Double, dz: Double, cx: Double, cy: Double, cz: Double, radius: Double): Double {
    var lx: Double = __pytra_float((__pytra_float(ox) - __pytra_float(cx)))
    var ly: Double = __pytra_float((__pytra_float(oy) - __pytra_float(cy)))
    var lz: Double = __pytra_float((__pytra_float(oz) - __pytra_float(cz)))
    var b: Double = __pytra_float((__pytra_float((__pytra_float((__pytra_float(lx) * __pytra_float(dx))) + __pytra_float((__pytra_float(ly) * __pytra_float(dy))))) + __pytra_float((__pytra_float(lz) * __pytra_float(dz)))))
    var c: Double = __pytra_float((__pytra_float((__pytra_float((__pytra_float((__pytra_float(lx) * __pytra_float(lx))) + __pytra_float((__pytra_float(ly) * __pytra_float(ly))))) + __pytra_float((__pytra_float(lz) * __pytra_float(lz))))) - __pytra_float((__pytra_float(radius) * __pytra_float(radius)))))
    var h: Double = __pytra_float((__pytra_float((__pytra_float(b) * __pytra_float(b))) - __pytra_float(c)))
    if ((__pytra_float(h) < __pytra_float(0.0))) {
        return __pytra_float((-1.0))
    }
    var s: Double = __pytra_float(kotlin.math.sqrt(__pytra_float(h)))
    var t0: Double = __pytra_float(((-b) - s))
    if ((__pytra_float(t0) > __pytra_float(0.0001))) {
        return __pytra_float(t0)
    }
    var t1: Double = __pytra_float(((-b) + s))
    if ((__pytra_float(t1) > __pytra_float(0.0001))) {
        return __pytra_float(t1)
    }
    return __pytra_float((-1.0))
}

fun palette_332(): MutableList<Any?> {
    var p: MutableList<Any?> = __pytra_as_list(__pytra_bytearray((__pytra_int(256L) * __pytra_int(3L))))
    var __hoisted_cast_1: Double = __pytra_float(__pytra_float(7L))
    var __hoisted_cast_2: Double = __pytra_float(__pytra_float(3L))
    val __step_0 = __pytra_int(1L)
    var i = __pytra_int(0L)
    while ((__step_0 >= 0L && i < __pytra_int(256L)) || (__step_0 < 0L && i > __pytra_int(256L))) {
        var r: Long = __pytra_int((__pytra_int((__pytra_int(i) + __pytra_int(5L))) + __pytra_int(7L)))
        var g: Long = __pytra_int((__pytra_int((__pytra_int(i) + __pytra_int(2L))) + __pytra_int(7L)))
        var b: Long = __pytra_int((__pytra_int(i) + __pytra_int(3L)))
        __pytra_set_index(p, (__pytra_int((__pytra_int(i) * __pytra_int(3L))) + __pytra_int(0L)), __pytra_int((__pytra_float((__pytra_int(255L) * __pytra_int(r))) / __pytra_float(__hoisted_cast_1))))
        __pytra_set_index(p, (__pytra_int((__pytra_int(i) * __pytra_int(3L))) + __pytra_int(1L)), __pytra_int((__pytra_float((__pytra_int(255L) * __pytra_int(g))) / __pytra_float(__hoisted_cast_1))))
        __pytra_set_index(p, (__pytra_int((__pytra_int(i) * __pytra_int(3L))) + __pytra_int(2L)), __pytra_int((__pytra_float((__pytra_int(255L) * __pytra_int(b))) / __pytra_float(__hoisted_cast_2))))
        i += __step_0
    }
    return __pytra_as_list(__pytra_bytes(p))
}

fun quantize_332(r: Double, g: Double, b: Double): Long {
    var rr: Long = __pytra_int(__pytra_int((__pytra_float(clamp01(r)) * __pytra_float(255.0))))
    var gg: Long = __pytra_int(__pytra_int((__pytra_float(clamp01(g)) * __pytra_float(255.0))))
    var bb: Long = __pytra_int(__pytra_int((__pytra_float(clamp01(b)) * __pytra_float(255.0))))
    return __pytra_int((__pytra_int((__pytra_int((__pytra_int((__pytra_int(rr) + __pytra_int(5L))) + __pytra_int(5L))) + __pytra_int((__pytra_int((__pytra_int(gg) + __pytra_int(5L))) + __pytra_int(2L))))) + __pytra_int((__pytra_int(bb) + __pytra_int(6L)))))
}

fun render_frame(width: Long, height: Long, frame_id: Long, frames_n: Long): MutableList<Any?> {
    var t: Double = __pytra_float((__pytra_float(frame_id) / __pytra_float(frames_n)))
    var tphase: Double = __pytra_float(((2.0 * Math.PI) * t))
    var cam_r: Double = __pytra_float(3.0)
    var cam_x: Double = __pytra_float((cam_r * kotlin.math.cos(__pytra_float((tphase * 0.9)))))
    var cam_y: Double = __pytra_float((1.1 + (0.25 * kotlin.math.sin(__pytra_float((tphase * 0.6))))))
    var cam_z: Double = __pytra_float((cam_r * kotlin.math.sin(__pytra_float((tphase * 0.9)))))
    var look_x: Double = __pytra_float(0.0)
    var look_y: Double = __pytra_float(0.35)
    var look_z: Double = __pytra_float(0.0)
    val __tuple_0 = __pytra_as_list(normalize((look_x - cam_x), (look_y - cam_y), (look_z - cam_z)))
    var fwd_x: Double = __pytra_float(__tuple_0[0])
    var fwd_y: Double = __pytra_float(__tuple_0[1])
    var fwd_z: Double = __pytra_float(__tuple_0[2])
    val __tuple_1 = __pytra_as_list(normalize(fwd_z, 0.0, (-fwd_x)))
    var right_x: Double = __pytra_float(__tuple_1[0])
    var right_y: Double = __pytra_float(__tuple_1[1])
    var right_z: Double = __pytra_float(__tuple_1[2])
    val __tuple_2 = __pytra_as_list(normalize(((right_y * fwd_z) - (right_z * fwd_y)), ((right_z * fwd_x) - (right_x * fwd_z)), ((right_x * fwd_y) - (right_y * fwd_x))))
    var up_x: Double = __pytra_float(__tuple_2[0])
    var up_y: Double = __pytra_float(__tuple_2[1])
    var up_z: Double = __pytra_float(__tuple_2[2])
    var s0x: Double = __pytra_float((0.9 * kotlin.math.cos(__pytra_float((1.3 * tphase)))))
    var s0y: Double = __pytra_float((0.15 + (0.35 * kotlin.math.sin(__pytra_float((1.7 * tphase))))))
    var s0z: Double = __pytra_float((0.9 * kotlin.math.sin(__pytra_float((1.3 * tphase)))))
    var s1x: Double = __pytra_float((1.2 * kotlin.math.cos(__pytra_float(((1.3 * tphase) + 2.094)))))
    var s1y: Double = __pytra_float((0.1 + (0.4 * kotlin.math.sin(__pytra_float(((1.1 * tphase) + 0.8))))))
    var s1z: Double = __pytra_float((1.2 * kotlin.math.sin(__pytra_float(((1.3 * tphase) + 2.094)))))
    var s2x: Double = __pytra_float((1.0 * kotlin.math.cos(__pytra_float(((1.3 * tphase) + 4.188)))))
    var s2y: Double = __pytra_float((0.2 + (0.3 * kotlin.math.sin(__pytra_float(((1.5 * tphase) + 1.9))))))
    var s2z: Double = __pytra_float((1.0 * kotlin.math.sin(__pytra_float(((1.3 * tphase) + 4.188)))))
    var lr: Double = __pytra_float(0.35)
    var lx: Double = __pytra_float((2.4 * kotlin.math.cos(__pytra_float((tphase * 1.8)))))
    var ly: Double = __pytra_float((1.8 + (0.8 * kotlin.math.sin(__pytra_float((tphase * 1.2))))))
    var lz: Double = __pytra_float((2.4 * kotlin.math.sin(__pytra_float((tphase * 1.8)))))
    var frame: MutableList<Any?> = __pytra_as_list(__pytra_bytearray((__pytra_int(width) * __pytra_int(height))))
    var aspect: Double = __pytra_float((__pytra_float(width) / __pytra_float(height)))
    var fov: Double = __pytra_float(1.25)
    var __hoisted_cast_3: Double = __pytra_float(__pytra_float(height))
    var __hoisted_cast_4: Double = __pytra_float(__pytra_float(width))
    val __step_3 = __pytra_int(1L)
    var py = __pytra_int(0L)
    while ((__step_3 >= 0L && py < __pytra_int(height)) || (__step_3 < 0L && py > __pytra_int(height))) {
        var row_base: Long = __pytra_int((__pytra_int(py) * __pytra_int(width)))
        var sy: Double = __pytra_float((__pytra_float(1.0) - __pytra_float((__pytra_float((__pytra_float(2.0) * __pytra_float((__pytra_float(py) + __pytra_float(0.5))))) / __pytra_float(__hoisted_cast_3)))))
        val __step_4 = __pytra_int(1L)
        var px = __pytra_int(0L)
        while ((__step_4 >= 0L && px < __pytra_int(width)) || (__step_4 < 0L && px > __pytra_int(width))) {
            var sx: Double = __pytra_float((__pytra_float((__pytra_float((__pytra_float((__pytra_float(2.0) * __pytra_float((__pytra_float(px) + __pytra_float(0.5))))) / __pytra_float(__hoisted_cast_4))) - __pytra_float(1.0))) * __pytra_float(aspect)))
            var rx: Double = __pytra_float((fwd_x + (fov * ((sx * right_x) + (sy * up_x)))))
            var ry: Double = __pytra_float((fwd_y + (fov * ((sx * right_y) + (sy * up_y)))))
            var rz: Double = __pytra_float((fwd_z + (fov * ((sx * right_z) + (sy * up_z)))))
            val __tuple_5 = __pytra_as_list(normalize(rx, ry, rz))
            var dx: Double = __pytra_float(__tuple_5[0])
            var dy: Double = __pytra_float(__tuple_5[1])
            var dz: Double = __pytra_float(__tuple_5[2])
            var best_t: Double = __pytra_float(1000000000.0)
            var hit_kind: Long = __pytra_int(0L)
            var r: Double = __pytra_float(0.0)
            var g: Double = __pytra_float(0.0)
            var b: Double = __pytra_float(0.0)
            if ((__pytra_float(dy) < __pytra_float((-1e-06)))) {
                var tf: Double = __pytra_float((__pytra_float(((-1.2) - cam_y)) / __pytra_float(dy)))
                if (((__pytra_float(tf) > __pytra_float(0.0001)) && (__pytra_float(tf) < __pytra_float(best_t)))) {
                    best_t = __pytra_float(tf)
                    hit_kind = __pytra_int(1L)
                }
            }
            var t0: Double = __pytra_float(sphere_intersect(cam_x, cam_y, cam_z, dx, dy, dz, s0x, s0y, s0z, 0.65))
            if (((__pytra_float(t0) > __pytra_float(0.0)) && (__pytra_float(t0) < __pytra_float(best_t)))) {
                best_t = __pytra_float(t0)
                hit_kind = __pytra_int(2L)
            }
            var t1: Double = __pytra_float(sphere_intersect(cam_x, cam_y, cam_z, dx, dy, dz, s1x, s1y, s1z, 0.72))
            if (((__pytra_float(t1) > __pytra_float(0.0)) && (__pytra_float(t1) < __pytra_float(best_t)))) {
                best_t = __pytra_float(t1)
                hit_kind = __pytra_int(3L)
            }
            var t2: Double = __pytra_float(sphere_intersect(cam_x, cam_y, cam_z, dx, dy, dz, s2x, s2y, s2z, 0.58))
            if (((__pytra_float(t2) > __pytra_float(0.0)) && (__pytra_float(t2) < __pytra_float(best_t)))) {
                best_t = __pytra_float(t2)
                hit_kind = __pytra_int(4L)
            }
            if ((__pytra_int(hit_kind) == __pytra_int(0L))) {
                val __tuple_6 = __pytra_as_list(sky_color(dx, dy, dz, tphase))
                r = __pytra_float(__tuple_6[0])
                g = __pytra_float(__tuple_6[1])
                b = __pytra_float(__tuple_6[2])
            } else {
                if ((__pytra_int(hit_kind) == __pytra_int(1L))) {
                    var hx: Double = __pytra_float((cam_x + (best_t * dx)))
                    var hz: Double = __pytra_float((cam_z + (best_t * dz)))
                    var cx: Long = __pytra_int(__pytra_int(kotlin.math.floor(__pytra_float((hx * 2.0)))))
                    var cz: Long = __pytra_int(__pytra_int(kotlin.math.floor(__pytra_float((hz * 2.0)))))
                    var checker: Long = __pytra_int(__pytra_ifexp((__pytra_int((__pytra_int((__pytra_int(cx) + __pytra_int(cz))) % __pytra_int(2L))) == __pytra_int(0L)), 0L, 1L))
                    var base_r: Double = __pytra_float(__pytra_ifexp((__pytra_int(checker) == __pytra_int(0L)), 0.1, 0.04))
                    var base_g: Double = __pytra_float(__pytra_ifexp((__pytra_int(checker) == __pytra_int(0L)), 0.11, 0.05))
                    var base_b: Double = __pytra_float(__pytra_ifexp((__pytra_int(checker) == __pytra_int(0L)), 0.13, 0.08))
                    var lxv: Double = __pytra_float((lx - hx))
                    var lyv: Double = __pytra_float((ly - (-1.2)))
                    var lzv: Double = __pytra_float((lz - hz))
                    val __tuple_7 = __pytra_as_list(normalize(lxv, lyv, lzv))
                    var ldx: Double = __pytra_float(__tuple_7[0])
                    var ldy: Double = __pytra_float(__tuple_7[1])
                    var ldz: Double = __pytra_float(__tuple_7[2])
                    var ndotl: Double = __pytra_float(__pytra_max(ldy, 0.0))
                    var ldist2: Double = __pytra_float((((lxv * lxv) + (lyv * lyv)) + (lzv * lzv)))
                    var glow: Double = __pytra_float((__pytra_float(8.0) / __pytra_float((1.0 + ldist2))))
                    r = __pytra_float(((base_r + (0.8 * glow)) + (0.2 * ndotl)))
                    g = __pytra_float(((base_g + (0.5 * glow)) + (0.18 * ndotl)))
                    b = __pytra_float(((base_b + (1.0 * glow)) + (0.24 * ndotl)))
                } else {
                    var cx: Double = __pytra_float(0.0)
                    var cy: Double = __pytra_float(0.0)
                    var cz: Double = __pytra_float(0.0)
                    var rad: Double = __pytra_float(1.0)
                    if ((__pytra_int(hit_kind) == __pytra_int(2L))) {
                        cx = __pytra_float(s0x)
                        cy = __pytra_float(s0y)
                        cz = __pytra_float(s0z)
                        rad = __pytra_float(0.65)
                    } else {
                        if ((__pytra_int(hit_kind) == __pytra_int(3L))) {
                            cx = __pytra_float(s1x)
                            cy = __pytra_float(s1y)
                            cz = __pytra_float(s1z)
                            rad = __pytra_float(0.72)
                        } else {
                            cx = __pytra_float(s2x)
                            cy = __pytra_float(s2y)
                            cz = __pytra_float(s2z)
                            rad = __pytra_float(0.58)
                        }
                    }
                    var hx: Double = __pytra_float((cam_x + (best_t * dx)))
                    var hy: Double = __pytra_float((cam_y + (best_t * dy)))
                    var hz: Double = __pytra_float((cam_z + (best_t * dz)))
                    val __tuple_8 = __pytra_as_list(normalize((__pytra_float((hx - cx)) / __pytra_float(rad)), (__pytra_float((hy - cy)) / __pytra_float(rad)), (__pytra_float((hz - cz)) / __pytra_float(rad))))
                    var nx: Double = __pytra_float(__tuple_8[0])
                    var ny: Double = __pytra_float(__tuple_8[1])
                    var nz: Double = __pytra_float(__tuple_8[2])
                    val __tuple_9 = __pytra_as_list(reflect(dx, dy, dz, nx, ny, nz))
                    var rdx: Double = __pytra_float(__tuple_9[0])
                    var rdy: Double = __pytra_float(__tuple_9[1])
                    var rdz: Double = __pytra_float(__tuple_9[2])
                    val __tuple_10 = __pytra_as_list(refract(dx, dy, dz, nx, ny, nz, (__pytra_float(1.0) / __pytra_float(1.45))))
                    var tdx: Double = __pytra_float(__tuple_10[0])
                    var tdy: Double = __pytra_float(__tuple_10[1])
                    var tdz: Double = __pytra_float(__tuple_10[2])
                    val __tuple_11 = __pytra_as_list(sky_color(rdx, rdy, rdz, tphase))
                    var sr: Double = __pytra_float(__tuple_11[0])
                    var sg: Double = __pytra_float(__tuple_11[1])
                    var sb: Double = __pytra_float(__tuple_11[2])
                    val __tuple_12 = __pytra_as_list(sky_color(tdx, tdy, tdz, (tphase + 0.8)))
                    var tr: Double = __pytra_float(__tuple_12[0])
                    var tg: Double = __pytra_float(__tuple_12[1])
                    var tb: Double = __pytra_float(__tuple_12[2])
                    var cosi: Double = __pytra_float(__pytra_max((-(((dx * nx) + (dy * ny)) + (dz * nz))), 0.0))
                    var fr: Double = __pytra_float(schlick(cosi, 0.04))
                    r = __pytra_float(((tr * (__pytra_float(1.0) - __pytra_float(fr))) + (sr * fr)))
                    g = __pytra_float(((tg * (__pytra_float(1.0) - __pytra_float(fr))) + (sg * fr)))
                    b = __pytra_float(((tb * (__pytra_float(1.0) - __pytra_float(fr))) + (sb * fr)))
                    var lxv: Double = __pytra_float((lx - hx))
                    var lyv: Double = __pytra_float((ly - hy))
                    var lzv: Double = __pytra_float((lz - hz))
                    val __tuple_13 = __pytra_as_list(normalize(lxv, lyv, lzv))
                    var ldx: Double = __pytra_float(__tuple_13[0])
                    var ldy: Double = __pytra_float(__tuple_13[1])
                    var ldz: Double = __pytra_float(__tuple_13[2])
                    var ndotl: Double = __pytra_float(__pytra_max((((nx * ldx) + (ny * ldy)) + (nz * ldz)), 0.0))
                    val __tuple_14 = __pytra_as_list(normalize((ldx - dx), (ldy - dy), (ldz - dz)))
                    var hvx: Double = __pytra_float(__tuple_14[0])
                    var hvy: Double = __pytra_float(__tuple_14[1])
                    var hvz: Double = __pytra_float(__tuple_14[2])
                    var ndoth: Double = __pytra_float(__pytra_max((((nx * hvx) + (ny * hvy)) + (nz * hvz)), 0.0))
                    var spec: Double = __pytra_float((ndoth * ndoth))
                    spec = __pytra_float((spec * spec))
                    spec = __pytra_float((spec * spec))
                    spec = __pytra_float((spec * spec))
                    var glow: Double = __pytra_float((__pytra_float(10.0) / __pytra_float((((1.0 + (lxv * lxv)) + (lyv * lyv)) + (lzv * lzv)))))
                    r += (((0.2 * ndotl) + (0.8 * spec)) + (0.45 * glow))
                    g += (((0.18 * ndotl) + (0.6 * spec)) + (0.35 * glow))
                    b += (((0.26 * ndotl) + (1.0 * spec)) + (0.65 * glow))
                    if ((__pytra_int(hit_kind) == __pytra_int(2L))) {
                        r *= 0.95
                        g *= 1.05
                        b *= 1.1
                    } else {
                        if ((__pytra_int(hit_kind) == __pytra_int(3L))) {
                            r *= 1.08
                            g *= 0.98
                            b *= 1.04
                        } else {
                            r *= 1.02
                            g *= 1.1
                            b *= 0.95
                        }
                    }
                }
            }
            r = __pytra_float(kotlin.math.sqrt(__pytra_float(clamp01(r))))
            g = __pytra_float(kotlin.math.sqrt(__pytra_float(clamp01(g))))
            b = __pytra_float(kotlin.math.sqrt(__pytra_float(clamp01(b))))
            __pytra_set_index(frame, (__pytra_int(row_base) + __pytra_int(px)), quantize_332(r, g, b))
            px += __step_4
        }
        py += __step_3
    }
    return __pytra_as_list(__pytra_bytes(frame))
}

fun run_16_glass_sculpture_chaos() {
    var width: Long = __pytra_int(320L)
    var height: Long = __pytra_int(240L)
    var frames_n: Long = __pytra_int(72L)
    var out_path: String = __pytra_str("sample/out/16_glass_sculpture_chaos.gif")
    var start: Double = __pytra_float(__pytra_perf_counter())
    var frames: MutableList<Any?> = __pytra_as_list(mutableListOf<Any?>())
    val __step_0 = __pytra_int(1L)
    var i = __pytra_int(0L)
    while ((__step_0 >= 0L && i < __pytra_int(frames_n)) || (__step_0 < 0L && i > __pytra_int(frames_n))) {
        frames = __pytra_as_list(frames); frames.add(render_frame(width, height, i, frames_n))
        i += __step_0
    }
    __pytra_noop(out_path, width, height, frames, palette_332())
    var elapsed: Double = __pytra_float((__pytra_float(__pytra_perf_counter()) - __pytra_float(start)))
    __pytra_print("output:", out_path)
    __pytra_print("frames:", frames_n)
    __pytra_print("elapsed_sec:", elapsed)
}

fun main(args: Array<String>) {
    run_16_glass_sculpture_chaos()
}
