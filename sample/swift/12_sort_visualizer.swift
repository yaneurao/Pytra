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
let pytraEmbeddedSourceBase64 = "IyAxMjog44OQ44OW44Or44K944O844OI44Gu6YCU5Lit54q25oWL44KSR0lG5Ye65Yqb44GZ44KL44K144Oz44OX44Or44CCCgpmcm9tIF9fZnV0dXJlX18gaW1wb3J0IGFubm90YXRpb25zCgpmcm9tIHRpbWUgaW1wb3J0IHBlcmZfY291bnRlcgoKZnJvbSBweV9tb2R1bGUuZ2lmX2hlbHBlciBpbXBvcnQgZ3JheXNjYWxlX3BhbGV0dGUsIHNhdmVfZ2lmCgoKZGVmIHJlbmRlcih2YWx1ZXM6IGxpc3RbaW50XSwgdzogaW50LCBoOiBpbnQpIC0+IGJ5dGVzOgogICAgZnJhbWUgPSBieXRlYXJyYXkodyAqIGgpCiAgICBuID0gbGVuKHZhbHVlcykKICAgIGJhcl93ID0gdyAvIG4KICAgIGZvciBpIGluIHJhbmdlKG4pOgogICAgICAgIHgwID0gaW50KGkgKiBiYXJfdykKICAgICAgICB4MSA9IGludCgoaSArIDEpICogYmFyX3cpCiAgICAgICAgaWYgeDEgPD0geDA6CiAgICAgICAgICAgIHgxID0geDAgKyAxCiAgICAgICAgYmggPSBpbnQoKCh2YWx1ZXNbaV0gLyBuKSAqIGgpKQogICAgICAgIHkgPSBoIC0gYmgKICAgICAgICBmb3IgeSBpbiByYW5nZSh5LCBoKToKICAgICAgICAgICAgZm9yIHggaW4gcmFuZ2UoeDAsIHgxKToKICAgICAgICAgICAgICAgIGZyYW1lW3kgKiB3ICsgeF0gPSAyNTUKICAgIHJldHVybiBieXRlcyhmcmFtZSkKCgpkZWYgcnVuXzEyX3NvcnRfdmlzdWFsaXplcigpIC0+IE5vbmU6CiAgICB3ID0gMzIwCiAgICBoID0gMTgwCiAgICBuID0gMTI0CiAgICBvdXRfcGF0aCA9ICJzYW1wbGUvb3V0LzEyX3NvcnRfdmlzdWFsaXplci5naWYiCgogICAgc3RhcnQgPSBwZXJmX2NvdW50ZXIoKQogICAgdmFsdWVzOiBsaXN0W2ludF0gPSBbXQogICAgZm9yIGkgaW4gcmFuZ2Uobik6CiAgICAgICAgdmFsdWVzLmFwcGVuZCgoaSAqIDM3ICsgMTkpICUgbikKCiAgICBmcmFtZXM6IGxpc3RbYnl0ZXNdID0gW3JlbmRlcih2YWx1ZXMsIHcsIGgpXQoKICAgIG9wID0gMAogICAgZm9yIGkgaW4gcmFuZ2Uobik6CiAgICAgICAgc3dhcHBlZCA9IEZhbHNlCiAgICAgICAgZm9yIGogaW4gcmFuZ2UobiAtIGkgLSAxKToKICAgICAgICAgICAgaWYgdmFsdWVzW2pdID4gdmFsdWVzW2ogKyAxXToKICAgICAgICAgICAgICAgIHRtcCA9IHZhbHVlc1tqXQogICAgICAgICAgICAgICAgdmFsdWVzW2pdID0gdmFsdWVzW2ogKyAxXQogICAgICAgICAgICAgICAgdmFsdWVzW2ogKyAxXSA9IHRtcAogICAgICAgICAgICAgICAgc3dhcHBlZCA9IFRydWUKICAgICAgICAgICAgaWYgb3AgJSA4ID09IDA6CiAgICAgICAgICAgICAgICBmcmFtZXMuYXBwZW5kKHJlbmRlcih2YWx1ZXMsIHcsIGgpKQogICAgICAgICAgICBvcCArPSAxCiAgICAgICAgaWYgbm90IHN3YXBwZWQ6CiAgICAgICAgICAgIGJyZWFrCgogICAgc2F2ZV9naWYob3V0X3BhdGgsIHcsIGgsIGZyYW1lcywgZ3JheXNjYWxlX3BhbGV0dGUoKSwgZGVsYXlfY3M9MywgbG9vcD0wKQogICAgZWxhcHNlZCA9IHBlcmZfY291bnRlcigpIC0gc3RhcnQKICAgIHByaW50KCJvdXRwdXQ6Iiwgb3V0X3BhdGgpCiAgICBwcmludCgiZnJhbWVzOiIsIGxlbihmcmFtZXMpKQogICAgcHJpbnQoImVsYXBzZWRfc2VjOiIsIGVsYXBzZWQpCgoKaWYgX19uYW1lX18gPT0gIl9fbWFpbl9fIjoKICAgIHJ1bl8xMl9zb3J0X3Zpc3VhbGl6ZXIoKQo="
let pytraArgs = Array(CommandLine.arguments.dropFirst())
let pytraCode = pytraRunEmbeddedPython(pytraEmbeddedSourceBase64, pytraArgs)
Foundation.exit(pytraCode)
