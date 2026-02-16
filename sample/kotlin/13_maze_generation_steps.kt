// このファイルは自動生成です（Python -> Kotlin embedded mode）。

// Kotlin 埋め込み実行向け Python ランタイム補助。

import java.io.File
import java.nio.file.Files
import java.nio.file.Path
import java.util.Base64
import java.util.UUID

/**
 * Base64 で埋め込まれた Python ソースコードを一時ファイルに展開し、python3 で実行する。
 */
object PyRuntime {
    /**
     * @param sourceBase64 Python ソースコードの Base64 文字列。
     * @param args Python スクリプトへ渡す引数配列。
     * @return python プロセスの終了コード。失敗時は 1 を返す。
     */
    @JvmStatic
    fun runEmbeddedPython(sourceBase64: String, args: Array<String>): Int {
        val sourceBytes: ByteArray = try {
            Base64.getDecoder().decode(sourceBase64)
        } catch (ex: IllegalArgumentException) {
            System.err.println("error: failed to decode embedded Python source")
            return 1
        }

        val tempFile: Path = try {
            val name = "pytra_embedded_${UUID.randomUUID()}.py"
            val p = File(System.getProperty("java.io.tmpdir"), name).toPath()
            Files.write(p, sourceBytes)
            p
        } catch (ex: Exception) {
            System.err.println("error: failed to write temporary Python file: ${ex.message}")
            return 1
        }

        val command = mutableListOf("python3", tempFile.toString())
        command.addAll(args)
        // Python 製補助モジュールを import できるよう、src を PYTHONPATH に追加する。
        val env = mutableMapOf<String, String>()
        env.putAll(System.getenv())
        val currentPyPath = env["PYTHONPATH"]
        env["PYTHONPATH"] = if (currentPyPath.isNullOrEmpty()) "src" else "src:$currentPyPath"
        val process: Process = try {
            ProcessBuilder(command)
                .apply { environment().putAll(env) }
                .inheritIO()
                .start()
        } catch (ex: Exception) {
            System.err.println("error: failed to launch python3: ${ex.message}")
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
        // 埋め込み Python ソース（Base64）。
        private const val PYTRA_EMBEDDED_SOURCE_BASE64: String = "IyAxMzogREZT6L+36Lev55Sf5oiQ44Gu6YCy6KGM54q25rOB44KSR0lG5Ye65Yqb44GZ44KL44K144Oz44OX44Or44CCCgpmcm9tIF9fZnV0dXJlX18gaW1wb3J0IGFubm90YXRpb25zCgpmcm9tIHRpbWUgaW1wb3J0IHBlcmZfY291bnRlcgoKZnJvbSBweV9tb2R1bGUuZ2lmX2hlbHBlciBpbXBvcnQgZ3JheXNjYWxlX3BhbGV0dGUsIHNhdmVfZ2lmCgoKZGVmIGNhcHR1cmUoZ3JpZDogbGlzdFtsaXN0W2ludF1dLCB3OiBpbnQsIGg6IGludCwgc2NhbGU6IGludCkgLT4gYnl0ZXM6CiAgICB3aWR0aCA9IHcgKiBzY2FsZQogICAgaGVpZ2h0ID0gaCAqIHNjYWxlCiAgICBmcmFtZSA9IGJ5dGVhcnJheSh3aWR0aCAqIGhlaWdodCkKICAgIGZvciB5IGluIHJhbmdlKGgpOgogICAgICAgIGZvciB4IGluIHJhbmdlKHcpOgogICAgICAgICAgICB2ID0gMjU1IGlmIGdyaWRbeV1beF0gPT0gMCBlbHNlIDQwCiAgICAgICAgICAgIGZvciB5eSBpbiByYW5nZShzY2FsZSk6CiAgICAgICAgICAgICAgICBiYXNlID0gKHkgKiBzY2FsZSArIHl5KSAqIHdpZHRoICsgeCAqIHNjYWxlCiAgICAgICAgICAgICAgICBmb3IgeHggaW4gcmFuZ2Uoc2NhbGUpOgogICAgICAgICAgICAgICAgICAgIGZyYW1lW2Jhc2UgKyB4eF0gPSB2CiAgICByZXR1cm4gYnl0ZXMoZnJhbWUpCgoKZGVmIHJ1bl8xM19tYXplX2dlbmVyYXRpb25fc3RlcHMoKSAtPiBOb25lOgogICAgIyDlrp/ooYzmmYLplpPjgpLljYHliIbjgavnorrkv53jgZnjgovjgZ/jgoHjgIHov7fot6/jgrXjgqTjgrrjgajmj4/nlLvop6Plg4/luqbjgpLkuIrjgZLjgovjgIIKICAgIGNlbGxfdyA9IDg5CiAgICBjZWxsX2ggPSA2NwogICAgc2NhbGUgPSA1CiAgICBjYXB0dXJlX2V2ZXJ5ID0gMjAKICAgIG91dF9wYXRoID0gInNhbXBsZS9vdXQvMTNfbWF6ZV9nZW5lcmF0aW9uX3N0ZXBzLmdpZiIKCiAgICBzdGFydCA9IHBlcmZfY291bnRlcigpCiAgICBncmlkOiBsaXN0W2xpc3RbaW50XV0gPSBbXQogICAgZm9yIF8gaW4gcmFuZ2UoY2VsbF9oKToKICAgICAgICByb3c6IGxpc3RbaW50XSA9IFtdCiAgICAgICAgZm9yIF8gaW4gcmFuZ2UoY2VsbF93KToKICAgICAgICAgICAgcm93LmFwcGVuZCgxKQogICAgICAgIGdyaWQuYXBwZW5kKHJvdykKICAgIHN0YWNrOiBsaXN0W3R1cGxlW2ludCwgaW50XV0gPSBbKDEsIDEpXQogICAgZ3JpZFsxXVsxXSA9IDAKCiAgICBkaXJzOiBsaXN0W3R1cGxlW2ludCwgaW50XV0gPSBbKDIsIDApLCAoLTIsIDApLCAoMCwgMiksICgwLCAtMildCiAgICBmcmFtZXM6IGxpc3RbYnl0ZXNdID0gW10KICAgIHN0ZXAgPSAwCgogICAgd2hpbGUgbGVuKHN0YWNrKSA+IDA6CiAgICAgICAgbGFzdF9pbmRleCA9IGxlbihzdGFjaykgLSAxCiAgICAgICAgeCwgeSA9IHN0YWNrW2xhc3RfaW5kZXhdCiAgICAgICAgY2FuZGlkYXRlczogbGlzdFt0dXBsZVtpbnQsIGludCwgaW50LCBpbnRdXSA9IFtdCiAgICAgICAgZm9yIGsgaW4gcmFuZ2UoNCk6CiAgICAgICAgICAgIGR4LCBkeSA9IGRpcnNba10KICAgICAgICAgICAgbnggPSB4ICsgZHgKICAgICAgICAgICAgbnkgPSB5ICsgZHkKICAgICAgICAgICAgaWYgbnggPj0gMSBhbmQgbnggPCBjZWxsX3cgLSAxIGFuZCBueSA+PSAxIGFuZCBueSA8IGNlbGxfaCAtIDEgYW5kIGdyaWRbbnldW254XSA9PSAxOgogICAgICAgICAgICAgICAgaWYgZHggPT0gMjoKICAgICAgICAgICAgICAgICAgICBjYW5kaWRhdGVzLmFwcGVuZCgobngsIG55LCB4ICsgMSwgeSkpCiAgICAgICAgICAgICAgICBlbGlmIGR4ID09IC0yOgogICAgICAgICAgICAgICAgICAgIGNhbmRpZGF0ZXMuYXBwZW5kKChueCwgbnksIHggLSAxLCB5KSkKICAgICAgICAgICAgICAgIGVsaWYgZHkgPT0gMjoKICAgICAgICAgICAgICAgICAgICBjYW5kaWRhdGVzLmFwcGVuZCgobngsIG55LCB4LCB5ICsgMSkpCiAgICAgICAgICAgICAgICBlbHNlOgogICAgICAgICAgICAgICAgICAgIGNhbmRpZGF0ZXMuYXBwZW5kKChueCwgbnksIHgsIHkgLSAxKSkKCiAgICAgICAgaWYgbGVuKGNhbmRpZGF0ZXMpID09IDA6CiAgICAgICAgICAgIHN0YWNrLnBvcCgpCiAgICAgICAgZWxzZToKICAgICAgICAgICAgc2VsID0gY2FuZGlkYXRlc1soeCAqIDE3ICsgeSAqIDI5ICsgbGVuKHN0YWNrKSAqIDEzKSAlIGxlbihjYW5kaWRhdGVzKV0KICAgICAgICAgICAgbngsIG55LCB3eCwgd3kgPSBzZWwKICAgICAgICAgICAgZ3JpZFt3eV1bd3hdID0gMAogICAgICAgICAgICBncmlkW255XVtueF0gPSAwCiAgICAgICAgICAgIHN0YWNrLmFwcGVuZCgobngsIG55KSkKCiAgICAgICAgaWYgc3RlcCAlIGNhcHR1cmVfZXZlcnkgPT0gMDoKICAgICAgICAgICAgZnJhbWVzLmFwcGVuZChjYXB0dXJlKGdyaWQsIGNlbGxfdywgY2VsbF9oLCBzY2FsZSkpCiAgICAgICAgc3RlcCArPSAxCgogICAgZnJhbWVzLmFwcGVuZChjYXB0dXJlKGdyaWQsIGNlbGxfdywgY2VsbF9oLCBzY2FsZSkpCiAgICBzYXZlX2dpZihvdXRfcGF0aCwgY2VsbF93ICogc2NhbGUsIGNlbGxfaCAqIHNjYWxlLCBmcmFtZXMsIGdyYXlzY2FsZV9wYWxldHRlKCksIGRlbGF5X2NzPTQsIGxvb3A9MCkKICAgIGVsYXBzZWQgPSBwZXJmX2NvdW50ZXIoKSAtIHN0YXJ0CiAgICBwcmludCgib3V0cHV0OiIsIG91dF9wYXRoKQogICAgcHJpbnQoImZyYW1lczoiLCBsZW4oZnJhbWVzKSkKICAgIHByaW50KCJlbGFwc2VkX3NlYzoiLCBlbGFwc2VkKQoKCmlmIF9fbmFtZV9fID09ICJfX21haW5fXyI6CiAgICBydW5fMTNfbWF6ZV9nZW5lcmF0aW9uX3N0ZXBzKCkK"

        // main は埋め込み Python を実行するエントリポイント。
        @JvmStatic
        fun main(args: Array<String>) {
            val code: Int = PyRuntime.runEmbeddedPython(PYTRA_EMBEDDED_SOURCE_BASE64, args)
            kotlin.system.exitProcess(code)
        }
    }
}
