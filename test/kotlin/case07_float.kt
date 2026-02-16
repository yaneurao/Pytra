// このファイルは自動生成です（Python -> Kotlin embedded mode）。

// Kotlin 埋め込み実行向け Python ランタイム補助。

import java.io.File
import java.nio.file.Files
import java.nio.file.Path
import java.util.Base64
import java.util.UUID

/**
 * Base64 で埋め込まれた Python ソースコードを一時ファイルに展開し、python3 で実行する。
 */
object PyRuntime {
    /**
     * @param sourceBase64 Python ソースコードの Base64 文字列。
     * @param args Python スクリプトへ渡す引数配列。
     * @return python プロセスの終了コード。失敗時は 1 を返す。
     */
    @JvmStatic
    fun runEmbeddedPython(sourceBase64: String, args: Array<String>): Int {
        val sourceBytes: ByteArray = try {
            Base64.getDecoder().decode(sourceBase64)
        } catch (ex: IllegalArgumentException) {
            System.err.println("error: failed to decode embedded Python source")
            return 1
        }

        val tempFile: Path = try {
            val name = "pytra_embedded_${UUID.randomUUID()}.py"
            val p = File(System.getProperty("java.io.tmpdir"), name).toPath()
            Files.write(p, sourceBytes)
            p
        } catch (ex: Exception) {
            System.err.println("error: failed to write temporary Python file: ${ex.message}")
            return 1
        }

        val command = mutableListOf("python3", tempFile.toString())
        command.addAll(args)
        val process: Process = try {
            ProcessBuilder(command)
                .inheritIO()
                .start()
        } catch (ex: Exception) {
            System.err.println("error: failed to launch python3: ${ex.message}")
            try {
                Files.deleteIfExists(tempFile)
            } catch (_: Exception) {
            }
            return 1
        }

        val code = process.waitFor()
        try {
            Files.deleteIfExists(tempFile)
        } catch (_: Exception) {
        }
        return code
    }
}

class case07_float {
    companion object {
        // 埋め込み Python ソース（Base64）。
        private const val PYTRA_EMBEDDED_SOURCE_BASE64: String = "IyDjgZPjga7jg5XjgqHjgqTjg6vjga8gYHRlc3QvcHkvY2FzZTA3X2Zsb2F0LnB5YCDjga7jg4bjgrnjg4gv5a6f6KOF44Kz44O844OJ44Gn44GZ44CCCiMg5b255Ymy44GM5YiG44GL44KK44KE44GZ44GE44KI44GG44Gr44CB6Kqt44G/5omL5ZCR44GR44Gu6Kqs5piO44Kz44Oh44Oz44OI44KS5LuY5LiO44GX44Gm44GE44G+44GZ44CCCiMg5aSJ5pu05pmC44Gv44CB5pei5a2Y5LuV5qeY44Go44Gu5pW05ZCI5oCn44Go44OG44K544OI57WQ5p6c44KS5b+F44Ga56K66KqN44GX44Gm44GP44Gg44GV44GE44CCCgpkZWYgaGFsZih4OiBmbG9hdCkgLT4gZmxvYXQ6CiAgICByZXR1cm4geCAvIDIuMAoKCmlmIF9fbmFtZV9fID09ICJfX21haW5fXyI6CiAgICBwcmludChoYWxmKDUuMCkpCg=="

        // main は埋め込み Python を実行するエントリポイント。
        @JvmStatic
        fun main(args: Array<String>) {
            val code: Int = PyRuntime.runEmbeddedPython(PYTRA_EMBEDDED_SOURCE_BASE64, args)
            kotlin.system.exitProcess(code)
        }
    }
}
