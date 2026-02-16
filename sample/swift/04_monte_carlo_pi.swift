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
let pytraEmbeddedSourceBase64 = "IyAxMDog44Oi44Oz44OG44Kr44Or44Ot5rOV44Gn5YaG5ZGo546H44KS5o6o5a6a44GZ44KL44K144Oz44OX44Or44Gn44GZ44CCCiMgaW1wb3J0IHJhbmRvbSDjgpLkvb/jgo/jgZrjgIFMQ0cg44KS6Ieq5YmN5a6f6KOF44GX44Gm44OI44Op44Oz44K544OR44Kk44Or5LqS5o+b5oCn44KS6auY44KB44Gm44GE44G+44GZ44CCCgpmcm9tIHRpbWUgaW1wb3J0IHBlcmZfY291bnRlcgoKCmRlZiBsY2dfbmV4dChzdGF0ZTogaW50KSAtPiBpbnQ6CiAgICAjIDMyYml0IExDRwogICAgcmV0dXJuICgxNjY0NTI1ICogc3RhdGUgKyAxMDEzOTA0MjIzKSAlIDQyOTQ5NjcyOTYKCgpkZWYgcnVuX3BpX3RyaWFsKHRvdGFsX3NhbXBsZXM6IGludCwgc2VlZDogaW50KSAtPiBmbG9hdDoKICAgIGluc2lkZTogaW50ID0gMAogICAgc3RhdGU6IGludCA9IHNlZWQKCiAgICBmb3IgXyBpbiByYW5nZSh0b3RhbF9zYW1wbGVzKToKICAgICAgICBzdGF0ZSA9IGxjZ19uZXh0KHN0YXRlKQogICAgICAgIHg6IGZsb2F0ID0gc3RhdGUgLyA0Mjk0OTY3Mjk2LjAKCiAgICAgICAgc3RhdGUgPSBsY2dfbmV4dChzdGF0ZSkKICAgICAgICB5OiBmbG9hdCA9IHN0YXRlIC8gNDI5NDk2NzI5Ni4wCgogICAgICAgIGR4OiBmbG9hdCA9IHggLSAwLjUKICAgICAgICBkeTogZmxvYXQgPSB5IC0gMC41CiAgICAgICAgaWYgZHggKiBkeCArIGR5ICogZHkgPD0gMC4yNToKICAgICAgICAgICAgaW5zaWRlICs9IDEKCiAgICByZXR1cm4gNC4wICogaW5zaWRlIC8gdG90YWxfc2FtcGxlcwoKCmRlZiBydW5fbW9udGVfY2FybG9fcGkoKSAtPiBOb25lOgogICAgc2FtcGxlczogaW50ID0gNTQwMDAwMDAKICAgIHNlZWQ6IGludCA9IDEyMzQ1Njc4OQoKICAgIHN0YXJ0OiBmbG9hdCA9IHBlcmZfY291bnRlcigpCiAgICBwaV9lc3Q6IGZsb2F0ID0gcnVuX3BpX3RyaWFsKHNhbXBsZXMsIHNlZWQpCiAgICBlbGFwc2VkOiBmbG9hdCA9IHBlcmZfY291bnRlcigpIC0gc3RhcnQKCiAgICBwcmludCgic2FtcGxlczoiLCBzYW1wbGVzKQogICAgcHJpbnQoInBpX2VzdGltYXRlOiIsIHBpX2VzdCkKICAgIHByaW50KCJlbGFwc2VkX3NlYzoiLCBlbGFwc2VkKQoKCmlmIF9fbmFtZV9fID09ICJfX21haW5fXyI6CiAgICBydW5fbW9udGVfY2FybG9fcGkoKQo="
let pytraArgs = Array(CommandLine.arguments.dropFirst())
let pytraCode = pytraRunEmbeddedPython(pytraEmbeddedSourceBase64, pytraArgs)
Foundation.exit(pytraCode)
