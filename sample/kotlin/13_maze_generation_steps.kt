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

class pytra_13_maze_generation_steps {
    companion object {
        // 埋め込み JavaScript ソース（Base64）。
        private const val PYTRA_EMBEDDED_JS_BASE64: String = "Ly8gZ2VuZXJhdGVkIGludGVybmFsIEphdmFTY3JpcHQKCmNvbnN0IF9fcHl0cmFfcm9vdCA9IHByb2Nlc3MuY3dkKCk7CmNvbnN0IHB5X3J1bnRpbWUgPSByZXF1aXJlKF9fcHl0cmFfcm9vdCArICcvc3JjL2pzX21vZHVsZS9weV9ydW50aW1lLmpzJyk7CmNvbnN0IHB5X21hdGggPSByZXF1aXJlKF9fcHl0cmFfcm9vdCArICcvc3JjL2pzX21vZHVsZS9tYXRoLmpzJyk7CmNvbnN0IHB5X3RpbWUgPSByZXF1aXJlKF9fcHl0cmFfcm9vdCArICcvc3JjL2pzX21vZHVsZS90aW1lLmpzJyk7CmNvbnN0IHsgcHlQcmludCwgcHlMZW4sIHB5Qm9vbCwgcHlSYW5nZSwgcHlGbG9vckRpdiwgcHlNb2QsIHB5SW4sIHB5U2xpY2UsIHB5T3JkLCBweUNociwgcHlCeXRlYXJyYXksIHB5Qnl0ZXMsIHB5SXNEaWdpdCwgcHlJc0FscGhhIH0gPSBweV9ydW50aW1lOwpjb25zdCB7IHBlcmZDb3VudGVyIH0gPSBweV90aW1lOwpjb25zdCBwZXJmX2NvdW50ZXIgPSBwZXJmQ291bnRlcjsKY29uc3QgeyBncmF5c2NhbGVfcGFsZXR0ZSwgc2F2ZV9naWYgfSA9IHJlcXVpcmUoX19weXRyYV9yb290ICsgJy9zcmMvanNfbW9kdWxlL2dpZl9oZWxwZXIuanMnKTsKCmZ1bmN0aW9uIGNhcHR1cmUoZ3JpZCwgdywgaCwgc2NhbGUpIHsKICAgIGxldCB3aWR0aCA9ICgodykgKiAoc2NhbGUpKTsKICAgIGxldCBoZWlnaHQgPSAoKGgpICogKHNjYWxlKSk7CiAgICBsZXQgZnJhbWUgPSBweUJ5dGVhcnJheSgoKHdpZHRoKSAqIChoZWlnaHQpKSk7CiAgICBsZXQgeTsKICAgIGZvciAobGV0IF9fcHl0cmFfaV8xID0gMDsgX19weXRyYV9pXzEgPCBoOyBfX3B5dHJhX2lfMSArPSAxKSB7CiAgICAgICAgeSA9IF9fcHl0cmFfaV8xOwogICAgICAgIGxldCB4OwogICAgICAgIGZvciAobGV0IF9fcHl0cmFfaV8yID0gMDsgX19weXRyYV9pXzIgPCB3OyBfX3B5dHJhX2lfMiArPSAxKSB7CiAgICAgICAgICAgIHggPSBfX3B5dHJhX2lfMjsKICAgICAgICAgICAgbGV0IHYgPSAocHlCb29sKCgoZ3JpZFt5XVt4XSkgPT09ICgwKSkpID8gMjU1IDogNDApOwogICAgICAgICAgICBsZXQgeXk7CiAgICAgICAgICAgIGZvciAobGV0IF9fcHl0cmFfaV8zID0gMDsgX19weXRyYV9pXzMgPCBzY2FsZTsgX19weXRyYV9pXzMgKz0gMSkgewogICAgICAgICAgICAgICAgeXkgPSBfX3B5dHJhX2lfMzsKICAgICAgICAgICAgICAgIGxldCBiYXNlID0gKCgoKCgoKCh5KSAqIChzY2FsZSkpKSArICh5eSkpKSAqICh3aWR0aCkpKSArICgoKHgpICogKHNjYWxlKSkpKTsKICAgICAgICAgICAgICAgIGxldCB4eDsKICAgICAgICAgICAgICAgIGZvciAobGV0IF9fcHl0cmFfaV80ID0gMDsgX19weXRyYV9pXzQgPCBzY2FsZTsgX19weXRyYV9pXzQgKz0gMSkgewogICAgICAgICAgICAgICAgICAgIHh4ID0gX19weXRyYV9pXzQ7CiAgICAgICAgICAgICAgICAgICAgZnJhbWVbKChiYXNlKSArICh4eCkpXSA9IHY7CiAgICAgICAgICAgICAgICB9CiAgICAgICAgICAgIH0KICAgICAgICB9CiAgICB9CiAgICByZXR1cm4gcHlCeXRlcyhmcmFtZSk7Cn0KZnVuY3Rpb24gcnVuXzEzX21hemVfZ2VuZXJhdGlvbl9zdGVwcygpIHsKICAgIGxldCBjZWxsX3cgPSA4OTsKICAgIGxldCBjZWxsX2ggPSA2NzsKICAgIGxldCBzY2FsZSA9IDU7CiAgICBsZXQgY2FwdHVyZV9ldmVyeSA9IDIwOwogICAgbGV0IG91dF9wYXRoID0gJ3NhbXBsZS9vdXQvMTNfbWF6ZV9nZW5lcmF0aW9uX3N0ZXBzLmdpZic7CiAgICBsZXQgc3RhcnQgPSBwZXJmX2NvdW50ZXIoKTsKICAgIGxldCBncmlkID0gW107CiAgICBsZXQgXzsKICAgIGZvciAobGV0IF9fcHl0cmFfaV81ID0gMDsgX19weXRyYV9pXzUgPCBjZWxsX2g7IF9fcHl0cmFfaV81ICs9IDEpIHsKICAgICAgICBfID0gX19weXRyYV9pXzU7CiAgICAgICAgbGV0IHJvdyA9IFtdOwogICAgICAgIGZvciAobGV0IF9fcHl0cmFfaV82ID0gMDsgX19weXRyYV9pXzYgPCBjZWxsX3c7IF9fcHl0cmFfaV82ICs9IDEpIHsKICAgICAgICAgICAgXyA9IF9fcHl0cmFfaV82OwogICAgICAgICAgICByb3cucHVzaCgxKTsKICAgICAgICB9CiAgICAgICAgZ3JpZC5wdXNoKHJvdyk7CiAgICB9CiAgICBsZXQgc3RhY2sgPSBbWzEsIDFdXTsKICAgIGdyaWRbMV1bMV0gPSAwOwogICAgbGV0IGRpcnMgPSBbWzIsIDBdLCBbKC0oMikpLCAwXSwgWzAsIDJdLCBbMCwgKC0oMikpXV07CiAgICBsZXQgZnJhbWVzID0gW107CiAgICBsZXQgc3RlcCA9IDA7CiAgICB3aGlsZSAocHlCb29sKCgocHlMZW4oc3RhY2spKSA+ICgwKSkpKSB7CiAgICAgICAgbGV0IGxhc3RfaW5kZXggPSAoKHB5TGVuKHN0YWNrKSkgLSAoMSkpOwogICAgICAgIGNvbnN0IF9fcHl0cmFfdHVwbGVfNyA9IHN0YWNrW2xhc3RfaW5kZXhdOwogICAgICAgIGxldCB4ID0gX19weXRyYV90dXBsZV83WzBdOwogICAgICAgIGxldCB5ID0gX19weXRyYV90dXBsZV83WzFdOwogICAgICAgIGxldCBjYW5kaWRhdGVzID0gW107CiAgICAgICAgbGV0IGs7CiAgICAgICAgZm9yIChsZXQgX19weXRyYV9pXzggPSAwOyBfX3B5dHJhX2lfOCA8IDQ7IF9fcHl0cmFfaV84ICs9IDEpIHsKICAgICAgICAgICAgayA9IF9fcHl0cmFfaV84OwogICAgICAgICAgICBjb25zdCBfX3B5dHJhX3R1cGxlXzkgPSBkaXJzW2tdOwogICAgICAgICAgICBsZXQgZHggPSBfX3B5dHJhX3R1cGxlXzlbMF07CiAgICAgICAgICAgIGxldCBkeSA9IF9fcHl0cmFfdHVwbGVfOVsxXTsKICAgICAgICAgICAgbGV0IG54ID0gKCh4KSArIChkeCkpOwogICAgICAgICAgICBsZXQgbnkgPSAoKHkpICsgKGR5KSk7CiAgICAgICAgICAgIGlmIChweUJvb2woKCgobngpID49ICgxKSkgJiYgKChueCkgPCAoKChjZWxsX3cpIC0gKDEpKSkpICYmICgobnkpID49ICgxKSkgJiYgKChueSkgPCAoKChjZWxsX2gpIC0gKDEpKSkpICYmICgoZ3JpZFtueV1bbnhdKSA9PT0gKDEpKSkpKSB7CiAgICAgICAgICAgICAgICBpZiAocHlCb29sKCgoZHgpID09PSAoMikpKSkgewogICAgICAgICAgICAgICAgICAgIGNhbmRpZGF0ZXMucHVzaChbbngsIG55LCAoKHgpICsgKDEpKSwgeV0pOwogICAgICAgICAgICAgICAgfSBlbHNlIHsKICAgICAgICAgICAgICAgICAgICBpZiAocHlCb29sKCgoZHgpID09PSAoKC0oMikpKSkpKSB7CiAgICAgICAgICAgICAgICAgICAgICAgIGNhbmRpZGF0ZXMucHVzaChbbngsIG55LCAoKHgpIC0gKDEpKSwgeV0pOwogICAgICAgICAgICAgICAgICAgIH0gZWxzZSB7CiAgICAgICAgICAgICAgICAgICAgICAgIGlmIChweUJvb2woKChkeSkgPT09ICgyKSkpKSB7CiAgICAgICAgICAgICAgICAgICAgICAgICAgICBjYW5kaWRhdGVzLnB1c2goW254LCBueSwgeCwgKCh5KSArICgxKSldKTsKICAgICAgICAgICAgICAgICAgICAgICAgfSBlbHNlIHsKICAgICAgICAgICAgICAgICAgICAgICAgICAgIGNhbmRpZGF0ZXMucHVzaChbbngsIG55LCB4LCAoKHkpIC0gKDEpKV0pOwogICAgICAgICAgICAgICAgICAgICAgICB9CiAgICAgICAgICAgICAgICAgICAgfQogICAgICAgICAgICAgICAgfQogICAgICAgICAgICB9CiAgICAgICAgfQogICAgICAgIGlmIChweUJvb2woKChweUxlbihjYW5kaWRhdGVzKSkgPT09ICgwKSkpKSB7CiAgICAgICAgICAgIHN0YWNrLnBvcCgpOwogICAgICAgIH0gZWxzZSB7CiAgICAgICAgICAgIGxldCBzZWwgPSBjYW5kaWRhdGVzW3B5TW9kKCgoKCgoKHgpICogKDE3KSkpICsgKCgoeSkgKiAoMjkpKSkpKSArICgoKHB5TGVuKHN0YWNrKSkgKiAoMTMpKSkpLCBweUxlbihjYW5kaWRhdGVzKSldOwogICAgICAgICAgICBjb25zdCBfX3B5dHJhX3R1cGxlXzEwID0gc2VsOwogICAgICAgICAgICBsZXQgbnggPSBfX3B5dHJhX3R1cGxlXzEwWzBdOwogICAgICAgICAgICBsZXQgbnkgPSBfX3B5dHJhX3R1cGxlXzEwWzFdOwogICAgICAgICAgICBsZXQgd3ggPSBfX3B5dHJhX3R1cGxlXzEwWzJdOwogICAgICAgICAgICBsZXQgd3kgPSBfX3B5dHJhX3R1cGxlXzEwWzNdOwogICAgICAgICAgICBncmlkW3d5XVt3eF0gPSAwOwogICAgICAgICAgICBncmlkW255XVtueF0gPSAwOwogICAgICAgICAgICBzdGFjay5wdXNoKFtueCwgbnldKTsKICAgICAgICB9CiAgICAgICAgaWYgKHB5Qm9vbCgoKHB5TW9kKHN0ZXAsIGNhcHR1cmVfZXZlcnkpKSA9PT0gKDApKSkpIHsKICAgICAgICAgICAgZnJhbWVzLnB1c2goY2FwdHVyZShncmlkLCBjZWxsX3csIGNlbGxfaCwgc2NhbGUpKTsKICAgICAgICB9CiAgICAgICAgc3RlcCA9IHN0ZXAgKyAxOwogICAgfQogICAgZnJhbWVzLnB1c2goY2FwdHVyZShncmlkLCBjZWxsX3csIGNlbGxfaCwgc2NhbGUpKTsKICAgIHNhdmVfZ2lmKG91dF9wYXRoLCAoKGNlbGxfdykgKiAoc2NhbGUpKSwgKChjZWxsX2gpICogKHNjYWxlKSksIGZyYW1lcywgZ3JheXNjYWxlX3BhbGV0dGUoKSwgNCwgMCk7CiAgICBsZXQgZWxhcHNlZCA9ICgocGVyZl9jb3VudGVyKCkpIC0gKHN0YXJ0KSk7CiAgICBweVByaW50KCdvdXRwdXQ6Jywgb3V0X3BhdGgpOwogICAgcHlQcmludCgnZnJhbWVzOicsIHB5TGVuKGZyYW1lcykpOwogICAgcHlQcmludCgnZWxhcHNlZF9zZWM6JywgZWxhcHNlZCk7Cn0KcnVuXzEzX21hemVfZ2VuZXJhdGlvbl9zdGVwcygpOwo="

        // エントリポイント。
        @JvmStatic
        fun main(args: Array<String>) {
            val code = PyRuntime.runEmbeddedNode(PYTRA_EMBEDDED_JS_BASE64, args)
            kotlin.system.exitProcess(code)
        }
    }
}
