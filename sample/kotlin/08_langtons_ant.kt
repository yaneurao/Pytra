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

class pytra_08_langtons_ant {
    companion object {
        // 埋め込み Python ソース（Base64）。
        private const val PYTRA_EMBEDDED_SOURCE_BASE64: String = "IyAwODog44Op44Oz44Kw44OI44Oz44Gu44Ki44Oq44Gu6LuM6Leh44KSR0lG5Ye65Yqb44GZ44KL44K144Oz44OX44Or44CCCgpmcm9tIF9fZnV0dXJlX18gaW1wb3J0IGFubm90YXRpb25zCgpmcm9tIHRpbWUgaW1wb3J0IHBlcmZfY291bnRlcgoKZnJvbSBweV9tb2R1bGUuZ2lmX2hlbHBlciBpbXBvcnQgZ3JheXNjYWxlX3BhbGV0dGUsIHNhdmVfZ2lmCgoKZGVmIGNhcHR1cmUoZ3JpZDogbGlzdFtsaXN0W2ludF1dLCB3OiBpbnQsIGg6IGludCkgLT4gYnl0ZXM6CiAgICBmcmFtZSA9IGJ5dGVhcnJheSh3ICogaCkKICAgIGkgPSAwCiAgICBmb3IgeSBpbiByYW5nZShoKToKICAgICAgICBmb3IgeCBpbiByYW5nZSh3KToKICAgICAgICAgICAgZnJhbWVbaV0gPSAyNTUgaWYgZ3JpZFt5XVt4XSBlbHNlIDAKICAgICAgICAgICAgaSArPSAxCiAgICByZXR1cm4gYnl0ZXMoZnJhbWUpCgoKZGVmIHJ1bl8wOF9sYW5ndG9uc19hbnQoKSAtPiBOb25lOgogICAgdyA9IDQyMAogICAgaCA9IDQyMAogICAgb3V0X3BhdGggPSAic2FtcGxlL291dC8wOF9sYW5ndG9uc19hbnQuZ2lmIgoKICAgIHN0YXJ0ID0gcGVyZl9jb3VudGVyKCkKCiAgICBncmlkOiBsaXN0W2xpc3RbaW50XV0gPSBbXQogICAgZm9yIGd5IGluIHJhbmdlKGgpOgogICAgICAgIHJvdzogbGlzdFtpbnRdID0gW10KICAgICAgICBmb3IgZ3ggaW4gcmFuZ2Uodyk6CiAgICAgICAgICAgIHJvdy5hcHBlbmQoMCkKICAgICAgICBncmlkLmFwcGVuZChyb3cpCiAgICB4ID0gdyAvLyAyCiAgICB5ID0gaCAvLyAyCiAgICBkID0gMAoKICAgIHN0ZXBzX3RvdGFsID0gNjAwMDAwCiAgICBjYXB0dXJlX2V2ZXJ5ID0gMzAwMAogICAgZnJhbWVzOiBsaXN0W2J5dGVzXSA9IFtdCgogICAgZm9yIGkgaW4gcmFuZ2Uoc3RlcHNfdG90YWwpOgogICAgICAgIGlmIGdyaWRbeV1beF0gPT0gMDoKICAgICAgICAgICAgZCA9IChkICsgMSkgJSA0CiAgICAgICAgICAgIGdyaWRbeV1beF0gPSAxCiAgICAgICAgZWxzZToKICAgICAgICAgICAgZCA9IChkICsgMykgJSA0CiAgICAgICAgICAgIGdyaWRbeV1beF0gPSAwCgogICAgICAgIGlmIGQgPT0gMDoKICAgICAgICAgICAgeSA9ICh5IC0gMSArIGgpICUgaAogICAgICAgIGVsaWYgZCA9PSAxOgogICAgICAgICAgICB4ID0gKHggKyAxKSAlIHcKICAgICAgICBlbGlmIGQgPT0gMjoKICAgICAgICAgICAgeSA9ICh5ICsgMSkgJSBoCiAgICAgICAgZWxzZToKICAgICAgICAgICAgeCA9ICh4IC0gMSArIHcpICUgdwoKICAgICAgICBpZiBpICUgY2FwdHVyZV9ldmVyeSA9PSAwOgogICAgICAgICAgICBmcmFtZXMuYXBwZW5kKGNhcHR1cmUoZ3JpZCwgdywgaCkpCgogICAgc2F2ZV9naWYob3V0X3BhdGgsIHcsIGgsIGZyYW1lcywgZ3JheXNjYWxlX3BhbGV0dGUoKSwgZGVsYXlfY3M9NSwgbG9vcD0wKQogICAgZWxhcHNlZCA9IHBlcmZfY291bnRlcigpIC0gc3RhcnQKICAgIHByaW50KCJvdXRwdXQ6Iiwgb3V0X3BhdGgpCiAgICBwcmludCgiZnJhbWVzOiIsIGxlbihmcmFtZXMpKQogICAgcHJpbnQoImVsYXBzZWRfc2VjOiIsIGVsYXBzZWQpCgoKaWYgX19uYW1lX18gPT0gIl9fbWFpbl9fIjoKICAgIHJ1bl8wOF9sYW5ndG9uc19hbnQoKQo="

        // main は埋め込み Python を実行するエントリポイント。
        @JvmStatic
        fun main(args: Array<String>) {
            val code: Int = PyRuntime.runEmbeddedPython(PYTRA_EMBEDDED_SOURCE_BASE64, args)
            kotlin.system.exitProcess(code)
        }
    }
}
