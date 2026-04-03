import Foundation

class Path: CustomStringConvertible {
    var _value: String

    init() {
        self._value = ""
    }

    init(_ value: Any) {
        if let path = value as? Path {
            self._value = path._value
        } else {
            self._value = __pytra_str(value)
        }
    }

    var description: String {
        return _value
    }

    func __truediv__(_ rhs: Any) -> Path {
        return Path((self._value as NSString).appendingPathComponent(__pytra_str(rhs)))
    }

    var parent: Path {
        let parentPath = (self._value as NSString).deletingLastPathComponent
        return Path(parentPath == "" ? "." : parentPath)
    }

    var name: String {
        return (self._value as NSString).lastPathComponent
    }

    var stem: String {
        return ((self._value as NSString).deletingPathExtension as NSString).lastPathComponent
    }

    var suffix: String {
        let ext = (self._value as NSString).pathExtension
        return ext == "" ? "" : "." + ext
    }

    func with_suffix(_ suffix: String) -> Path {
        return Path((self._value as NSString).deletingPathExtension + suffix)
    }

    func joinpath(_ part: Any) -> Path {
        return Path((self._value as NSString).appendingPathComponent(__pytra_str(part)))
    }

    func resolve() -> Path {
        return Path(URL(fileURLWithPath: _value).standardizedFileURL.path)
    }

    func exists() -> Bool {
        return FileManager.default.fileExists(atPath: _value)
    }

    func mkdir(_ parents: Bool = false, _ exist_ok: Bool = false) {
        do {
            try FileManager.default.createDirectory(atPath: _value, withIntermediateDirectories: parents)
        } catch {
            if exist_ok && FileManager.default.fileExists(atPath: _value) {
                return
            }
            fatalError("Path.mkdir failed: \(error)")
        }
    }

    func read_text(_ encoding: String = "utf-8") -> String {
        _ = encoding
        return (try? String(contentsOfFile: _value, encoding: .utf8)) ?? ""
    }

    @discardableResult
    func write_text(_ text: String, _ encoding: String = "utf-8") -> Int64 {
        _ = encoding
        let value = __pytra_str(text)
        do {
            try value.write(toFile: _value, atomically: true, encoding: .utf8)
        } catch {
            fatalError("Path.write_text failed: \(error)")
        }
        return Int64(value.count)
    }

    func glob(_ pattern: String) -> [Any] {
        let joined = URL(fileURLWithPath: _value).appendingPathComponent(pattern).path
        return glob_native_glob(joined).map { Path($0) as Any }
    }

    static func cwd() -> Path {
        return Path(FileManager.default.currentDirectoryPath)
    }
}
