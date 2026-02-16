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

class pytra_01_mandelbrot {
    companion object {
        // 埋め込み JavaScript ソース（Base64）。
        private const val PYTRA_EMBEDDED_JS_BASE64: String = "Ly8gZ2VuZXJhdGVkIGludGVybmFsIEphdmFTY3JpcHQKCmNvbnN0IF9fcHl0cmFfcm9vdCA9IHByb2Nlc3MuY3dkKCk7CmNvbnN0IHB5X3J1bnRpbWUgPSByZXF1aXJlKF9fcHl0cmFfcm9vdCArICcvc3JjL2pzX21vZHVsZS9weV9ydW50aW1lLmpzJyk7CmNvbnN0IHB5X21hdGggPSByZXF1aXJlKF9fcHl0cmFfcm9vdCArICcvc3JjL2pzX21vZHVsZS9tYXRoLmpzJyk7CmNvbnN0IHB5X3RpbWUgPSByZXF1aXJlKF9fcHl0cmFfcm9vdCArICcvc3JjL2pzX21vZHVsZS90aW1lLmpzJyk7CmNvbnN0IHsgcHlQcmludCwgcHlMZW4sIHB5Qm9vbCwgcHlSYW5nZSwgcHlGbG9vckRpdiwgcHlNb2QsIHB5SW4sIHB5U2xpY2UsIHB5T3JkLCBweUNociwgcHlCeXRlYXJyYXksIHB5Qnl0ZXMsIHB5SXNEaWdpdCwgcHlJc0FscGhhIH0gPSBweV9ydW50aW1lOwpjb25zdCB7IHBlcmZDb3VudGVyIH0gPSBweV90aW1lOwpjb25zdCBwZXJmX2NvdW50ZXIgPSBwZXJmQ291bnRlcjsKY29uc3QgcG5nX2hlbHBlciA9IHJlcXVpcmUoX19weXRyYV9yb290ICsgJy9zcmMvanNfbW9kdWxlL3BuZ19oZWxwZXIuanMnKTsKCmZ1bmN0aW9uIGVzY2FwZV9jb3VudChjeCwgY3ksIG1heF9pdGVyKSB7CiAgICBsZXQgeCA9IDAuMDsKICAgIGxldCB5ID0gMC4wOwogICAgbGV0IGk7CiAgICBmb3IgKGxldCBfX3B5dHJhX2lfMSA9IDA7IF9fcHl0cmFfaV8xIDwgbWF4X2l0ZXI7IF9fcHl0cmFfaV8xICs9IDEpIHsKICAgICAgICBpID0gX19weXRyYV9pXzE7CiAgICAgICAgbGV0IHgyID0gKCh4KSAqICh4KSk7CiAgICAgICAgbGV0IHkyID0gKCh5KSAqICh5KSk7CiAgICAgICAgaWYgKHB5Qm9vbCgoKCgoeDIpICsgKHkyKSkpID4gKDQuMCkpKSkgewogICAgICAgICAgICByZXR1cm4gaTsKICAgICAgICB9CiAgICAgICAgeSA9ICgoKCgoKDIuMCkgKiAoeCkpKSAqICh5KSkpICsgKGN5KSk7CiAgICAgICAgeCA9ICgoKCh4MikgLSAoeTIpKSkgKyAoY3gpKTsKICAgIH0KICAgIHJldHVybiBtYXhfaXRlcjsKfQpmdW5jdGlvbiBjb2xvcl9tYXAoaXRlcl9jb3VudCwgbWF4X2l0ZXIpIHsKICAgIGlmIChweUJvb2woKChpdGVyX2NvdW50KSA+PSAobWF4X2l0ZXIpKSkpIHsKICAgICAgICByZXR1cm4gWzAsIDAsIDBdOwogICAgfQogICAgbGV0IHQgPSAoKGl0ZXJfY291bnQpIC8gKG1heF9pdGVyKSk7CiAgICBsZXQgciA9IE1hdGgudHJ1bmMoTnVtYmVyKCgoMjU1LjApICogKCgodCkgKiAodCkpKSkpKTsKICAgIGxldCBnID0gTWF0aC50cnVuYyhOdW1iZXIoKCgyNTUuMCkgKiAodCkpKSk7CiAgICBsZXQgYiA9IE1hdGgudHJ1bmMoTnVtYmVyKCgoMjU1LjApICogKCgoMS4wKSAtICh0KSkpKSkpOwogICAgcmV0dXJuIFtyLCBnLCBiXTsKfQpmdW5jdGlvbiByZW5kZXJfbWFuZGVsYnJvdCh3aWR0aCwgaGVpZ2h0LCBtYXhfaXRlciwgeF9taW4sIHhfbWF4LCB5X21pbiwgeV9tYXgpIHsKICAgIGxldCBwaXhlbHMgPSBweUJ5dGVhcnJheSgpOwogICAgbGV0IHk7CiAgICBmb3IgKGxldCBfX3B5dHJhX2lfMiA9IDA7IF9fcHl0cmFfaV8yIDwgaGVpZ2h0OyBfX3B5dHJhX2lfMiArPSAxKSB7CiAgICAgICAgeSA9IF9fcHl0cmFfaV8yOwogICAgICAgIGxldCBweSA9ICgoeV9taW4pICsgKCgoKCh5X21heCkgLSAoeV9taW4pKSkgKiAoKCh5KSAvICgoKGhlaWdodCkgLSAoMSkpKSkpKSkpOwogICAgICAgIGxldCB4OwogICAgICAgIGZvciAobGV0IF9fcHl0cmFfaV8zID0gMDsgX19weXRyYV9pXzMgPCB3aWR0aDsgX19weXRyYV9pXzMgKz0gMSkgewogICAgICAgICAgICB4ID0gX19weXRyYV9pXzM7CiAgICAgICAgICAgIGxldCBweCA9ICgoeF9taW4pICsgKCgoKCh4X21heCkgLSAoeF9taW4pKSkgKiAoKCh4KSAvICgoKHdpZHRoKSAtICgxKSkpKSkpKSk7CiAgICAgICAgICAgIGxldCBpdCA9IGVzY2FwZV9jb3VudChweCwgcHksIG1heF9pdGVyKTsKICAgICAgICAgICAgbGV0IHIgPSBudWxsOwogICAgICAgICAgICBsZXQgZyA9IG51bGw7CiAgICAgICAgICAgIGxldCBiID0gbnVsbDsKICAgICAgICAgICAgaWYgKHB5Qm9vbCgoKGl0KSA+PSAobWF4X2l0ZXIpKSkpIHsKICAgICAgICAgICAgICAgIHIgPSAwOwogICAgICAgICAgICAgICAgZyA9IDA7CiAgICAgICAgICAgICAgICBiID0gMDsKICAgICAgICAgICAgfSBlbHNlIHsKICAgICAgICAgICAgICAgIGxldCB0ID0gKChpdCkgLyAobWF4X2l0ZXIpKTsKICAgICAgICAgICAgICAgIHIgPSBNYXRoLnRydW5jKE51bWJlcigoKDI1NS4wKSAqICgoKHQpICogKHQpKSkpKSk7CiAgICAgICAgICAgICAgICBnID0gTWF0aC50cnVuYyhOdW1iZXIoKCgyNTUuMCkgKiAodCkpKSk7CiAgICAgICAgICAgICAgICBiID0gTWF0aC50cnVuYyhOdW1iZXIoKCgyNTUuMCkgKiAoKCgxLjApIC0gKHQpKSkpKSk7CiAgICAgICAgICAgIH0KICAgICAgICAgICAgcGl4ZWxzLnB1c2gocik7CiAgICAgICAgICAgIHBpeGVscy5wdXNoKGcpOwogICAgICAgICAgICBwaXhlbHMucHVzaChiKTsKICAgICAgICB9CiAgICB9CiAgICByZXR1cm4gcGl4ZWxzOwp9CmZ1bmN0aW9uIHJ1bl9tYW5kZWxicm90KCkgewogICAgbGV0IHdpZHRoID0gMTYwMDsKICAgIGxldCBoZWlnaHQgPSAxMjAwOwogICAgbGV0IG1heF9pdGVyID0gMTAwMDsKICAgIGxldCBvdXRfcGF0aCA9ICdzYW1wbGUvb3V0L21hbmRlbGJyb3RfMDEucG5nJzsKICAgIGxldCBzdGFydCA9IHBlcmZfY291bnRlcigpOwogICAgbGV0IHBpeGVscyA9IHJlbmRlcl9tYW5kZWxicm90KHdpZHRoLCBoZWlnaHQsIG1heF9pdGVyLCAoLSgyLjIpKSwgMS4wLCAoLSgxLjIpKSwgMS4yKTsKICAgIHBuZ19oZWxwZXIud3JpdGVfcmdiX3BuZyhvdXRfcGF0aCwgd2lkdGgsIGhlaWdodCwgcGl4ZWxzKTsKICAgIGxldCBlbGFwc2VkID0gKChwZXJmX2NvdW50ZXIoKSkgLSAoc3RhcnQpKTsKICAgIHB5UHJpbnQoJ291dHB1dDonLCBvdXRfcGF0aCk7CiAgICBweVByaW50KCdzaXplOicsIHdpZHRoLCAneCcsIGhlaWdodCk7CiAgICBweVByaW50KCdtYXhfaXRlcjonLCBtYXhfaXRlcik7CiAgICBweVByaW50KCdlbGFwc2VkX3NlYzonLCBlbGFwc2VkKTsKfQpydW5fbWFuZGVsYnJvdCgpOwo="

        // エントリポイント。
        @JvmStatic
        fun main(args: Array<String>) {
            val code = PyRuntime.runEmbeddedNode(PYTRA_EMBEDDED_JS_BASE64, args)
            kotlin.system.exitProcess(code)
        }
    }
}
