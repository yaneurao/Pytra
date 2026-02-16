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

class pytra_04_monte_carlo_pi {
    companion object {
        // 埋め込み JavaScript ソース（Base64）。
        private const val PYTRA_EMBEDDED_JS_BASE64: String = "Ly8gZ2VuZXJhdGVkIGludGVybmFsIEphdmFTY3JpcHQKCmNvbnN0IF9fcHl0cmFfcm9vdCA9IHByb2Nlc3MuY3dkKCk7CmNvbnN0IHB5X3J1bnRpbWUgPSByZXF1aXJlKF9fcHl0cmFfcm9vdCArICcvc3JjL2pzX21vZHVsZS9weV9ydW50aW1lLmpzJyk7CmNvbnN0IHB5X21hdGggPSByZXF1aXJlKF9fcHl0cmFfcm9vdCArICcvc3JjL2pzX21vZHVsZS9tYXRoLmpzJyk7CmNvbnN0IHB5X3RpbWUgPSByZXF1aXJlKF9fcHl0cmFfcm9vdCArICcvc3JjL2pzX21vZHVsZS90aW1lLmpzJyk7CmNvbnN0IHsgcHlQcmludCwgcHlMZW4sIHB5Qm9vbCwgcHlSYW5nZSwgcHlGbG9vckRpdiwgcHlNb2QsIHB5SW4sIHB5U2xpY2UsIHB5T3JkLCBweUNociwgcHlCeXRlYXJyYXksIHB5Qnl0ZXMsIHB5SXNEaWdpdCwgcHlJc0FscGhhIH0gPSBweV9ydW50aW1lOwpjb25zdCB7IHBlcmZDb3VudGVyIH0gPSBweV90aW1lOwpjb25zdCBwZXJmX2NvdW50ZXIgPSBwZXJmQ291bnRlcjsKCmZ1bmN0aW9uIGxjZ19uZXh0KHN0YXRlKSB7CiAgICByZXR1cm4gcHlNb2QoKCgoKDE2NjQ1MjUpICogKHN0YXRlKSkpICsgKDEwMTM5MDQyMjMpKSwgNDI5NDk2NzI5Nik7Cn0KZnVuY3Rpb24gcnVuX3BpX3RyaWFsKHRvdGFsX3NhbXBsZXMsIHNlZWQpIHsKICAgIGxldCBpbnNpZGUgPSAwOwogICAgbGV0IHN0YXRlID0gc2VlZDsKICAgIGxldCBfOwogICAgZm9yIChsZXQgX19weXRyYV9pXzEgPSAwOyBfX3B5dHJhX2lfMSA8IHRvdGFsX3NhbXBsZXM7IF9fcHl0cmFfaV8xICs9IDEpIHsKICAgICAgICBfID0gX19weXRyYV9pXzE7CiAgICAgICAgc3RhdGUgPSBsY2dfbmV4dChzdGF0ZSk7CiAgICAgICAgbGV0IHggPSAoKHN0YXRlKSAvICg0Mjk0OTY3Mjk2LjApKTsKICAgICAgICBzdGF0ZSA9IGxjZ19uZXh0KHN0YXRlKTsKICAgICAgICBsZXQgeSA9ICgoc3RhdGUpIC8gKDQyOTQ5NjcyOTYuMCkpOwogICAgICAgIGxldCBkeCA9ICgoeCkgLSAoMC41KSk7CiAgICAgICAgbGV0IGR5ID0gKCh5KSAtICgwLjUpKTsKICAgICAgICBpZiAocHlCb29sKCgoKCgoKGR4KSAqIChkeCkpKSArICgoKGR5KSAqIChkeSkpKSkpIDw9ICgwLjI1KSkpKSB7CiAgICAgICAgICAgIGluc2lkZSA9IGluc2lkZSArIDE7CiAgICAgICAgfQogICAgfQogICAgcmV0dXJuICgoKCg0LjApICogKGluc2lkZSkpKSAvICh0b3RhbF9zYW1wbGVzKSk7Cn0KZnVuY3Rpb24gcnVuX21vbnRlX2NhcmxvX3BpKCkgewogICAgbGV0IHNhbXBsZXMgPSA1NDAwMDAwMDsKICAgIGxldCBzZWVkID0gMTIzNDU2Nzg5OwogICAgbGV0IHN0YXJ0ID0gcGVyZl9jb3VudGVyKCk7CiAgICBsZXQgcGlfZXN0ID0gcnVuX3BpX3RyaWFsKHNhbXBsZXMsIHNlZWQpOwogICAgbGV0IGVsYXBzZWQgPSAoKHBlcmZfY291bnRlcigpKSAtIChzdGFydCkpOwogICAgcHlQcmludCgnc2FtcGxlczonLCBzYW1wbGVzKTsKICAgIHB5UHJpbnQoJ3BpX2VzdGltYXRlOicsIHBpX2VzdCk7CiAgICBweVByaW50KCdlbGFwc2VkX3NlYzonLCBlbGFwc2VkKTsKfQpydW5fbW9udGVfY2FybG9fcGkoKTsK"

        // エントリポイント。
        @JvmStatic
        fun main(args: Array<String>) {
            val code = PyRuntime.runEmbeddedNode(PYTRA_EMBEDDED_JS_BASE64, args)
            kotlin.system.exitProcess(code)
        }
    }
}
