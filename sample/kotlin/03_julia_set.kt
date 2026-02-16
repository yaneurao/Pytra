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

class pytra_03_julia_set {
    companion object {
        // 埋め込み Python ソース（Base64）。
        private const val PYTRA_EMBEDDED_SOURCE_BASE64: String = "IyAwMzog44K444Ol44Oq44Ki6ZuG5ZCI44KSIFBORyDlvaLlvI/jgaflh7rlipvjgZnjgovjgrXjg7Pjg5fjg6vjgafjgZnjgIIKIyDjg4jjg6njg7Pjgrnjg5HjgqTjg6vkupLmj5vjgpLmhI/orZjjgZfjgIHljZjntJTjgarjg6vjg7zjg5fkuK3lv4Pjgaflrp/oo4XjgZfjgabjgYTjgb7jgZnjgIIKCmZyb20gdGltZSBpbXBvcnQgcGVyZl9jb3VudGVyCmZyb20gcHlfbW9kdWxlIGltcG9ydCBwbmdfaGVscGVyCgoKZGVmIHJlbmRlcl9qdWxpYSh3aWR0aDogaW50LCBoZWlnaHQ6IGludCwgbWF4X2l0ZXI6IGludCwgY3g6IGZsb2F0LCBjeTogZmxvYXQpIC0+IGJ5dGVhcnJheToKICAgIHBpeGVsczogYnl0ZWFycmF5ID0gYnl0ZWFycmF5KCkKCiAgICBmb3IgeSBpbiByYW5nZShoZWlnaHQpOgogICAgICAgIHp5MDogZmxvYXQgPSAtMS4yICsgMi40ICogKHkgLyAoaGVpZ2h0IC0gMSkpCgogICAgICAgIGZvciB4IGluIHJhbmdlKHdpZHRoKToKICAgICAgICAgICAgeng6IGZsb2F0ID0gLTEuOCArIDMuNiAqICh4IC8gKHdpZHRoIC0gMSkpCiAgICAgICAgICAgIHp5OiBmbG9hdCA9IHp5MAoKICAgICAgICAgICAgaTogaW50ID0gMAogICAgICAgICAgICB3aGlsZSBpIDwgbWF4X2l0ZXI6CiAgICAgICAgICAgICAgICB6eDI6IGZsb2F0ID0genggKiB6eAogICAgICAgICAgICAgICAgenkyOiBmbG9hdCA9IHp5ICogenkKICAgICAgICAgICAgICAgIGlmIHp4MiArIHp5MiA+IDQuMDoKICAgICAgICAgICAgICAgICAgICBicmVhawogICAgICAgICAgICAgICAgenkgPSAyLjAgKiB6eCAqIHp5ICsgY3kKICAgICAgICAgICAgICAgIHp4ID0gengyIC0genkyICsgY3gKICAgICAgICAgICAgICAgIGkgKz0gMQoKICAgICAgICAgICAgcjogaW50ID0gMAogICAgICAgICAgICBnOiBpbnQgPSAwCiAgICAgICAgICAgIGI6IGludCA9IDAKICAgICAgICAgICAgaWYgaSA+PSBtYXhfaXRlcjoKICAgICAgICAgICAgICAgIHIgPSAwCiAgICAgICAgICAgICAgICBnID0gMAogICAgICAgICAgICAgICAgYiA9IDAKICAgICAgICAgICAgZWxzZToKICAgICAgICAgICAgICAgIHQ6IGZsb2F0ID0gaSAvIG1heF9pdGVyCiAgICAgICAgICAgICAgICByID0gaW50KDI1NS4wICogKDAuMiArIDAuOCAqIHQpKQogICAgICAgICAgICAgICAgZyA9IGludCgyNTUuMCAqICgwLjEgKyAwLjkgKiAodCAqIHQpKSkKICAgICAgICAgICAgICAgIGIgPSBpbnQoMjU1LjAgKiAoMS4wIC0gdCkpCgogICAgICAgICAgICBwaXhlbHMuYXBwZW5kKHIpCiAgICAgICAgICAgIHBpeGVscy5hcHBlbmQoZykKICAgICAgICAgICAgcGl4ZWxzLmFwcGVuZChiKQoKICAgIHJldHVybiBwaXhlbHMKCgpkZWYgcnVuX2p1bGlhKCkgLT4gTm9uZToKICAgIHdpZHRoOiBpbnQgPSAzODQwCiAgICBoZWlnaHQ6IGludCA9IDIxNjAKICAgIG1heF9pdGVyOiBpbnQgPSAyMDAwMAogICAgb3V0X3BhdGg6IHN0ciA9ICJzYW1wbGUvb3V0L2p1bGlhXzAzLnBuZyIKCiAgICBzdGFydDogZmxvYXQgPSBwZXJmX2NvdW50ZXIoKQogICAgcGl4ZWxzOiBieXRlYXJyYXkgPSByZW5kZXJfanVsaWEod2lkdGgsIGhlaWdodCwgbWF4X2l0ZXIsIC0wLjgsIDAuMTU2KQogICAgcG5nX2hlbHBlci53cml0ZV9yZ2JfcG5nKG91dF9wYXRoLCB3aWR0aCwgaGVpZ2h0LCBwaXhlbHMpCiAgICBlbGFwc2VkOiBmbG9hdCA9IHBlcmZfY291bnRlcigpIC0gc3RhcnQKCiAgICBwcmludCgib3V0cHV0OiIsIG91dF9wYXRoKQogICAgcHJpbnQoInNpemU6Iiwgd2lkdGgsICJ4IiwgaGVpZ2h0KQogICAgcHJpbnQoIm1heF9pdGVyOiIsIG1heF9pdGVyKQogICAgcHJpbnQoImVsYXBzZWRfc2VjOiIsIGVsYXBzZWQpCgoKaWYgX19uYW1lX18gPT0gIl9fbWFpbl9fIjoKICAgIHJ1bl9qdWxpYSgpCg=="

        // main は埋め込み Python を実行するエントリポイント。
        @JvmStatic
        fun main(args: Array<String>) {
            val code: Int = PyRuntime.runEmbeddedPython(PYTRA_EMBEDDED_SOURCE_BASE64, args)
            kotlin.system.exitProcess(code)
        }
    }
}
