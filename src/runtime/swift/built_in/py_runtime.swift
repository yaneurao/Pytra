// Swift 実行向け Node.js ランタイム補助。
import Foundation
import CoreFoundation

/// Base64 で埋め込まれた JavaScript ソースコードを一時ファイルへ展開し、node で実行する。
/// - Parameters:
///   - sourceBase64: JavaScript ソースコードの Base64 文字列。
///   - args: JavaScript 側へ渡す引数配列。
/// - Returns:
///   node プロセスの終了コード。失敗時は 1 を返す。
func pytraRunEmbeddedNode(_ sourceBase64: String, _ args: [String]) -> Int32 {
    guard let sourceData = Data(base64Encoded: sourceBase64) else {
        fputs("error: failed to decode embedded JavaScript source\n", stderr)
        return 1
    }

    let tmpDir = URL(fileURLWithPath: NSTemporaryDirectory(), isDirectory: true)
    let fileName = "pytra_embedded_\(UUID().uuidString).js"
    let scriptURL = tmpDir.appendingPathComponent(fileName)

    do {
        try sourceData.write(to: scriptURL)
    } catch {
        fputs("error: failed to write temporary JavaScript file: \(error)\n", stderr)
        return 1
    }

    let process = Process()
    process.executableURL = URL(fileURLWithPath: "/usr/bin/env")
    process.arguments = ["node", scriptURL.path] + args
    process.environment = ProcessInfo.processInfo.environment
    process.standardInput = FileHandle.standardInput
    process.standardOutput = FileHandle.standardOutput
    process.standardError = FileHandle.standardError

    do {
        try process.run()
        process.waitUntilExit()
    } catch {
        fputs("error: failed to launch node: \(error)\n", stderr)
        try? FileManager.default.removeItem(at: scriptURL)
        return 1
    }

    try? FileManager.default.removeItem(at: scriptURL)
    return process.terminationStatus
}


// ---- legacy swift emitter helper compatibility ----
func __pytra_noop(_ args: Any...) {}

class BaseException: Error, CustomStringConvertible {
    var message: String

    init(_ message: String = "") {
        self.message = message
    }

    var description: String {
        return message
    }
}

class Exception: BaseException {}
class RuntimeError: Exception {}
class ValueError: Exception {}
class TypeError: Exception {}
class IndexError: Exception {}
class KeyError: Exception {}
class NameError: Exception {}

class Enum: CustomStringConvertible {
    let value: AnyHashable

    required init(_ value: AnyHashable) {
        self.value = value
    }

    var description: String {
        return String(describing: value)
    }
}

final class PytraNone: CustomStringConvertible {
    static let shared = PytraNone()

    private init() {}

    var description: String {
        return "None"
    }
}

func ==(lhs: Enum, rhs: Enum) -> Bool {
    return type(of: lhs) == type(of: rhs) && lhs.value == rhs.value
}

func __pytra_any_default() -> Any {
    return Int64(0)
}

func __pytra_none() -> Any {
    return PytraNone.shared
}

func __pytra_assert(_ args: Any...) -> String {
    _ = args
    return "True"
}

func __pytra_assert_true(_ cond: Any?, _ label: Any? = nil) -> Bool {
    _ = label
    return __pytra_truthy(cond)
}

func __pytra_assert_eq(_ actual: Any?, _ expected: Any?, _ label: Any? = nil) -> Bool {
    _ = label
    return __pytra_str(actual) == __pytra_str(expected)
}

func __pytra_assert_all(_ items: Any?, _ label: Any? = nil) -> Bool {
    _ = label
    if let arr = items as? [Any] {
        for item in arr {
            if !__pytra_truthy(item) { return false }
        }
        return true
    }
    return __pytra_truthy(items)
}

func __pytra_is_none(_ v: Any?) -> Bool {
    guard let value = v else { return true }
    if value is PytraNone { return true }
    let mirror = Mirror(reflecting: value)
    if mirror.displayStyle == .optional {
        return mirror.children.first == nil
    }
    return false
}

func __pytra_perf_counter() -> Double {
    return Date().timeIntervalSince1970
}

func __pytra_truthy(_ v: Any?) -> Bool {
    guard let value = v else { return false }
    if value is PytraNone { return false }
    if let b = value as? Bool { return b }
    if let i = value as? Int64 { return i != 0 }
    if let i = value as? Int { return i != 0 }
    if let d = value as? Double { return d != 0.0 }
    if let s = value as? String { return s != "" }
    if let a = value as? [Any] { return !a.isEmpty }
    if let a = value as? [UInt8] { return !a.isEmpty }
    if let m = value as? [AnyHashable: Any] { return !m.isEmpty }
    return true
}

func __pytra_int(_ v: Any?) -> Int64 {
    guard let value = v else { return 0 }
    if value is PytraNone { return 0 }
    if let i = value as? Int64 { return i }
    if let i = value as? Int { return Int64(i) }
    if let i = value as? UInt8 { return Int64(i) }
    if let d = value as? Double { return Int64(d) }
    if let b = value as? Bool { return b ? 1 : 0 }
    if let s = value as? String { return Int64(s) ?? 0 }
    return 0
}

func __pytra_float(_ v: Any?) -> Double {
    guard let value = v else { return 0.0 }
    if value is PytraNone { return 0.0 }
    let mirror = Mirror(reflecting: value)
    if mirror.displayStyle == .optional {
        if let child = mirror.children.first {
            return __pytra_float(child.value)
        }
        return 0.0
    }
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
    if value is PytraNone { return "None" }
    let mirror = Mirror(reflecting: value)
    if mirror.displayStyle == .optional {
        if let child = mirror.children.first {
            return __pytra_str(child.value)
        }
        return ""
    }
    if let s = value as? String { return s }
    if let b = value as? Bool { return b ? "True" : "False" }
    if let arr = value as? [Any] {
        let parts = arr.map { __pytra_repr_item($0) }
        return "[" + parts.joined(separator: ", ") + "]"
    }
    if let dict = value as? [AnyHashable: Any] {
        let parts = dict.keys
            .sorted { __pytra_str($0.base) < __pytra_str($1.base) }
            .map { key in __pytra_repr_item(key.base) + ": " + __pytra_repr_item(dict[key]) }
        return "{" + parts.joined(separator: ", ") + "}"
    }
    return String(describing: value)
}

func __pytra_py_to_string(_ v: Any?) -> String {
    return __pytra_str(v)
}

func __pytra_repr_item(_ v: Any?) -> String {
    guard let value = v else { return "" }
    if value is PytraNone { return "None" }
    let mirror = Mirror(reflecting: value)
    if mirror.displayStyle == .optional {
        if let child = mirror.children.first {
            return __pytra_repr_item(child.value)
        }
        return ""
    }
    if let s = value as? String { return "'" + s + "'" }
    if let b = value as? Bool { return b ? "True" : "False" }
    if let arr = value as? [Any] {
        let parts = arr.map { __pytra_repr_item($0) }
        return "[" + parts.joined(separator: ", ") + "]"
    }
    if let dict = value as? [AnyHashable: Any] {
        let parts = dict.keys
            .sorted { __pytra_str($0.base) < __pytra_str($1.base) }
            .map { key in __pytra_repr_item(key.base) + ": " + __pytra_repr_item(dict[key]) }
        return "{" + parts.joined(separator: ", ") + "}"
    }
    return __pytra_str(value)
}

func __pytra_tuple_str(_ v: Any?) -> String {
    let arr = __pytra_as_list(v)
    if arr.count == 1 {
        return "(" + __pytra_repr_item(arr[0]) + ",)"
    }
    return "(" + arr.map { __pytra_repr_item($0) }.joined(separator: ", ") + ")"
}

func __pytra_type_name(_ v: Any?) -> String {
    guard let value = v else { return "NoneType" }
    if value is PytraNone { return "NoneType" }
    if value is Int64 || value is Int { return "int" }
    if value is Double { return "float" }
    if value is Bool { return "bool" }
    if value is String { return "str" }
    if value is [Any] { return "list" }
    if value is [UInt8] { return "bytearray" }
    if value is [AnyHashable: Any] { return "dict" }
    return String(describing: type(of: value))
}

func __pytra_format_value(_ v: Any?, _ spec: String) -> String {
    if spec == "" {
        return __pytra_str(v)
    }
    if spec.hasSuffix("d") {
        let width = Int(spec.dropLast()) ?? 0
        let body = String(__pytra_int(v))
        if width <= body.count {
            return body
        }
        return String(repeating: " ", count: width - body.count) + body
    }
    if spec.hasSuffix("f") {
        let core = String(spec.dropLast())
        var precision = 6
        if core.hasPrefix(".") {
            precision = Int(core.dropFirst()) ?? precision
        }
        return String(format: "%.\(precision)f", __pytra_float(v))
    }
    return __pytra_str(v)
}

func __pytra_len(_ v: Any?) -> Int64 {
    guard let value = v else { return 0 }
    if let s = value as? String { return Int64(s.count) }
    if let a = value as? [Any] { return Int64(a.count) }
    if let a = value as? [UInt8] { return Int64(a.count) }
    if let m = value as? [AnyHashable: Any] { return Int64(m.count) }
    return 0
}

func __pytra_index(_ i: Int64, _ n: Int64) -> Int64 {
    if i < 0 {
        return i + n
    }
    return i
}

func __pytra_index(_ items: [Any], _ needle: Any?) -> Int64 {
    return __pytra_list_index(items, needle)
}

func __pytra_index(_ text: String, _ needle: Any?) -> Int64 {
    return __pytra_index_str(text, needle)
}

func __pytra_getIndex(_ container: Any?, _ index: Any?) throws -> Any {
    if let list = container as? [Any] {
        if list.isEmpty { throw IndexError("list index out of range") }
        let i = __pytra_index(__pytra_int(index), Int64(list.count))
        if i < 0 || i >= Int64(list.count) { throw IndexError("list index out of range") }
        return list[Int(i)]
    }
    if let list = container as? [UInt8] {
        if list.isEmpty { throw IndexError("list index out of range") }
        let i = __pytra_index(__pytra_int(index), Int64(list.count))
        if i < 0 || i >= Int64(list.count) { throw IndexError("list index out of range") }
        return Int64(list[Int(i)])
    }
    if let dict = container as? [AnyHashable: Any] {
        let key = AnyHashable(__pytra_str(index))
        return dict[key] ?? __pytra_any_default()
    }
    if let s = container as? String {
        let chars = Array(s)
        if chars.isEmpty { throw IndexError("string index out of range") }
        let i = __pytra_index(__pytra_int(index), Int64(chars.count))
        if i < 0 || i >= Int64(chars.count) { throw IndexError("string index out of range") }
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
    if var list = container as? [UInt8] {
        if list.isEmpty { return }
        let i = __pytra_index(__pytra_int(index), Int64(list.count))
        if i < 0 || i >= Int64(list.count) { return }
        list[Int(i)] = UInt8(clamping: __pytra_int(value))
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

func __pytra_as_list(_ v: Any?) -> [Any] {
    if let list = v as? [Any] {
        return list
    }
    if let bytes = v as? [UInt8] {
        return bytes.map { Int64($0) as Any }
    }
    if let s = v as? String {
        return Array(s).map { String($0) as Any }
    }
    if let mutableList = v as? NSArray {
        return mutableList.map { $0 }
    }
    return []
}

func __pytra_as_dict(_ v: Any?) -> [AnyHashable: Any] {
    if let dict = v as? [AnyHashable: Any] {
        return dict
    }
    if let nsDict = v as? NSDictionary {
        var out: [AnyHashable: Any] = [:]
        for (key, value) in nsDict {
            if let hashableKey = key as? AnyHashable {
                out[hashableKey] = value
            }
        }
        return out
    }
    return [:]
}

func __pytra_set_literal(_ items: [Any]) -> [Any] {
    var out: [Any] = []
    for item in items {
        if !__pytra_contains(out, item) {
            out.append(item)
        }
    }
    return out
}

func __pytra_set_add(_ items: inout [Any], _ value: Any?) {
    if !__pytra_contains(items, value) {
        if let unwrapped = value {
            items.append(unwrapped)
        } else {
            items.append(__pytra_any_default())
        }
    }
}

func __pytra_dict_pop(_ dict: inout [AnyHashable: Any], _ key: Any?) -> Any {
    let hashed = AnyHashable(__pytra_str(key))
    let value = dict[hashed] ?? __pytra_any_default()
    dict.removeValue(forKey: hashed)
    return value
}

func __pytra_dict_setdefault(_ dict: inout [AnyHashable: Any], _ key: Any?, _ defaultValue: Any?) -> Any {
    let hashed = AnyHashable(__pytra_str(key))
    if let value = dict[hashed] {
        return value
    }
    let stored: Any = defaultValue ?? __pytra_any_default()
    dict[hashed] = stored
    return stored
}

func __pytra_get(_ dict: Any?, _ key: Any?, _ defaultValue: Any? = nil) -> Any? {
    if let map = dict as? [AnyHashable: Any] {
        return map[AnyHashable(__pytra_str(key))] ?? defaultValue
    }
    return defaultValue
}

func __pytra_keys(_ dict: Any?) -> [Any] {
    if let map = dict as? [AnyHashable: Any] {
        return map.keys.map { $0.base }
    }
    return []
}

func __pytra_items(_ dict: Any?) -> [Any] {
    if let map = dict as? [AnyHashable: Any] {
        return map.keys.map { key in [key.base, map[key] ?? __pytra_any_default()] as [Any] }
    }
    return []
}

func __pytra_values(_ dict: Any?) -> [Any] {
    if let map = dict as? [AnyHashable: Any] {
        return Array(map.values)
    }
    return []
}

func __pytra_py_int_from_str(_ value: Any?) -> Int64 {
    return __pytra_int(value)
}

func __pytra_deque_appendleft(_ items: inout [Any], _ value: Any?) {
    items.insert(value ?? __pytra_any_default(), at: 0)
}

func __pytra_deque_popleft(_ items: inout [Any]) -> Any {
    if items.isEmpty { return __pytra_any_default() }
    return items.removeFirst()
}

func __pytra_deque_pop(_ items: inout [Any]) -> Any {
    if items.isEmpty { return __pytra_any_default() }
    return items.removeLast()
}

func __pytra_ifexp(_ cond: Bool, _ a: Any, _ b: Any) -> Any {
    return cond ? a : b
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
    Swift.print(args.map { __pytra_str($0) }.joined(separator: " "))
}

func __pytra_py_print(_ args: Any...) {
    if args.isEmpty {
        Swift.print()
        return
    }
    Swift.print(args.map { __pytra_str($0) }.joined(separator: " "))
}

func __pytra_static_cast<T>(_ v: Any?) -> T {
    if T.self == Int64.self {
        return __pytra_int(v) as! T
    }
    if T.self == Double.self {
        return __pytra_float(v) as! T
    }
    if T.self == Bool.self {
        return __pytra_truthy(v) as! T
    }
    if T.self == String.self {
        return __pytra_str(v) as! T
    }
    if T.self == [Any].self {
        return __pytra_as_list(v) as! T
    }
    if T.self == [AnyHashable: Any].self {
        return __pytra_as_dict(v) as! T
    }
    return v as! T
}

func __pytra_makedirs(_ path: Any?, _ existOk: Any? = nil) {
    let p = __pytra_str(path)
    let ok = __pytra_truthy(existOk)
    do {
        try FileManager.default.createDirectory(atPath: p, withIntermediateDirectories: true)
    } catch {
        if !ok {
            return
        }
    }
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

// Int64 overloads for type-safe assignment
func __pytra_min(_ a: Int64, _ b: Int64) -> Int64 { return a < b ? a : b }
func __pytra_max(_ a: Int64, _ b: Int64) -> Int64 { return a > b ? a : b }
func __pytra_min(_ a: Int64, _ b: Any?) -> Int64 { return min(a, __pytra_int(b)) }
func __pytra_max(_ a: Int64, _ b: Any?) -> Int64 { return max(a, __pytra_int(b)) }
func __pytra_min(_ a: Any?, _ b: Int64) -> Int64 { return min(__pytra_int(a), b) }
func __pytra_max(_ a: Any?, _ b: Int64) -> Int64 { return max(__pytra_int(a), b) }
// Double overloads
func __pytra_min(_ a: Double, _ b: Double) -> Double { return a < b ? a : b }
func __pytra_max(_ a: Double, _ b: Double) -> Double { return a > b ? a : b }
func __pytra_min(_ a: Double, _ b: Any?) -> Double { return min(a, __pytra_float(b)) }
func __pytra_max(_ a: Double, _ b: Any?) -> Double { return max(a, __pytra_float(b)) }
func __pytra_min(_ a: Any?, _ b: Double) -> Double { return min(__pytra_float(a), b) }
func __pytra_max(_ a: Any?, _ b: Double) -> Double { return max(__pytra_float(a), b) }

func pyMathSqrt(_ v: Any?) -> Double { return Foundation.sqrt(__pytra_float(v)) }
func pyMathSin(_ v: Any?) -> Double { return Foundation.sin(__pytra_float(v)) }
func pyMathCos(_ v: Any?) -> Double { return Foundation.cos(__pytra_float(v)) }
func pyMathTan(_ v: Any?) -> Double { return Foundation.tan(__pytra_float(v)) }
func pyMathExp(_ v: Any?) -> Double { return Foundation.exp(__pytra_float(v)) }
func pyMathLog(_ v: Any?) -> Double { return Foundation.log(__pytra_float(v)) }
func pyMathFabs(_ v: Any?) -> Double { return Foundation.fabs(__pytra_float(v)) }
func pyMathFloor(_ v: Any?) -> Double { return Foundation.floor(__pytra_float(v)) }
func pyMathCeil(_ v: Any?) -> Double { return Foundation.ceil(__pytra_float(v)) }
func pyMathPow(_ a: Any?, _ b: Any?) -> Double { return Foundation.pow(__pytra_float(a), __pytra_float(b)) }
func pyMathPi() -> Double { return Double.pi }
func pyMathE() -> Double { return Foundation.exp(1.0) }

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

func __pytra_is_dict(_ v: Any?) -> Bool {
    return v is [AnyHashable: Any]
}

// --- bytearray / bytes ---

func __pytra_bytearray(_ size: Any?) -> [UInt8] {
    if let list = size as? [UInt8] {
        return list
    }
    if let list = size as? [Int64] {
        return list.map { UInt8(clamping: $0) }
    }
    if let list = size as? [Int] {
        return list.map { UInt8(clamping: $0) }
    }
    if let list = size as? [Any] {
        return list.map { UInt8(clamping: __pytra_int($0)) }
    }
    let n = __pytra_int(size)
    return [UInt8](repeating: 0, count: Int(n))
}

func __pytra_bytes(_ v: Any?) -> [UInt8] {
    if let list = v as? [UInt8] {
        return list
    }
    if let list = v as? [Int64] {
        return list.map { UInt8(clamping: $0) }
    }
    if let list = v as? [Int] {
        return list.map { UInt8(clamping: $0) }
    }
    if let list = v as? [Any] {
        return list.map { UInt8(clamping: __pytra_int($0)) }
    }
    return []
}

func __pytra_as_u8_list(_ v: Any?) -> [UInt8] {
    if let arr = v as? [UInt8] { return arr }
    if let arr = v as? [Int64] { return arr.map { UInt8(clamping: $0) } }
    if let arr = v as? [Int] { return arr.map { UInt8(clamping: $0) } }
    if let arr = v as? [Any] { return arr.map { UInt8(clamping: __pytra_int($0)) } }
    return []
}

func __pytra_list_repeat(_ value: Any?, _ count: Any?) -> [Any] {
    let n = Int(__pytra_int(count))
    if n <= 0 {
        return []
    }
    if let list = value as? [Any] {
        var out: [Any] = []
        for _ in 0..<n {
            out.append(contentsOf: list)
        }
        return out
    }
    return [Any](repeating: value as Any, count: n)
}

func __pytra_range(_ start: Any?, _ stop: Any?, _ step: Any?) -> [Any] {
    let s = Int(__pytra_int(start))
    let e = Int(__pytra_int(stop))
    let st = Int(__pytra_int(step))
    var result: [Any] = []
    if st > 0 {
        var i = s; while i < e { result.append(Int64(i) as Any); i += st }
    } else if st < 0 {
        var i = s; while i > e { result.append(Int64(i) as Any); i += st }
    }
    return result
}

func __pytra_py_range(_ stop: Any?) -> [Any] {
    return __pytra_range(Int64(0), stop, Int64(1))
}

func __pytra_py_range(_ start: Any?, _ stop: Any?, _ step: Any?) -> [Any] {
    return __pytra_range(start, stop, step)
}

func __pytra_abs(_ v: Any?) -> Any {
    if let i = v as? Int64 { return i < 0 ? -i : i }
    if let d = v as? Double { return Swift.abs(d) }
    return __pytra_int(v)
}

func __pytra_enumerate(_ v: Any?) -> [(Int64, Any)] {
    let list = (v as? [Any]) ?? []
    var result: [(Int64, Any)] = []
    for (i, item) in list.enumerated() { result.append((Int64(i), item)) }
    return result
}

func __pytra_py_enumerate_object(_ v: Any?, _ start: Any? = nil) -> [(Int64, Any)] {
    let list = (v as? [Any]) ?? []
    let offset = __pytra_int(start)
    var result: [(Int64, Any)] = []
    for (i, item) in list.enumerated() { result.append((offset + Int64(i), item)) }
    return result
}

func __pytra_reversed(_ v: Any?) -> [Any] {
    if let list = v as? [Any] { return list.reversed() }
    if let s = v as? String { return Array(s.reversed()).map { String($0) as Any } }
    return []
}

func __pytra_py_reversed_object(_ v: Any?) -> [Any] {
    return __pytra_reversed(v)
}

func __pytra_sorted(_ v: Any?) -> [Any] {
    if let list = v as? [Any] {
        return list.sorted { __pytra_float($0) < __pytra_float($1) }
    }
    return []
}

func __pytra_join(_ sep: Any?, _ items: Any?) -> String {
    let s = __pytra_str(sep)
    let list = (items as? [Any]) ?? []
    return list.map { __pytra_str($0) }.joined(separator: s)
}

func __pytra_split(_ v: Any?, _ sep: Any?) -> [Any] {
    let s = __pytra_str(v)
    let delimiter = __pytra_str(sep)
    return s.components(separatedBy: delimiter).map { $0 as Any }
}

func __pytra_replace(_ v: Any?, _ old: Any?, _ new: Any?) -> String {
    return __pytra_str(v).replacingOccurrences(of: __pytra_str(old), with: __pytra_str(new))
}

func __pytra_strip(_ v: Any?) -> String {
    return __pytra_str(v).trimmingCharacters(in: .whitespacesAndNewlines)
}

func __pytra_lstrip(_ v: Any?) -> String {
    return __pytra_str(v).replacingOccurrences(
        of: #"^\s+"#,
        with: "",
        options: .regularExpression
    )
}

func __pytra_rstrip(_ v: Any?) -> String {
    return __pytra_str(v).replacingOccurrences(
        of: #"\s+$"#,
        with: "",
        options: .regularExpression
    )
}

func __pytra_startswith(_ v: Any?, _ prefix: Any?) -> Bool {
    return __pytra_str(v).hasPrefix(__pytra_str(prefix))
}

func __pytra_endswith(_ v: Any?, _ suffix: Any?) -> Bool {
    return __pytra_str(v).hasSuffix(__pytra_str(suffix))
}

func __pytra_find(_ v: Any?, _ sub: Any?) -> Int64 {
    let s = __pytra_str(v)
    let t = __pytra_str(sub)
    if let range = s.range(of: t) { return Int64(s.distance(from: s.startIndex, to: range.lowerBound)) }
    return -1
}

func __pytra_index_str(_ v: Any?, _ sub: Any?) -> Int64 {
    return __pytra_find(v, sub)
}

func __pytra_list_index(_ v: Any?, _ needle: Any?) -> Int64 {
    let items = __pytra_as_list(v)
    let target = __pytra_str(needle)
    var i = 0
    while i < items.count {
        if __pytra_str(items[i]) == target {
            return Int64(i)
        }
        i += 1
    }
    return -1
}

func __pytra_isalnum(_ v: Any?) -> Bool {
    let s = __pytra_str(v)
    if s.isEmpty { return false }
    return s.unicodeScalars.allSatisfy {
        CharacterSet.alphanumerics.contains($0)
    }
}

func __pytra_upper(_ v: Any?) -> String { return __pytra_str(v).uppercased() }
func __pytra_lower(_ v: Any?) -> String { return __pytra_str(v).lowercased() }

func __pytra_extend(_ items: inout [Any], _ extra: Any?) {
    items.append(contentsOf: __pytra_as_list(extra))
}

func __pytra_sum(_ items: Any?) -> Any {
    let arr = __pytra_as_list(items)
    var sawFloat = false
    var floatTotal = 0.0
    var intTotal: Int64 = 0
    for item in arr {
        if item is Double {
            sawFloat = true
            floatTotal += __pytra_float(item)
        } else {
            intTotal += __pytra_int(item)
        }
    }
    if sawFloat {
        return Double(intTotal) + floatTotal
    }
    return intTotal
}

func __pytra_zip(_ left: Any?, _ right: Any?) -> [Any] {
    let lhs = __pytra_as_list(left)
    let rhs = __pytra_as_list(right)
    let count = min(lhs.count, rhs.count)
    var out: [Any] = []
    var i = 0
    while i < count {
        out.append([lhs[i], rhs[i]])
        i += 1
    }
    return out
}

func __pytra_set_ctor() -> [Any] {
    return []
}

func __pytra_discard(_ items: inout [Any], _ value: Any?) {
    let needle = __pytra_str(value)
    items.removeAll { __pytra_str($0) == needle }
}

func __pytra_remove(_ items: inout [Any], _ value: Any?) {
    __pytra_discard(&items, value)
}

// --- Any arithmetic operators (for untyped variables used in arithmetic) ---

func + (_ a: Any, _ b: Any) -> Double { return __pytra_float(a) + __pytra_float(b) }
func - (_ a: Any, _ b: Any) -> Double { return __pytra_float(a) - __pytra_float(b) }
func * (_ a: Any, _ b: Any) -> Double { return __pytra_float(a) * __pytra_float(b) }
func / (_ a: Any, _ b: Any) -> Double { return __pytra_float(a) / __pytra_float(b) }
func + (_ a: Double, _ b: Any) -> Double { return a + __pytra_float(b) }
func - (_ a: Double, _ b: Any) -> Double { return a - __pytra_float(b) }
func * (_ a: Double, _ b: Any) -> Double { return a * __pytra_float(b) }
func / (_ a: Double, _ b: Any) -> Double { return a / __pytra_float(b) }
func + (_ a: Any, _ b: Double) -> Double { return __pytra_float(a) + b }
func - (_ a: Any, _ b: Double) -> Double { return __pytra_float(a) - b }
func * (_ a: Any, _ b: Double) -> Double { return __pytra_float(a) * b }
func / (_ a: Any, _ b: Double) -> Double { return __pytra_float(a) / b }

// --- image stubs (png/gif) ---

func write_rgb_png(_ path: Any?, _ width: Any?, _ height: Any?, _ pixels: Any?) {
    let p = __pytra_str(path)
    let w = Int(__pytra_int(width))
    let h = Int(__pytra_int(height))
    let pxBytes = pixels as? [UInt8]
    let pxList = pxBytes == nil ? ((pixels as? [Any]) ?? []) : []
    // Minimal raw PNG writer
    var data = Data()
    func _u32be(_ v: UInt32) -> Data { var b = v.bigEndian; return Data(bytes: &b, count: 4) }
    func _u16be(_ v: UInt16) -> Data { var b = v.bigEndian; return Data(bytes: &b, count: 2) }
    func _crc32(_ d: Data) -> UInt32 {
        var c: UInt32 = 0xFFFFFFFF
        for byte in d { for bit in 0..<8 { c = (c & 1) == 1 ? 0xEDB88320 ^ (c >> 1) : c >> 1; _ = bit } }  // placeholder
        // Use a proper crc table
        var table = [UInt32](repeating: 0, count: 256)
        for i in 0..<256 { var cc: UInt32 = UInt32(i); for _ in 0..<8 { cc = (cc & 1) != 0 ? 0xEDB88320 ^ (cc >> 1) : cc >> 1 }; table[i] = cc }
        c = 0xFFFFFFFF; for byte in d { c = table[Int((c ^ UInt32(byte)) & 0xFF)] ^ (c >> 8) }
        return c ^ 0xFFFFFFFF
    }
    func _chunk(_ tag: String, _ payload: Data) -> Data {
        let tagData = tag.data(using: .ascii)!
        var chunk = Data()
        chunk.append(_u32be(UInt32(payload.count)))
        chunk.append(tagData)
        chunk.append(payload)
        var crcInput = Data(); crcInput.append(tagData); crcInput.append(payload)
        chunk.append(_u32be(_crc32(crcInput)))
        return chunk
    }
    // PNG signature
    data.append(contentsOf: [0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A] as [UInt8])
    // IHDR
    var ihdr = Data()
    ihdr.append(_u32be(UInt32(w))); ihdr.append(_u32be(UInt32(h)))
    ihdr.append(contentsOf: [8, 2, 0, 0, 0] as [UInt8]) // 8-bit RGB
    data.append(_chunk("IHDR", ihdr))
    // IDAT (uncompressed deflate)
    var raw = Data()
    for y in 0..<h {
        raw.append(0) // filter none
        for x in 0..<w {
            let idx = (y * w + x) * 3
            let r = pxBytes != nil ? (idx < pxBytes!.count ? pxBytes![idx] : 0) : (idx < pxList.count ? UInt8(clamping: __pytra_int(pxList[idx])) : 0)
            let g = pxBytes != nil ? (idx + 1 < pxBytes!.count ? pxBytes![idx + 1] : 0) : (idx + 1 < pxList.count ? UInt8(clamping: __pytra_int(pxList[idx + 1])) : 0)
            let b = pxBytes != nil ? (idx + 2 < pxBytes!.count ? pxBytes![idx + 2] : 0) : (idx + 2 < pxList.count ? UInt8(clamping: __pytra_int(pxList[idx + 2])) : 0)
            raw.append(contentsOf: [r, g, b])
        }
    }
    // Wrap raw in zlib (stored blocks)
    var zlib = Data()
    zlib.append(contentsOf: [0x78, 0x01] as [UInt8]) // zlib header
    var offset = 0
    while offset < raw.count {
        let remaining = raw.count - offset
        let blockSize = min(remaining, 65535)
        let isLast: UInt8 = (offset + blockSize >= raw.count) ? 1 : 0
        zlib.append(isLast)
        zlib.append(contentsOf: _u16be(UInt16(blockSize)).reversed())
        zlib.append(contentsOf: _u16be(UInt16(blockSize) ^ 0xFFFF).reversed())
        zlib.append(raw[offset..<(offset + blockSize)])
        offset += blockSize
    }
    // adler32
    var a1: UInt32 = 1; var a2: UInt32 = 0
    for byte in raw { a1 = (a1 + UInt32(byte)) % 65521; a2 = (a2 + a1) % 65521 }
    zlib.append(_u32be((a2 << 16) | a1))
    data.append(_chunk("IDAT", zlib))
    data.append(_chunk("IEND", Data()))
    try? data.write(to: URL(fileURLWithPath: p))
}

func __pytra_grayscale_palette() -> [Any] {
    var pal: [Any] = []
    for i in 0..<256 { pal.append(Int64(i) as Any); pal.append(Int64(i) as Any); pal.append(Int64(i) as Any) }
    return pal
}

func __pytra_save_gif(_ path: Any?, _ width: Any?, _ height: Any?, _ frames: Any?, _ palette: Any?, _ delay: Any?, _ loop: Any?) {
    // Minimal stub: write a placeholder file
    let p = __pytra_str(path)
    let frameList = (frames as? [Any]) ?? []
    __pytra_print("gif: " + p + " frames=" + String(frameList.count))
    // Write minimal valid GIF
    let w = Int(__pytra_int(width))
    let h = Int(__pytra_int(height))
    var data = Data()
    data.append(contentsOf: [0x47, 0x49, 0x46, 0x38, 0x39, 0x61] as [UInt8]) // GIF89a
    data.append(contentsOf: [UInt8(w & 0xFF), UInt8((w >> 8) & 0xFF)])
    data.append(contentsOf: [UInt8(h & 0xFF), UInt8((h >> 8) & 0xFF)])
    data.append(contentsOf: [0xF7, 0x00, 0x00] as [UInt8]) // GCT flag, 256 colors
    // Global color table (256 * 3 bytes)
    let palList = (palette as? [Any]) ?? []
    for i in 0..<256 {
        let idx = i * 3
        let r = idx < palList.count ? UInt8(clamping: __pytra_int(palList[idx])) : 0
        let g = idx + 1 < palList.count ? UInt8(clamping: __pytra_int(palList[idx + 1])) : 0
        let b = idx + 2 < palList.count ? UInt8(clamping: __pytra_int(palList[idx + 2])) : 0
        data.append(contentsOf: [r, g, b])
    }
    // Application extension for looping
    data.append(contentsOf: [0x21, 0xFF, 0x0B] as [UInt8])
    data.append(contentsOf: "NETSCAPE2.0".data(using: .ascii)!)
    data.append(contentsOf: [0x03, 0x01, 0x00, 0x00, 0x00] as [UInt8])
    let delayVal = UInt16(__pytra_int(delay))
    // Write each frame
    for frameAny in frameList {
        let framePixels = (frameAny as? [Any]) ?? []
        // Graphic control extension
        data.append(contentsOf: [0x21, 0xF9, 0x04, 0x00] as [UInt8])
        data.append(contentsOf: [UInt8(delayVal & 0xFF), UInt8((delayVal >> 8) & 0xFF)])
        data.append(contentsOf: [0x00, 0x00] as [UInt8])
        // Image descriptor
        data.append(0x2C)
        data.append(contentsOf: [0x00, 0x00, 0x00, 0x00] as [UInt8]) // left, top
        data.append(contentsOf: [UInt8(w & 0xFF), UInt8((w >> 8) & 0xFF)])
        data.append(contentsOf: [UInt8(h & 0xFF), UInt8((h >> 8) & 0xFF)])
        data.append(0x00) // no local color table
        // LZW minimum code size
        data.append(0x08)
        // Uncompressed LZW: clear + pixel indices + EOI
        let totalPixels = w * h
        var lzwData = Data()
        lzwData.append(0x00) // clear code (256) low byte placeholder
        // Simple: output each pixel as a literal (very inefficient but valid)
        var subBlock = Data()
        subBlock.append(0x00) // clear
        subBlock.append(0x01) // clear high byte = 256
        for pi in 0..<totalPixels {
            let v = pi < framePixels.count ? UInt8(clamping: __pytra_int(framePixels[pi])) : 0
            subBlock.append(v)
        }
        // Write sub-blocks (max 255 bytes each)
        var soff = 0
        while soff < subBlock.count {
            let slen = min(subBlock.count - soff, 255)
            data.append(UInt8(slen))
            data.append(subBlock[soff..<(soff + slen)])
            soff += slen
        }
        data.append(0x00) // block terminator
    }
    data.append(0x3B) // GIF trailer
    try? data.write(to: URL(fileURLWithPath: p))
}

func __pytra_dict_get(_ dict: Any?, _ key: Any?, _ default_val: Any? = nil) -> Any? {
    if let d = dict as? [AnyHashable: Any] {
        let k = AnyHashable(__pytra_str(key))
        if let v = d[k] { return v }
    }
    return default_val
}

// --- json ---

func pyJsonDumps(_ v: Any?) -> String {
    return __pytra_json_stringify(v)
}

func pyJsonLoads(_ v: Any?) -> Any? {
    let text = __pytra_str(v)
    guard let data = text.data(using: .utf8) else {
        fatalError("invalid json: utf8 decode failed")
    }
    do {
        let obj = try JSONSerialization.jsonObject(with: data, options: [.fragmentsAllowed])
        return __pytra_json_from_foundation(obj)
    } catch {
        fatalError("invalid json: \(error)")
    }
}

private func __pytra_json_stringify(_ v: Any?) -> String {
    guard let value = v else { return "null" }
    if let b = value as? Bool {
        return b ? "true" : "false"
    }
    if let i = value as? Int {
        return String(i)
    }
    if let i = value as? Int64 {
        return String(i)
    }
    if let d = value as? Double {
        if !d.isFinite {
            fatalError("json.dumps: non-finite float")
        }
        return String(d)
    }
    if let f = value as? Float {
        if !f.isFinite {
            fatalError("json.dumps: non-finite float")
        }
        return String(f)
    }
    if let s = value as? String {
        return __pytra_json_escape_string(s)
    }
    if let arr = value as? [Any] {
        let elems = arr.map { __pytra_json_stringify($0) }
        return "[" + elems.joined(separator: ",") + "]"
    }
    if let dict = value as? [AnyHashable: Any] {
        var pairs: [String] = []
        for (k, item) in dict {
            pairs.append(__pytra_json_escape_string(__pytra_str(k)) + ":" + __pytra_json_stringify(item))
        }
        return "{" + pairs.joined(separator: ",") + "}"
    }
    return __pytra_json_escape_string(__pytra_str(value))
}

private func __pytra_json_escape_string(_ s: String) -> String {
    var out = "\""
    for ch in s {
        if ch == "\"" {
            out += "\\\""
        } else if ch == "\\" {
            out += "\\\\"
        } else if ch == "\u{0008}" {
            out += "\\b"
        } else if ch == "\u{000C}" {
            out += "\\f"
        } else if ch == "\n" {
            out += "\\n"
        } else if ch == "\r" {
            out += "\\r"
        } else if ch == "\t" {
            out += "\\t"
        } else if let scalar = ch.unicodeScalars.first, scalar.value < 0x20 {
            let hex = String(scalar.value, radix: 16, uppercase: false)
            out += "\\u" + String(repeating: "0", count: max(0, 4 - hex.count)) + hex
        } else {
            out.append(ch)
        }
    }
    out += "\""
    return out
}

private func __pytra_json_from_foundation(_ value: Any) -> Any? {
    if value is NSNull {
        return nil
    }
    if let b = value as? Bool {
        return b
    }
    if let s = value as? String {
        return s
    }
    if let arr = value as? [Any] {
        return arr.map { __pytra_json_from_foundation($0) }
    }
    if let dict = value as? [String: Any] {
        var out: [AnyHashable: Any] = [:]
        for (k, v) in dict {
            out[k] = __pytra_json_from_foundation(v)
        }
        return out
    }
    if let num = value as? NSNumber {
        if CFGetTypeID(num) == CFBooleanGetTypeID() {
            return num.boolValue
        }
        let d = num.doubleValue
        if d.rounded() == d {
            return num.int64Value
        }
        return d
    }
    return value
}

// --- pathlib ---

final class Path: CustomStringConvertible {
    let value: String

    init(_ raw: Any?) {
        self.value = __pytra_str(raw)
    }

    var parent: Path {
        let url = URL(fileURLWithPath: value)
        let parentURL = url.deletingLastPathComponent()
        let parentPath = parentURL.path
        if parentPath == value {
            return self
        }
        return Path(parentPath)
    }

    var name: String {
        let url = URL(fileURLWithPath: value)
        return url.lastPathComponent
    }

    var stem: String {
        let n = name
        if let idx = n.lastIndex(of: ".") {
            if idx > n.startIndex {
                return String(n[..<idx])
            }
        }
        return n
    }

    func exists() -> Bool {
        return FileManager.default.fileExists(atPath: value)
    }

    func read_text() -> String {
        do {
            return try String(contentsOfFile: value, encoding: .utf8)
        } catch {
            fatalError("Path.read_text failed: \(error)")
        }
    }

    @discardableResult
    func write_text(_ content: Any?) -> Any? {
        let outURL = URL(fileURLWithPath: value)
        let parentURL = outURL.deletingLastPathComponent()
        if parentURL.path != "" && parentURL.path != "." {
            try? FileManager.default.createDirectory(at: parentURL, withIntermediateDirectories: true)
        }
        do {
            try __pytra_str(content).write(to: outURL, atomically: true, encoding: .utf8)
            return nil
        } catch {
            fatalError("Path.write_text failed: \(error)")
        }
    }

    @discardableResult
    func mkdir(_ parents: Any? = false, _ exist_ok: Any? = false) -> Any? {
        let dirURL = URL(fileURLWithPath: value)
        let withIntermediate = __pytra_truthy(parents)
        do {
            try FileManager.default.createDirectory(at: dirURL, withIntermediateDirectories: withIntermediate)
            return nil
        } catch {
            if __pytra_truthy(exist_ok) && FileManager.default.fileExists(atPath: value) {
                return nil
            }
            fatalError("Path.mkdir failed: \(error)")
        }
    }

    func resolve() -> Path {
        let abs = URL(fileURLWithPath: value).standardizedFileURL.path
        return Path(abs)
    }

    var description: String {
        return value
    }
}

// --- file I/O (Python open/write/close bridge) ---

final class PyFile {
    private let handle: FileHandle
    private let path: String

    init(_ path: String, _ mode: String = "r") {
        self.path = path
        if mode == "wb" || mode == "w" {
            FileManager.default.createFile(atPath: path, contents: nil)
            self.handle = FileHandle(forWritingAtPath: path)!
        } else if mode == "ab" || mode == "a" {
            if !FileManager.default.fileExists(atPath: path) {
                FileManager.default.createFile(atPath: path, contents: nil)
            }
            self.handle = FileHandle(forWritingAtPath: path)!
            self.handle.seekToEndOfFile()
        } else {
            self.handle = FileHandle(forReadingAtPath: path) ?? FileHandle.nullDevice
        }
    }

    func write(_ data: Any?) {
        if let list = data as? [Any] {
            let bytes = list.map { UInt8(clamping: __pytra_int($0)) }
            handle.write(Data(bytes))
        } else if let s = data as? String {
            if let d = s.data(using: .utf8) { handle.write(d) }
        }
    }

    func close() {
        handle.closeFile()
    }
}

func __pytra_open(_ path: Any?, _ mode: Any? = "r") -> PyFile {
    return PyFile(__pytra_str(path), __pytra_str(mode))
}
