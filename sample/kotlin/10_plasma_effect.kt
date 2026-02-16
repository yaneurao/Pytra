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

class pytra_10_plasma_effect {
    companion object {
        // 埋め込み JavaScript ソース（Base64）。
        private const val PYTRA_EMBEDDED_JS_BASE64: String = "Ly8gZ2VuZXJhdGVkIGludGVybmFsIEphdmFTY3JpcHQKCmNvbnN0IF9fcHl0cmFfcm9vdCA9IHByb2Nlc3MuY3dkKCk7CmNvbnN0IHB5X3J1bnRpbWUgPSByZXF1aXJlKF9fcHl0cmFfcm9vdCArICcvc3JjL2pzX21vZHVsZS9weV9ydW50aW1lLmpzJyk7CmNvbnN0IHB5X21hdGggPSByZXF1aXJlKF9fcHl0cmFfcm9vdCArICcvc3JjL2pzX21vZHVsZS9tYXRoLmpzJyk7CmNvbnN0IHB5X3RpbWUgPSByZXF1aXJlKF9fcHl0cmFfcm9vdCArICcvc3JjL2pzX21vZHVsZS90aW1lLmpzJyk7CmNvbnN0IHsgcHlQcmludCwgcHlMZW4sIHB5Qm9vbCwgcHlSYW5nZSwgcHlGbG9vckRpdiwgcHlNb2QsIHB5SW4sIHB5U2xpY2UsIHB5T3JkLCBweUNociwgcHlCeXRlYXJyYXksIHB5Qnl0ZXMsIHB5SXNEaWdpdCwgcHlJc0FscGhhIH0gPSBweV9ydW50aW1lOwpjb25zdCB7IHBlcmZDb3VudGVyIH0gPSBweV90aW1lOwpjb25zdCBtYXRoID0gcmVxdWlyZShfX3B5dHJhX3Jvb3QgKyAnL3NyYy9qc19tb2R1bGUvbWF0aC5qcycpOwpjb25zdCBwZXJmX2NvdW50ZXIgPSBwZXJmQ291bnRlcjsKY29uc3QgeyBncmF5c2NhbGVfcGFsZXR0ZSwgc2F2ZV9naWYgfSA9IHJlcXVpcmUoX19weXRyYV9yb290ICsgJy9zcmMvanNfbW9kdWxlL2dpZl9oZWxwZXIuanMnKTsKCmZ1bmN0aW9uIHJ1bl8xMF9wbGFzbWFfZWZmZWN0KCkgewogICAgbGV0IHcgPSAzMjA7CiAgICBsZXQgaCA9IDI0MDsKICAgIGxldCBmcmFtZXNfbiA9IDIxNjsKICAgIGxldCBvdXRfcGF0aCA9ICdzYW1wbGUvb3V0LzEwX3BsYXNtYV9lZmZlY3QuZ2lmJzsKICAgIGxldCBzdGFydCA9IHBlcmZfY291bnRlcigpOwogICAgbGV0IGZyYW1lcyA9IFtdOwogICAgbGV0IHQ7CiAgICBmb3IgKGxldCBfX3B5dHJhX2lfMSA9IDA7IF9fcHl0cmFfaV8xIDwgZnJhbWVzX247IF9fcHl0cmFfaV8xICs9IDEpIHsKICAgICAgICB0ID0gX19weXRyYV9pXzE7CiAgICAgICAgbGV0IGZyYW1lID0gcHlCeXRlYXJyYXkoKCh3KSAqIChoKSkpOwogICAgICAgIGxldCBpID0gMDsKICAgICAgICBsZXQgeTsKICAgICAgICBmb3IgKGxldCBfX3B5dHJhX2lfMiA9IDA7IF9fcHl0cmFfaV8yIDwgaDsgX19weXRyYV9pXzIgKz0gMSkgewogICAgICAgICAgICB5ID0gX19weXRyYV9pXzI7CiAgICAgICAgICAgIGxldCB4OwogICAgICAgICAgICBmb3IgKGxldCBfX3B5dHJhX2lfMyA9IDA7IF9fcHl0cmFfaV8zIDwgdzsgX19weXRyYV9pXzMgKz0gMSkgewogICAgICAgICAgICAgICAgeCA9IF9fcHl0cmFfaV8zOwogICAgICAgICAgICAgICAgbGV0IGR4ID0gKCh4KSAtICgxNjApKTsKICAgICAgICAgICAgICAgIGxldCBkeSA9ICgoeSkgLSAoMTIwKSk7CiAgICAgICAgICAgICAgICBsZXQgdiA9ICgoKCgoKG1hdGguc2luKCgoKCh4KSArICgoKHQpICogKDIuMCkpKSkpICogKDAuMDQ1KSkpKSArIChtYXRoLnNpbigoKCgoeSkgLSAoKCh0KSAqICgxLjIpKSkpKSAqICgwLjA1KSkpKSkpICsgKG1hdGguc2luKCgoKCgoKHgpICsgKHkpKSkgKyAoKCh0KSAqICgxLjcpKSkpKSAqICgwLjAzKSkpKSkpICsgKG1hdGguc2luKCgoKChtYXRoLnNxcnQoKCgoKGR4KSAqIChkeCkpKSArICgoKGR5KSAqIChkeSkpKSkpKSAqICgwLjA3KSkpIC0gKCgodCkgKiAoMC4xOCkpKSkpKSk7CiAgICAgICAgICAgICAgICBsZXQgYyA9IE1hdGgudHJ1bmMoTnVtYmVyKCgoKCh2KSArICg0LjApKSkgKiAoKCgyNTUuMCkgLyAoOC4wKSkpKSkpOwogICAgICAgICAgICAgICAgaWYgKHB5Qm9vbCgoKGMpIDwgKDApKSkpIHsKICAgICAgICAgICAgICAgICAgICBjID0gMDsKICAgICAgICAgICAgICAgIH0KICAgICAgICAgICAgICAgIGlmIChweUJvb2woKChjKSA+ICgyNTUpKSkpIHsKICAgICAgICAgICAgICAgICAgICBjID0gMjU1OwogICAgICAgICAgICAgICAgfQogICAgICAgICAgICAgICAgZnJhbWVbaV0gPSBjOwogICAgICAgICAgICAgICAgaSA9IGkgKyAxOwogICAgICAgICAgICB9CiAgICAgICAgfQogICAgICAgIGZyYW1lcy5wdXNoKHB5Qnl0ZXMoZnJhbWUpKTsKICAgIH0KICAgIHNhdmVfZ2lmKG91dF9wYXRoLCB3LCBoLCBmcmFtZXMsIGdyYXlzY2FsZV9wYWxldHRlKCksIDMsIDApOwogICAgbGV0IGVsYXBzZWQgPSAoKHBlcmZfY291bnRlcigpKSAtIChzdGFydCkpOwogICAgcHlQcmludCgnb3V0cHV0OicsIG91dF9wYXRoKTsKICAgIHB5UHJpbnQoJ2ZyYW1lczonLCBmcmFtZXNfbik7CiAgICBweVByaW50KCdlbGFwc2VkX3NlYzonLCBlbGFwc2VkKTsKfQpydW5fMTBfcGxhc21hX2VmZmVjdCgpOwo="

        // エントリポイント。
        @JvmStatic
        fun main(args: Array<String>) {
            val code = PyRuntime.runEmbeddedNode(PYTRA_EMBEDDED_JS_BASE64, args)
            kotlin.system.exitProcess(code)
        }
    }
}
