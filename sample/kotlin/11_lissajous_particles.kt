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

class pytra_11_lissajous_particles {
    companion object {
        // 埋め込み JavaScript ソース（Base64）。
        private const val PYTRA_EMBEDDED_JS_BASE64: String = "Ly8gZ2VuZXJhdGVkIGludGVybmFsIEphdmFTY3JpcHQKCmNvbnN0IF9fcHl0cmFfcm9vdCA9IHByb2Nlc3MuY3dkKCk7CmNvbnN0IHB5X3J1bnRpbWUgPSByZXF1aXJlKF9fcHl0cmFfcm9vdCArICcvc3JjL2pzX21vZHVsZS9weV9ydW50aW1lLmpzJyk7CmNvbnN0IHB5X21hdGggPSByZXF1aXJlKF9fcHl0cmFfcm9vdCArICcvc3JjL2pzX21vZHVsZS9tYXRoLmpzJyk7CmNvbnN0IHB5X3RpbWUgPSByZXF1aXJlKF9fcHl0cmFfcm9vdCArICcvc3JjL2pzX21vZHVsZS90aW1lLmpzJyk7CmNvbnN0IHsgcHlQcmludCwgcHlMZW4sIHB5Qm9vbCwgcHlSYW5nZSwgcHlGbG9vckRpdiwgcHlNb2QsIHB5SW4sIHB5U2xpY2UsIHB5T3JkLCBweUNociwgcHlCeXRlYXJyYXksIHB5Qnl0ZXMsIHB5SXNEaWdpdCwgcHlJc0FscGhhIH0gPSBweV9ydW50aW1lOwpjb25zdCB7IHBlcmZDb3VudGVyIH0gPSBweV90aW1lOwpjb25zdCBtYXRoID0gcmVxdWlyZShfX3B5dHJhX3Jvb3QgKyAnL3NyYy9qc19tb2R1bGUvbWF0aC5qcycpOwpjb25zdCBwZXJmX2NvdW50ZXIgPSBwZXJmQ291bnRlcjsKY29uc3QgeyBzYXZlX2dpZiB9ID0gcmVxdWlyZShfX3B5dHJhX3Jvb3QgKyAnL3NyYy9qc19tb2R1bGUvZ2lmX2hlbHBlci5qcycpOwoKZnVuY3Rpb24gY29sb3JfcGFsZXR0ZSgpIHsKICAgIGxldCBwID0gcHlCeXRlYXJyYXkoKTsKICAgIGxldCBpOwogICAgZm9yIChsZXQgX19weXRyYV9pXzEgPSAwOyBfX3B5dHJhX2lfMSA8IDI1NjsgX19weXRyYV9pXzEgKz0gMSkgewogICAgICAgIGkgPSBfX3B5dHJhX2lfMTsKICAgICAgICBsZXQgciA9IGk7CiAgICAgICAgbGV0IGcgPSBweU1vZCgoKGkpICogKDMpKSwgMjU2KTsKICAgICAgICBsZXQgYiA9ICgoMjU1KSAtIChpKSk7CiAgICAgICAgcC5wdXNoKHIpOwogICAgICAgIHAucHVzaChnKTsKICAgICAgICBwLnB1c2goYik7CiAgICB9CiAgICByZXR1cm4gcHlCeXRlcyhwKTsKfQpmdW5jdGlvbiBydW5fMTFfbGlzc2Fqb3VzX3BhcnRpY2xlcygpIHsKICAgIGxldCB3ID0gMzIwOwogICAgbGV0IGggPSAyNDA7CiAgICBsZXQgZnJhbWVzX24gPSAzNjA7CiAgICBsZXQgcGFydGljbGVzID0gNDg7CiAgICBsZXQgb3V0X3BhdGggPSAnc2FtcGxlL291dC8xMV9saXNzYWpvdXNfcGFydGljbGVzLmdpZic7CiAgICBsZXQgc3RhcnQgPSBwZXJmX2NvdW50ZXIoKTsKICAgIGxldCBmcmFtZXMgPSBbXTsKICAgIGxldCB0OwogICAgZm9yIChsZXQgX19weXRyYV9pXzIgPSAwOyBfX3B5dHJhX2lfMiA8IGZyYW1lc19uOyBfX3B5dHJhX2lfMiArPSAxKSB7CiAgICAgICAgdCA9IF9fcHl0cmFfaV8yOwogICAgICAgIGxldCBmcmFtZSA9IHB5Qnl0ZWFycmF5KCgodykgKiAoaCkpKTsKICAgICAgICBsZXQgcDsKICAgICAgICBmb3IgKGxldCBfX3B5dHJhX2lfMyA9IDA7IF9fcHl0cmFfaV8zIDwgcGFydGljbGVzOyBfX3B5dHJhX2lfMyArPSAxKSB7CiAgICAgICAgICAgIHAgPSBfX3B5dHJhX2lfMzsKICAgICAgICAgICAgbGV0IHBoYXNlID0gKChwKSAqICgwLjI2MTc5OSkpOwogICAgICAgICAgICBsZXQgeCA9IE1hdGgudHJ1bmMoTnVtYmVyKCgoKCh3KSAqICgwLjUpKSkgKyAoKCgoKHcpICogKDAuMzgpKSkgKiAobWF0aC5zaW4oKCgoKDAuMTEpICogKHQpKSkgKyAoKChwaGFzZSkgKiAoMi4wKSkpKSkpKSkpKSk7CiAgICAgICAgICAgIGxldCB5ID0gTWF0aC50cnVuYyhOdW1iZXIoKCgoKGgpICogKDAuNSkpKSArICgoKCgoaCkgKiAoMC4zOCkpKSAqIChtYXRoLnNpbigoKCgoMC4xNykgKiAodCkpKSArICgoKHBoYXNlKSAqICgzLjApKSkpKSkpKSkpKTsKICAgICAgICAgICAgbGV0IGNvbG9yID0gKCgzMCkgKyAocHlNb2QoKChwKSAqICg5KSksIDIyMCkpKTsKICAgICAgICAgICAgbGV0IGR5OwogICAgICAgICAgICBmb3IgKGxldCBfX3B5dHJhX2lfNCA9ICgtKDIpKTsgX19weXRyYV9pXzQgPCAzOyBfX3B5dHJhX2lfNCArPSAxKSB7CiAgICAgICAgICAgICAgICBkeSA9IF9fcHl0cmFfaV80OwogICAgICAgICAgICAgICAgbGV0IGR4OwogICAgICAgICAgICAgICAgZm9yIChsZXQgX19weXRyYV9pXzUgPSAoLSgyKSk7IF9fcHl0cmFfaV81IDwgMzsgX19weXRyYV9pXzUgKz0gMSkgewogICAgICAgICAgICAgICAgICAgIGR4ID0gX19weXRyYV9pXzU7CiAgICAgICAgICAgICAgICAgICAgbGV0IHh4ID0gKCh4KSArIChkeCkpOwogICAgICAgICAgICAgICAgICAgIGxldCB5eSA9ICgoeSkgKyAoZHkpKTsKICAgICAgICAgICAgICAgICAgICBpZiAocHlCb29sKCgoKHh4KSA+PSAoMCkpICYmICgoeHgpIDwgKHcpKSAmJiAoKHl5KSA+PSAoMCkpICYmICgoeXkpIDwgKGgpKSkpKSB7CiAgICAgICAgICAgICAgICAgICAgICAgIGxldCBkMiA9ICgoKChkeCkgKiAoZHgpKSkgKyAoKChkeSkgKiAoZHkpKSkpOwogICAgICAgICAgICAgICAgICAgICAgICBpZiAocHlCb29sKCgoZDIpIDw9ICg0KSkpKSB7CiAgICAgICAgICAgICAgICAgICAgICAgICAgICBsZXQgaWR4ID0gKCgoKHl5KSAqICh3KSkpICsgKHh4KSk7CiAgICAgICAgICAgICAgICAgICAgICAgICAgICBsZXQgdiA9ICgoY29sb3IpIC0gKCgoZDIpICogKDIwKSkpKTsKICAgICAgICAgICAgICAgICAgICAgICAgICAgIGlmIChweUJvb2woKCh2KSA8ICgwKSkpKSB7CiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgdiA9IDA7CiAgICAgICAgICAgICAgICAgICAgICAgICAgICB9CiAgICAgICAgICAgICAgICAgICAgICAgICAgICBpZiAocHlCb29sKCgodikgPiAoZnJhbWVbaWR4XSkpKSkgewogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIGZyYW1lW2lkeF0gPSB2OwogICAgICAgICAgICAgICAgICAgICAgICAgICAgfQogICAgICAgICAgICAgICAgICAgICAgICB9CiAgICAgICAgICAgICAgICAgICAgfQogICAgICAgICAgICAgICAgfQogICAgICAgICAgICB9CiAgICAgICAgfQogICAgICAgIGZyYW1lcy5wdXNoKHB5Qnl0ZXMoZnJhbWUpKTsKICAgIH0KICAgIHNhdmVfZ2lmKG91dF9wYXRoLCB3LCBoLCBmcmFtZXMsIGNvbG9yX3BhbGV0dGUoKSwgMywgMCk7CiAgICBsZXQgZWxhcHNlZCA9ICgocGVyZl9jb3VudGVyKCkpIC0gKHN0YXJ0KSk7CiAgICBweVByaW50KCdvdXRwdXQ6Jywgb3V0X3BhdGgpOwogICAgcHlQcmludCgnZnJhbWVzOicsIGZyYW1lc19uKTsKICAgIHB5UHJpbnQoJ2VsYXBzZWRfc2VjOicsIGVsYXBzZWQpOwp9CnJ1bl8xMV9saXNzYWpvdXNfcGFydGljbGVzKCk7Cg=="

        // エントリポイント。
        @JvmStatic
        fun main(args: Array<String>) {
            val code = PyRuntime.runEmbeddedNode(PYTRA_EMBEDDED_JS_BASE64, args)
            kotlin.system.exitProcess(code)
        }
    }
}
