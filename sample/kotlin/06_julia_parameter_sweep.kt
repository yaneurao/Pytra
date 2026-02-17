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

class pytra_06_julia_parameter_sweep {
    companion object {
        // 埋め込み JavaScript ソース（Base64）。
        private const val PYTRA_EMBEDDED_JS_BASE64: String = "Ly8gZ2VuZXJhdGVkIGludGVybmFsIEphdmFTY3JpcHQKCmNvbnN0IF9fcHl0cmFfcm9vdCA9IHByb2Nlc3MuY3dkKCk7CmNvbnN0IHB5X3J1bnRpbWUgPSByZXF1aXJlKF9fcHl0cmFfcm9vdCArICcvc3JjL2pzX21vZHVsZS9weV9ydW50aW1lLmpzJyk7CmNvbnN0IHB5X21hdGggPSByZXF1aXJlKF9fcHl0cmFfcm9vdCArICcvc3JjL2pzX21vZHVsZS9tYXRoLmpzJyk7CmNvbnN0IHB5X3RpbWUgPSByZXF1aXJlKF9fcHl0cmFfcm9vdCArICcvc3JjL2pzX21vZHVsZS90aW1lLmpzJyk7CmNvbnN0IHsgcHlQcmludCwgcHlMZW4sIHB5Qm9vbCwgcHlSYW5nZSwgcHlGbG9vckRpdiwgcHlNb2QsIHB5SW4sIHB5U2xpY2UsIHB5T3JkLCBweUNociwgcHlCeXRlYXJyYXksIHB5Qnl0ZXMsIHB5SXNEaWdpdCwgcHlJc0FscGhhIH0gPSBweV9ydW50aW1lOwpjb25zdCB7IHBlcmZDb3VudGVyIH0gPSBweV90aW1lOwpjb25zdCBtYXRoID0gcmVxdWlyZShfX3B5dHJhX3Jvb3QgKyAnL3NyYy9qc19tb2R1bGUvbWF0aC5qcycpOwpjb25zdCBwZXJmX2NvdW50ZXIgPSBwZXJmQ291bnRlcjsKY29uc3QgeyBzYXZlX2dpZiB9ID0gcmVxdWlyZShfX3B5dHJhX3Jvb3QgKyAnL3NyYy9qc19tb2R1bGUvZ2lmX2hlbHBlci5qcycpOwoKZnVuY3Rpb24ganVsaWFfcGFsZXR0ZSgpIHsKICAgIGxldCBwYWxldHRlID0gcHlCeXRlYXJyYXkoKCgyNTYpICogKDMpKSk7CiAgICBwYWxldHRlWzBdID0gMDsKICAgIHBhbGV0dGVbMV0gPSAwOwogICAgcGFsZXR0ZVsyXSA9IDA7CiAgICBsZXQgaTsKICAgIGZvciAobGV0IF9fcHl0cmFfaV8xID0gMTsgX19weXRyYV9pXzEgPCAyNTY7IF9fcHl0cmFfaV8xICs9IDEpIHsKICAgICAgICBpID0gX19weXRyYV9pXzE7CiAgICAgICAgbGV0IHQgPSAoKCgoaSkgLSAoMSkpKSAvICgyNTQuMCkpOwogICAgICAgIGxldCByID0gTWF0aC50cnVuYyhOdW1iZXIoKCgyNTUuMCkgKiAoKCgoKCgoKCg5LjApICogKCgoMS4wKSAtICh0KSkpKSkgKiAodCkpKSAqICh0KSkpICogKHQpKSkpKSk7CiAgICAgICAgbGV0IGcgPSBNYXRoLnRydW5jKE51bWJlcigoKDI1NS4wKSAqICgoKCgoKCgoKDE1LjApICogKCgoMS4wKSAtICh0KSkpKSkgKiAoKCgxLjApIC0gKHQpKSkpKSAqICh0KSkpICogKHQpKSkpKSk7CiAgICAgICAgbGV0IGIgPSBNYXRoLnRydW5jKE51bWJlcigoKDI1NS4wKSAqICgoKCgoKCgoKDguNSkgKiAoKCgxLjApIC0gKHQpKSkpKSAqICgoKDEuMCkgLSAodCkpKSkpICogKCgoMS4wKSAtICh0KSkpKSkgKiAodCkpKSkpKTsKICAgICAgICBwYWxldHRlWygoKChpKSAqICgzKSkpICsgKDApKV0gPSByOwogICAgICAgIHBhbGV0dGVbKCgoKGkpICogKDMpKSkgKyAoMSkpXSA9IGc7CiAgICAgICAgcGFsZXR0ZVsoKCgoaSkgKiAoMykpKSArICgyKSldID0gYjsKICAgIH0KICAgIHJldHVybiBweUJ5dGVzKHBhbGV0dGUpOwp9CmZ1bmN0aW9uIHJlbmRlcl9mcmFtZSh3aWR0aCwgaGVpZ2h0LCBjciwgY2ksIG1heF9pdGVyLCBwaGFzZSkgewogICAgbGV0IGZyYW1lID0gcHlCeXRlYXJyYXkoKCh3aWR0aCkgKiAoaGVpZ2h0KSkpOwogICAgbGV0IGlkeCA9IDA7CiAgICBsZXQgeTsKICAgIGZvciAobGV0IF9fcHl0cmFfaV8yID0gMDsgX19weXRyYV9pXzIgPCBoZWlnaHQ7IF9fcHl0cmFfaV8yICs9IDEpIHsKICAgICAgICB5ID0gX19weXRyYV9pXzI7CiAgICAgICAgbGV0IHp5MCA9ICgoKC0oMS4yKSkpICsgKCgoMi40KSAqICgoKHkpIC8gKCgoaGVpZ2h0KSAtICgxKSkpKSkpKSk7CiAgICAgICAgbGV0IHg7CiAgICAgICAgZm9yIChsZXQgX19weXRyYV9pXzMgPSAwOyBfX3B5dHJhX2lfMyA8IHdpZHRoOyBfX3B5dHJhX2lfMyArPSAxKSB7CiAgICAgICAgICAgIHggPSBfX3B5dHJhX2lfMzsKICAgICAgICAgICAgbGV0IHp4ID0gKCgoLSgxLjgpKSkgKyAoKCgzLjYpICogKCgoeCkgLyAoKCh3aWR0aCkgLSAoMSkpKSkpKSkpOwogICAgICAgICAgICBsZXQgenkgPSB6eTA7CiAgICAgICAgICAgIGxldCBpID0gMDsKICAgICAgICAgICAgd2hpbGUgKHB5Qm9vbCgoKGkpIDwgKG1heF9pdGVyKSkpKSB7CiAgICAgICAgICAgICAgICBsZXQgengyID0gKCh6eCkgKiAoengpKTsKICAgICAgICAgICAgICAgIGxldCB6eTIgPSAoKHp5KSAqICh6eSkpOwogICAgICAgICAgICAgICAgaWYgKHB5Qm9vbCgoKCgoengyKSArICh6eTIpKSkgPiAoNC4wKSkpKSB7CiAgICAgICAgICAgICAgICAgICAgYnJlYWs7CiAgICAgICAgICAgICAgICB9CiAgICAgICAgICAgICAgICB6eSA9ICgoKCgoKDIuMCkgKiAoengpKSkgKiAoenkpKSkgKyAoY2kpKTsKICAgICAgICAgICAgICAgIHp4ID0gKCgoKHp4MikgLSAoenkyKSkpICsgKGNyKSk7CiAgICAgICAgICAgICAgICBpID0gaSArIDE7CiAgICAgICAgICAgIH0KICAgICAgICAgICAgaWYgKHB5Qm9vbCgoKGkpID49IChtYXhfaXRlcikpKSkgewogICAgICAgICAgICAgICAgZnJhbWVbaWR4XSA9IDA7CiAgICAgICAgICAgIH0gZWxzZSB7CiAgICAgICAgICAgICAgICBsZXQgY29sb3JfaW5kZXggPSAoKDEpICsgKHB5TW9kKCgocHlGbG9vckRpdigoKGkpICogKDIyNCkpLCBtYXhfaXRlcikpICsgKHBoYXNlKSksIDI1NSkpKTsKICAgICAgICAgICAgICAgIGZyYW1lW2lkeF0gPSBjb2xvcl9pbmRleDsKICAgICAgICAgICAgfQogICAgICAgICAgICBpZHggPSBpZHggKyAxOwogICAgICAgIH0KICAgIH0KICAgIHJldHVybiBweUJ5dGVzKGZyYW1lKTsKfQpmdW5jdGlvbiBydW5fMDZfanVsaWFfcGFyYW1ldGVyX3N3ZWVwKCkgewogICAgbGV0IHdpZHRoID0gMzIwOwogICAgbGV0IGhlaWdodCA9IDI0MDsKICAgIGxldCBmcmFtZXNfbiA9IDcyOwogICAgbGV0IG1heF9pdGVyID0gMTgwOwogICAgbGV0IG91dF9wYXRoID0gJ3NhbXBsZS9vdXQvMDZfanVsaWFfcGFyYW1ldGVyX3N3ZWVwLmdpZic7CiAgICBsZXQgc3RhcnQgPSBwZXJmX2NvdW50ZXIoKTsKICAgIGxldCBmcmFtZXMgPSBbXTsKICAgIGxldCBjZW50ZXJfY3IgPSAoLSgwLjc0NSkpOwogICAgbGV0IGNlbnRlcl9jaSA9IDAuMTg2OwogICAgbGV0IHJhZGl1c19jciA9IDAuMTI7CiAgICBsZXQgcmFkaXVzX2NpID0gMC4xOwogICAgbGV0IHN0YXJ0X29mZnNldCA9IDIwOwogICAgbGV0IHBoYXNlX29mZnNldCA9IDE4MDsKICAgIGxldCBpOwogICAgZm9yIChsZXQgX19weXRyYV9pXzQgPSAwOyBfX3B5dHJhX2lfNCA8IGZyYW1lc19uOyBfX3B5dHJhX2lfNCArPSAxKSB7CiAgICAgICAgaSA9IF9fcHl0cmFfaV80OwogICAgICAgIGxldCB0ID0gKChweU1vZCgoKGkpICsgKHN0YXJ0X29mZnNldCkpLCBmcmFtZXNfbikpIC8gKGZyYW1lc19uKSk7CiAgICAgICAgbGV0IGFuZ2xlID0gKCgoKDIuMCkgKiAobWF0aC5waSkpKSAqICh0KSk7CiAgICAgICAgbGV0IGNyID0gKChjZW50ZXJfY3IpICsgKCgocmFkaXVzX2NyKSAqIChtYXRoLmNvcyhhbmdsZSkpKSkpOwogICAgICAgIGxldCBjaSA9ICgoY2VudGVyX2NpKSArICgoKHJhZGl1c19jaSkgKiAobWF0aC5zaW4oYW5nbGUpKSkpKTsKICAgICAgICBsZXQgcGhhc2UgPSBweU1vZCgoKHBoYXNlX29mZnNldCkgKyAoKChpKSAqICg1KSkpKSwgMjU1KTsKICAgICAgICBmcmFtZXMucHVzaChyZW5kZXJfZnJhbWUod2lkdGgsIGhlaWdodCwgY3IsIGNpLCBtYXhfaXRlciwgcGhhc2UpKTsKICAgIH0KICAgIHNhdmVfZ2lmKG91dF9wYXRoLCB3aWR0aCwgaGVpZ2h0LCBmcmFtZXMsIGp1bGlhX3BhbGV0dGUoKSwgOCwgMCk7CiAgICBsZXQgZWxhcHNlZCA9ICgocGVyZl9jb3VudGVyKCkpIC0gKHN0YXJ0KSk7CiAgICBweVByaW50KCdvdXRwdXQ6Jywgb3V0X3BhdGgpOwogICAgcHlQcmludCgnZnJhbWVzOicsIGZyYW1lc19uKTsKICAgIHB5UHJpbnQoJ2VsYXBzZWRfc2VjOicsIGVsYXBzZWQpOwp9CnJ1bl8wNl9qdWxpYV9wYXJhbWV0ZXJfc3dlZXAoKTsK"

        // エントリポイント。
        @JvmStatic
        fun main(args: Array<String>) {
            val code = PyRuntime.runEmbeddedNode(PYTRA_EMBEDDED_JS_BASE64, args)
            kotlin.system.exitProcess(code)
        }
    }
}
