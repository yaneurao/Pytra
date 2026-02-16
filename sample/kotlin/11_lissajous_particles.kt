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

class pytra_11_lissajous_particles {
    companion object {
        // 埋め込み Python ソース（Base64）。
        private const val PYTRA_EMBEDDED_SOURCE_BASE64: String = "IyAxMTog44Oq44K144O844K444Ol6YGL5YuV44GZ44KL57KS5a2Q44KSR0lG5Ye65Yqb44GZ44KL44K144Oz44OX44Or44CCCgpmcm9tIF9fZnV0dXJlX18gaW1wb3J0IGFubm90YXRpb25zCgppbXBvcnQgbWF0aApmcm9tIHRpbWUgaW1wb3J0IHBlcmZfY291bnRlcgoKZnJvbSBweV9tb2R1bGUuZ2lmX2hlbHBlciBpbXBvcnQgc2F2ZV9naWYKCgpkZWYgY29sb3JfcGFsZXR0ZSgpIC0+IGJ5dGVzOgogICAgcCA9IGJ5dGVhcnJheSgpCiAgICBmb3IgaSBpbiByYW5nZSgyNTYpOgogICAgICAgIHIgPSBpCiAgICAgICAgZyA9IChpICogMykgJSAyNTYKICAgICAgICBiID0gMjU1IC0gaQogICAgICAgIHAuYXBwZW5kKHIpCiAgICAgICAgcC5hcHBlbmQoZykKICAgICAgICBwLmFwcGVuZChiKQogICAgcmV0dXJuIGJ5dGVzKHApCgoKZGVmIHJ1bl8xMV9saXNzYWpvdXNfcGFydGljbGVzKCkgLT4gTm9uZToKICAgIHcgPSAzMjAKICAgIGggPSAyNDAKICAgIGZyYW1lc19uID0gMzYwCiAgICBwYXJ0aWNsZXMgPSA0OAogICAgb3V0X3BhdGggPSAic2FtcGxlL291dC8xMV9saXNzYWpvdXNfcGFydGljbGVzLmdpZiIKCiAgICBzdGFydCA9IHBlcmZfY291bnRlcigpCiAgICBmcmFtZXM6IGxpc3RbYnl0ZXNdID0gW10KCiAgICBmb3IgdCBpbiByYW5nZShmcmFtZXNfbik6CiAgICAgICAgZnJhbWUgPSBieXRlYXJyYXkodyAqIGgpCgogICAgICAgIGZvciBwIGluIHJhbmdlKHBhcnRpY2xlcyk6CiAgICAgICAgICAgIHBoYXNlID0gcCAqIDAuMjYxNzk5CiAgICAgICAgICAgIHggPSBpbnQoKHcgKiAwLjUpICsgKHcgKiAwLjM4KSAqIG1hdGguc2luKDAuMTEgKiB0ICsgcGhhc2UgKiAyLjApKQogICAgICAgICAgICB5ID0gaW50KChoICogMC41KSArIChoICogMC4zOCkgKiBtYXRoLnNpbigwLjE3ICogdCArIHBoYXNlICogMy4wKSkKICAgICAgICAgICAgY29sb3IgPSAzMCArIChwICogOSkgJSAyMjAKCiAgICAgICAgICAgIGZvciBkeSBpbiByYW5nZSgtMiwgMyk6CiAgICAgICAgICAgICAgICBmb3IgZHggaW4gcmFuZ2UoLTIsIDMpOgogICAgICAgICAgICAgICAgICAgIHh4ID0geCArIGR4CiAgICAgICAgICAgICAgICAgICAgeXkgPSB5ICsgZHkKICAgICAgICAgICAgICAgICAgICBpZiB4eCA+PSAwIGFuZCB4eCA8IHcgYW5kIHl5ID49IDAgYW5kIHl5IDwgaDoKICAgICAgICAgICAgICAgICAgICAgICAgZDIgPSBkeCAqIGR4ICsgZHkgKiBkeQogICAgICAgICAgICAgICAgICAgICAgICBpZiBkMiA8PSA0OgogICAgICAgICAgICAgICAgICAgICAgICAgICAgaWR4ID0geXkgKiB3ICsgeHgKICAgICAgICAgICAgICAgICAgICAgICAgICAgIHYgPSBjb2xvciAtIGQyICogMjAKICAgICAgICAgICAgICAgICAgICAgICAgICAgIGlmIHYgPCAwOgogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIHYgPSAwCiAgICAgICAgICAgICAgICAgICAgICAgICAgICBpZiB2ID4gZnJhbWVbaWR4XToKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICBmcmFtZVtpZHhdID0gdgoKICAgICAgICBmcmFtZXMuYXBwZW5kKGJ5dGVzKGZyYW1lKSkKCiAgICBzYXZlX2dpZihvdXRfcGF0aCwgdywgaCwgZnJhbWVzLCBjb2xvcl9wYWxldHRlKCksIGRlbGF5X2NzPTMsIGxvb3A9MCkKICAgIGVsYXBzZWQgPSBwZXJmX2NvdW50ZXIoKSAtIHN0YXJ0CiAgICBwcmludCgib3V0cHV0OiIsIG91dF9wYXRoKQogICAgcHJpbnQoImZyYW1lczoiLCBmcmFtZXNfbikKICAgIHByaW50KCJlbGFwc2VkX3NlYzoiLCBlbGFwc2VkKQoKCmlmIF9fbmFtZV9fID09ICJfX21haW5fXyI6CiAgICBydW5fMTFfbGlzc2Fqb3VzX3BhcnRpY2xlcygpCg=="

        // main は埋め込み Python を実行するエントリポイント。
        @JvmStatic
        fun main(args: Array<String>) {
            val code: Int = PyRuntime.runEmbeddedPython(PYTRA_EMBEDDED_SOURCE_BASE64, args)
            kotlin.system.exitProcess(code)
        }
    }
}
