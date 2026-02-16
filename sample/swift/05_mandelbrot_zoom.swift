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
let pytraEmbeddedSourceBase64 = "IyAwNTog44Oe44Oz44OH44Or44OW44Ot6ZuG5ZCI44K644O844Og44KS44Ki44OL44Oh44O844K344On44OzR0lG44Go44GX44Gm5Ye65Yqb44GZ44KL44K144Oz44OX44Or44CCCgpmcm9tIF9fZnV0dXJlX18gaW1wb3J0IGFubm90YXRpb25zCgpmcm9tIHRpbWUgaW1wb3J0IHBlcmZfY291bnRlcgoKZnJvbSBweV9tb2R1bGUuZ2lmX2hlbHBlciBpbXBvcnQgZ3JheXNjYWxlX3BhbGV0dGUsIHNhdmVfZ2lmCgoKZGVmIHJlbmRlcl9mcmFtZSh3aWR0aDogaW50LCBoZWlnaHQ6IGludCwgY2VudGVyX3g6IGZsb2F0LCBjZW50ZXJfeTogZmxvYXQsIHNjYWxlOiBmbG9hdCwgbWF4X2l0ZXI6IGludCkgLT4gYnl0ZXM6CiAgICBmcmFtZSA9IGJ5dGVhcnJheSh3aWR0aCAqIGhlaWdodCkKICAgIGlkeCA9IDAKICAgIGZvciB5IGluIHJhbmdlKGhlaWdodCk6CiAgICAgICAgY3kgPSBjZW50ZXJfeSArICh5IC0gaGVpZ2h0ICogMC41KSAqIHNjYWxlCiAgICAgICAgZm9yIHggaW4gcmFuZ2Uod2lkdGgpOgogICAgICAgICAgICBjeCA9IGNlbnRlcl94ICsgKHggLSB3aWR0aCAqIDAuNSkgKiBzY2FsZQogICAgICAgICAgICB6eCA9IDAuMAogICAgICAgICAgICB6eSA9IDAuMAogICAgICAgICAgICBpID0gMAogICAgICAgICAgICB3aGlsZSBpIDwgbWF4X2l0ZXI6CiAgICAgICAgICAgICAgICB6eDIgPSB6eCAqIHp4CiAgICAgICAgICAgICAgICB6eTIgPSB6eSAqIHp5CiAgICAgICAgICAgICAgICBpZiB6eDIgKyB6eTIgPiA0LjA6CiAgICAgICAgICAgICAgICAgICAgYnJlYWsKICAgICAgICAgICAgICAgIHp5ID0gMi4wICogenggKiB6eSArIGN5CiAgICAgICAgICAgICAgICB6eCA9IHp4MiAtIHp5MiArIGN4CiAgICAgICAgICAgICAgICBpICs9IDEKICAgICAgICAgICAgZnJhbWVbaWR4XSA9IGludCgoMjU1LjAgKiBpKSAvIG1heF9pdGVyKQogICAgICAgICAgICBpZHggKz0gMQogICAgcmV0dXJuIGJ5dGVzKGZyYW1lKQoKCmRlZiBydW5fMDVfbWFuZGVsYnJvdF96b29tKCkgLT4gTm9uZToKICAgIHdpZHRoID0gMzIwCiAgICBoZWlnaHQgPSAyNDAKICAgIGZyYW1lX2NvdW50ID0gNDgKICAgIG1heF9pdGVyID0gMTEwCiAgICBjZW50ZXJfeCA9IC0wLjc0MzY0Mzg4NzAzNzE1MQogICAgY2VudGVyX3kgPSAwLjEzMTgyNTkwNDIwNTMzCiAgICBiYXNlX3NjYWxlID0gMy4yIC8gd2lkdGgKICAgIHpvb21fcGVyX2ZyYW1lID0gMC45MwogICAgb3V0X3BhdGggPSAic2FtcGxlL291dC8wNV9tYW5kZWxicm90X3pvb20uZ2lmIgoKICAgIHN0YXJ0ID0gcGVyZl9jb3VudGVyKCkKICAgIGZyYW1lczogbGlzdFtieXRlc10gPSBbXQogICAgc2NhbGUgPSBiYXNlX3NjYWxlCiAgICBmb3IgXyBpbiByYW5nZShmcmFtZV9jb3VudCk6CiAgICAgICAgZnJhbWVzLmFwcGVuZChyZW5kZXJfZnJhbWUod2lkdGgsIGhlaWdodCwgY2VudGVyX3gsIGNlbnRlcl95LCBzY2FsZSwgbWF4X2l0ZXIpKQogICAgICAgIHNjYWxlICo9IHpvb21fcGVyX2ZyYW1lCgogICAgc2F2ZV9naWYob3V0X3BhdGgsIHdpZHRoLCBoZWlnaHQsIGZyYW1lcywgZ3JheXNjYWxlX3BhbGV0dGUoKSwgZGVsYXlfY3M9NSwgbG9vcD0wKQogICAgZWxhcHNlZCA9IHBlcmZfY291bnRlcigpIC0gc3RhcnQKICAgIHByaW50KCJvdXRwdXQ6Iiwgb3V0X3BhdGgpCiAgICBwcmludCgiZnJhbWVzOiIsIGZyYW1lX2NvdW50KQogICAgcHJpbnQoImVsYXBzZWRfc2VjOiIsIGVsYXBzZWQpCgoKaWYgX19uYW1lX18gPT0gIl9fbWFpbl9fIjoKICAgIHJ1bl8wNV9tYW5kZWxicm90X3pvb20oKQo="
let pytraArgs = Array(CommandLine.arguments.dropFirst())
let pytraCode = pytraRunEmbeddedPython(pytraEmbeddedSourceBase64, pytraArgs)
Foundation.exit(pytraCode)
