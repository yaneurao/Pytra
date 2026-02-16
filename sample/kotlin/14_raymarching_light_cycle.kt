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

class pytra_14_raymarching_light_cycle {
    companion object {
        // 埋め込み Python ソース（Base64）。
        private const val PYTRA_EMBEDDED_SOURCE_BASE64: String = "IyAxNDog57Ch5piT44Os44Kk44Oe44O844OB6aKo44Gu5YWJ5rqQ56e75YuV44K344O844Oz44KSR0lG5Ye65Yqb44GZ44KL44K144Oz44OX44Or44CCCgpmcm9tIF9fZnV0dXJlX18gaW1wb3J0IGFubm90YXRpb25zCgppbXBvcnQgbWF0aApmcm9tIHRpbWUgaW1wb3J0IHBlcmZfY291bnRlcgoKZnJvbSBweV9tb2R1bGUuZ2lmX2hlbHBlciBpbXBvcnQgc2F2ZV9naWYKCgpkZWYgcGFsZXR0ZSgpIC0+IGJ5dGVzOgogICAgcCA9IGJ5dGVhcnJheSgpCiAgICBmb3IgaSBpbiByYW5nZSgyNTYpOgogICAgICAgIHIgPSBpbnQoMjAgKyBpICogMC45KQogICAgICAgIGlmIHIgPiAyNTU6CiAgICAgICAgICAgIHIgPSAyNTUKICAgICAgICBnID0gaW50KDEwICsgaSAqIDAuNykKICAgICAgICBpZiBnID4gMjU1OgogICAgICAgICAgICBnID0gMjU1CiAgICAgICAgYiA9IGludCgzMCArIGkpCiAgICAgICAgaWYgYiA+IDI1NToKICAgICAgICAgICAgYiA9IDI1NQogICAgICAgIHAuYXBwZW5kKHIpCiAgICAgICAgcC5hcHBlbmQoZykKICAgICAgICBwLmFwcGVuZChiKQogICAgcmV0dXJuIGJ5dGVzKHApCgoKZGVmIHNjZW5lKHg6IGZsb2F0LCB5OiBmbG9hdCwgbGlnaHRfeDogZmxvYXQsIGxpZ2h0X3k6IGZsb2F0KSAtPiBpbnQ6CiAgICB4MSA9IHggKyAwLjQ1CiAgICB5MSA9IHkgKyAwLjIKICAgIHgyID0geCAtIDAuMzUKICAgIHkyID0geSAtIDAuMTUKICAgIHIxID0gbWF0aC5zcXJ0KHgxICogeDEgKyB5MSAqIHkxKQogICAgcjIgPSBtYXRoLnNxcnQoeDIgKiB4MiArIHkyICogeTIpCiAgICBibG9iID0gbWF0aC5leHAoLTcuMCAqIHIxICogcjEpICsgbWF0aC5leHAoLTguMCAqIHIyICogcjIpCgogICAgbHggPSB4IC0gbGlnaHRfeAogICAgbHkgPSB5IC0gbGlnaHRfeQogICAgbCA9IG1hdGguc3FydChseCAqIGx4ICsgbHkgKiBseSkKICAgIGxpdCA9IDEuMCAvICgxLjAgKyAzLjUgKiBsICogbCkKCiAgICB2ID0gaW50KDI1NS4wICogYmxvYiAqIGxpdCAqIDUuMCkKICAgIGlmIHYgPCAwOgogICAgICAgIHJldHVybiAwCiAgICBpZiB2ID4gMjU1OgogICAgICAgIHJldHVybiAyNTUKICAgIHJldHVybiB2CgoKZGVmIHJ1bl8xNF9yYXltYXJjaGluZ19saWdodF9jeWNsZSgpIC0+IE5vbmU6CiAgICB3ID0gMzIwCiAgICBoID0gMjQwCiAgICBmcmFtZXNfbiA9IDg0CiAgICBvdXRfcGF0aCA9ICJzYW1wbGUvb3V0LzE0X3JheW1hcmNoaW5nX2xpZ2h0X2N5Y2xlLmdpZiIKCiAgICBzdGFydCA9IHBlcmZfY291bnRlcigpCiAgICBmcmFtZXM6IGxpc3RbYnl0ZXNdID0gW10KCiAgICBmb3IgdCBpbiByYW5nZShmcmFtZXNfbik6CiAgICAgICAgZnJhbWUgPSBieXRlYXJyYXkodyAqIGgpCiAgICAgICAgYSA9ICh0IC8gZnJhbWVzX24pICogbWF0aC5waSAqIDIuMAogICAgICAgIGxpZ2h0X3ggPSAwLjc1ICogbWF0aC5jb3MoYSkKICAgICAgICBsaWdodF95ID0gMC41NSAqIG1hdGguc2luKGEgKiAxLjIpCgogICAgICAgIGkgPSAwCiAgICAgICAgZm9yIHkgaW4gcmFuZ2UoaCk6CiAgICAgICAgICAgIHB5ID0gKHkgLyAoaCAtIDEpKSAqIDIuMCAtIDEuMAogICAgICAgICAgICBmb3IgeCBpbiByYW5nZSh3KToKICAgICAgICAgICAgICAgIHB4ID0gKHggLyAodyAtIDEpKSAqIDIuMCAtIDEuMAogICAgICAgICAgICAgICAgZnJhbWVbaV0gPSBzY2VuZShweCwgcHksIGxpZ2h0X3gsIGxpZ2h0X3kpCiAgICAgICAgICAgICAgICBpICs9IDEKCiAgICAgICAgZnJhbWVzLmFwcGVuZChieXRlcyhmcmFtZSkpCgogICAgc2F2ZV9naWYob3V0X3BhdGgsIHcsIGgsIGZyYW1lcywgcGFsZXR0ZSgpLCBkZWxheV9jcz0zLCBsb29wPTApCiAgICBlbGFwc2VkID0gcGVyZl9jb3VudGVyKCkgLSBzdGFydAogICAgcHJpbnQoIm91dHB1dDoiLCBvdXRfcGF0aCkKICAgIHByaW50KCJmcmFtZXM6IiwgZnJhbWVzX24pCiAgICBwcmludCgiZWxhcHNlZF9zZWM6IiwgZWxhcHNlZCkKCgppZiBfX25hbWVfXyA9PSAiX19tYWluX18iOgogICAgcnVuXzE0X3JheW1hcmNoaW5nX2xpZ2h0X2N5Y2xlKCkK"

        // main は埋め込み Python を実行するエントリポイント。
        @JvmStatic
        fun main(args: Array<String>) {
            val code: Int = PyRuntime.runEmbeddedPython(PYTRA_EMBEDDED_SOURCE_BASE64, args)
            kotlin.system.exitProcess(code)
        }
    }
}
