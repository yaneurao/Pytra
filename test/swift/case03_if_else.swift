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
    process.environment = ProcessInfo.processInfo.environment
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
let pytraEmbeddedSourceBase64 = "IyDjgZPjga7jg5XjgqHjgqTjg6vjga8gYHRlc3QvcHkvY2FzZTAzX2lmX2Vsc2UucHlgIOOBruODhuOCueODiC/lrp/oo4XjgrPjg7zjg4njgafjgZnjgIIKIyDlvbnlibLjgYzliIbjgYvjgorjgoTjgZnjgYTjgojjgYbjgavjgIHoqq3jgb/miYvlkJHjgZHjga7oqqzmmI7jgrPjg6Hjg7Pjg4jjgpLku5jkuI7jgZfjgabjgYTjgb7jgZnjgIIKIyDlpInmm7TmmYLjga/jgIHml6LlrZjku5Xmp5jjgajjga7mlbTlkIjmgKfjgajjg4bjgrnjg4jntZDmnpzjgpLlv4XjgZrnorroqo3jgZfjgabjgY/jgaDjgZXjgYTjgIIKCmRlZiBhYnNfbGlrZShuOiBpbnQpIC0+IGludDoKICAgIGlmIG4gPCAwOgogICAgICAgIHJldHVybiAtbgogICAgZWxzZToKICAgICAgICByZXR1cm4gbgoKCmlmIF9fbmFtZV9fID09ICJfX21haW5fXyI6CiAgICBwcmludChhYnNfbGlrZSgtMTIpKQo="
let pytraArgs = Array(CommandLine.arguments.dropFirst())
let pytraCode = pytraRunEmbeddedPython(pytraEmbeddedSourceBase64, pytraArgs)
Foundation.exit(pytraCode)
