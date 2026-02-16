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

class pytra_14_raymarching_light_cycle {
    companion object {
        // 埋め込み JavaScript ソース（Base64）。
        private const val PYTRA_EMBEDDED_JS_BASE64: String = "Ly8gZ2VuZXJhdGVkIGludGVybmFsIEphdmFTY3JpcHQKCmNvbnN0IF9fcHl0cmFfcm9vdCA9IHByb2Nlc3MuY3dkKCk7CmNvbnN0IHB5X3J1bnRpbWUgPSByZXF1aXJlKF9fcHl0cmFfcm9vdCArICcvc3JjL2pzX21vZHVsZS9weV9ydW50aW1lLmpzJyk7CmNvbnN0IHB5X21hdGggPSByZXF1aXJlKF9fcHl0cmFfcm9vdCArICcvc3JjL2pzX21vZHVsZS9tYXRoLmpzJyk7CmNvbnN0IHB5X3RpbWUgPSByZXF1aXJlKF9fcHl0cmFfcm9vdCArICcvc3JjL2pzX21vZHVsZS90aW1lLmpzJyk7CmNvbnN0IHsgcHlQcmludCwgcHlMZW4sIHB5Qm9vbCwgcHlSYW5nZSwgcHlGbG9vckRpdiwgcHlNb2QsIHB5SW4sIHB5U2xpY2UsIHB5T3JkLCBweUNociwgcHlCeXRlYXJyYXksIHB5Qnl0ZXMsIHB5SXNEaWdpdCwgcHlJc0FscGhhIH0gPSBweV9ydW50aW1lOwpjb25zdCB7IHBlcmZDb3VudGVyIH0gPSBweV90aW1lOwpjb25zdCBtYXRoID0gcmVxdWlyZShfX3B5dHJhX3Jvb3QgKyAnL3NyYy9qc19tb2R1bGUvbWF0aC5qcycpOwpjb25zdCBwZXJmX2NvdW50ZXIgPSBwZXJmQ291bnRlcjsKY29uc3QgeyBzYXZlX2dpZiB9ID0gcmVxdWlyZShfX3B5dHJhX3Jvb3QgKyAnL3NyYy9qc19tb2R1bGUvZ2lmX2hlbHBlci5qcycpOwoKZnVuY3Rpb24gcGFsZXR0ZSgpIHsKICAgIGxldCBwID0gcHlCeXRlYXJyYXkoKTsKICAgIGxldCBpOwogICAgZm9yIChsZXQgX19weXRyYV9pXzEgPSAwOyBfX3B5dHJhX2lfMSA8IDI1NjsgX19weXRyYV9pXzEgKz0gMSkgewogICAgICAgIGkgPSBfX3B5dHJhX2lfMTsKICAgICAgICBsZXQgciA9IE1hdGgudHJ1bmMoTnVtYmVyKCgoMjApICsgKCgoaSkgKiAoMC45KSkpKSkpOwogICAgICAgIGlmIChweUJvb2woKChyKSA+ICgyNTUpKSkpIHsKICAgICAgICAgICAgciA9IDI1NTsKICAgICAgICB9CiAgICAgICAgbGV0IGcgPSBNYXRoLnRydW5jKE51bWJlcigoKDEwKSArICgoKGkpICogKDAuNykpKSkpKTsKICAgICAgICBpZiAocHlCb29sKCgoZykgPiAoMjU1KSkpKSB7CiAgICAgICAgICAgIGcgPSAyNTU7CiAgICAgICAgfQogICAgICAgIGxldCBiID0gTWF0aC50cnVuYyhOdW1iZXIoKCgzMCkgKyAoaSkpKSk7CiAgICAgICAgaWYgKHB5Qm9vbCgoKGIpID4gKDI1NSkpKSkgewogICAgICAgICAgICBiID0gMjU1OwogICAgICAgIH0KICAgICAgICBwLnB1c2gocik7CiAgICAgICAgcC5wdXNoKGcpOwogICAgICAgIHAucHVzaChiKTsKICAgIH0KICAgIHJldHVybiBweUJ5dGVzKHApOwp9CmZ1bmN0aW9uIHNjZW5lKHgsIHksIGxpZ2h0X3gsIGxpZ2h0X3kpIHsKICAgIGxldCB4MSA9ICgoeCkgKyAoMC40NSkpOwogICAgbGV0IHkxID0gKCh5KSArICgwLjIpKTsKICAgIGxldCB4MiA9ICgoeCkgLSAoMC4zNSkpOwogICAgbGV0IHkyID0gKCh5KSAtICgwLjE1KSk7CiAgICBsZXQgcjEgPSBtYXRoLnNxcnQoKCgoKHgxKSAqICh4MSkpKSArICgoKHkxKSAqICh5MSkpKSkpOwogICAgbGV0IHIyID0gbWF0aC5zcXJ0KCgoKCh4MikgKiAoeDIpKSkgKyAoKCh5MikgKiAoeTIpKSkpKTsKICAgIGxldCBibG9iID0gKChtYXRoLmV4cCgoKCgoKC0oNy4wKSkpICogKHIxKSkpICogKHIxKSkpKSArIChtYXRoLmV4cCgoKCgoKC0oOC4wKSkpICogKHIyKSkpICogKHIyKSkpKSk7CiAgICBsZXQgbHggPSAoKHgpIC0gKGxpZ2h0X3gpKTsKICAgIGxldCBseSA9ICgoeSkgLSAobGlnaHRfeSkpOwogICAgbGV0IGwgPSBtYXRoLnNxcnQoKCgoKGx4KSAqIChseCkpKSArICgoKGx5KSAqIChseSkpKSkpOwogICAgbGV0IGxpdCA9ICgoMS4wKSAvICgoKDEuMCkgKyAoKCgoKDMuNSkgKiAobCkpKSAqIChsKSkpKSkpOwogICAgbGV0IHYgPSBNYXRoLnRydW5jKE51bWJlcigoKCgoKCgyNTUuMCkgKiAoYmxvYikpKSAqIChsaXQpKSkgKiAoNS4wKSkpKTsKICAgIGlmIChweUJvb2woKCh2KSA8ICgwKSkpKSB7CiAgICAgICAgcmV0dXJuIDA7CiAgICB9CiAgICBpZiAocHlCb29sKCgodikgPiAoMjU1KSkpKSB7CiAgICAgICAgcmV0dXJuIDI1NTsKICAgIH0KICAgIHJldHVybiB2Owp9CmZ1bmN0aW9uIHJ1bl8xNF9yYXltYXJjaGluZ19saWdodF9jeWNsZSgpIHsKICAgIGxldCB3ID0gMzIwOwogICAgbGV0IGggPSAyNDA7CiAgICBsZXQgZnJhbWVzX24gPSA4NDsKICAgIGxldCBvdXRfcGF0aCA9ICdzYW1wbGUvb3V0LzE0X3JheW1hcmNoaW5nX2xpZ2h0X2N5Y2xlLmdpZic7CiAgICBsZXQgc3RhcnQgPSBwZXJmX2NvdW50ZXIoKTsKICAgIGxldCBmcmFtZXMgPSBbXTsKICAgIGxldCB0OwogICAgZm9yIChsZXQgX19weXRyYV9pXzIgPSAwOyBfX3B5dHJhX2lfMiA8IGZyYW1lc19uOyBfX3B5dHJhX2lfMiArPSAxKSB7CiAgICAgICAgdCA9IF9fcHl0cmFfaV8yOwogICAgICAgIGxldCBmcmFtZSA9IHB5Qnl0ZWFycmF5KCgodykgKiAoaCkpKTsKICAgICAgICBsZXQgYSA9ICgoKCgoKHQpIC8gKGZyYW1lc19uKSkpICogKG1hdGgucGkpKSkgKiAoMi4wKSk7CiAgICAgICAgbGV0IGxpZ2h0X3ggPSAoKDAuNzUpICogKG1hdGguY29zKGEpKSk7CiAgICAgICAgbGV0IGxpZ2h0X3kgPSAoKDAuNTUpICogKG1hdGguc2luKCgoYSkgKiAoMS4yKSkpKSk7CiAgICAgICAgbGV0IGkgPSAwOwogICAgICAgIGxldCB5OwogICAgICAgIGZvciAobGV0IF9fcHl0cmFfaV8zID0gMDsgX19weXRyYV9pXzMgPCBoOyBfX3B5dHJhX2lfMyArPSAxKSB7CiAgICAgICAgICAgIHkgPSBfX3B5dHJhX2lfMzsKICAgICAgICAgICAgbGV0IHB5ID0gKCgoKCgoeSkgLyAoKChoKSAtICgxKSkpKSkgKiAoMi4wKSkpIC0gKDEuMCkpOwogICAgICAgICAgICBsZXQgeDsKICAgICAgICAgICAgZm9yIChsZXQgX19weXRyYV9pXzQgPSAwOyBfX3B5dHJhX2lfNCA8IHc7IF9fcHl0cmFfaV80ICs9IDEpIHsKICAgICAgICAgICAgICAgIHggPSBfX3B5dHJhX2lfNDsKICAgICAgICAgICAgICAgIGxldCBweCA9ICgoKCgoKHgpIC8gKCgodykgLSAoMSkpKSkpICogKDIuMCkpKSAtICgxLjApKTsKICAgICAgICAgICAgICAgIGZyYW1lW2ldID0gc2NlbmUocHgsIHB5LCBsaWdodF94LCBsaWdodF95KTsKICAgICAgICAgICAgICAgIGkgPSBpICsgMTsKICAgICAgICAgICAgfQogICAgICAgIH0KICAgICAgICBmcmFtZXMucHVzaChweUJ5dGVzKGZyYW1lKSk7CiAgICB9CiAgICBzYXZlX2dpZihvdXRfcGF0aCwgdywgaCwgZnJhbWVzLCBwYWxldHRlKCksIDMsIDApOwogICAgbGV0IGVsYXBzZWQgPSAoKHBlcmZfY291bnRlcigpKSAtIChzdGFydCkpOwogICAgcHlQcmludCgnb3V0cHV0OicsIG91dF9wYXRoKTsKICAgIHB5UHJpbnQoJ2ZyYW1lczonLCBmcmFtZXNfbik7CiAgICBweVByaW50KCdlbGFwc2VkX3NlYzonLCBlbGFwc2VkKTsKfQpydW5fMTRfcmF5bWFyY2hpbmdfbGlnaHRfY3ljbGUoKTsK"

        // エントリポイント。
        @JvmStatic
        fun main(args: Array<String>) {
            val code = PyRuntime.runEmbeddedNode(PYTRA_EMBEDDED_JS_BASE64, args)
            kotlin.system.exitProcess(code)
        }
    }
}
