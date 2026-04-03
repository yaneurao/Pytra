import Foundation

func glob(_ pattern: String) -> [Any] {
    return glob_native_glob(pattern)
}
