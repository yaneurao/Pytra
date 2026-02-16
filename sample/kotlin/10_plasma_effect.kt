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
        // Python 製補助モジュールを import できるよう、src を PYTHONPATH に追加する。
        val env = mutableMapOf<String, String>()
        env.putAll(System.getenv())
        val currentPyPath = env["PYTHONPATH"]
        env["PYTHONPATH"] = if (currentPyPath.isNullOrEmpty()) "src" else "src:$currentPyPath"
        val process: Process = try {
            ProcessBuilder(command)
                .apply { environment().putAll(env) }
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

class pytra_10_plasma_effect {
    companion object {
        // 埋め込み Python ソース（Base64）。
        private const val PYTRA_EMBEDDED_SOURCE_BASE64: String = "IyAxMDog44OX44Op44K644Oe44Ko44OV44Kn44Kv44OI44KSR0lG5Ye65Yqb44GZ44KL44K144Oz44OX44Or44CCCgpmcm9tIF9fZnV0dXJlX18gaW1wb3J0IGFubm90YXRpb25zCgppbXBvcnQgbWF0aApmcm9tIHRpbWUgaW1wb3J0IHBlcmZfY291bnRlcgoKZnJvbSBweV9tb2R1bGUuZ2lmX2hlbHBlciBpbXBvcnQgZ3JheXNjYWxlX3BhbGV0dGUsIHNhdmVfZ2lmCgoKZGVmIHJ1bl8xMF9wbGFzbWFfZWZmZWN0KCkgLT4gTm9uZToKICAgIHcgPSAzMjAKICAgIGggPSAyNDAKICAgIGZyYW1lc19uID0gMjE2CiAgICBvdXRfcGF0aCA9ICJzYW1wbGUvb3V0LzEwX3BsYXNtYV9lZmZlY3QuZ2lmIgoKICAgIHN0YXJ0ID0gcGVyZl9jb3VudGVyKCkKICAgIGZyYW1lczogbGlzdFtieXRlc10gPSBbXQoKICAgIGZvciB0IGluIHJhbmdlKGZyYW1lc19uKToKICAgICAgICBmcmFtZSA9IGJ5dGVhcnJheSh3ICogaCkKICAgICAgICBpID0gMAogICAgICAgIGZvciB5IGluIHJhbmdlKGgpOgogICAgICAgICAgICBmb3IgeCBpbiByYW5nZSh3KToKICAgICAgICAgICAgICAgIGR4ID0geCAtIDE2MAogICAgICAgICAgICAgICAgZHkgPSB5IC0gMTIwCiAgICAgICAgICAgICAgICB2ID0gKAogICAgICAgICAgICAgICAgICAgIG1hdGguc2luKCh4ICsgdCAqIDIuMCkgKiAwLjA0NSkKICAgICAgICAgICAgICAgICAgICArIG1hdGguc2luKCh5IC0gdCAqIDEuMikgKiAwLjA1KQogICAgICAgICAgICAgICAgICAgICsgbWF0aC5zaW4oKHggKyB5ICsgdCAqIDEuNykgKiAwLjAzKQogICAgICAgICAgICAgICAgICAgICsgbWF0aC5zaW4obWF0aC5zcXJ0KGR4ICogZHggKyBkeSAqIGR5KSAqIDAuMDcgLSB0ICogMC4xOCkKICAgICAgICAgICAgICAgICkKICAgICAgICAgICAgICAgIGMgPSBpbnQoKHYgKyA0LjApICogKDI1NS4wIC8gOC4wKSkKICAgICAgICAgICAgICAgIGlmIGMgPCAwOgogICAgICAgICAgICAgICAgICAgIGMgPSAwCiAgICAgICAgICAgICAgICBpZiBjID4gMjU1OgogICAgICAgICAgICAgICAgICAgIGMgPSAyNTUKICAgICAgICAgICAgICAgIGZyYW1lW2ldID0gYwogICAgICAgICAgICAgICAgaSArPSAxCiAgICAgICAgZnJhbWVzLmFwcGVuZChieXRlcyhmcmFtZSkpCgogICAgc2F2ZV9naWYob3V0X3BhdGgsIHcsIGgsIGZyYW1lcywgZ3JheXNjYWxlX3BhbGV0dGUoKSwgZGVsYXlfY3M9MywgbG9vcD0wKQogICAgZWxhcHNlZCA9IHBlcmZfY291bnRlcigpIC0gc3RhcnQKICAgIHByaW50KCJvdXRwdXQ6Iiwgb3V0X3BhdGgpCiAgICBwcmludCgiZnJhbWVzOiIsIGZyYW1lc19uKQogICAgcHJpbnQoImVsYXBzZWRfc2VjOiIsIGVsYXBzZWQpCgoKaWYgX19uYW1lX18gPT0gIl9fbWFpbl9fIjoKICAgIHJ1bl8xMF9wbGFzbWFfZWZmZWN0KCkK"

        // main は埋め込み Python を実行するエントリポイント。
        @JvmStatic
        fun main(args: Array<String>) {
            val code: Int = PyRuntime.runEmbeddedPython(PYTRA_EMBEDDED_SOURCE_BASE64, args)
            kotlin.system.exitProcess(code)
        }
    }
}
