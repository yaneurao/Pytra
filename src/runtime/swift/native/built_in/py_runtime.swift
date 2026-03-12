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

func __pytra_as_list(_ v: Any?) -> [Any] {
    if let list = v as? [Any] {
        return list
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
