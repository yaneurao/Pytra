import scala.collection.mutable
import scala.util.boundary, boundary.break
import scala.math.*
import java.nio.file.{Files, Paths}


// 02: Sample that runs a mini sphere-only ray tracer and outputs a PNG image.
// Dependencies are kept minimal (time only) for transpilation compatibility.

def clamp01(v: Double): Double = {
    if (v < 0.0) {
        return 0.0
    }
    if (v > 1.0) {
        return 1.0
    }
    return v
}

def hit_sphere(ox: Double, oy: Double, oz: Double, dx: Double, dy: Double, dz: Double, cx: Double, cy: Double, cz: Double, r: Double): Double = {
    var lx: Double = ox - cx
    var ly: Double = oy - cy
    var lz: Double = oz - cz
    var a: Double = ((dx * dx + dy * dy) + dz * dz)
    var b: Double = (2.0 * (((lx * dx + ly * dy) + lz * dz)))
    var c: Double = (((lx * lx + ly * ly) + lz * lz) - r * r)
    var d: Double = (b * b - (4.0 * a * c))
    if (d < 0.0) {
        return __pytra_float(-1.0)
    }
    var sd: Double = __pytra_float(scala.math.sqrt(__pytra_float(d)))
    var t0: Double = ((((-b) - sd)) / (2.0 * a))
    var t1: Double = ((((-b) + sd)) / (2.0 * a))
    if (t0 > 0.001) {
        return t0
    }
    if (t1 > 0.001) {
        return t1
    }
    return __pytra_float(-1.0)
}

def render(width: Long, height: Long, aa: Long): mutable.ArrayBuffer[Long] = {
    var pixels: mutable.ArrayBuffer[Long] = mutable.ArrayBuffer[Long]()
    var ox: Double = 0.0
    var oy: Double = 0.0
    var oz: Double = __pytra_float(-3.0)
    var lx: Double = __pytra_float(-0.4)
    var ly: Double = 0.8
    var lz: Double = __pytra_float(-0.45)
    var __hoisted_cast_1: Double = __pytra_float(aa)
    var __hoisted_cast_2: Double = __pytra_float(height - 1L)
    var __hoisted_cast_3: Double = __pytra_float(width - 1L)
    var __hoisted_cast_4: Double = __pytra_float(height)
    var y: Long = 0L
    while (y < height) {
        var x: Long = 0L
        while (x < width) {
            var ar: Long = 0L
            var ag: Long = 0L
            var ab: Long = 0L
            var ay: Long = 0L
            while (ay < aa) {
                var ax: Long = 0L
                while (ax < aa) {
                    var fy: Double = (((__pytra_float(y) + ((__pytra_float(ay) + 0.5) / __hoisted_cast_1))) / __hoisted_cast_2)
                    var fx: Double = (((__pytra_float(x) + ((__pytra_float(ax) + 0.5) / __hoisted_cast_1))) / __hoisted_cast_3)
                    var sy: Double = (1.0 - 2.0 * fy)
                    var sx: Double = (((2.0 * fx - 1.0)) * (__pytra_float(width) / __hoisted_cast_4))
                    var dx: Double = sx
                    var dy: Double = sy
                    var dz: Double = 1.0
                    var inv_len: Double = __pytra_float(1.0 / __pytra_float(scala.math.sqrt(__pytra_float((dx * dx + dy * dy) + dz * dz))))
                    dx *= inv_len
                    dy *= inv_len
                    dz *= inv_len
                    var t_min: Double = 1e+30
                    var hit_id: Long = __pytra_int(-1L)
                    var t: Double = hit_sphere(ox, oy, oz, dx, dy, dz, (-0.8), (-0.2), 2.2, 0.8)
                    if ((t > 0.0) && (t < t_min)) {
                        t_min = t
                        hit_id = 0L
                    }
                    t = hit_sphere(ox, oy, oz, dx, dy, dz, 0.9, 0.1, 2.9, 0.95)
                    if ((t > 0.0) && (t < t_min)) {
                        t_min = t
                        hit_id = 1L
                    }
                    t = hit_sphere(ox, oy, oz, dx, dy, dz, 0.0, (-1001.0), 3.0, 1000.0)
                    if ((t > 0.0) && (t < t_min)) {
                        t_min = t
                        hit_id = 2L
                    }
                    var r: Long = 0L
                    var g: Long = 0L
                    var b: Long = 0L
                    if (hit_id >= 0L) {
                        var px: Double = (ox + dx * t_min)
                        var py: Double = (oy + dy * t_min)
                        var pz: Double = (oz + dz * t_min)
                        var nx: Double = 0.0
                        var ny: Double = 0.0
                        var nz: Double = 0.0
                        if (hit_id == 0L) {
                            nx = ((px + 0.8) / 0.8)
                            ny = ((py + 0.2) / 0.8)
                            nz = ((pz - 2.2) / 0.8)
                        } else {
                            if (hit_id == 1L) {
                                nx = ((px - 0.9) / 0.95)
                                ny = ((py - 0.1) / 0.95)
                                nz = ((pz - 2.9) / 0.95)
                            } else {
                                nx = 0.0
                                ny = 1.0
                                nz = 0.0
                            }
                        }
                        var diff: Double = (((nx * (-lx)) + (ny * (-ly))) + (nz * (-lz)))
                        diff = clamp01(diff)
                        var base_r: Double = 0.0
                        var base_g: Double = 0.0
                        var base_b: Double = 0.0
                        if (hit_id == 0L) {
                            base_r = 0.95
                            base_g = 0.35
                            base_b = 0.25
                        } else {
                            if (hit_id == 1L) {
                                base_r = 0.25
                                base_g = 0.55
                                base_b = 0.95
                            } else {
                                var checker: Long = __pytra_int((px + 50.0) * 0.8) + __pytra_int((pz + 50.0) * 0.8)
                                if (checker % 2L == 0L) {
                                    base_r = 0.85
                                    base_g = 0.85
                                    base_b = 0.85
                                } else {
                                    base_r = 0.2
                                    base_g = 0.2
                                    base_b = 0.2
                                }
                            }
                        }
                        var shade: Double = (0.12 + 0.88 * diff)
                        r = __pytra_int(255.0 * clamp01(base_r * shade))
                        g = __pytra_int(255.0 * clamp01(base_g * shade))
                        b = __pytra_int(255.0 * clamp01(base_b * shade))
                    } else {
                        var tsky: Double = (0.5 * (dy + 1.0))
                        r = __pytra_int(255.0 * ((0.65 + 0.2 * tsky)))
                        g = __pytra_int(255.0 * ((0.75 + 0.18 * tsky)))
                        b = __pytra_int(255.0 * ((0.9 + 0.08 * tsky)))
                    }
                    ar += r
                    ag += g
                    ab += b
                    ax += 1L
                }
                ay += 1L
            }
            var samples: Long = aa * aa
            pixels.append(__pytra_int(ar / samples))
            pixels.append(__pytra_int(ag / samples))
            pixels.append(__pytra_int(ab / samples))
            x += 1L
        }
        y += 1L
    }
    return pixels
}

def run_raytrace(): Unit = {
    var width: Long = 1600L
    var height: Long = 900L
    var aa: Long = 2L
    var out_path: String = "sample/out/02_raytrace_spheres.png"
    var start: Double = __pytra_perf_counter()
    var pixels: mutable.ArrayBuffer[Long] = render(width, height, aa)
    __pytra_write_rgb_png(out_path, width, height, pixels)
    var elapsed: Double = __pytra_perf_counter() - start
    __pytra_print("output:", out_path)
    __pytra_print("size:", width, "x", height)
    __pytra_print("elapsed_sec:", elapsed)
}

def main(args: Array[String]): Unit = {
    run_raytrace()
}