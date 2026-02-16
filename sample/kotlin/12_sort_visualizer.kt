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

class pytra_12_sort_visualizer {
    companion object {
        // 埋め込み JavaScript ソース（Base64）。
        private const val PYTRA_EMBEDDED_JS_BASE64: String = "Ly8gZ2VuZXJhdGVkIGludGVybmFsIEphdmFTY3JpcHQKCmNvbnN0IF9fcHl0cmFfcm9vdCA9IHByb2Nlc3MuY3dkKCk7CmNvbnN0IHB5X3J1bnRpbWUgPSByZXF1aXJlKF9fcHl0cmFfcm9vdCArICcvc3JjL2pzX21vZHVsZS9weV9ydW50aW1lLmpzJyk7CmNvbnN0IHB5X21hdGggPSByZXF1aXJlKF9fcHl0cmFfcm9vdCArICcvc3JjL2pzX21vZHVsZS9tYXRoLmpzJyk7CmNvbnN0IHB5X3RpbWUgPSByZXF1aXJlKF9fcHl0cmFfcm9vdCArICcvc3JjL2pzX21vZHVsZS90aW1lLmpzJyk7CmNvbnN0IHsgcHlQcmludCwgcHlMZW4sIHB5Qm9vbCwgcHlSYW5nZSwgcHlGbG9vckRpdiwgcHlNb2QsIHB5SW4sIHB5U2xpY2UsIHB5T3JkLCBweUNociwgcHlCeXRlYXJyYXksIHB5Qnl0ZXMsIHB5SXNEaWdpdCwgcHlJc0FscGhhIH0gPSBweV9ydW50aW1lOwpjb25zdCB7IHBlcmZDb3VudGVyIH0gPSBweV90aW1lOwpjb25zdCBwZXJmX2NvdW50ZXIgPSBwZXJmQ291bnRlcjsKY29uc3QgeyBncmF5c2NhbGVfcGFsZXR0ZSwgc2F2ZV9naWYgfSA9IHJlcXVpcmUoX19weXRyYV9yb290ICsgJy9zcmMvanNfbW9kdWxlL2dpZl9oZWxwZXIuanMnKTsKCmZ1bmN0aW9uIHJlbmRlcih2YWx1ZXMsIHcsIGgpIHsKICAgIGxldCBmcmFtZSA9IHB5Qnl0ZWFycmF5KCgodykgKiAoaCkpKTsKICAgIGxldCBuID0gcHlMZW4odmFsdWVzKTsKICAgIGxldCBiYXJfdyA9ICgodykgLyAobikpOwogICAgbGV0IGk7CiAgICBmb3IgKGxldCBfX3B5dHJhX2lfMSA9IDA7IF9fcHl0cmFfaV8xIDwgbjsgX19weXRyYV9pXzEgKz0gMSkgewogICAgICAgIGkgPSBfX3B5dHJhX2lfMTsKICAgICAgICBsZXQgeDAgPSBNYXRoLnRydW5jKE51bWJlcigoKGkpICogKGJhcl93KSkpKTsKICAgICAgICBsZXQgeDEgPSBNYXRoLnRydW5jKE51bWJlcigoKCgoaSkgKyAoMSkpKSAqIChiYXJfdykpKSk7CiAgICAgICAgaWYgKHB5Qm9vbCgoKHgxKSA8PSAoeDApKSkpIHsKICAgICAgICAgICAgeDEgPSAoKHgwKSArICgxKSk7CiAgICAgICAgfQogICAgICAgIGxldCBiaCA9IE1hdGgudHJ1bmMoTnVtYmVyKCgoKCh2YWx1ZXNbaV0pIC8gKG4pKSkgKiAoaCkpKSk7CiAgICAgICAgbGV0IHkgPSAoKGgpIC0gKGJoKSk7CiAgICAgICAgZm9yIChsZXQgX19weXRyYV9pXzIgPSB5OyBfX3B5dHJhX2lfMiA8IGg7IF9fcHl0cmFfaV8yICs9IDEpIHsKICAgICAgICAgICAgeSA9IF9fcHl0cmFfaV8yOwogICAgICAgICAgICBsZXQgeDsKICAgICAgICAgICAgZm9yIChsZXQgX19weXRyYV9pXzMgPSB4MDsgX19weXRyYV9pXzMgPCB4MTsgX19weXRyYV9pXzMgKz0gMSkgewogICAgICAgICAgICAgICAgeCA9IF9fcHl0cmFfaV8zOwogICAgICAgICAgICAgICAgZnJhbWVbKCgoKHkpICogKHcpKSkgKyAoeCkpXSA9IDI1NTsKICAgICAgICAgICAgfQogICAgICAgIH0KICAgIH0KICAgIHJldHVybiBweUJ5dGVzKGZyYW1lKTsKfQpmdW5jdGlvbiBydW5fMTJfc29ydF92aXN1YWxpemVyKCkgewogICAgbGV0IHcgPSAzMjA7CiAgICBsZXQgaCA9IDE4MDsKICAgIGxldCBuID0gMTI0OwogICAgbGV0IG91dF9wYXRoID0gJ3NhbXBsZS9vdXQvMTJfc29ydF92aXN1YWxpemVyLmdpZic7CiAgICBsZXQgc3RhcnQgPSBwZXJmX2NvdW50ZXIoKTsKICAgIGxldCB2YWx1ZXMgPSBbXTsKICAgIGxldCBpOwogICAgZm9yIChsZXQgX19weXRyYV9pXzQgPSAwOyBfX3B5dHJhX2lfNCA8IG47IF9fcHl0cmFfaV80ICs9IDEpIHsKICAgICAgICBpID0gX19weXRyYV9pXzQ7CiAgICAgICAgdmFsdWVzLnB1c2gocHlNb2QoKCgoKGkpICogKDM3KSkpICsgKDE5KSksIG4pKTsKICAgIH0KICAgIGxldCBmcmFtZXMgPSBbcmVuZGVyKHZhbHVlcywgdywgaCldOwogICAgbGV0IG9wID0gMDsKICAgIGZvciAobGV0IF9fcHl0cmFfaV81ID0gMDsgX19weXRyYV9pXzUgPCBuOyBfX3B5dHJhX2lfNSArPSAxKSB7CiAgICAgICAgaSA9IF9fcHl0cmFfaV81OwogICAgICAgIGxldCBzd2FwcGVkID0gZmFsc2U7CiAgICAgICAgbGV0IGo7CiAgICAgICAgZm9yIChsZXQgX19weXRyYV9pXzYgPSAwOyBfX3B5dHJhX2lfNiA8ICgoKChuKSAtIChpKSkpIC0gKDEpKTsgX19weXRyYV9pXzYgKz0gMSkgewogICAgICAgICAgICBqID0gX19weXRyYV9pXzY7CiAgICAgICAgICAgIGlmIChweUJvb2woKCh2YWx1ZXNbal0pID4gKHZhbHVlc1soKGopICsgKDEpKV0pKSkpIHsKICAgICAgICAgICAgICAgIGxldCB0bXAgPSB2YWx1ZXNbal07CiAgICAgICAgICAgICAgICB2YWx1ZXNbal0gPSB2YWx1ZXNbKChqKSArICgxKSldOwogICAgICAgICAgICAgICAgdmFsdWVzWygoaikgKyAoMSkpXSA9IHRtcDsKICAgICAgICAgICAgICAgIHN3YXBwZWQgPSB0cnVlOwogICAgICAgICAgICB9CiAgICAgICAgICAgIGlmIChweUJvb2woKChweU1vZChvcCwgOCkpID09PSAoMCkpKSkgewogICAgICAgICAgICAgICAgZnJhbWVzLnB1c2gocmVuZGVyKHZhbHVlcywgdywgaCkpOwogICAgICAgICAgICB9CiAgICAgICAgICAgIG9wID0gb3AgKyAxOwogICAgICAgIH0KICAgICAgICBpZiAocHlCb29sKCghcHlCb29sKHN3YXBwZWQpKSkpIHsKICAgICAgICAgICAgYnJlYWs7CiAgICAgICAgfQogICAgfQogICAgc2F2ZV9naWYob3V0X3BhdGgsIHcsIGgsIGZyYW1lcywgZ3JheXNjYWxlX3BhbGV0dGUoKSwgMywgMCk7CiAgICBsZXQgZWxhcHNlZCA9ICgocGVyZl9jb3VudGVyKCkpIC0gKHN0YXJ0KSk7CiAgICBweVByaW50KCdvdXRwdXQ6Jywgb3V0X3BhdGgpOwogICAgcHlQcmludCgnZnJhbWVzOicsIHB5TGVuKGZyYW1lcykpOwogICAgcHlQcmludCgnZWxhcHNlZF9zZWM6JywgZWxhcHNlZCk7Cn0KcnVuXzEyX3NvcnRfdmlzdWFsaXplcigpOwo="

        // エントリポイント。
        @JvmStatic
        fun main(args: Array<String>) {
            val code = PyRuntime.runEmbeddedNode(PYTRA_EMBEDDED_JS_BASE64, args)
            kotlin.system.exitProcess(code)
        }
    }
}
