// このファイルは自動生成です（Python -> Kotlin node-backed mode）。

// Kotlin 実行向け Node.js ランタイム補助。

import java.io.File
import java.nio.file.Files
import java.nio.file.Path
import java.util.Base64
import java.util.UUID

/**
 * Base64 で埋め込まれた JavaScript ソースコードを一時ファイルへ展開し、node で実行する。
 */
object PyRuntime {
    /**
     * @param sourceBase64 JavaScript ソースコードの Base64 文字列。
     * @param args JavaScript 側へ渡す引数配列。
     * @return node プロセスの終了コード。失敗時は 1 を返す。
     */
    @JvmStatic
    fun runEmbeddedNode(sourceBase64: String, args: Array<String>): Int {
        val sourceBytes: ByteArray = try {
            Base64.getDecoder().decode(sourceBase64)
        } catch (ex: IllegalArgumentException) {
            System.err.println("error: failed to decode embedded JavaScript source")
            return 1
        }

        val tempFile: Path = try {
            val name = "pytra_embedded_${UUID.randomUUID()}.js"
            val p = File(System.getProperty("java.io.tmpdir"), name).toPath()
            Files.write(p, sourceBytes)
            p
        } catch (ex: Exception) {
            System.err.println("error: failed to write temporary JavaScript file: ${ex.message}")
            return 1
        }

        val command = mutableListOf("node", tempFile.toString())
        command.addAll(args)
        val process: Process = try {
            ProcessBuilder(command)
                .inheritIO()
                .start()
        } catch (ex: Exception) {
            System.err.println("error: failed to launch node: ${ex.message}")
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
        // 埋め込み JavaScript ソース（Base64）。
        private const val PYTRA_EMBEDDED_JS_BASE64: String = "Ly8gZ2VuZXJhdGVkIGludGVybmFsIEphdmFTY3JpcHQKCmNvbnN0IF9fcHl0cmFfcm9vdCA9IHByb2Nlc3MuY3dkKCk7CmNvbnN0IHB5X3J1bnRpbWUgPSByZXF1aXJlKF9fcHl0cmFfcm9vdCArICcvc3JjL2pzX21vZHVsZS9weV9ydW50aW1lLmpzJyk7CmNvbnN0IHB5X21hdGggPSByZXF1aXJlKF9fcHl0cmFfcm9vdCArICcvc3JjL2pzX21vZHVsZS9tYXRoLmpzJyk7CmNvbnN0IHB5X3RpbWUgPSByZXF1aXJlKF9fcHl0cmFfcm9vdCArICcvc3JjL2pzX21vZHVsZS90aW1lLmpzJyk7CmNvbnN0IHsgcHlQcmludCwgcHlMZW4sIHB5Qm9vbCwgcHlSYW5nZSwgcHlGbG9vckRpdiwgcHlNb2QsIHB5SW4sIHB5U2xpY2UsIHB5T3JkLCBweUNociwgcHlCeXRlYXJyYXksIHB5Qnl0ZXMsIHB5SXNEaWdpdCwgcHlJc0FscGhhIH0gPSBweV9ydW50aW1lOwpjb25zdCB7IHBlcmZDb3VudGVyIH0gPSBweV90aW1lOwpjb25zdCBwZXJmX2NvdW50ZXIgPSBwZXJmQ291bnRlcjsKY29uc3QgeyBzYXZlX2dpZiB9ID0gcmVxdWlyZShfX3B5dHJhX3Jvb3QgKyAnL3NyYy9qc19tb2R1bGUvZ2lmX2hlbHBlci5qcycpOwoKZnVuY3Rpb24gZmlyZV9wYWxldHRlKCkgewogICAgbGV0IHAgPSBweUJ5dGVhcnJheSgpOwogICAgbGV0IGk7CiAgICBmb3IgKGxldCBfX3B5dHJhX2lfMSA9IDA7IF9fcHl0cmFfaV8xIDwgMjU2OyBfX3B5dHJhX2lfMSArPSAxKSB7CiAgICAgICAgaSA9IF9fcHl0cmFfaV8xOwogICAgICAgIGxldCByID0gMDsKICAgICAgICBsZXQgZyA9IDA7CiAgICAgICAgbGV0IGIgPSAwOwogICAgICAgIGlmIChweUJvb2woKChpKSA8ICg4NSkpKSkgewogICAgICAgICAgICByID0gKChpKSAqICgzKSk7CiAgICAgICAgICAgIGcgPSAwOwogICAgICAgICAgICBiID0gMDsKICAgICAgICB9IGVsc2UgewogICAgICAgICAgICBpZiAocHlCb29sKCgoaSkgPCAoMTcwKSkpKSB7CiAgICAgICAgICAgICAgICByID0gMjU1OwogICAgICAgICAgICAgICAgZyA9ICgoKChpKSAtICg4NSkpKSAqICgzKSk7CiAgICAgICAgICAgICAgICBiID0gMDsKICAgICAgICAgICAgfSBlbHNlIHsKICAgICAgICAgICAgICAgIHIgPSAyNTU7CiAgICAgICAgICAgICAgICBnID0gMjU1OwogICAgICAgICAgICAgICAgYiA9ICgoKChpKSAtICgxNzApKSkgKiAoMykpOwogICAgICAgICAgICB9CiAgICAgICAgfQogICAgICAgIHAucHVzaChyKTsKICAgICAgICBwLnB1c2goZyk7CiAgICAgICAgcC5wdXNoKGIpOwogICAgfQogICAgcmV0dXJuIHB5Qnl0ZXMocCk7Cn0KZnVuY3Rpb24gcnVuXzA5X2ZpcmVfc2ltdWxhdGlvbigpIHsKICAgIGxldCB3ID0gMzgwOwogICAgbGV0IGggPSAyNjA7CiAgICBsZXQgc3RlcHMgPSA0MjA7CiAgICBsZXQgb3V0X3BhdGggPSAnc2FtcGxlL291dC8wOV9maXJlX3NpbXVsYXRpb24uZ2lmJzsKICAgIGxldCBzdGFydCA9IHBlcmZfY291bnRlcigpOwogICAgbGV0IGhlYXQgPSBbXTsKICAgIGxldCBfOwogICAgZm9yIChsZXQgX19weXRyYV9pXzIgPSAwOyBfX3B5dHJhX2lfMiA8IGg7IF9fcHl0cmFfaV8yICs9IDEpIHsKICAgICAgICBfID0gX19weXRyYV9pXzI7CiAgICAgICAgbGV0IHJvdyA9IFtdOwogICAgICAgIGZvciAobGV0IF9fcHl0cmFfaV8zID0gMDsgX19weXRyYV9pXzMgPCB3OyBfX3B5dHJhX2lfMyArPSAxKSB7CiAgICAgICAgICAgIF8gPSBfX3B5dHJhX2lfMzsKICAgICAgICAgICAgcm93LnB1c2goMCk7CiAgICAgICAgfQogICAgICAgIGhlYXQucHVzaChyb3cpOwogICAgfQogICAgbGV0IGZyYW1lcyA9IFtdOwogICAgbGV0IHQ7CiAgICBmb3IgKGxldCBfX3B5dHJhX2lfNCA9IDA7IF9fcHl0cmFfaV80IDwgc3RlcHM7IF9fcHl0cmFfaV80ICs9IDEpIHsKICAgICAgICB0ID0gX19weXRyYV9pXzQ7CiAgICAgICAgbGV0IHg7CiAgICAgICAgZm9yIChsZXQgX19weXRyYV9pXzUgPSAwOyBfX3B5dHJhX2lfNSA8IHc7IF9fcHl0cmFfaV81ICs9IDEpIHsKICAgICAgICAgICAgeCA9IF9fcHl0cmFfaV81OwogICAgICAgICAgICBsZXQgdmFsID0gKCgxNzApICsgKHB5TW9kKCgoKCh4KSAqICgxMykpKSArICgoKHQpICogKDE3KSkpKSwgODYpKSk7CiAgICAgICAgICAgIGhlYXRbKChoKSAtICgxKSldW3hdID0gdmFsOwogICAgICAgIH0KICAgICAgICBsZXQgeTsKICAgICAgICBmb3IgKGxldCBfX3B5dHJhX2lfNiA9IDE7IF9fcHl0cmFfaV82IDwgaDsgX19weXRyYV9pXzYgKz0gMSkgewogICAgICAgICAgICB5ID0gX19weXRyYV9pXzY7CiAgICAgICAgICAgIGZvciAobGV0IF9fcHl0cmFfaV83ID0gMDsgX19weXRyYV9pXzcgPCB3OyBfX3B5dHJhX2lfNyArPSAxKSB7CiAgICAgICAgICAgICAgICB4ID0gX19weXRyYV9pXzc7CiAgICAgICAgICAgICAgICBsZXQgYSA9IGhlYXRbeV1beF07CiAgICAgICAgICAgICAgICBsZXQgYiA9IGhlYXRbeV1bcHlNb2QoKCgoKHgpIC0gKDEpKSkgKyAodykpLCB3KV07CiAgICAgICAgICAgICAgICBsZXQgYyA9IGhlYXRbeV1bcHlNb2QoKCh4KSArICgxKSksIHcpXTsKICAgICAgICAgICAgICAgIGxldCBkID0gaGVhdFtweU1vZCgoKHkpICsgKDEpKSwgaCldW3hdOwogICAgICAgICAgICAgICAgbGV0IHYgPSBweUZsb29yRGl2KCgoKCgoKGEpICsgKGIpKSkgKyAoYykpKSArIChkKSksIDQpOwogICAgICAgICAgICAgICAgbGV0IGNvb2wgPSAoKDEpICsgKHB5TW9kKCgoKCh4KSArICh5KSkpICsgKHQpKSwgMykpKTsKICAgICAgICAgICAgICAgIGxldCBudiA9ICgodikgLSAoY29vbCkpOwogICAgICAgICAgICAgICAgaGVhdFsoKHkpIC0gKDEpKV1beF0gPSAocHlCb29sKCgobnYpID4gKDApKSkgPyBudiA6IDApOwogICAgICAgICAgICB9CiAgICAgICAgfQogICAgICAgIGxldCBmcmFtZSA9IHB5Qnl0ZWFycmF5KCgodykgKiAoaCkpKTsKICAgICAgICBsZXQgaSA9IDA7CiAgICAgICAgbGV0IHl5OwogICAgICAgIGZvciAobGV0IF9fcHl0cmFfaV84ID0gMDsgX19weXRyYV9pXzggPCBoOyBfX3B5dHJhX2lfOCArPSAxKSB7CiAgICAgICAgICAgIHl5ID0gX19weXRyYV9pXzg7CiAgICAgICAgICAgIGxldCB4eDsKICAgICAgICAgICAgZm9yIChsZXQgX19weXRyYV9pXzkgPSAwOyBfX3B5dHJhX2lfOSA8IHc7IF9fcHl0cmFfaV85ICs9IDEpIHsKICAgICAgICAgICAgICAgIHh4ID0gX19weXRyYV9pXzk7CiAgICAgICAgICAgICAgICBmcmFtZVtpXSA9IGhlYXRbeXldW3h4XTsKICAgICAgICAgICAgICAgIGkgPSBpICsgMTsKICAgICAgICAgICAgfQogICAgICAgIH0KICAgICAgICBmcmFtZXMucHVzaChweUJ5dGVzKGZyYW1lKSk7CiAgICB9CiAgICBzYXZlX2dpZihvdXRfcGF0aCwgdywgaCwgZnJhbWVzLCBmaXJlX3BhbGV0dGUoKSwgNCwgMCk7CiAgICBsZXQgZWxhcHNlZCA9ICgocGVyZl9jb3VudGVyKCkpIC0gKHN0YXJ0KSk7CiAgICBweVByaW50KCdvdXRwdXQ6Jywgb3V0X3BhdGgpOwogICAgcHlQcmludCgnZnJhbWVzOicsIHN0ZXBzKTsKICAgIHB5UHJpbnQoJ2VsYXBzZWRfc2VjOicsIGVsYXBzZWQpOwp9CnJ1bl8wOV9maXJlX3NpbXVsYXRpb24oKTsK"

        // エントリポイント。
        @JvmStatic
        fun main(args: Array<String>) {
            val code = PyRuntime.runEmbeddedNode(PYTRA_EMBEDDED_JS_BASE64, args)
            kotlin.system.exitProcess(code)
        }
    }
}
