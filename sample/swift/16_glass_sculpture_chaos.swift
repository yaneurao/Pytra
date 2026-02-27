// Auto-generated Pytra Swift native source from EAST3.
import Foundation

func __pytra_noop(_ args: Any...) {}

func __pytra_any_default() -> Any {
    return Int64(0)
}

func __pytra_assert(_ args: Any...) -> String {
    _ = args
    return "True"
}

func __pytra_perf_counter() -> Double {
    return Date().timeIntervalSince1970
}

func __pytra_truthy(_ v: Any?) -> Bool {
    guard let value = v else { return false }
    if let b = value as? Bool { return b }
    if let i = value as? Int64 { return i != 0 }
    if let i = value as? Int { return i != 0 }
    if let d = value as? Double { return d != 0.0 }
    if let s = value as? String { return s != "" }
    if let a = value as? [Any] { return !a.isEmpty }
    if let m = value as? [AnyHashable: Any] { return !m.isEmpty }
    return true
}

func __pytra_int(_ v: Any?) -> Int64 {
    guard let value = v else { return 0 }
    if let i = value as? Int64 { return i }
    if let i = value as? Int { return Int64(i) }
    if let d = value as? Double { return Int64(d) }
    if let b = value as? Bool { return b ? 1 : 0 }
    if let s = value as? String { return Int64(s) ?? 0 }
    return 0
}

func __pytra_float(_ v: Any?) -> Double {
    guard let value = v else { return 0.0 }
    if let d = value as? Double { return d }
    if let f = value as? Float { return Double(f) }
    if let i = value as? Int64 { return Double(i) }
    if let i = value as? Int { return Double(i) }
    if let b = value as? Bool { return b ? 1.0 : 0.0 }
    if let s = value as? String { return Double(s) ?? 0.0 }
    return 0.0
}

func __pytra_str(_ v: Any?) -> String {
    guard let value = v else { return "" }
    if let s = value as? String { return s }
    return String(describing: value)
}

func __pytra_len(_ v: Any?) -> Int64 {
    guard let value = v else { return 0 }
    if let s = value as? String { return Int64(s.count) }
    if let a = value as? [Any] { return Int64(a.count) }
    if let m = value as? [AnyHashable: Any] { return Int64(m.count) }
    return 0
}

func __pytra_index(_ i: Int64, _ n: Int64) -> Int64 {
    if i < 0 {
        return i + n
    }
    return i
}

func __pytra_getIndex(_ container: Any?, _ index: Any?) -> Any {
    if let list = container as? [Any] {
        if list.isEmpty { return __pytra_any_default() }
        let i = __pytra_index(__pytra_int(index), Int64(list.count))
        if i < 0 || i >= Int64(list.count) { return __pytra_any_default() }
        return list[Int(i)]
    }
    if let dict = container as? [AnyHashable: Any] {
        let key = AnyHashable(__pytra_str(index))
        return dict[key] ?? __pytra_any_default()
    }
    if let s = container as? String {
        let chars = Array(s)
        if chars.isEmpty { return "" }
        let i = __pytra_index(__pytra_int(index), Int64(chars.count))
        if i < 0 || i >= Int64(chars.count) { return "" }
        return String(chars[Int(i)])
    }
    return __pytra_any_default()
}

func __pytra_setIndex(_ container: Any?, _ index: Any?, _ value: Any?) {
    if var list = container as? [Any] {
        if list.isEmpty { return }
        let i = __pytra_index(__pytra_int(index), Int64(list.count))
        if i < 0 || i >= Int64(list.count) { return }
        list[Int(i)] = value as Any
        return
    }
    if var dict = container as? [AnyHashable: Any] {
        let key = AnyHashable(__pytra_str(index))
        dict[key] = value
    }
}

func __pytra_slice(_ container: Any?, _ lower: Any?, _ upper: Any?) -> Any {
    if let s = container as? String {
        let chars = Array(s)
        let n = Int64(chars.count)
        var lo = __pytra_index(__pytra_int(lower), n)
        var hi = __pytra_index(__pytra_int(upper), n)
        if lo < 0 { lo = 0 }
        if hi < 0 { hi = 0 }
        if lo > n { lo = n }
        if hi > n { hi = n }
        if hi < lo { hi = lo }
        if lo >= hi { return "" }
        return String(chars[Int(lo)..<Int(hi)])
    }
    if let list = container as? [Any] {
        let n = Int64(list.count)
        var lo = __pytra_index(__pytra_int(lower), n)
        var hi = __pytra_index(__pytra_int(upper), n)
        if lo < 0 { lo = 0 }
        if hi < 0 { hi = 0 }
        if lo > n { lo = n }
        if hi > n { hi = n }
        if hi < lo { hi = lo }
        if lo >= hi { return [Any]() }
        return Array(list[Int(lo)..<Int(hi)])
    }
    return __pytra_any_default()
}

func __pytra_isdigit(_ v: Any?) -> Bool {
    let s = __pytra_str(v)
    if s.isEmpty { return false }
    return s.unicodeScalars.allSatisfy { CharacterSet.decimalDigits.contains($0) }
}

func __pytra_isalpha(_ v: Any?) -> Bool {
    let s = __pytra_str(v)
    if s.isEmpty { return false }
    return s.unicodeScalars.allSatisfy { CharacterSet.letters.contains($0) }
}

func __pytra_contains(_ container: Any?, _ value: Any?) -> Bool {
    if let list = container as? [Any] {
        let needle = __pytra_str(value)
        for item in list {
            if __pytra_str(item) == needle {
                return true
            }
        }
        return false
    }
    if let dict = container as? [AnyHashable: Any] {
        return dict[AnyHashable(__pytra_str(value))] != nil
    }
    if let s = container as? String {
        let needle = __pytra_str(value)
        return s.contains(needle)
    }
    return false
}

func __pytra_ifexp(_ cond: Bool, _ a: Any, _ b: Any) -> Any {
    return cond ? a : b
}

func __pytra_bytearray(_ initValue: Any?) -> [Any] {
    if let i = initValue as? Int64 {
        return Array(repeating: Int64(0), count: max(0, Int(i)))
    }
    if let i = initValue as? Int {
        return Array(repeating: Int64(0), count: max(0, i))
    }
    if let arr = initValue as? [Any] {
        return arr
    }
    return []
}

func __pytra_bytes(_ v: Any?) -> [Any] {
    if let arr = v as? [Any] {
        return arr
    }
    return []
}

func __pytra_list_repeat(_ value: Any, _ count: Any?) -> [Any] {
    var out: [Any] = []
    var i: Int64 = 0
    let n = __pytra_int(count)
    while i < n {
        out.append(value)
        i += 1
    }
    return out
}

func __pytra_as_list(_ v: Any?) -> [Any] {
    if let arr = v as? [Any] { return arr }
    return []
}

func __pytra_as_u8_list(_ v: Any?) -> [UInt8] {
    if let arr = v as? [UInt8] { return arr }
    return []
}

func __pytra_as_dict(_ v: Any?) -> [AnyHashable: Any] {
    if let dict = v as? [AnyHashable: Any] { return dict }
    return [:]
}

func __pytra_pop_last(_ v: [Any]) -> [Any] {
    if v.isEmpty { return v }
    return Array(v.dropLast())
}

func __pytra_print(_ args: Any...) {
    if args.isEmpty {
        Swift.print()
        return
    }
    Swift.print(args.map { String(describing: $0) }.joined(separator: " "))
}

func __pytra_min(_ a: Any?, _ b: Any?) -> Any {
    let af = __pytra_float(a)
    let bf = __pytra_float(b)
    if af < bf {
        if __pytra_is_float(a) || __pytra_is_float(b) { return af }
        return __pytra_int(a)
    }
    if __pytra_is_float(a) || __pytra_is_float(b) { return bf }
    return __pytra_int(b)
}

func __pytra_max(_ a: Any?, _ b: Any?) -> Any {
    let af = __pytra_float(a)
    let bf = __pytra_float(b)
    if af > bf {
        if __pytra_is_float(a) || __pytra_is_float(b) { return af }
        return __pytra_int(a)
    }
    if __pytra_is_float(a) || __pytra_is_float(b) { return bf }
    return __pytra_int(b)
}

func __pytra_is_int(_ v: Any?) -> Bool {
    return (v is Int) || (v is Int64)
}

func __pytra_is_float(_ v: Any?) -> Bool {
    return v is Double
}

func __pytra_is_bool(_ v: Any?) -> Bool {
    return v is Bool
}

func __pytra_is_str(_ v: Any?) -> Bool {
    return v is String
}

func __pytra_is_list(_ v: Any?) -> Bool {
    return v is [Any]
}

func clamp01(v: Double) -> Double {
    if (__pytra_float(v) < __pytra_float(Double(0.0))) {
        return Double(0.0)
    }
    if (__pytra_float(v) > __pytra_float(Double(1.0))) {
        return Double(1.0)
    }
    return v
}

func dot(ax: Double, ay: Double, az: Double, bx: Double, by: Double, bz: Double) -> Double {
    return (__pytra_float((__pytra_float((__pytra_float(ax) * __pytra_float(bx))) + __pytra_float((__pytra_float(ay) * __pytra_float(by))))) + __pytra_float((__pytra_float(az) * __pytra_float(bz))))
}

func length(x: Double, y: Double, z: Double) -> Double {
    return sqrt(__pytra_float((__pytra_float((__pytra_float((__pytra_float(x) * __pytra_float(x))) + __pytra_float((__pytra_float(y) * __pytra_float(y))))) + __pytra_float((__pytra_float(z) * __pytra_float(z))))))
}

func normalize(x: Double, y: Double, z: Double) -> [Any] {
    var l: Double = __pytra_float(length(x, y, z))
    if (__pytra_float(l) < __pytra_float(Double(1e-09))) {
        return [Double(0.0), Double(0.0), Double(0.0)]
    }
    return [(__pytra_float(x) / __pytra_float(l)), (__pytra_float(y) / __pytra_float(l)), (__pytra_float(z) / __pytra_float(l))]
}

func reflect(ix: Double, iy: Double, iz: Double, nx: Double, ny: Double, nz: Double) -> [Any] {
    var d: Double = __pytra_float((__pytra_float(dot(ix, iy, iz, nx, ny, nz)) * __pytra_float(Double(2.0))))
    return [(__pytra_float(ix) - __pytra_float((__pytra_float(d) * __pytra_float(nx)))), (__pytra_float(iy) - __pytra_float((__pytra_float(d) * __pytra_float(ny)))), (__pytra_float(iz) - __pytra_float((__pytra_float(d) * __pytra_float(nz))))]
}

func refract(ix: Double, iy: Double, iz: Double, nx: Double, ny: Double, nz: Double, eta: Double) -> [Any] {
    var cosi: Double = __pytra_float((-dot(ix, iy, iz, nx, ny, nz)))
    var sint2: Double = __pytra_float((__pytra_float((__pytra_float(eta) * __pytra_float(eta))) * __pytra_float((__pytra_float(Double(1.0)) - __pytra_float((__pytra_float(cosi) * __pytra_float(cosi)))))))
    if (__pytra_float(sint2) > __pytra_float(Double(1.0))) {
        return reflect(ix, iy, iz, nx, ny, nz)
    }
    var cost: Any = sqrt(__pytra_float((__pytra_float(Double(1.0)) - __pytra_float(sint2))))
    var k: Double = __pytra_float(((__pytra_float(eta) * __pytra_float(cosi)) - cost))
    return [((__pytra_float(eta) * __pytra_float(ix)) + (k * nx)), ((__pytra_float(eta) * __pytra_float(iy)) + (k * ny)), ((__pytra_float(eta) * __pytra_float(iz)) + (k * nz))]
}

func schlick(cos_theta: Double, f0: Double) -> Double {
    var m: Double = __pytra_float((__pytra_float(Double(1.0)) - __pytra_float(cos_theta)))
    return (__pytra_float(f0) + __pytra_float((__pytra_float((__pytra_float(Double(1.0)) - __pytra_float(f0))) * __pytra_float((__pytra_float((__pytra_float((__pytra_float((__pytra_float(m) * __pytra_float(m))) * __pytra_float(m))) * __pytra_float(m))) * __pytra_float(m))))))
}

func sky_color(dx: Double, dy: Double, dz: Double, tphase: Double) -> [Any] {
    var t: Double = __pytra_float((__pytra_float(Double(0.5)) * __pytra_float((__pytra_float(dy) + __pytra_float(Double(1.0))))))
    var r: Double = __pytra_float((__pytra_float(Double(0.06)) + __pytra_float((__pytra_float(Double(0.2)) * __pytra_float(t)))))
    var g: Double = __pytra_float((__pytra_float(Double(0.1)) + __pytra_float((__pytra_float(Double(0.25)) * __pytra_float(t)))))
    var b: Double = __pytra_float((__pytra_float(Double(0.16)) + __pytra_float((__pytra_float(Double(0.45)) * __pytra_float(t)))))
    var band: Double = __pytra_float((Double(0.5) + (Double(0.5) * sin(__pytra_float((__pytra_float((__pytra_float((__pytra_float(Double(8.0)) * __pytra_float(dx))) + __pytra_float((__pytra_float(Double(6.0)) * __pytra_float(dz))))) + __pytra_float(tphase)))))))
    r += (Double(0.08) * band)
    g += (Double(0.05) * band)
    b += (Double(0.12) * band)
    return [clamp01(r), clamp01(g), clamp01(b)]
}

func sphere_intersect(ox: Double, oy: Double, oz: Double, dx: Double, dy: Double, dz: Double, cx: Double, cy: Double, cz: Double, radius: Double) -> Double {
    var lx: Double = __pytra_float((__pytra_float(ox) - __pytra_float(cx)))
    var ly: Double = __pytra_float((__pytra_float(oy) - __pytra_float(cy)))
    var lz: Double = __pytra_float((__pytra_float(oz) - __pytra_float(cz)))
    var b: Double = __pytra_float((__pytra_float((__pytra_float((__pytra_float(lx) * __pytra_float(dx))) + __pytra_float((__pytra_float(ly) * __pytra_float(dy))))) + __pytra_float((__pytra_float(lz) * __pytra_float(dz)))))
    var c: Double = __pytra_float((__pytra_float((__pytra_float((__pytra_float((__pytra_float(lx) * __pytra_float(lx))) + __pytra_float((__pytra_float(ly) * __pytra_float(ly))))) + __pytra_float((__pytra_float(lz) * __pytra_float(lz))))) - __pytra_float((__pytra_float(radius) * __pytra_float(radius)))))
    var h: Double = __pytra_float((__pytra_float((__pytra_float(b) * __pytra_float(b))) - __pytra_float(c)))
    if (__pytra_float(h) < __pytra_float(Double(0.0))) {
        return (-Double(1.0))
    }
    var s: Any = sqrt(__pytra_float(h))
    var t0: Double = __pytra_float(((-b) - s))
    if (__pytra_float(t0) > __pytra_float(Double(0.0001))) {
        return t0
    }
    var t1: Double = __pytra_float(((-b) + s))
    if (__pytra_float(t1) > __pytra_float(Double(0.0001))) {
        return t1
    }
    return (-Double(1.0))
}

func palette_332() -> [Any] {
    var p: [Any] = __pytra_as_list(__pytra_bytearray((__pytra_int(Int64(256)) * __pytra_int(Int64(3)))))
    let __step_0 = __pytra_int(Int64(1))
    var i = __pytra_int(Int64(0))
    while ((__step_0 >= 0 && i < __pytra_int(Int64(256))) || (__step_0 < 0 && i > __pytra_int(Int64(256)))) {
        var r: Int64 = __pytra_int((__pytra_int((__pytra_int(i) + __pytra_int(Int64(5)))) + __pytra_int(Int64(7))))
        var g: Int64 = __pytra_int((__pytra_int((__pytra_int(i) + __pytra_int(Int64(2)))) + __pytra_int(Int64(7))))
        var b: Int64 = __pytra_int((__pytra_int(i) + __pytra_int(Int64(3))))
        __pytra_setIndex(p, (__pytra_int((__pytra_int(i) * __pytra_int(Int64(3)))) + __pytra_int(Int64(0))), __pytra_int((__pytra_float((__pytra_int(Int64(255)) * __pytra_int(r))) / __pytra_float(Int64(7)))))
        __pytra_setIndex(p, (__pytra_int((__pytra_int(i) * __pytra_int(Int64(3)))) + __pytra_int(Int64(1))), __pytra_int((__pytra_float((__pytra_int(Int64(255)) * __pytra_int(g))) / __pytra_float(Int64(7)))))
        __pytra_setIndex(p, (__pytra_int((__pytra_int(i) * __pytra_int(Int64(3)))) + __pytra_int(Int64(2))), __pytra_int((__pytra_float((__pytra_int(Int64(255)) * __pytra_int(b))) / __pytra_float(Int64(3)))))
        i += __step_0
    }
    return __pytra_bytes(p)
}

func quantize_332(r: Double, g: Double, b: Double) -> Int64 {
    var rr: Int64 = __pytra_int(__pytra_int((__pytra_float(clamp01(r)) * __pytra_float(Double(255.0)))))
    var gg: Int64 = __pytra_int(__pytra_int((__pytra_float(clamp01(g)) * __pytra_float(Double(255.0)))))
    var bb: Int64 = __pytra_int(__pytra_int((__pytra_float(clamp01(b)) * __pytra_float(Double(255.0)))))
    return (__pytra_int((__pytra_int((__pytra_int((__pytra_int(rr) + __pytra_int(Int64(5)))) + __pytra_int(Int64(5)))) + __pytra_int((__pytra_int((__pytra_int(gg) + __pytra_int(Int64(5)))) + __pytra_int(Int64(2)))))) + __pytra_int((__pytra_int(bb) + __pytra_int(Int64(6)))))
}

func render_frame(width: Int64, height: Int64, frame_id: Int64, frames_n: Int64) -> [Any] {
    var t: Double = __pytra_float((__pytra_float(frame_id) / __pytra_float(frames_n)))
    var tphase: Double = __pytra_float(((Double(2.0) * Double.pi) * t))
    var cam_r: Double = __pytra_float(Double(3.0))
    var cam_x: Double = __pytra_float((cam_r * cos(__pytra_float((tphase * Double(0.9))))))
    var cam_y: Double = __pytra_float((Double(1.1) + (Double(0.25) * sin(__pytra_float((tphase * Double(0.6)))))))
    var cam_z: Double = __pytra_float((cam_r * sin(__pytra_float((tphase * Double(0.9))))))
    var look_x: Double = __pytra_float(Double(0.0))
    var look_y: Double = __pytra_float(Double(0.35))
    var look_z: Double = __pytra_float(Double(0.0))
    let __tuple_0 = __pytra_as_list(normalize((look_x - cam_x), (look_y - cam_y), (look_z - cam_z)))
    var fwd_x: Double = __pytra_float(__tuple_0[0])
    var fwd_y: Double = __pytra_float(__tuple_0[1])
    var fwd_z: Double = __pytra_float(__tuple_0[2])
    let __tuple_1 = __pytra_as_list(normalize(fwd_z, Double(0.0), (-fwd_x)))
    var right_x: Double = __pytra_float(__tuple_1[0])
    var right_y: Double = __pytra_float(__tuple_1[1])
    var right_z: Double = __pytra_float(__tuple_1[2])
    let __tuple_2 = __pytra_as_list(normalize(((right_y * fwd_z) - (right_z * fwd_y)), ((right_z * fwd_x) - (right_x * fwd_z)), ((right_x * fwd_y) - (right_y * fwd_x))))
    var up_x: Double = __pytra_float(__tuple_2[0])
    var up_y: Double = __pytra_float(__tuple_2[1])
    var up_z: Double = __pytra_float(__tuple_2[2])
    var s0x: Double = __pytra_float((Double(0.9) * cos(__pytra_float((Double(1.3) * tphase)))))
    var s0y: Double = __pytra_float((Double(0.15) + (Double(0.35) * sin(__pytra_float((Double(1.7) * tphase))))))
    var s0z: Double = __pytra_float((Double(0.9) * sin(__pytra_float((Double(1.3) * tphase)))))
    var s1x: Double = __pytra_float((Double(1.2) * cos(__pytra_float(((Double(1.3) * tphase) + Double(2.094))))))
    var s1y: Double = __pytra_float((Double(0.1) + (Double(0.4) * sin(__pytra_float(((Double(1.1) * tphase) + Double(0.8)))))))
    var s1z: Double = __pytra_float((Double(1.2) * sin(__pytra_float(((Double(1.3) * tphase) + Double(2.094))))))
    var s2x: Double = __pytra_float((Double(1.0) * cos(__pytra_float(((Double(1.3) * tphase) + Double(4.188))))))
    var s2y: Double = __pytra_float((Double(0.2) + (Double(0.3) * sin(__pytra_float(((Double(1.5) * tphase) + Double(1.9)))))))
    var s2z: Double = __pytra_float((Double(1.0) * sin(__pytra_float(((Double(1.3) * tphase) + Double(4.188))))))
    var lr: Double = __pytra_float(Double(0.35))
    var lx: Double = __pytra_float((Double(2.4) * cos(__pytra_float((tphase * Double(1.8))))))
    var ly: Double = __pytra_float((Double(1.8) + (Double(0.8) * sin(__pytra_float((tphase * Double(1.2)))))))
    var lz: Double = __pytra_float((Double(2.4) * sin(__pytra_float((tphase * Double(1.8))))))
    var frame: [Any] = __pytra_as_list(__pytra_bytearray((__pytra_int(width) * __pytra_int(height))))
    var aspect: Double = __pytra_float((__pytra_float(width) / __pytra_float(height)))
    var fov: Double = __pytra_float(Double(1.25))
    let __step_3 = __pytra_int(Int64(1))
    var py = __pytra_int(Int64(0))
    while ((__step_3 >= 0 && py < __pytra_int(height)) || (__step_3 < 0 && py > __pytra_int(height))) {
        var row_base: Int64 = __pytra_int((__pytra_int(py) * __pytra_int(width)))
        var sy: Double = __pytra_float((__pytra_float(Double(1.0)) - __pytra_float((__pytra_float((__pytra_float(Double(2.0)) * __pytra_float((__pytra_float(py) + __pytra_float(Double(0.5)))))) / __pytra_float(height)))))
        let __step_4 = __pytra_int(Int64(1))
        var px = __pytra_int(Int64(0))
        while ((__step_4 >= 0 && px < __pytra_int(width)) || (__step_4 < 0 && px > __pytra_int(width))) {
            var sx: Double = __pytra_float((__pytra_float((__pytra_float((__pytra_float((__pytra_float(Double(2.0)) * __pytra_float((__pytra_float(px) + __pytra_float(Double(0.5)))))) / __pytra_float(width))) - __pytra_float(Double(1.0)))) * __pytra_float(aspect)))
            var rx: Double = __pytra_float((fwd_x + (fov * ((sx * right_x) + (sy * up_x)))))
            var ry: Double = __pytra_float((fwd_y + (fov * ((sx * right_y) + (sy * up_y)))))
            var rz: Double = __pytra_float((fwd_z + (fov * ((sx * right_z) + (sy * up_z)))))
            let __tuple_5 = __pytra_as_list(normalize(rx, ry, rz))
            var dx: Double = __pytra_float(__tuple_5[0])
            var dy: Double = __pytra_float(__tuple_5[1])
            var dz: Double = __pytra_float(__tuple_5[2])
            var best_t: Double = __pytra_float(Double(1000000000.0))
            var hit_kind: Int64 = __pytra_int(Int64(0))
            var r: Double = __pytra_float(Double(0.0))
            var g: Double = __pytra_float(Double(0.0))
            var b: Double = __pytra_float(Double(0.0))
            if (__pytra_float(dy) < __pytra_float((-Double(1e-06)))) {
                var tf: Double = __pytra_float((__pytra_float(((-Double(1.2)) - cam_y)) / __pytra_float(dy)))
                if ((__pytra_float(tf) > __pytra_float(Double(0.0001))) && (__pytra_float(tf) < __pytra_float(best_t))) {
                    best_t = __pytra_float(tf)
                    hit_kind = __pytra_int(Int64(1))
                }
            }
            var t0: Double = __pytra_float(sphere_intersect(cam_x, cam_y, cam_z, dx, dy, dz, s0x, s0y, s0z, Double(0.65)))
            if ((__pytra_float(t0) > __pytra_float(Double(0.0))) && (__pytra_float(t0) < __pytra_float(best_t))) {
                best_t = __pytra_float(t0)
                hit_kind = __pytra_int(Int64(2))
            }
            var t1: Double = __pytra_float(sphere_intersect(cam_x, cam_y, cam_z, dx, dy, dz, s1x, s1y, s1z, Double(0.72)))
            if ((__pytra_float(t1) > __pytra_float(Double(0.0))) && (__pytra_float(t1) < __pytra_float(best_t))) {
                best_t = __pytra_float(t1)
                hit_kind = __pytra_int(Int64(3))
            }
            var t2: Double = __pytra_float(sphere_intersect(cam_x, cam_y, cam_z, dx, dy, dz, s2x, s2y, s2z, Double(0.58)))
            if ((__pytra_float(t2) > __pytra_float(Double(0.0))) && (__pytra_float(t2) < __pytra_float(best_t))) {
                best_t = __pytra_float(t2)
                hit_kind = __pytra_int(Int64(4))
            }
            if (__pytra_int(hit_kind) == __pytra_int(Int64(0))) {
                let __tuple_6 = __pytra_as_list(sky_color(dx, dy, dz, tphase))
                r = __pytra_float(__tuple_6[0])
                g = __pytra_float(__tuple_6[1])
                b = __pytra_float(__tuple_6[2])
            } else {
                if (__pytra_int(hit_kind) == __pytra_int(Int64(1))) {
                    var hx: Double = __pytra_float((cam_x + (best_t * dx)))
                    var hz: Double = __pytra_float((cam_z + (best_t * dz)))
                    var cx: Int64 = __pytra_int(__pytra_int(floor(__pytra_float((hx * Double(2.0))))))
                    var cz: Int64 = __pytra_int(__pytra_int(floor(__pytra_float((hz * Double(2.0))))))
                    var checker: Int64 = __pytra_int(__pytra_ifexp((__pytra_int((__pytra_int((__pytra_int(cx) + __pytra_int(cz))) % __pytra_int(Int64(2)))) == __pytra_int(Int64(0))), Int64(0), Int64(1)))
                    var base_r: Double = __pytra_float(__pytra_ifexp((__pytra_int(checker) == __pytra_int(Int64(0))), Double(0.1), Double(0.04)))
                    var base_g: Double = __pytra_float(__pytra_ifexp((__pytra_int(checker) == __pytra_int(Int64(0))), Double(0.11), Double(0.05)))
                    var base_b: Double = __pytra_float(__pytra_ifexp((__pytra_int(checker) == __pytra_int(Int64(0))), Double(0.13), Double(0.08)))
                    var lxv: Double = __pytra_float((lx - hx))
                    var lyv: Double = __pytra_float((ly - (-Double(1.2))))
                    var lzv: Double = __pytra_float((lz - hz))
                    let __tuple_7 = __pytra_as_list(normalize(lxv, lyv, lzv))
                    var ldx: Double = __pytra_float(__tuple_7[0])
                    var ldy: Double = __pytra_float(__tuple_7[1])
                    var ldz: Double = __pytra_float(__tuple_7[2])
                    var ndotl: Int64 = __pytra_int(__pytra_max(ldy, Double(0.0)))
                    var ldist2: Double = __pytra_float((((lxv * lxv) + (lyv * lyv)) + (lzv * lzv)))
                    var glow: Double = __pytra_float((__pytra_float(Double(8.0)) / __pytra_float((Double(1.0) + ldist2))))
                    r = __pytra_float(((base_r + (Double(0.8) * glow)) + (Double(0.2) * ndotl)))
                    g = __pytra_float(((base_g + (Double(0.5) * glow)) + (Double(0.18) * ndotl)))
                    b = __pytra_float(((base_b + (Double(1.0) * glow)) + (Double(0.24) * ndotl)))
                } else {
                    var cx: Double = __pytra_float(Double(0.0))
                    var cy: Double = __pytra_float(Double(0.0))
                    var cz: Double = __pytra_float(Double(0.0))
                    var rad: Double = __pytra_float(Double(1.0))
                    if (__pytra_int(hit_kind) == __pytra_int(Int64(2))) {
                        cx = __pytra_float(s0x)
                        cy = __pytra_float(s0y)
                        cz = __pytra_float(s0z)
                        rad = __pytra_float(Double(0.65))
                    } else {
                        if (__pytra_int(hit_kind) == __pytra_int(Int64(3))) {
                            cx = __pytra_float(s1x)
                            cy = __pytra_float(s1y)
                            cz = __pytra_float(s1z)
                            rad = __pytra_float(Double(0.72))
                        } else {
                            cx = __pytra_float(s2x)
                            cy = __pytra_float(s2y)
                            cz = __pytra_float(s2z)
                            rad = __pytra_float(Double(0.58))
                        }
                    }
                    var hx: Double = __pytra_float((cam_x + (best_t * dx)))
                    var hy: Double = __pytra_float((cam_y + (best_t * dy)))
                    var hz: Double = __pytra_float((cam_z + (best_t * dz)))
                    let __tuple_8 = __pytra_as_list(normalize((__pytra_float((hx - cx)) / __pytra_float(rad)), (__pytra_float((hy - cy)) / __pytra_float(rad)), (__pytra_float((hz - cz)) / __pytra_float(rad))))
                    var nx: Double = __pytra_float(__tuple_8[0])
                    var ny: Double = __pytra_float(__tuple_8[1])
                    var nz: Double = __pytra_float(__tuple_8[2])
                    let __tuple_9 = __pytra_as_list(reflect(dx, dy, dz, nx, ny, nz))
                    var rdx: Double = __pytra_float(__tuple_9[0])
                    var rdy: Double = __pytra_float(__tuple_9[1])
                    var rdz: Double = __pytra_float(__tuple_9[2])
                    let __tuple_10 = __pytra_as_list(refract(dx, dy, dz, nx, ny, nz, (__pytra_float(Double(1.0)) / __pytra_float(Double(1.45)))))
                    var tdx: Double = __pytra_float(__tuple_10[0])
                    var tdy: Double = __pytra_float(__tuple_10[1])
                    var tdz: Double = __pytra_float(__tuple_10[2])
                    let __tuple_11 = __pytra_as_list(sky_color(rdx, rdy, rdz, tphase))
                    var sr: Double = __pytra_float(__tuple_11[0])
                    var sg: Double = __pytra_float(__tuple_11[1])
                    var sb: Double = __pytra_float(__tuple_11[2])
                    let __tuple_12 = __pytra_as_list(sky_color(tdx, tdy, tdz, (tphase + Double(0.8))))
                    var tr: Double = __pytra_float(__tuple_12[0])
                    var tg: Double = __pytra_float(__tuple_12[1])
                    var tb: Double = __pytra_float(__tuple_12[2])
                    var cosi: Int64 = __pytra_int(__pytra_max((-(((dx * nx) + (dy * ny)) + (dz * nz))), Double(0.0)))
                    var fr: Double = __pytra_float(schlick(cosi, Double(0.04)))
                    r = __pytra_float(((tr * (__pytra_float(Double(1.0)) - __pytra_float(fr))) + (sr * fr)))
                    g = __pytra_float(((tg * (__pytra_float(Double(1.0)) - __pytra_float(fr))) + (sg * fr)))
                    b = __pytra_float(((tb * (__pytra_float(Double(1.0)) - __pytra_float(fr))) + (sb * fr)))
                    var lxv: Double = __pytra_float((lx - hx))
                    var lyv: Double = __pytra_float((ly - hy))
                    var lzv: Double = __pytra_float((lz - hz))
                    let __tuple_13 = __pytra_as_list(normalize(lxv, lyv, lzv))
                    var ldx: Double = __pytra_float(__tuple_13[0])
                    var ldy: Double = __pytra_float(__tuple_13[1])
                    var ldz: Double = __pytra_float(__tuple_13[2])
                    var ndotl: Int64 = __pytra_int(__pytra_max((((nx * ldx) + (ny * ldy)) + (nz * ldz)), Double(0.0)))
                    let __tuple_14 = __pytra_as_list(normalize((ldx - dx), (ldy - dy), (ldz - dz)))
                    var hvx: Double = __pytra_float(__tuple_14[0])
                    var hvy: Double = __pytra_float(__tuple_14[1])
                    var hvz: Double = __pytra_float(__tuple_14[2])
                    var ndoth: Int64 = __pytra_int(__pytra_max((((nx * hvx) + (ny * hvy)) + (nz * hvz)), Double(0.0)))
                    var spec: Int64 = __pytra_int((ndoth * ndoth))
                    spec = __pytra_int((spec * spec))
                    spec = __pytra_int((spec * spec))
                    spec = __pytra_int((spec * spec))
                    var glow: Double = __pytra_float((__pytra_float(Double(10.0)) / __pytra_float((((Double(1.0) + (lxv * lxv)) + (lyv * lyv)) + (lzv * lzv)))))
                    r += (((Double(0.2) * ndotl) + (Double(0.8) * spec)) + (Double(0.45) * glow))
                    g += (((Double(0.18) * ndotl) + (Double(0.6) * spec)) + (Double(0.35) * glow))
                    b += (((Double(0.26) * ndotl) + (Double(1.0) * spec)) + (Double(0.65) * glow))
                    if (__pytra_int(hit_kind) == __pytra_int(Int64(2))) {
                        r *= Double(0.95)
                        g *= Double(1.05)
                        b *= Double(1.1)
                    } else {
                        if (__pytra_int(hit_kind) == __pytra_int(Int64(3))) {
                            r *= Double(1.08)
                            g *= Double(0.98)
                            b *= Double(1.04)
                        } else {
                            r *= Double(1.02)
                            g *= Double(1.1)
                            b *= Double(0.95)
                        }
                    }
                }
            }
            r = __pytra_float(sqrt(__pytra_float(clamp01(r))))
            g = __pytra_float(sqrt(__pytra_float(clamp01(g))))
            b = __pytra_float(sqrt(__pytra_float(clamp01(b))))
            __pytra_setIndex(frame, (__pytra_int(row_base) + __pytra_int(px)), quantize_332(r, g, b))
            px += __step_4
        }
        py += __step_3
    }
    return __pytra_bytes(frame)
}

func run_16_glass_sculpture_chaos() {
    var width: Int64 = __pytra_int(Int64(320))
    var height: Int64 = __pytra_int(Int64(240))
    var frames_n: Int64 = __pytra_int(Int64(72))
    var out_path: String = __pytra_str("sample/out/16_glass_sculpture_chaos.gif")
    var start: Double = __pytra_float(__pytra_perf_counter())
    var frames: [Any] = __pytra_as_list([])
    let __step_0 = __pytra_int(Int64(1))
    var i = __pytra_int(Int64(0))
    while ((__step_0 >= 0 && i < __pytra_int(frames_n)) || (__step_0 < 0 && i > __pytra_int(frames_n))) {
        frames = __pytra_as_list(frames); frames.append(render_frame(width, height, i, frames_n))
        i += __step_0
    }
    __pytra_noop(out_path, width, height, frames, palette_332())
    var elapsed: Double = __pytra_float((__pytra_perf_counter() - start))
    __pytra_print("output:", out_path)
    __pytra_print("frames:", frames_n)
    __pytra_print("elapsed_sec:", elapsed)
}

@main
struct Main {
    static func main() {
        run_16_glass_sculpture_chaos()
    }
}
