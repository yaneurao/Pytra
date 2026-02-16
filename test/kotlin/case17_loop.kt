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

class case17_loop {
    companion object {
        // 埋め込み Python ソース（Base64）。
        private const val PYTRA_EMBEDDED_SOURCE_BASE64: String = "IyDjgZPjga7jg5XjgqHjgqTjg6vjga8gYHRlc3QvcHkvY2FzZTE3X2xvb3AucHlgIOOBruODhuOCueODiC/lrp/oo4XjgrPjg7zjg4njgafjgZnjgIIKIyDlvbnlibLjgYzliIbjgYvjgorjgoTjgZnjgYTjgojjgYbjgavjgIHoqq3jgb/miYvlkJHjgZHjga7oqqzmmI7jgrPjg6Hjg7Pjg4jjgpLku5jkuI7jgZfjgabjgYTjgb7jgZnjgIIKIyDlpInmm7TmmYLjga/jgIHml6LlrZjku5Xmp5jjgajjga7mlbTlkIjmgKfjgajjg4bjgrnjg4jntZDmnpzjgpLlv4XjgZrnorroqo3jgZfjgabjgY/jgaDjgZXjgYTjgIIKCmRlZiBjYWxjXzE3KHZhbHVlczogbGlzdFtpbnRdKSAtPiBpbnQ6CiAgICB0b3RhbDogaW50ID0gMAogICAgZm9yIHYgaW4gdmFsdWVzOgogICAgICAgIGlmIHYgJSAyID09IDA6CiAgICAgICAgICAgIHRvdGFsICs9IHYKICAgICAgICBlbHNlOgogICAgICAgICAgICB0b3RhbCArPSAodiAqIDIpCiAgICByZXR1cm4gdG90YWwKCgppZiBfX25hbWVfXyA9PSAiX19tYWluX18iOgogICAgcHJpbnQoY2FsY18xNyhbMSwgMiwgMywgNF0pKQo="

        // main は埋め込み Python を実行するエントリポイント。
        @JvmStatic
        fun main(args: Array<String>) {
            val code: Int = PyRuntime.runEmbeddedPython(PYTRA_EMBEDDED_SOURCE_BASE64, args)
            kotlin.system.exitProcess(code)
        }
    }
}
