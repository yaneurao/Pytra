import Foundation
import CoreFoundation

class JsonObj {
    var raw: [AnyHashable: Any]

    init() {
        self.raw = [:]
    }

    init(_ raw: [AnyHashable: Any]) {
        self.raw = raw
    }

    func get(_ key: String) -> Any {
        guard let value = raw[AnyHashable(key)] else {
            return __pytra_none()
        }
        return JsonValue(value)
    }

    func get_str(_ key: String) -> Any {
        return JsonValue(raw[AnyHashable(key)] ?? __pytra_none()).as_str()
    }

    func get_obj(_ key: String) -> Any {
        return JsonValue(raw[AnyHashable(key)] ?? __pytra_none()).as_obj()
    }

    func get_arr(_ key: String) -> Any {
        return JsonValue(raw[AnyHashable(key)] ?? __pytra_none()).as_arr()
    }
}

class JsonArr {
    var raw: [Any]

    init() {
        self.raw = []
    }

    init(_ raw: [Any]) {
        self.raw = raw
    }

    func get(_ index: Int64) -> Any {
        let i = Int(index)
        if i < 0 || i >= raw.count {
            return __pytra_none()
        }
        return JsonValue(raw[i])
    }

    func get_int(_ index: Int64) -> Any {
        let value = get(index)
        if let jv = value as? JsonValue {
            return jv.as_int()
        }
        return JsonValue(value).as_int()
    }
}

class JsonValue {
    var raw: Any

    init() {
        self.raw = __pytra_none()
    }

    init(_ raw: Any) {
        self.raw = raw
    }

    func as_obj() -> Any {
        if let obj = raw as? [AnyHashable: Any] {
            return JsonObj(obj)
        }
        return __pytra_none()
    }

    func as_arr() -> Any {
        if let arr = raw as? [Any] {
            return JsonArr(arr)
        }
        return __pytra_none()
    }

    func as_str() -> Any {
        if let value = raw as? String {
            return value
        }
        return __pytra_none()
    }

    func as_int() -> Any {
        if let value = raw as? Int64 {
            return value
        }
        if let value = raw as? Int {
            return Int64(value)
        }
        return __pytra_none()
    }

    func as_float() -> Any {
        if let value = raw as? Double {
            return value
        }
        return __pytra_none()
    }

    func as_bool() -> Any {
        if let value = raw as? Bool {
            return value
        }
        return __pytra_none()
    }
}

private func _jsonToPytra(_ value: Any) -> Any {
    if value is NSNull {
        return __pytra_none()
    }
    if let dict = value as? [String: Any] {
        var out: [AnyHashable: Any] = [:]
        for (k, v) in dict {
            out[AnyHashable(k)] = _jsonToPytra(v)
        }
        return out
    }
    if let arr = value as? [Any] {
        return arr.map(_jsonToPytra)
    }
    if let num = value as? NSNumber {
        if CFGetTypeID(num) == CFBooleanGetTypeID() {
            return num.boolValue
        }
        let asDouble = num.doubleValue
        let asInt = num.int64Value
        if Double(asInt) == asDouble {
            return asInt
        }
        return asDouble
    }
    return value
}

private func _pytraToJSON(_ value: Any) -> Any {
    if __pytra_is_none(value) {
        return NSNull()
    }
    if let dict = value as? [AnyHashable: Any] {
        var out: [String: Any] = [:]
        for (k, v) in dict {
            out[String(describing: k.base)] = _pytraToJSON(v)
        }
        return out
    }
    if let arr = value as? [Any] {
        return arr.map(_pytraToJSON)
    }
    if let b = value as? Bool {
        return b
    }
    if let i = value as? Int64 {
        return i
    }
    if let i = value as? Int {
        return i
    }
    if let d = value as? Double {
        return d
    }
    if let s = value as? String {
        return s
    }
    if let obj = value as? JsonValue {
        return _pytraToJSON(obj.raw)
    }
    if let obj = value as? JsonObj {
        return _pytraToJSON(obj.raw)
    }
    if let obj = value as? JsonArr {
        return _pytraToJSON(obj.raw)
    }
    return String(describing: value)
}

private func _escapeNonAscii(_ text: String) -> String {
    var out = ""
    for scalar in text.unicodeScalars {
        if scalar.value > 0x7F {
            out += String(format: "\\u%04x", scalar.value)
        } else {
            out.append(String(scalar))
        }
    }
    return out
}

func loads(_ text: String) throws -> JsonValue {
    let data = text.data(using: .utf8) ?? Data()
    let value = try JSONSerialization.jsonObject(with: data, options: [.fragmentsAllowed])
    return JsonValue(_jsonToPytra(value))
}

func loads_obj(_ text: String) throws -> Any {
    let value = try loads(text).raw
    if let obj = value as? [AnyHashable: Any] {
        return JsonObj(obj)
    }
    return __pytra_none()
}

func loads_arr(_ text: String) throws -> Any {
    let value = try loads(text).raw
    if let arr = value as? [Any] {
        return JsonArr(arr)
    }
    return __pytra_none()
}

func dumps(_ obj: Any, _ ensure_ascii: Bool = true, _ indent: Any = __pytra_none(), _ separators: Any = __pytra_none()) throws -> String {
    let jsonValue = _pytraToJSON(obj)
    let options: JSONSerialization.WritingOptions = __pytra_is_none(indent) ? [.fragmentsAllowed] : [.prettyPrinted, .fragmentsAllowed]
    let data = try JSONSerialization.data(withJSONObject: jsonValue, options: options)
    var text = String(data: data, encoding: .utf8) ?? ""
    if __pytra_truthy(ensure_ascii) {
        text = _escapeNonAscii(text)
    }
    return text
}

func dumps_jv(_ jv: Any, _ ensure_ascii: Bool = true, _ indent: Any = __pytra_none(), _ separators: Any = __pytra_none()) throws -> String {
    return try dumps(jv, ensure_ascii, indent, separators)
}
