// このファイルは自動生成です（Python -> Swift embedded mode）。

// Swift 埋め込み実行向け Python ランタイム補助。

import Foundation

/// Base64 で埋め込まれた Python ソースコードを一時ファイルに展開し、python3 で実行する。
/// - Parameters:
///   - sourceBase64: Python ソースコードの Base64 文字列。
///   - args: Python スクリプトへ渡す引数配列。
/// - Returns:
///   python プロセスの終了コード。失敗時は 1 を返す。
func pytraRunEmbeddedPython(_ sourceBase64: String, _ args: [String]) -> Int32 {
    guard let sourceData = Data(base64Encoded: sourceBase64) else {
        fputs("error: failed to decode embedded Python source\n", stderr)
        return 1
    }

    let tmpDir = URL(fileURLWithPath: NSTemporaryDirectory(), isDirectory: true)
    let fileName = "pytra_embedded_\(UUID().uuidString).py"
    let scriptURL = tmpDir.appendingPathComponent(fileName)

    do {
        try sourceData.write(to: scriptURL)
    } catch {
        fputs("error: failed to write temporary Python file: \(error)\n", stderr)
        return 1
    }

    let process = Process()
    process.executableURL = URL(fileURLWithPath: "/usr/bin/env")
    process.arguments = ["python3", scriptURL.path] + args
    var env = ProcessInfo.processInfo.environment
    // Python 製補助モジュールを import できるよう、src を PYTHONPATH に追加する。
    if let current = env["PYTHONPATH"], !current.isEmpty {
        env["PYTHONPATH"] = "src:\(current)"
    } else {
        env["PYTHONPATH"] = "src"
    }
    process.environment = env
    process.standardInput = FileHandle.standardInput
    process.standardOutput = FileHandle.standardOutput
    process.standardError = FileHandle.standardError

    do {
        try process.run()
        process.waitUntilExit()
    } catch {
        fputs("error: failed to launch python3: \(error)\n", stderr)
        try? FileManager.default.removeItem(at: scriptURL)
        return 1
    }

    try? FileManager.default.removeItem(at: scriptURL)
    return process.terminationStatus
}

// 埋め込み Python ソース（Base64）。
let pytraEmbeddedSourceBase64 = "IyAwMzog44K444Ol44Oq44Ki6ZuG5ZCI44KSIFBORyDlvaLlvI/jgaflh7rlipvjgZnjgovjgrXjg7Pjg5fjg6vjgafjgZnjgIIKIyDjg4jjg6njg7Pjgrnjg5HjgqTjg6vkupLmj5vjgpLmhI/orZjjgZfjgIHljZjntJTjgarjg6vjg7zjg5fkuK3lv4Pjgaflrp/oo4XjgZfjgabjgYTjgb7jgZnjgIIKCmZyb20gdGltZSBpbXBvcnQgcGVyZl9jb3VudGVyCmZyb20gcHlfbW9kdWxlIGltcG9ydCBwbmdfaGVscGVyCgoKZGVmIHJlbmRlcl9qdWxpYSh3aWR0aDogaW50LCBoZWlnaHQ6IGludCwgbWF4X2l0ZXI6IGludCwgY3g6IGZsb2F0LCBjeTogZmxvYXQpIC0+IGJ5dGVhcnJheToKICAgIHBpeGVsczogYnl0ZWFycmF5ID0gYnl0ZWFycmF5KCkKCiAgICBmb3IgeSBpbiByYW5nZShoZWlnaHQpOgogICAgICAgIHp5MDogZmxvYXQgPSAtMS4yICsgMi40ICogKHkgLyAoaGVpZ2h0IC0gMSkpCgogICAgICAgIGZvciB4IGluIHJhbmdlKHdpZHRoKToKICAgICAgICAgICAgeng6IGZsb2F0ID0gLTEuOCArIDMuNiAqICh4IC8gKHdpZHRoIC0gMSkpCiAgICAgICAgICAgIHp5OiBmbG9hdCA9IHp5MAoKICAgICAgICAgICAgaTogaW50ID0gMAogICAgICAgICAgICB3aGlsZSBpIDwgbWF4X2l0ZXI6CiAgICAgICAgICAgICAgICB6eDI6IGZsb2F0ID0genggKiB6eAogICAgICAgICAgICAgICAgenkyOiBmbG9hdCA9IHp5ICogenkKICAgICAgICAgICAgICAgIGlmIHp4MiArIHp5MiA+IDQuMDoKICAgICAgICAgICAgICAgICAgICBicmVhawogICAgICAgICAgICAgICAgenkgPSAyLjAgKiB6eCAqIHp5ICsgY3kKICAgICAgICAgICAgICAgIHp4ID0gengyIC0genkyICsgY3gKICAgICAgICAgICAgICAgIGkgKz0gMQoKICAgICAgICAgICAgcjogaW50ID0gMAogICAgICAgICAgICBnOiBpbnQgPSAwCiAgICAgICAgICAgIGI6IGludCA9IDAKICAgICAgICAgICAgaWYgaSA+PSBtYXhfaXRlcjoKICAgICAgICAgICAgICAgIHIgPSAwCiAgICAgICAgICAgICAgICBnID0gMAogICAgICAgICAgICAgICAgYiA9IDAKICAgICAgICAgICAgZWxzZToKICAgICAgICAgICAgICAgIHQ6IGZsb2F0ID0gaSAvIG1heF9pdGVyCiAgICAgICAgICAgICAgICByID0gaW50KDI1NS4wICogKDAuMiArIDAuOCAqIHQpKQogICAgICAgICAgICAgICAgZyA9IGludCgyNTUuMCAqICgwLjEgKyAwLjkgKiAodCAqIHQpKSkKICAgICAgICAgICAgICAgIGIgPSBpbnQoMjU1LjAgKiAoMS4wIC0gdCkpCgogICAgICAgICAgICBwaXhlbHMuYXBwZW5kKHIpCiAgICAgICAgICAgIHBpeGVscy5hcHBlbmQoZykKICAgICAgICAgICAgcGl4ZWxzLmFwcGVuZChiKQoKICAgIHJldHVybiBwaXhlbHMKCgpkZWYgcnVuX2p1bGlhKCkgLT4gTm9uZToKICAgIHdpZHRoOiBpbnQgPSAzODQwCiAgICBoZWlnaHQ6IGludCA9IDIxNjAKICAgIG1heF9pdGVyOiBpbnQgPSAyMDAwMAogICAgb3V0X3BhdGg6IHN0ciA9ICJzYW1wbGUvb3V0L2p1bGlhXzAzLnBuZyIKCiAgICBzdGFydDogZmxvYXQgPSBwZXJmX2NvdW50ZXIoKQogICAgcGl4ZWxzOiBieXRlYXJyYXkgPSByZW5kZXJfanVsaWEod2lkdGgsIGhlaWdodCwgbWF4X2l0ZXIsIC0wLjgsIDAuMTU2KQogICAgcG5nX2hlbHBlci53cml0ZV9yZ2JfcG5nKG91dF9wYXRoLCB3aWR0aCwgaGVpZ2h0LCBwaXhlbHMpCiAgICBlbGFwc2VkOiBmbG9hdCA9IHBlcmZfY291bnRlcigpIC0gc3RhcnQKCiAgICBwcmludCgib3V0cHV0OiIsIG91dF9wYXRoKQogICAgcHJpbnQoInNpemU6Iiwgd2lkdGgsICJ4IiwgaGVpZ2h0KQogICAgcHJpbnQoIm1heF9pdGVyOiIsIG1heF9pdGVyKQogICAgcHJpbnQoImVsYXBzZWRfc2VjOiIsIGVsYXBzZWQpCgoKaWYgX19uYW1lX18gPT0gIl9fbWFpbl9fIjoKICAgIHJ1bl9qdWxpYSgpCg=="
let pytraArgs = Array(CommandLine.arguments.dropFirst())
let pytraCode = pytraRunEmbeddedPython(pytraEmbeddedSourceBase64, pytraArgs)
Foundation.exit(pytraCode)
