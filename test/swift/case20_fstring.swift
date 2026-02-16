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
let pytraEmbeddedJsBase64 = "Ly8gZ2VuZXJhdGVkIGludGVybmFsIEphdmFTY3JpcHQKCmNvbnN0IF9fcHl0cmFfcm9vdCA9IHByb2Nlc3MuY3dkKCk7CmNvbnN0IHB5X3J1bnRpbWUgPSByZXF1aXJlKF9fcHl0cmFfcm9vdCArICcvc3JjL2pzX21vZHVsZS9weV9ydW50aW1lLmpzJyk7CmNvbnN0IHB5X21hdGggPSByZXF1aXJlKF9fcHl0cmFfcm9vdCArICcvc3JjL2pzX21vZHVsZS9tYXRoLmpzJyk7CmNvbnN0IHB5X3RpbWUgPSByZXF1aXJlKF9fcHl0cmFfcm9vdCArICcvc3JjL2pzX21vZHVsZS90aW1lLmpzJyk7CmNvbnN0IHsgcHlQcmludCwgcHlMZW4sIHB5Qm9vbCwgcHlSYW5nZSwgcHlGbG9vckRpdiwgcHlNb2QsIHB5SW4sIHB5U2xpY2UsIHB5T3JkLCBweUNociwgcHlCeXRlYXJyYXksIHB5Qnl0ZXMsIHB5SXNEaWdpdCwgcHlJc0FscGhhIH0gPSBweV9ydW50aW1lOwpjb25zdCB7IHBlcmZDb3VudGVyIH0gPSBweV90aW1lOwoKZnVuY3Rpb24gbWFrZV9tc2dfMjIobmFtZSwgY291bnQpIHsKICAgIHJldHVybiBgJHtuYW1lfToyMjoke2NvdW50fWA7Cn0KcHlQcmludChtYWtlX21zZ18yMigndXNlcicsIDcpKTsK"
let pytraArgs = Array(CommandLine.arguments.dropFirst())
let pytraCode = pytraRunEmbeddedNode(pytraEmbeddedJsBase64, pytraArgs)
Foundation.exit(pytraCode)
