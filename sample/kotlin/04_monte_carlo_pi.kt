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

class pytra_04_monte_carlo_pi {
    companion object {
        // 埋め込み Python ソース（Base64）。
        private const val PYTRA_EMBEDDED_SOURCE_BASE64: String = "IyAxMDog44Oi44Oz44OG44Kr44Or44Ot5rOV44Gn5YaG5ZGo546H44KS5o6o5a6a44GZ44KL44K144Oz44OX44Or44Gn44GZ44CCCiMgaW1wb3J0IHJhbmRvbSDjgpLkvb/jgo/jgZrjgIFMQ0cg44KS6Ieq5YmN5a6f6KOF44GX44Gm44OI44Op44Oz44K544OR44Kk44Or5LqS5o+b5oCn44KS6auY44KB44Gm44GE44G+44GZ44CCCgpmcm9tIHRpbWUgaW1wb3J0IHBlcmZfY291bnRlcgoKCmRlZiBsY2dfbmV4dChzdGF0ZTogaW50KSAtPiBpbnQ6CiAgICAjIDMyYml0IExDRwogICAgcmV0dXJuICgxNjY0NTI1ICogc3RhdGUgKyAxMDEzOTA0MjIzKSAlIDQyOTQ5NjcyOTYKCgpkZWYgcnVuX3BpX3RyaWFsKHRvdGFsX3NhbXBsZXM6IGludCwgc2VlZDogaW50KSAtPiBmbG9hdDoKICAgIGluc2lkZTogaW50ID0gMAogICAgc3RhdGU6IGludCA9IHNlZWQKCiAgICBmb3IgXyBpbiByYW5nZSh0b3RhbF9zYW1wbGVzKToKICAgICAgICBzdGF0ZSA9IGxjZ19uZXh0KHN0YXRlKQogICAgICAgIHg6IGZsb2F0ID0gc3RhdGUgLyA0Mjk0OTY3Mjk2LjAKCiAgICAgICAgc3RhdGUgPSBsY2dfbmV4dChzdGF0ZSkKICAgICAgICB5OiBmbG9hdCA9IHN0YXRlIC8gNDI5NDk2NzI5Ni4wCgogICAgICAgIGR4OiBmbG9hdCA9IHggLSAwLjUKICAgICAgICBkeTogZmxvYXQgPSB5IC0gMC41CiAgICAgICAgaWYgZHggKiBkeCArIGR5ICogZHkgPD0gMC4yNToKICAgICAgICAgICAgaW5zaWRlICs9IDEKCiAgICByZXR1cm4gNC4wICogaW5zaWRlIC8gdG90YWxfc2FtcGxlcwoKCmRlZiBydW5fbW9udGVfY2FybG9fcGkoKSAtPiBOb25lOgogICAgc2FtcGxlczogaW50ID0gNTQwMDAwMDAKICAgIHNlZWQ6IGludCA9IDEyMzQ1Njc4OQoKICAgIHN0YXJ0OiBmbG9hdCA9IHBlcmZfY291bnRlcigpCiAgICBwaV9lc3Q6IGZsb2F0ID0gcnVuX3BpX3RyaWFsKHNhbXBsZXMsIHNlZWQpCiAgICBlbGFwc2VkOiBmbG9hdCA9IHBlcmZfY291bnRlcigpIC0gc3RhcnQKCiAgICBwcmludCgic2FtcGxlczoiLCBzYW1wbGVzKQogICAgcHJpbnQoInBpX2VzdGltYXRlOiIsIHBpX2VzdCkKICAgIHByaW50KCJlbGFwc2VkX3NlYzoiLCBlbGFwc2VkKQoKCmlmIF9fbmFtZV9fID09ICJfX21haW5fXyI6CiAgICBydW5fbW9udGVfY2FybG9fcGkoKQo="

        // main は埋め込み Python を実行するエントリポイント。
        @JvmStatic
        fun main(args: Array<String>) {
            val code: Int = PyRuntime.runEmbeddedPython(PYTRA_EMBEDDED_SOURCE_BASE64, args)
            kotlin.system.exitProcess(code)
        }
    }
}
