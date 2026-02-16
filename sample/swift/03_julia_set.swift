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
let pytraEmbeddedJsBase64 = "Ly8gZ2VuZXJhdGVkIGludGVybmFsIEphdmFTY3JpcHQKCmNvbnN0IF9fcHl0cmFfcm9vdCA9IHByb2Nlc3MuY3dkKCk7CmNvbnN0IHB5X3J1bnRpbWUgPSByZXF1aXJlKF9fcHl0cmFfcm9vdCArICcvc3JjL2pzX21vZHVsZS9weV9ydW50aW1lLmpzJyk7CmNvbnN0IHB5X21hdGggPSByZXF1aXJlKF9fcHl0cmFfcm9vdCArICcvc3JjL2pzX21vZHVsZS9tYXRoLmpzJyk7CmNvbnN0IHB5X3RpbWUgPSByZXF1aXJlKF9fcHl0cmFfcm9vdCArICcvc3JjL2pzX21vZHVsZS90aW1lLmpzJyk7CmNvbnN0IHsgcHlQcmludCwgcHlMZW4sIHB5Qm9vbCwgcHlSYW5nZSwgcHlGbG9vckRpdiwgcHlNb2QsIHB5SW4sIHB5U2xpY2UsIHB5T3JkLCBweUNociwgcHlCeXRlYXJyYXksIHB5Qnl0ZXMsIHB5SXNEaWdpdCwgcHlJc0FscGhhIH0gPSBweV9ydW50aW1lOwpjb25zdCB7IHBlcmZDb3VudGVyIH0gPSBweV90aW1lOwpjb25zdCBwZXJmX2NvdW50ZXIgPSBwZXJmQ291bnRlcjsKY29uc3QgcG5nX2hlbHBlciA9IHJlcXVpcmUoX19weXRyYV9yb290ICsgJy9zcmMvanNfbW9kdWxlL3BuZ19oZWxwZXIuanMnKTsKCmZ1bmN0aW9uIHJlbmRlcl9qdWxpYSh3aWR0aCwgaGVpZ2h0LCBtYXhfaXRlciwgY3gsIGN5KSB7CiAgICBsZXQgcGl4ZWxzID0gcHlCeXRlYXJyYXkoKTsKICAgIGxldCB5OwogICAgZm9yIChsZXQgX19weXRyYV9pXzEgPSAwOyBfX3B5dHJhX2lfMSA8IGhlaWdodDsgX19weXRyYV9pXzEgKz0gMSkgewogICAgICAgIHkgPSBfX3B5dHJhX2lfMTsKICAgICAgICBsZXQgenkwID0gKCgoLSgxLjIpKSkgKyAoKCgyLjQpICogKCgoeSkgLyAoKChoZWlnaHQpIC0gKDEpKSkpKSkpKTsKICAgICAgICBsZXQgeDsKICAgICAgICBmb3IgKGxldCBfX3B5dHJhX2lfMiA9IDA7IF9fcHl0cmFfaV8yIDwgd2lkdGg7IF9fcHl0cmFfaV8yICs9IDEpIHsKICAgICAgICAgICAgeCA9IF9fcHl0cmFfaV8yOwogICAgICAgICAgICBsZXQgenggPSAoKCgtKDEuOCkpKSArICgoKDMuNikgKiAoKCh4KSAvICgoKHdpZHRoKSAtICgxKSkpKSkpKSk7CiAgICAgICAgICAgIGxldCB6eSA9IHp5MDsKICAgICAgICAgICAgbGV0IGkgPSAwOwogICAgICAgICAgICB3aGlsZSAocHlCb29sKCgoaSkgPCAobWF4X2l0ZXIpKSkpIHsKICAgICAgICAgICAgICAgIGxldCB6eDIgPSAoKHp4KSAqICh6eCkpOwogICAgICAgICAgICAgICAgbGV0IHp5MiA9ICgoenkpICogKHp5KSk7CiAgICAgICAgICAgICAgICBpZiAocHlCb29sKCgoKCh6eDIpICsgKHp5MikpKSA+ICg0LjApKSkpIHsKICAgICAgICAgICAgICAgICAgICBicmVhazsKICAgICAgICAgICAgICAgIH0KICAgICAgICAgICAgICAgIHp5ID0gKCgoKCgoMi4wKSAqICh6eCkpKSAqICh6eSkpKSArIChjeSkpOwogICAgICAgICAgICAgICAgenggPSAoKCgoengyKSAtICh6eTIpKSkgKyAoY3gpKTsKICAgICAgICAgICAgICAgIGkgPSBpICsgMTsKICAgICAgICAgICAgfQogICAgICAgICAgICBsZXQgciA9IDA7CiAgICAgICAgICAgIGxldCBnID0gMDsKICAgICAgICAgICAgbGV0IGIgPSAwOwogICAgICAgICAgICBpZiAocHlCb29sKCgoaSkgPj0gKG1heF9pdGVyKSkpKSB7CiAgICAgICAgICAgICAgICByID0gMDsKICAgICAgICAgICAgICAgIGcgPSAwOwogICAgICAgICAgICAgICAgYiA9IDA7CiAgICAgICAgICAgIH0gZWxzZSB7CiAgICAgICAgICAgICAgICBsZXQgdCA9ICgoaSkgLyAobWF4X2l0ZXIpKTsKICAgICAgICAgICAgICAgIHIgPSBNYXRoLnRydW5jKE51bWJlcigoKDI1NS4wKSAqICgoKDAuMikgKyAoKCgwLjgpICogKHQpKSkpKSkpKTsKICAgICAgICAgICAgICAgIGcgPSBNYXRoLnRydW5jKE51bWJlcigoKDI1NS4wKSAqICgoKDAuMSkgKyAoKCgwLjkpICogKCgodCkgKiAodCkpKSkpKSkpKSk7CiAgICAgICAgICAgICAgICBiID0gTWF0aC50cnVuYyhOdW1iZXIoKCgyNTUuMCkgKiAoKCgxLjApIC0gKHQpKSkpKSk7CiAgICAgICAgICAgIH0KICAgICAgICAgICAgcGl4ZWxzLnB1c2gocik7CiAgICAgICAgICAgIHBpeGVscy5wdXNoKGcpOwogICAgICAgICAgICBwaXhlbHMucHVzaChiKTsKICAgICAgICB9CiAgICB9CiAgICByZXR1cm4gcGl4ZWxzOwp9CmZ1bmN0aW9uIHJ1bl9qdWxpYSgpIHsKICAgIGxldCB3aWR0aCA9IDM4NDA7CiAgICBsZXQgaGVpZ2h0ID0gMjE2MDsKICAgIGxldCBtYXhfaXRlciA9IDIwMDAwOwogICAgbGV0IG91dF9wYXRoID0gJ3NhbXBsZS9vdXQvanVsaWFfMDMucG5nJzsKICAgIGxldCBzdGFydCA9IHBlcmZfY291bnRlcigpOwogICAgbGV0IHBpeGVscyA9IHJlbmRlcl9qdWxpYSh3aWR0aCwgaGVpZ2h0LCBtYXhfaXRlciwgKC0oMC44KSksIDAuMTU2KTsKICAgIHBuZ19oZWxwZXIud3JpdGVfcmdiX3BuZyhvdXRfcGF0aCwgd2lkdGgsIGhlaWdodCwgcGl4ZWxzKTsKICAgIGxldCBlbGFwc2VkID0gKChwZXJmX2NvdW50ZXIoKSkgLSAoc3RhcnQpKTsKICAgIHB5UHJpbnQoJ291dHB1dDonLCBvdXRfcGF0aCk7CiAgICBweVByaW50KCdzaXplOicsIHdpZHRoLCAneCcsIGhlaWdodCk7CiAgICBweVByaW50KCdtYXhfaXRlcjonLCBtYXhfaXRlcik7CiAgICBweVByaW50KCdlbGFwc2VkX3NlYzonLCBlbGFwc2VkKTsKfQpydW5fanVsaWEoKTsK"
let pytraArgs = Array(CommandLine.arguments.dropFirst())
let pytraCode = pytraRunEmbeddedNode(pytraEmbeddedJsBase64, pytraArgs)
Foundation.exit(pytraCode)
