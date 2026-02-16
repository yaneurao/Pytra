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
let pytraEmbeddedSourceBase64 = "IyAxMzogREZT6L+36Lev55Sf5oiQ44Gu6YCy6KGM54q25rOB44KSR0lG5Ye65Yqb44GZ44KL44K144Oz44OX44Or44CCCgpmcm9tIF9fZnV0dXJlX18gaW1wb3J0IGFubm90YXRpb25zCgpmcm9tIHRpbWUgaW1wb3J0IHBlcmZfY291bnRlcgoKZnJvbSBweV9tb2R1bGUuZ2lmX2hlbHBlciBpbXBvcnQgZ3JheXNjYWxlX3BhbGV0dGUsIHNhdmVfZ2lmCgoKZGVmIGNhcHR1cmUoZ3JpZDogbGlzdFtsaXN0W2ludF1dLCB3OiBpbnQsIGg6IGludCwgc2NhbGU6IGludCkgLT4gYnl0ZXM6CiAgICB3aWR0aCA9IHcgKiBzY2FsZQogICAgaGVpZ2h0ID0gaCAqIHNjYWxlCiAgICBmcmFtZSA9IGJ5dGVhcnJheSh3aWR0aCAqIGhlaWdodCkKICAgIGZvciB5IGluIHJhbmdlKGgpOgogICAgICAgIGZvciB4IGluIHJhbmdlKHcpOgogICAgICAgICAgICB2ID0gMjU1IGlmIGdyaWRbeV1beF0gPT0gMCBlbHNlIDQwCiAgICAgICAgICAgIGZvciB5eSBpbiByYW5nZShzY2FsZSk6CiAgICAgICAgICAgICAgICBiYXNlID0gKHkgKiBzY2FsZSArIHl5KSAqIHdpZHRoICsgeCAqIHNjYWxlCiAgICAgICAgICAgICAgICBmb3IgeHggaW4gcmFuZ2Uoc2NhbGUpOgogICAgICAgICAgICAgICAgICAgIGZyYW1lW2Jhc2UgKyB4eF0gPSB2CiAgICByZXR1cm4gYnl0ZXMoZnJhbWUpCgoKZGVmIHJ1bl8xM19tYXplX2dlbmVyYXRpb25fc3RlcHMoKSAtPiBOb25lOgogICAgIyDlrp/ooYzmmYLplpPjgpLljYHliIbjgavnorrkv53jgZnjgovjgZ/jgoHjgIHov7fot6/jgrXjgqTjgrrjgajmj4/nlLvop6Plg4/luqbjgpLkuIrjgZLjgovjgIIKICAgIGNlbGxfdyA9IDg5CiAgICBjZWxsX2ggPSA2NwogICAgc2NhbGUgPSA1CiAgICBjYXB0dXJlX2V2ZXJ5ID0gMjAKICAgIG91dF9wYXRoID0gInNhbXBsZS9vdXQvMTNfbWF6ZV9nZW5lcmF0aW9uX3N0ZXBzLmdpZiIKCiAgICBzdGFydCA9IHBlcmZfY291bnRlcigpCiAgICBncmlkOiBsaXN0W2xpc3RbaW50XV0gPSBbXQogICAgZm9yIF8gaW4gcmFuZ2UoY2VsbF9oKToKICAgICAgICByb3c6IGxpc3RbaW50XSA9IFtdCiAgICAgICAgZm9yIF8gaW4gcmFuZ2UoY2VsbF93KToKICAgICAgICAgICAgcm93LmFwcGVuZCgxKQogICAgICAgIGdyaWQuYXBwZW5kKHJvdykKICAgIHN0YWNrOiBsaXN0W3R1cGxlW2ludCwgaW50XV0gPSBbKDEsIDEpXQogICAgZ3JpZFsxXVsxXSA9IDAKCiAgICBkaXJzOiBsaXN0W3R1cGxlW2ludCwgaW50XV0gPSBbKDIsIDApLCAoLTIsIDApLCAoMCwgMiksICgwLCAtMildCiAgICBmcmFtZXM6IGxpc3RbYnl0ZXNdID0gW10KICAgIHN0ZXAgPSAwCgogICAgd2hpbGUgbGVuKHN0YWNrKSA+IDA6CiAgICAgICAgbGFzdF9pbmRleCA9IGxlbihzdGFjaykgLSAxCiAgICAgICAgeCwgeSA9IHN0YWNrW2xhc3RfaW5kZXhdCiAgICAgICAgY2FuZGlkYXRlczogbGlzdFt0dXBsZVtpbnQsIGludCwgaW50LCBpbnRdXSA9IFtdCiAgICAgICAgZm9yIGsgaW4gcmFuZ2UoNCk6CiAgICAgICAgICAgIGR4LCBkeSA9IGRpcnNba10KICAgICAgICAgICAgbnggPSB4ICsgZHgKICAgICAgICAgICAgbnkgPSB5ICsgZHkKICAgICAgICAgICAgaWYgbnggPj0gMSBhbmQgbnggPCBjZWxsX3cgLSAxIGFuZCBueSA+PSAxIGFuZCBueSA8IGNlbGxfaCAtIDEgYW5kIGdyaWRbbnldW254XSA9PSAxOgogICAgICAgICAgICAgICAgaWYgZHggPT0gMjoKICAgICAgICAgICAgICAgICAgICBjYW5kaWRhdGVzLmFwcGVuZCgobngsIG55LCB4ICsgMSwgeSkpCiAgICAgICAgICAgICAgICBlbGlmIGR4ID09IC0yOgogICAgICAgICAgICAgICAgICAgIGNhbmRpZGF0ZXMuYXBwZW5kKChueCwgbnksIHggLSAxLCB5KSkKICAgICAgICAgICAgICAgIGVsaWYgZHkgPT0gMjoKICAgICAgICAgICAgICAgICAgICBjYW5kaWRhdGVzLmFwcGVuZCgobngsIG55LCB4LCB5ICsgMSkpCiAgICAgICAgICAgICAgICBlbHNlOgogICAgICAgICAgICAgICAgICAgIGNhbmRpZGF0ZXMuYXBwZW5kKChueCwgbnksIHgsIHkgLSAxKSkKCiAgICAgICAgaWYgbGVuKGNhbmRpZGF0ZXMpID09IDA6CiAgICAgICAgICAgIHN0YWNrLnBvcCgpCiAgICAgICAgZWxzZToKICAgICAgICAgICAgc2VsID0gY2FuZGlkYXRlc1soeCAqIDE3ICsgeSAqIDI5ICsgbGVuKHN0YWNrKSAqIDEzKSAlIGxlbihjYW5kaWRhdGVzKV0KICAgICAgICAgICAgbngsIG55LCB3eCwgd3kgPSBzZWwKICAgICAgICAgICAgZ3JpZFt3eV1bd3hdID0gMAogICAgICAgICAgICBncmlkW255XVtueF0gPSAwCiAgICAgICAgICAgIHN0YWNrLmFwcGVuZCgobngsIG55KSkKCiAgICAgICAgaWYgc3RlcCAlIGNhcHR1cmVfZXZlcnkgPT0gMDoKICAgICAgICAgICAgZnJhbWVzLmFwcGVuZChjYXB0dXJlKGdyaWQsIGNlbGxfdywgY2VsbF9oLCBzY2FsZSkpCiAgICAgICAgc3RlcCArPSAxCgogICAgZnJhbWVzLmFwcGVuZChjYXB0dXJlKGdyaWQsIGNlbGxfdywgY2VsbF9oLCBzY2FsZSkpCiAgICBzYXZlX2dpZihvdXRfcGF0aCwgY2VsbF93ICogc2NhbGUsIGNlbGxfaCAqIHNjYWxlLCBmcmFtZXMsIGdyYXlzY2FsZV9wYWxldHRlKCksIGRlbGF5X2NzPTQsIGxvb3A9MCkKICAgIGVsYXBzZWQgPSBwZXJmX2NvdW50ZXIoKSAtIHN0YXJ0CiAgICBwcmludCgib3V0cHV0OiIsIG91dF9wYXRoKQogICAgcHJpbnQoImZyYW1lczoiLCBsZW4oZnJhbWVzKSkKICAgIHByaW50KCJlbGFwc2VkX3NlYzoiLCBlbGFwc2VkKQoKCmlmIF9fbmFtZV9fID09ICJfX21haW5fXyI6CiAgICBydW5fMTNfbWF6ZV9nZW5lcmF0aW9uX3N0ZXBzKCkK"
let pytraArgs = Array(CommandLine.arguments.dropFirst())
let pytraCode = pytraRunEmbeddedPython(pytraEmbeddedSourceBase64, pytraArgs)
Foundation.exit(pytraCode)
