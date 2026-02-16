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
let pytraEmbeddedSourceBase64 = "IyDjgZPjga7jg5XjgqHjgqTjg6vjga8gYHRlc3QvcHkvY2FzZTEzX2NsYXNzLnB5YCDjga7jg4bjgrnjg4gv5a6f6KOF44Kz44O844OJ44Gn44GZ44CCCiMg5b255Ymy44GM5YiG44GL44KK44KE44GZ44GE44KI44GG44Gr44CB6Kqt44G/5omL5ZCR44GR44Gu6Kqs5piO44Kz44Oh44Oz44OI44KS5LuY5LiO44GX44Gm44GE44G+44GZ44CCCiMg5aSJ5pu05pmC44Gv44CB5pei5a2Y5LuV5qeY44Go44Gu5pW05ZCI5oCn44Go44OG44K544OI57WQ5p6c44KS5b+F44Ga56K66KqN44GX44Gm44GP44Gg44GV44GE44CCCgpjbGFzcyBNdWx0aXBsaWVyOgogICAgZGVmIG11bChzZWxmLCB4OiBpbnQsIHk6IGludCkgLT4gaW50OgogICAgICAgIHJldHVybiB4ICogeQoKCmlmIF9fbmFtZV9fID09ICJfX21haW5fXyI6CiAgICBtOiBNdWx0aXBsaWVyID0gTXVsdGlwbGllcigpCiAgICBwcmludChtLm11bCg2LCA3KSkK"
let pytraArgs = Array(CommandLine.arguments.dropFirst())
let pytraCode = pytraRunEmbeddedPython(pytraEmbeddedSourceBase64, pytraArgs)
Foundation.exit(pytraCode)
