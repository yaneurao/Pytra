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

func render_frame(width: Int64, height: Int64, center_x: Double, center_y: Double, scale: Double, max_iter: Int64) -> [Any] {
    var frame: [Any] = __pytra_as_list(__pytra_bytearray((__pytra_int(width) * __pytra_int(height))))
    let __step_0 = __pytra_int(Int64(1))
    var y = __pytra_int(Int64(0))
    while ((__step_0 >= 0 && y < __pytra_int(height)) || (__step_0 < 0 && y > __pytra_int(height))) {
        var row_base: Int64 = __pytra_int((__pytra_int(y) * __pytra_int(width)))
        var cy: Double = __pytra_float((__pytra_float(center_y) + __pytra_float((__pytra_float((__pytra_float(y) - __pytra_float((__pytra_float(height) * __pytra_float(Double(0.5)))))) * __pytra_float(scale)))))
        let __step_1 = __pytra_int(Int64(1))
        var x = __pytra_int(Int64(0))
        while ((__step_1 >= 0 && x < __pytra_int(width)) || (__step_1 < 0 && x > __pytra_int(width))) {
            var cx: Double = __pytra_float((__pytra_float(center_x) + __pytra_float((__pytra_float((__pytra_float(x) - __pytra_float((__pytra_float(width) * __pytra_float(Double(0.5)))))) * __pytra_float(scale)))))
            var zx: Double = __pytra_float(Double(0.0))
            var zy: Double = __pytra_float(Double(0.0))
            var i: Int64 = __pytra_int(Int64(0))
            while (__pytra_int(i) < __pytra_int(max_iter)) {
                var zx2: Double = __pytra_float((__pytra_float(zx) * __pytra_float(zx)))
                var zy2: Double = __pytra_float((__pytra_float(zy) * __pytra_float(zy)))
                if (__pytra_float((__pytra_float(zx2) + __pytra_float(zy2))) > __pytra_float(Double(4.0))) {
                    break
                }
                zy = __pytra_float((__pytra_float((__pytra_float((__pytra_float(Double(2.0)) * __pytra_float(zx))) * __pytra_float(zy))) + __pytra_float(cy)))
                zx = __pytra_float((__pytra_float((__pytra_float(zx2) - __pytra_float(zy2))) + __pytra_float(cx)))
                i += Int64(1)
            }
            __pytra_setIndex(frame, (__pytra_int(row_base) + __pytra_int(x)), __pytra_int((__pytra_float((__pytra_float(Double(255.0)) * __pytra_float(i))) / __pytra_float(max_iter))))
            x += __step_1
        }
        y += __step_0
    }
    return __pytra_bytes(frame)
}

func run_05_mandelbrot_zoom() {
    var width: Int64 = __pytra_int(Int64(320))
    var height: Int64 = __pytra_int(Int64(240))
    var frame_count: Int64 = __pytra_int(Int64(48))
    var max_iter: Int64 = __pytra_int(Int64(110))
    var center_x: Double = __pytra_float((-Double(0.743643887037151)))
    var center_y: Double = __pytra_float(Double(0.13182590420533))
    var base_scale: Double = __pytra_float((__pytra_float(Double(3.2)) / __pytra_float(width)))
    var zoom_per_frame: Double = __pytra_float(Double(0.93))
    var out_path: String = __pytra_str("sample/out/05_mandelbrot_zoom.gif")
    var start: Double = __pytra_float(__pytra_perf_counter())
    var frames: [Any] = __pytra_as_list([])
    var scale: Double = __pytra_float(base_scale)
    let __step_1 = __pytra_int(Int64(1))
    var __loop_0 = __pytra_int(Int64(0))
    while ((__step_1 >= 0 && __loop_0 < __pytra_int(frame_count)) || (__step_1 < 0 && __loop_0 > __pytra_int(frame_count))) {
        frames = __pytra_as_list(frames); frames.append(render_frame(width, height, center_x, center_y, scale, max_iter))
        scale *= zoom_per_frame
        __loop_0 += __step_1
    }
    __pytra_noop(out_path, width, height, frames, [])
    var elapsed: Double = __pytra_float((__pytra_perf_counter() - start))
    __pytra_print("output:", out_path)
    __pytra_print("frames:", frame_count)
    __pytra_print("elapsed_sec:", elapsed)
}

@main
struct Main {
    static func main() {
        run_05_mandelbrot_zoom()
    }
}
