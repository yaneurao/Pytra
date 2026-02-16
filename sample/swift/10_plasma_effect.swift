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
let pytraEmbeddedSourceBase64 = "IyAxMDog44OX44Op44K644Oe44Ko44OV44Kn44Kv44OI44KSR0lG5Ye65Yqb44GZ44KL44K144Oz44OX44Or44CCCgpmcm9tIF9fZnV0dXJlX18gaW1wb3J0IGFubm90YXRpb25zCgppbXBvcnQgbWF0aApmcm9tIHRpbWUgaW1wb3J0IHBlcmZfY291bnRlcgoKZnJvbSBweV9tb2R1bGUuZ2lmX2hlbHBlciBpbXBvcnQgZ3JheXNjYWxlX3BhbGV0dGUsIHNhdmVfZ2lmCgoKZGVmIHJ1bl8xMF9wbGFzbWFfZWZmZWN0KCkgLT4gTm9uZToKICAgIHcgPSAzMjAKICAgIGggPSAyNDAKICAgIGZyYW1lc19uID0gMjE2CiAgICBvdXRfcGF0aCA9ICJzYW1wbGUvb3V0LzEwX3BsYXNtYV9lZmZlY3QuZ2lmIgoKICAgIHN0YXJ0ID0gcGVyZl9jb3VudGVyKCkKICAgIGZyYW1lczogbGlzdFtieXRlc10gPSBbXQoKICAgIGZvciB0IGluIHJhbmdlKGZyYW1lc19uKToKICAgICAgICBmcmFtZSA9IGJ5dGVhcnJheSh3ICogaCkKICAgICAgICBpID0gMAogICAgICAgIGZvciB5IGluIHJhbmdlKGgpOgogICAgICAgICAgICBmb3IgeCBpbiByYW5nZSh3KToKICAgICAgICAgICAgICAgIGR4ID0geCAtIDE2MAogICAgICAgICAgICAgICAgZHkgPSB5IC0gMTIwCiAgICAgICAgICAgICAgICB2ID0gKAogICAgICAgICAgICAgICAgICAgIG1hdGguc2luKCh4ICsgdCAqIDIuMCkgKiAwLjA0NSkKICAgICAgICAgICAgICAgICAgICArIG1hdGguc2luKCh5IC0gdCAqIDEuMikgKiAwLjA1KQogICAgICAgICAgICAgICAgICAgICsgbWF0aC5zaW4oKHggKyB5ICsgdCAqIDEuNykgKiAwLjAzKQogICAgICAgICAgICAgICAgICAgICsgbWF0aC5zaW4obWF0aC5zcXJ0KGR4ICogZHggKyBkeSAqIGR5KSAqIDAuMDcgLSB0ICogMC4xOCkKICAgICAgICAgICAgICAgICkKICAgICAgICAgICAgICAgIGMgPSBpbnQoKHYgKyA0LjApICogKDI1NS4wIC8gOC4wKSkKICAgICAgICAgICAgICAgIGlmIGMgPCAwOgogICAgICAgICAgICAgICAgICAgIGMgPSAwCiAgICAgICAgICAgICAgICBpZiBjID4gMjU1OgogICAgICAgICAgICAgICAgICAgIGMgPSAyNTUKICAgICAgICAgICAgICAgIGZyYW1lW2ldID0gYwogICAgICAgICAgICAgICAgaSArPSAxCiAgICAgICAgZnJhbWVzLmFwcGVuZChieXRlcyhmcmFtZSkpCgogICAgc2F2ZV9naWYob3V0X3BhdGgsIHcsIGgsIGZyYW1lcywgZ3JheXNjYWxlX3BhbGV0dGUoKSwgZGVsYXlfY3M9MywgbG9vcD0wKQogICAgZWxhcHNlZCA9IHBlcmZfY291bnRlcigpIC0gc3RhcnQKICAgIHByaW50KCJvdXRwdXQ6Iiwgb3V0X3BhdGgpCiAgICBwcmludCgiZnJhbWVzOiIsIGZyYW1lc19uKQogICAgcHJpbnQoImVsYXBzZWRfc2VjOiIsIGVsYXBzZWQpCgoKaWYgX19uYW1lX18gPT0gIl9fbWFpbl9fIjoKICAgIHJ1bl8xMF9wbGFzbWFfZWZmZWN0KCkK"
let pytraArgs = Array(CommandLine.arguments.dropFirst())
let pytraCode = pytraRunEmbeddedPython(pytraEmbeddedSourceBase64, pytraArgs)
Foundation.exit(pytraCode)
