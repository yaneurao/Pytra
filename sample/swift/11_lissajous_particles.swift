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
let pytraEmbeddedSourceBase64 = "IyAxMTog44Oq44K144O844K444Ol6YGL5YuV44GZ44KL57KS5a2Q44KSR0lG5Ye65Yqb44GZ44KL44K144Oz44OX44Or44CCCgpmcm9tIF9fZnV0dXJlX18gaW1wb3J0IGFubm90YXRpb25zCgppbXBvcnQgbWF0aApmcm9tIHRpbWUgaW1wb3J0IHBlcmZfY291bnRlcgoKZnJvbSBweV9tb2R1bGUuZ2lmX2hlbHBlciBpbXBvcnQgc2F2ZV9naWYKCgpkZWYgY29sb3JfcGFsZXR0ZSgpIC0+IGJ5dGVzOgogICAgcCA9IGJ5dGVhcnJheSgpCiAgICBmb3IgaSBpbiByYW5nZSgyNTYpOgogICAgICAgIHIgPSBpCiAgICAgICAgZyA9IChpICogMykgJSAyNTYKICAgICAgICBiID0gMjU1IC0gaQogICAgICAgIHAuYXBwZW5kKHIpCiAgICAgICAgcC5hcHBlbmQoZykKICAgICAgICBwLmFwcGVuZChiKQogICAgcmV0dXJuIGJ5dGVzKHApCgoKZGVmIHJ1bl8xMV9saXNzYWpvdXNfcGFydGljbGVzKCkgLT4gTm9uZToKICAgIHcgPSAzMjAKICAgIGggPSAyNDAKICAgIGZyYW1lc19uID0gMzYwCiAgICBwYXJ0aWNsZXMgPSA0OAogICAgb3V0X3BhdGggPSAic2FtcGxlL291dC8xMV9saXNzYWpvdXNfcGFydGljbGVzLmdpZiIKCiAgICBzdGFydCA9IHBlcmZfY291bnRlcigpCiAgICBmcmFtZXM6IGxpc3RbYnl0ZXNdID0gW10KCiAgICBmb3IgdCBpbiByYW5nZShmcmFtZXNfbik6CiAgICAgICAgZnJhbWUgPSBieXRlYXJyYXkodyAqIGgpCgogICAgICAgIGZvciBwIGluIHJhbmdlKHBhcnRpY2xlcyk6CiAgICAgICAgICAgIHBoYXNlID0gcCAqIDAuMjYxNzk5CiAgICAgICAgICAgIHggPSBpbnQoKHcgKiAwLjUpICsgKHcgKiAwLjM4KSAqIG1hdGguc2luKDAuMTEgKiB0ICsgcGhhc2UgKiAyLjApKQogICAgICAgICAgICB5ID0gaW50KChoICogMC41KSArIChoICogMC4zOCkgKiBtYXRoLnNpbigwLjE3ICogdCArIHBoYXNlICogMy4wKSkKICAgICAgICAgICAgY29sb3IgPSAzMCArIChwICogOSkgJSAyMjAKCiAgICAgICAgICAgIGZvciBkeSBpbiByYW5nZSgtMiwgMyk6CiAgICAgICAgICAgICAgICBmb3IgZHggaW4gcmFuZ2UoLTIsIDMpOgogICAgICAgICAgICAgICAgICAgIHh4ID0geCArIGR4CiAgICAgICAgICAgICAgICAgICAgeXkgPSB5ICsgZHkKICAgICAgICAgICAgICAgICAgICBpZiB4eCA+PSAwIGFuZCB4eCA8IHcgYW5kIHl5ID49IDAgYW5kIHl5IDwgaDoKICAgICAgICAgICAgICAgICAgICAgICAgZDIgPSBkeCAqIGR4ICsgZHkgKiBkeQogICAgICAgICAgICAgICAgICAgICAgICBpZiBkMiA8PSA0OgogICAgICAgICAgICAgICAgICAgICAgICAgICAgaWR4ID0geXkgKiB3ICsgeHgKICAgICAgICAgICAgICAgICAgICAgICAgICAgIHYgPSBjb2xvciAtIGQyICogMjAKICAgICAgICAgICAgICAgICAgICAgICAgICAgIGlmIHYgPCAwOgogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIHYgPSAwCiAgICAgICAgICAgICAgICAgICAgICAgICAgICBpZiB2ID4gZnJhbWVbaWR4XToKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICBmcmFtZVtpZHhdID0gdgoKICAgICAgICBmcmFtZXMuYXBwZW5kKGJ5dGVzKGZyYW1lKSkKCiAgICBzYXZlX2dpZihvdXRfcGF0aCwgdywgaCwgZnJhbWVzLCBjb2xvcl9wYWxldHRlKCksIGRlbGF5X2NzPTMsIGxvb3A9MCkKICAgIGVsYXBzZWQgPSBwZXJmX2NvdW50ZXIoKSAtIHN0YXJ0CiAgICBwcmludCgib3V0cHV0OiIsIG91dF9wYXRoKQogICAgcHJpbnQoImZyYW1lczoiLCBmcmFtZXNfbikKICAgIHByaW50KCJlbGFwc2VkX3NlYzoiLCBlbGFwc2VkKQoKCmlmIF9fbmFtZV9fID09ICJfX21haW5fXyI6CiAgICBydW5fMTFfbGlzc2Fqb3VzX3BhcnRpY2xlcygpCg=="
let pytraArgs = Array(CommandLine.arguments.dropFirst())
let pytraCode = pytraRunEmbeddedPython(pytraEmbeddedSourceBase64, pytraArgs)
Foundation.exit(pytraCode)
