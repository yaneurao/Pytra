// このファイルは自動生成です（Python -> Swift node-backed mode）。

// Swift 実行向け Node.js ランタイム補助。

import Foundation

/// Base64 で埋め込まれた JavaScript ソースコードを一時ファイルへ展開し、node で実行する。
/// - Parameters:
///   - sourceBase64: JavaScript ソースコードの Base64 文字列。
///   - args: JavaScript 側へ渡す引数配列。
/// - Returns:
///   node プロセスの終了コード。失敗時は 1 を返す。
func pytraRunEmbeddedNode(_ sourceBase64: String, _ args: [String]) -> Int32 {
    guard let sourceData = Data(base64Encoded: sourceBase64) else {
        fputs("error: failed to decode embedded JavaScript source\n", stderr)
        return 1
    }

    let tmpDir = URL(fileURLWithPath: NSTemporaryDirectory(), isDirectory: true)
    let fileName = "pytra_embedded_\(UUID().uuidString).js"
    let scriptURL = tmpDir.appendingPathComponent(fileName)

    do {
        try sourceData.write(to: scriptURL)
    } catch {
        fputs("error: failed to write temporary JavaScript file: \(error)\n", stderr)
        return 1
    }

    let process = Process()
    process.executableURL = URL(fileURLWithPath: "/usr/bin/env")
    process.arguments = ["node", scriptURL.path] + args
    process.environment = ProcessInfo.processInfo.environment
    process.standardInput = FileHandle.standardInput
    process.standardOutput = FileHandle.standardOutput
    process.standardError = FileHandle.standardError

    do {
        try process.run()
        process.waitUntilExit()
    } catch {
        fputs("error: failed to launch node: \(error)\n", stderr)
        try? FileManager.default.removeItem(at: scriptURL)
        return 1
    }

    try? FileManager.default.removeItem(at: scriptURL)
    return process.terminationStatus
}

// 埋め込み JavaScript ソース（Base64）。
let pytraEmbeddedJsBase64 = "Ly8gZ2VuZXJhdGVkIGludGVybmFsIEphdmFTY3JpcHQKCmNvbnN0IF9fcHl0cmFfcm9vdCA9IHByb2Nlc3MuY3dkKCk7CmNvbnN0IHB5X3J1bnRpbWUgPSByZXF1aXJlKF9fcHl0cmFfcm9vdCArICcvc3JjL2pzX21vZHVsZS9weV9ydW50aW1lLmpzJyk7CmNvbnN0IHB5X21hdGggPSByZXF1aXJlKF9fcHl0cmFfcm9vdCArICcvc3JjL2pzX21vZHVsZS9tYXRoLmpzJyk7CmNvbnN0IHB5X3RpbWUgPSByZXF1aXJlKF9fcHl0cmFfcm9vdCArICcvc3JjL2pzX21vZHVsZS90aW1lLmpzJyk7CmNvbnN0IHsgcHlQcmludCwgcHlMZW4sIHB5Qm9vbCwgcHlSYW5nZSwgcHlGbG9vckRpdiwgcHlNb2QsIHB5SW4sIHB5U2xpY2UsIHB5T3JkLCBweUNociwgcHlCeXRlYXJyYXksIHB5Qnl0ZXMsIHB5SXNEaWdpdCwgcHlJc0FscGhhIH0gPSBweV9ydW50aW1lOwpjb25zdCB7IHBlcmZDb3VudGVyIH0gPSBweV90aW1lOwpjb25zdCBwZXJmX2NvdW50ZXIgPSBwZXJmQ291bnRlcjsKY29uc3QgeyBncmF5c2NhbGVfcGFsZXR0ZSwgc2F2ZV9naWYgfSA9IHJlcXVpcmUoX19weXRyYV9yb290ICsgJy9zcmMvanNfbW9kdWxlL2dpZl9oZWxwZXIuanMnKTsKCmZ1bmN0aW9uIHJlbmRlcl9mcmFtZSh3aWR0aCwgaGVpZ2h0LCBjZW50ZXJfeCwgY2VudGVyX3ksIHNjYWxlLCBtYXhfaXRlcikgewogICAgbGV0IGZyYW1lID0gcHlCeXRlYXJyYXkoKCh3aWR0aCkgKiAoaGVpZ2h0KSkpOwogICAgbGV0IGlkeCA9IDA7CiAgICBsZXQgeTsKICAgIGZvciAobGV0IF9fcHl0cmFfaV8xID0gMDsgX19weXRyYV9pXzEgPCBoZWlnaHQ7IF9fcHl0cmFfaV8xICs9IDEpIHsKICAgICAgICB5ID0gX19weXRyYV9pXzE7CiAgICAgICAgbGV0IGN5ID0gKChjZW50ZXJfeSkgKyAoKCgoKHkpIC0gKCgoaGVpZ2h0KSAqICgwLjUpKSkpKSAqIChzY2FsZSkpKSk7CiAgICAgICAgbGV0IHg7CiAgICAgICAgZm9yIChsZXQgX19weXRyYV9pXzIgPSAwOyBfX3B5dHJhX2lfMiA8IHdpZHRoOyBfX3B5dHJhX2lfMiArPSAxKSB7CiAgICAgICAgICAgIHggPSBfX3B5dHJhX2lfMjsKICAgICAgICAgICAgbGV0IGN4ID0gKChjZW50ZXJfeCkgKyAoKCgoKHgpIC0gKCgod2lkdGgpICogKDAuNSkpKSkpICogKHNjYWxlKSkpKTsKICAgICAgICAgICAgbGV0IHp4ID0gMC4wOwogICAgICAgICAgICBsZXQgenkgPSAwLjA7CiAgICAgICAgICAgIGxldCBpID0gMDsKICAgICAgICAgICAgd2hpbGUgKHB5Qm9vbCgoKGkpIDwgKG1heF9pdGVyKSkpKSB7CiAgICAgICAgICAgICAgICBsZXQgengyID0gKCh6eCkgKiAoengpKTsKICAgICAgICAgICAgICAgIGxldCB6eTIgPSAoKHp5KSAqICh6eSkpOwogICAgICAgICAgICAgICAgaWYgKHB5Qm9vbCgoKCgoengyKSArICh6eTIpKSkgPiAoNC4wKSkpKSB7CiAgICAgICAgICAgICAgICAgICAgYnJlYWs7CiAgICAgICAgICAgICAgICB9CiAgICAgICAgICAgICAgICB6eSA9ICgoKCgoKDIuMCkgKiAoengpKSkgKiAoenkpKSkgKyAoY3kpKTsKICAgICAgICAgICAgICAgIHp4ID0gKCgoKHp4MikgLSAoenkyKSkpICsgKGN4KSk7CiAgICAgICAgICAgICAgICBpID0gaSArIDE7CiAgICAgICAgICAgIH0KICAgICAgICAgICAgZnJhbWVbaWR4XSA9IE1hdGgudHJ1bmMoTnVtYmVyKCgoKCgyNTUuMCkgKiAoaSkpKSAvIChtYXhfaXRlcikpKSk7CiAgICAgICAgICAgIGlkeCA9IGlkeCArIDE7CiAgICAgICAgfQogICAgfQogICAgcmV0dXJuIHB5Qnl0ZXMoZnJhbWUpOwp9CmZ1bmN0aW9uIHJ1bl8wNV9tYW5kZWxicm90X3pvb20oKSB7CiAgICBsZXQgd2lkdGggPSAzMjA7CiAgICBsZXQgaGVpZ2h0ID0gMjQwOwogICAgbGV0IGZyYW1lX2NvdW50ID0gNDg7CiAgICBsZXQgbWF4X2l0ZXIgPSAxMTA7CiAgICBsZXQgY2VudGVyX3ggPSAoLSgwLjc0MzY0Mzg4NzAzNzE1MSkpOwogICAgbGV0IGNlbnRlcl95ID0gMC4xMzE4MjU5MDQyMDUzMzsKICAgIGxldCBiYXNlX3NjYWxlID0gKCgzLjIpIC8gKHdpZHRoKSk7CiAgICBsZXQgem9vbV9wZXJfZnJhbWUgPSAwLjkzOwogICAgbGV0IG91dF9wYXRoID0gJ3NhbXBsZS9vdXQvMDVfbWFuZGVsYnJvdF96b29tLmdpZic7CiAgICBsZXQgc3RhcnQgPSBwZXJmX2NvdW50ZXIoKTsKICAgIGxldCBmcmFtZXMgPSBbXTsKICAgIGxldCBzY2FsZSA9IGJhc2Vfc2NhbGU7CiAgICBsZXQgXzsKICAgIGZvciAobGV0IF9fcHl0cmFfaV8zID0gMDsgX19weXRyYV9pXzMgPCBmcmFtZV9jb3VudDsgX19weXRyYV9pXzMgKz0gMSkgewogICAgICAgIF8gPSBfX3B5dHJhX2lfMzsKICAgICAgICBmcmFtZXMucHVzaChyZW5kZXJfZnJhbWUod2lkdGgsIGhlaWdodCwgY2VudGVyX3gsIGNlbnRlcl95LCBzY2FsZSwgbWF4X2l0ZXIpKTsKICAgICAgICBzY2FsZSA9IHNjYWxlICogem9vbV9wZXJfZnJhbWU7CiAgICB9CiAgICBzYXZlX2dpZihvdXRfcGF0aCwgd2lkdGgsIGhlaWdodCwgZnJhbWVzLCBncmF5c2NhbGVfcGFsZXR0ZSgpLCA1LCAwKTsKICAgIGxldCBlbGFwc2VkID0gKChwZXJmX2NvdW50ZXIoKSkgLSAoc3RhcnQpKTsKICAgIHB5UHJpbnQoJ291dHB1dDonLCBvdXRfcGF0aCk7CiAgICBweVByaW50KCdmcmFtZXM6JywgZnJhbWVfY291bnQpOwogICAgcHlQcmludCgnZWxhcHNlZF9zZWM6JywgZWxhcHNlZCk7Cn0KcnVuXzA1X21hbmRlbGJyb3Rfem9vbSgpOwo="
let pytraArgs = Array(CommandLine.arguments.dropFirst())
let pytraCode = pytraRunEmbeddedNode(pytraEmbeddedJsBase64, pytraArgs)
Foundation.exit(pytraCode)
