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
let pytraEmbeddedSourceBase64 = "IyAwODog44Op44Oz44Kw44OI44Oz44Gu44Ki44Oq44Gu6LuM6Leh44KSR0lG5Ye65Yqb44GZ44KL44K144Oz44OX44Or44CCCgpmcm9tIF9fZnV0dXJlX18gaW1wb3J0IGFubm90YXRpb25zCgpmcm9tIHRpbWUgaW1wb3J0IHBlcmZfY291bnRlcgoKZnJvbSBweV9tb2R1bGUuZ2lmX2hlbHBlciBpbXBvcnQgZ3JheXNjYWxlX3BhbGV0dGUsIHNhdmVfZ2lmCgoKZGVmIGNhcHR1cmUoZ3JpZDogbGlzdFtsaXN0W2ludF1dLCB3OiBpbnQsIGg6IGludCkgLT4gYnl0ZXM6CiAgICBmcmFtZSA9IGJ5dGVhcnJheSh3ICogaCkKICAgIGkgPSAwCiAgICBmb3IgeSBpbiByYW5nZShoKToKICAgICAgICBmb3IgeCBpbiByYW5nZSh3KToKICAgICAgICAgICAgZnJhbWVbaV0gPSAyNTUgaWYgZ3JpZFt5XVt4XSBlbHNlIDAKICAgICAgICAgICAgaSArPSAxCiAgICByZXR1cm4gYnl0ZXMoZnJhbWUpCgoKZGVmIHJ1bl8wOF9sYW5ndG9uc19hbnQoKSAtPiBOb25lOgogICAgdyA9IDQyMAogICAgaCA9IDQyMAogICAgb3V0X3BhdGggPSAic2FtcGxlL291dC8wOF9sYW5ndG9uc19hbnQuZ2lmIgoKICAgIHN0YXJ0ID0gcGVyZl9jb3VudGVyKCkKCiAgICBncmlkOiBsaXN0W2xpc3RbaW50XV0gPSBbXQogICAgZm9yIGd5IGluIHJhbmdlKGgpOgogICAgICAgIHJvdzogbGlzdFtpbnRdID0gW10KICAgICAgICBmb3IgZ3ggaW4gcmFuZ2Uodyk6CiAgICAgICAgICAgIHJvdy5hcHBlbmQoMCkKICAgICAgICBncmlkLmFwcGVuZChyb3cpCiAgICB4ID0gdyAvLyAyCiAgICB5ID0gaCAvLyAyCiAgICBkID0gMAoKICAgIHN0ZXBzX3RvdGFsID0gNjAwMDAwCiAgICBjYXB0dXJlX2V2ZXJ5ID0gMzAwMAogICAgZnJhbWVzOiBsaXN0W2J5dGVzXSA9IFtdCgogICAgZm9yIGkgaW4gcmFuZ2Uoc3RlcHNfdG90YWwpOgogICAgICAgIGlmIGdyaWRbeV1beF0gPT0gMDoKICAgICAgICAgICAgZCA9IChkICsgMSkgJSA0CiAgICAgICAgICAgIGdyaWRbeV1beF0gPSAxCiAgICAgICAgZWxzZToKICAgICAgICAgICAgZCA9IChkICsgMykgJSA0CiAgICAgICAgICAgIGdyaWRbeV1beF0gPSAwCgogICAgICAgIGlmIGQgPT0gMDoKICAgICAgICAgICAgeSA9ICh5IC0gMSArIGgpICUgaAogICAgICAgIGVsaWYgZCA9PSAxOgogICAgICAgICAgICB4ID0gKHggKyAxKSAlIHcKICAgICAgICBlbGlmIGQgPT0gMjoKICAgICAgICAgICAgeSA9ICh5ICsgMSkgJSBoCiAgICAgICAgZWxzZToKICAgICAgICAgICAgeCA9ICh4IC0gMSArIHcpICUgdwoKICAgICAgICBpZiBpICUgY2FwdHVyZV9ldmVyeSA9PSAwOgogICAgICAgICAgICBmcmFtZXMuYXBwZW5kKGNhcHR1cmUoZ3JpZCwgdywgaCkpCgogICAgc2F2ZV9naWYob3V0X3BhdGgsIHcsIGgsIGZyYW1lcywgZ3JheXNjYWxlX3BhbGV0dGUoKSwgZGVsYXlfY3M9NSwgbG9vcD0wKQogICAgZWxhcHNlZCA9IHBlcmZfY291bnRlcigpIC0gc3RhcnQKICAgIHByaW50KCJvdXRwdXQ6Iiwgb3V0X3BhdGgpCiAgICBwcmludCgiZnJhbWVzOiIsIGxlbihmcmFtZXMpKQogICAgcHJpbnQoImVsYXBzZWRfc2VjOiIsIGVsYXBzZWQpCgoKaWYgX19uYW1lX18gPT0gIl9fbWFpbl9fIjoKICAgIHJ1bl8wOF9sYW5ndG9uc19hbnQoKQo="
let pytraArgs = Array(CommandLine.arguments.dropFirst())
let pytraCode = pytraRunEmbeddedPython(pytraEmbeddedSourceBase64, pytraArgs)
Foundation.exit(pytraCode)
