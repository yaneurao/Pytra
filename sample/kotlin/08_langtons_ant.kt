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

class pytra_08_langtons_ant {
    companion object {
        // 埋め込み JavaScript ソース（Base64）。
        private const val PYTRA_EMBEDDED_JS_BASE64: String = "Ly8gZ2VuZXJhdGVkIGludGVybmFsIEphdmFTY3JpcHQKCmNvbnN0IF9fcHl0cmFfcm9vdCA9IHByb2Nlc3MuY3dkKCk7CmNvbnN0IHB5X3J1bnRpbWUgPSByZXF1aXJlKF9fcHl0cmFfcm9vdCArICcvc3JjL2pzX21vZHVsZS9weV9ydW50aW1lLmpzJyk7CmNvbnN0IHB5X21hdGggPSByZXF1aXJlKF9fcHl0cmFfcm9vdCArICcvc3JjL2pzX21vZHVsZS9tYXRoLmpzJyk7CmNvbnN0IHB5X3RpbWUgPSByZXF1aXJlKF9fcHl0cmFfcm9vdCArICcvc3JjL2pzX21vZHVsZS90aW1lLmpzJyk7CmNvbnN0IHsgcHlQcmludCwgcHlMZW4sIHB5Qm9vbCwgcHlSYW5nZSwgcHlGbG9vckRpdiwgcHlNb2QsIHB5SW4sIHB5U2xpY2UsIHB5T3JkLCBweUNociwgcHlCeXRlYXJyYXksIHB5Qnl0ZXMsIHB5SXNEaWdpdCwgcHlJc0FscGhhIH0gPSBweV9ydW50aW1lOwpjb25zdCB7IHBlcmZDb3VudGVyIH0gPSBweV90aW1lOwpjb25zdCBwZXJmX2NvdW50ZXIgPSBwZXJmQ291bnRlcjsKY29uc3QgeyBncmF5c2NhbGVfcGFsZXR0ZSwgc2F2ZV9naWYgfSA9IHJlcXVpcmUoX19weXRyYV9yb290ICsgJy9zcmMvanNfbW9kdWxlL2dpZl9oZWxwZXIuanMnKTsKCmZ1bmN0aW9uIGNhcHR1cmUoZ3JpZCwgdywgaCkgewogICAgbGV0IGZyYW1lID0gcHlCeXRlYXJyYXkoKCh3KSAqIChoKSkpOwogICAgbGV0IGkgPSAwOwogICAgbGV0IHk7CiAgICBmb3IgKGxldCBfX3B5dHJhX2lfMSA9IDA7IF9fcHl0cmFfaV8xIDwgaDsgX19weXRyYV9pXzEgKz0gMSkgewogICAgICAgIHkgPSBfX3B5dHJhX2lfMTsKICAgICAgICBsZXQgeDsKICAgICAgICBmb3IgKGxldCBfX3B5dHJhX2lfMiA9IDA7IF9fcHl0cmFfaV8yIDwgdzsgX19weXRyYV9pXzIgKz0gMSkgewogICAgICAgICAgICB4ID0gX19weXRyYV9pXzI7CiAgICAgICAgICAgIGZyYW1lW2ldID0gKHB5Qm9vbChncmlkW3ldW3hdKSA/IDI1NSA6IDApOwogICAgICAgICAgICBpID0gaSArIDE7CiAgICAgICAgfQogICAgfQogICAgcmV0dXJuIHB5Qnl0ZXMoZnJhbWUpOwp9CmZ1bmN0aW9uIHJ1bl8wOF9sYW5ndG9uc19hbnQoKSB7CiAgICBsZXQgdyA9IDQyMDsKICAgIGxldCBoID0gNDIwOwogICAgbGV0IG91dF9wYXRoID0gJ3NhbXBsZS9vdXQvMDhfbGFuZ3RvbnNfYW50LmdpZic7CiAgICBsZXQgc3RhcnQgPSBwZXJmX2NvdW50ZXIoKTsKICAgIGxldCBncmlkID0gW107CiAgICBsZXQgZ3k7CiAgICBmb3IgKGxldCBfX3B5dHJhX2lfMyA9IDA7IF9fcHl0cmFfaV8zIDwgaDsgX19weXRyYV9pXzMgKz0gMSkgewogICAgICAgIGd5ID0gX19weXRyYV9pXzM7CiAgICAgICAgbGV0IHJvdyA9IFtdOwogICAgICAgIGxldCBneDsKICAgICAgICBmb3IgKGxldCBfX3B5dHJhX2lfNCA9IDA7IF9fcHl0cmFfaV80IDwgdzsgX19weXRyYV9pXzQgKz0gMSkgewogICAgICAgICAgICBneCA9IF9fcHl0cmFfaV80OwogICAgICAgICAgICByb3cucHVzaCgwKTsKICAgICAgICB9CiAgICAgICAgZ3JpZC5wdXNoKHJvdyk7CiAgICB9CiAgICBsZXQgeCA9IHB5Rmxvb3JEaXYodywgMik7CiAgICBsZXQgeSA9IHB5Rmxvb3JEaXYoaCwgMik7CiAgICBsZXQgZCA9IDA7CiAgICBsZXQgc3RlcHNfdG90YWwgPSA2MDAwMDA7CiAgICBsZXQgY2FwdHVyZV9ldmVyeSA9IDMwMDA7CiAgICBsZXQgZnJhbWVzID0gW107CiAgICBsZXQgaTsKICAgIGZvciAobGV0IF9fcHl0cmFfaV81ID0gMDsgX19weXRyYV9pXzUgPCBzdGVwc190b3RhbDsgX19weXRyYV9pXzUgKz0gMSkgewogICAgICAgIGkgPSBfX3B5dHJhX2lfNTsKICAgICAgICBpZiAocHlCb29sKCgoZ3JpZFt5XVt4XSkgPT09ICgwKSkpKSB7CiAgICAgICAgICAgIGQgPSBweU1vZCgoKGQpICsgKDEpKSwgNCk7CiAgICAgICAgICAgIGdyaWRbeV1beF0gPSAxOwogICAgICAgIH0gZWxzZSB7CiAgICAgICAgICAgIGQgPSBweU1vZCgoKGQpICsgKDMpKSwgNCk7CiAgICAgICAgICAgIGdyaWRbeV1beF0gPSAwOwogICAgICAgIH0KICAgICAgICBpZiAocHlCb29sKCgoZCkgPT09ICgwKSkpKSB7CiAgICAgICAgICAgIHkgPSBweU1vZCgoKCgoeSkgLSAoMSkpKSArIChoKSksIGgpOwogICAgICAgIH0gZWxzZSB7CiAgICAgICAgICAgIGlmIChweUJvb2woKChkKSA9PT0gKDEpKSkpIHsKICAgICAgICAgICAgICAgIHggPSBweU1vZCgoKHgpICsgKDEpKSwgdyk7CiAgICAgICAgICAgIH0gZWxzZSB7CiAgICAgICAgICAgICAgICBpZiAocHlCb29sKCgoZCkgPT09ICgyKSkpKSB7CiAgICAgICAgICAgICAgICAgICAgeSA9IHB5TW9kKCgoeSkgKyAoMSkpLCBoKTsKICAgICAgICAgICAgICAgIH0gZWxzZSB7CiAgICAgICAgICAgICAgICAgICAgeCA9IHB5TW9kKCgoKCh4KSAtICgxKSkpICsgKHcpKSwgdyk7CiAgICAgICAgICAgICAgICB9CiAgICAgICAgICAgIH0KICAgICAgICB9CiAgICAgICAgaWYgKHB5Qm9vbCgoKHB5TW9kKGksIGNhcHR1cmVfZXZlcnkpKSA9PT0gKDApKSkpIHsKICAgICAgICAgICAgZnJhbWVzLnB1c2goY2FwdHVyZShncmlkLCB3LCBoKSk7CiAgICAgICAgfQogICAgfQogICAgc2F2ZV9naWYob3V0X3BhdGgsIHcsIGgsIGZyYW1lcywgZ3JheXNjYWxlX3BhbGV0dGUoKSwgNSwgMCk7CiAgICBsZXQgZWxhcHNlZCA9ICgocGVyZl9jb3VudGVyKCkpIC0gKHN0YXJ0KSk7CiAgICBweVByaW50KCdvdXRwdXQ6Jywgb3V0X3BhdGgpOwogICAgcHlQcmludCgnZnJhbWVzOicsIHB5TGVuKGZyYW1lcykpOwogICAgcHlQcmludCgnZWxhcHNlZF9zZWM6JywgZWxhcHNlZCk7Cn0KcnVuXzA4X2xhbmd0b25zX2FudCgpOwo="

        // エントリポイント。
        @JvmStatic
        fun main(args: Array<String>) {
            val code = PyRuntime.runEmbeddedNode(PYTRA_EMBEDDED_JS_BASE64, args)
            kotlin.system.exitProcess(code)
        }
    }
}
