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
let pytraEmbeddedSourceBase64 = "IyAxNDog57Ch5piT44Os44Kk44Oe44O844OB6aKo44Gu5YWJ5rqQ56e75YuV44K344O844Oz44KSR0lG5Ye65Yqb44GZ44KL44K144Oz44OX44Or44CCCgpmcm9tIF9fZnV0dXJlX18gaW1wb3J0IGFubm90YXRpb25zCgppbXBvcnQgbWF0aApmcm9tIHRpbWUgaW1wb3J0IHBlcmZfY291bnRlcgoKZnJvbSBweV9tb2R1bGUuZ2lmX2hlbHBlciBpbXBvcnQgc2F2ZV9naWYKCgpkZWYgcGFsZXR0ZSgpIC0+IGJ5dGVzOgogICAgcCA9IGJ5dGVhcnJheSgpCiAgICBmb3IgaSBpbiByYW5nZSgyNTYpOgogICAgICAgIHIgPSBpbnQoMjAgKyBpICogMC45KQogICAgICAgIGlmIHIgPiAyNTU6CiAgICAgICAgICAgIHIgPSAyNTUKICAgICAgICBnID0gaW50KDEwICsgaSAqIDAuNykKICAgICAgICBpZiBnID4gMjU1OgogICAgICAgICAgICBnID0gMjU1CiAgICAgICAgYiA9IGludCgzMCArIGkpCiAgICAgICAgaWYgYiA+IDI1NToKICAgICAgICAgICAgYiA9IDI1NQogICAgICAgIHAuYXBwZW5kKHIpCiAgICAgICAgcC5hcHBlbmQoZykKICAgICAgICBwLmFwcGVuZChiKQogICAgcmV0dXJuIGJ5dGVzKHApCgoKZGVmIHNjZW5lKHg6IGZsb2F0LCB5OiBmbG9hdCwgbGlnaHRfeDogZmxvYXQsIGxpZ2h0X3k6IGZsb2F0KSAtPiBpbnQ6CiAgICB4MSA9IHggKyAwLjQ1CiAgICB5MSA9IHkgKyAwLjIKICAgIHgyID0geCAtIDAuMzUKICAgIHkyID0geSAtIDAuMTUKICAgIHIxID0gbWF0aC5zcXJ0KHgxICogeDEgKyB5MSAqIHkxKQogICAgcjIgPSBtYXRoLnNxcnQoeDIgKiB4MiArIHkyICogeTIpCiAgICBibG9iID0gbWF0aC5leHAoLTcuMCAqIHIxICogcjEpICsgbWF0aC5leHAoLTguMCAqIHIyICogcjIpCgogICAgbHggPSB4IC0gbGlnaHRfeAogICAgbHkgPSB5IC0gbGlnaHRfeQogICAgbCA9IG1hdGguc3FydChseCAqIGx4ICsgbHkgKiBseSkKICAgIGxpdCA9IDEuMCAvICgxLjAgKyAzLjUgKiBsICogbCkKCiAgICB2ID0gaW50KDI1NS4wICogYmxvYiAqIGxpdCAqIDUuMCkKICAgIGlmIHYgPCAwOgogICAgICAgIHJldHVybiAwCiAgICBpZiB2ID4gMjU1OgogICAgICAgIHJldHVybiAyNTUKICAgIHJldHVybiB2CgoKZGVmIHJ1bl8xNF9yYXltYXJjaGluZ19saWdodF9jeWNsZSgpIC0+IE5vbmU6CiAgICB3ID0gMzIwCiAgICBoID0gMjQwCiAgICBmcmFtZXNfbiA9IDg0CiAgICBvdXRfcGF0aCA9ICJzYW1wbGUvb3V0LzE0X3JheW1hcmNoaW5nX2xpZ2h0X2N5Y2xlLmdpZiIKCiAgICBzdGFydCA9IHBlcmZfY291bnRlcigpCiAgICBmcmFtZXM6IGxpc3RbYnl0ZXNdID0gW10KCiAgICBmb3IgdCBpbiByYW5nZShmcmFtZXNfbik6CiAgICAgICAgZnJhbWUgPSBieXRlYXJyYXkodyAqIGgpCiAgICAgICAgYSA9ICh0IC8gZnJhbWVzX24pICogbWF0aC5waSAqIDIuMAogICAgICAgIGxpZ2h0X3ggPSAwLjc1ICogbWF0aC5jb3MoYSkKICAgICAgICBsaWdodF95ID0gMC41NSAqIG1hdGguc2luKGEgKiAxLjIpCgogICAgICAgIGkgPSAwCiAgICAgICAgZm9yIHkgaW4gcmFuZ2UoaCk6CiAgICAgICAgICAgIHB5ID0gKHkgLyAoaCAtIDEpKSAqIDIuMCAtIDEuMAogICAgICAgICAgICBmb3IgeCBpbiByYW5nZSh3KToKICAgICAgICAgICAgICAgIHB4ID0gKHggLyAodyAtIDEpKSAqIDIuMCAtIDEuMAogICAgICAgICAgICAgICAgZnJhbWVbaV0gPSBzY2VuZShweCwgcHksIGxpZ2h0X3gsIGxpZ2h0X3kpCiAgICAgICAgICAgICAgICBpICs9IDEKCiAgICAgICAgZnJhbWVzLmFwcGVuZChieXRlcyhmcmFtZSkpCgogICAgc2F2ZV9naWYob3V0X3BhdGgsIHcsIGgsIGZyYW1lcywgcGFsZXR0ZSgpLCBkZWxheV9jcz0zLCBsb29wPTApCiAgICBlbGFwc2VkID0gcGVyZl9jb3VudGVyKCkgLSBzdGFydAogICAgcHJpbnQoIm91dHB1dDoiLCBvdXRfcGF0aCkKICAgIHByaW50KCJmcmFtZXM6IiwgZnJhbWVzX24pCiAgICBwcmludCgiZWxhcHNlZF9zZWM6IiwgZWxhcHNlZCkKCgppZiBfX25hbWVfXyA9PSAiX19tYWluX18iOgogICAgcnVuXzE0X3JheW1hcmNoaW5nX2xpZ2h0X2N5Y2xlKCkK"
let pytraArgs = Array(CommandLine.arguments.dropFirst())
let pytraCode = pytraRunEmbeddedPython(pytraEmbeddedSourceBase64, pytraArgs)
Foundation.exit(pytraCode)
