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

class pytra_09_fire_simulation {
    companion object {
        // 埋め込み Python ソース（Base64）。
        private const val PYTRA_EMBEDDED_SOURCE_BASE64: String = "IyAwOTog57Ch5piT44OV44Kh44Kk44Ki44Ko44OV44Kn44Kv44OI44KSR0lG5Ye65Yqb44GZ44KL44K144Oz44OX44Or44CCCgpmcm9tIF9fZnV0dXJlX18gaW1wb3J0IGFubm90YXRpb25zCgpmcm9tIHRpbWUgaW1wb3J0IHBlcmZfY291bnRlcgoKZnJvbSBweV9tb2R1bGUuZ2lmX2hlbHBlciBpbXBvcnQgc2F2ZV9naWYKCgpkZWYgZmlyZV9wYWxldHRlKCkgLT4gYnl0ZXM6CiAgICBwID0gYnl0ZWFycmF5KCkKICAgIGZvciBpIGluIHJhbmdlKDI1Nik6CiAgICAgICAgciA9IDAKICAgICAgICBnID0gMAogICAgICAgIGIgPSAwCiAgICAgICAgaWYgaSA8IDg1OgogICAgICAgICAgICByID0gaSAqIDMKICAgICAgICAgICAgZyA9IDAKICAgICAgICAgICAgYiA9IDAKICAgICAgICBlbGlmIGkgPCAxNzA6CiAgICAgICAgICAgIHIgPSAyNTUKICAgICAgICAgICAgZyA9IChpIC0gODUpICogMwogICAgICAgICAgICBiID0gMAogICAgICAgIGVsc2U6CiAgICAgICAgICAgIHIgPSAyNTUKICAgICAgICAgICAgZyA9IDI1NQogICAgICAgICAgICBiID0gKGkgLSAxNzApICogMwogICAgICAgIHAuYXBwZW5kKHIpCiAgICAgICAgcC5hcHBlbmQoZykKICAgICAgICBwLmFwcGVuZChiKQogICAgcmV0dXJuIGJ5dGVzKHApCgoKZGVmIHJ1bl8wOV9maXJlX3NpbXVsYXRpb24oKSAtPiBOb25lOgogICAgdyA9IDM4MAogICAgaCA9IDI2MAogICAgc3RlcHMgPSA0MjAKICAgIG91dF9wYXRoID0gInNhbXBsZS9vdXQvMDlfZmlyZV9zaW11bGF0aW9uLmdpZiIKCiAgICBzdGFydCA9IHBlcmZfY291bnRlcigpCiAgICBoZWF0OiBsaXN0W2xpc3RbaW50XV0gPSBbXQogICAgZm9yIF8gaW4gcmFuZ2UoaCk6CiAgICAgICAgcm93OiBsaXN0W2ludF0gPSBbXQogICAgICAgIGZvciBfIGluIHJhbmdlKHcpOgogICAgICAgICAgICByb3cuYXBwZW5kKDApCiAgICAgICAgaGVhdC5hcHBlbmQocm93KQogICAgZnJhbWVzOiBsaXN0W2J5dGVzXSA9IFtdCgogICAgZm9yIHQgaW4gcmFuZ2Uoc3RlcHMpOgogICAgICAgIGZvciB4IGluIHJhbmdlKHcpOgogICAgICAgICAgICB2YWwgPSAxNzAgKyAoKHggKiAxMyArIHQgKiAxNykgJSA4NikKICAgICAgICAgICAgaGVhdFtoIC0gMV1beF0gPSB2YWwKCiAgICAgICAgZm9yIHkgaW4gcmFuZ2UoMSwgaCk6CiAgICAgICAgICAgIGZvciB4IGluIHJhbmdlKHcpOgogICAgICAgICAgICAgICAgYSA9IGhlYXRbeV1beF0KICAgICAgICAgICAgICAgIGIgPSBoZWF0W3ldWyh4IC0gMSArIHcpICUgd10KICAgICAgICAgICAgICAgIGMgPSBoZWF0W3ldWyh4ICsgMSkgJSB3XQogICAgICAgICAgICAgICAgZCA9IGhlYXRbKHkgKyAxKSAlIGhdW3hdCiAgICAgICAgICAgICAgICB2ID0gKGEgKyBiICsgYyArIGQpIC8vIDQKICAgICAgICAgICAgICAgIGNvb2wgPSAxICsgKCh4ICsgeSArIHQpICUgMykKICAgICAgICAgICAgICAgIG52ID0gdiAtIGNvb2wKICAgICAgICAgICAgICAgIGhlYXRbeSAtIDFdW3hdID0gbnYgaWYgbnYgPiAwIGVsc2UgMAoKICAgICAgICBmcmFtZSA9IGJ5dGVhcnJheSh3ICogaCkKICAgICAgICBpID0gMAogICAgICAgIGZvciB5eSBpbiByYW5nZShoKToKICAgICAgICAgICAgZm9yIHh4IGluIHJhbmdlKHcpOgogICAgICAgICAgICAgICAgZnJhbWVbaV0gPSBoZWF0W3l5XVt4eF0KICAgICAgICAgICAgICAgIGkgKz0gMQogICAgICAgIGZyYW1lcy5hcHBlbmQoYnl0ZXMoZnJhbWUpKQoKICAgIHNhdmVfZ2lmKG91dF9wYXRoLCB3LCBoLCBmcmFtZXMsIGZpcmVfcGFsZXR0ZSgpLCBkZWxheV9jcz00LCBsb29wPTApCiAgICBlbGFwc2VkID0gcGVyZl9jb3VudGVyKCkgLSBzdGFydAogICAgcHJpbnQoIm91dHB1dDoiLCBvdXRfcGF0aCkKICAgIHByaW50KCJmcmFtZXM6Iiwgc3RlcHMpCiAgICBwcmludCgiZWxhcHNlZF9zZWM6IiwgZWxhcHNlZCkKCgppZiBfX25hbWVfXyA9PSAiX19tYWluX18iOgogICAgcnVuXzA5X2ZpcmVfc2ltdWxhdGlvbigpCg=="

        // main は埋め込み Python を実行するエントリポイント。
        @JvmStatic
        fun main(args: Array<String>) {
            val code: Int = PyRuntime.runEmbeddedPython(PYTRA_EMBEDDED_SOURCE_BASE64, args)
            kotlin.system.exitProcess(code)
        }
    }
}
