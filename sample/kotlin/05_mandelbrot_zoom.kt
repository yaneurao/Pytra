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

class pytra_05_mandelbrot_zoom {
    companion object {
        // 埋め込み Python ソース（Base64）。
        private const val PYTRA_EMBEDDED_SOURCE_BASE64: String = "IyAwNTog44Oe44Oz44OH44Or44OW44Ot6ZuG5ZCI44K644O844Og44KS44Ki44OL44Oh44O844K344On44OzR0lG44Go44GX44Gm5Ye65Yqb44GZ44KL44K144Oz44OX44Or44CCCgpmcm9tIF9fZnV0dXJlX18gaW1wb3J0IGFubm90YXRpb25zCgpmcm9tIHRpbWUgaW1wb3J0IHBlcmZfY291bnRlcgoKZnJvbSBweV9tb2R1bGUuZ2lmX2hlbHBlciBpbXBvcnQgZ3JheXNjYWxlX3BhbGV0dGUsIHNhdmVfZ2lmCgoKZGVmIHJlbmRlcl9mcmFtZSh3aWR0aDogaW50LCBoZWlnaHQ6IGludCwgY2VudGVyX3g6IGZsb2F0LCBjZW50ZXJfeTogZmxvYXQsIHNjYWxlOiBmbG9hdCwgbWF4X2l0ZXI6IGludCkgLT4gYnl0ZXM6CiAgICBmcmFtZSA9IGJ5dGVhcnJheSh3aWR0aCAqIGhlaWdodCkKICAgIGlkeCA9IDAKICAgIGZvciB5IGluIHJhbmdlKGhlaWdodCk6CiAgICAgICAgY3kgPSBjZW50ZXJfeSArICh5IC0gaGVpZ2h0ICogMC41KSAqIHNjYWxlCiAgICAgICAgZm9yIHggaW4gcmFuZ2Uod2lkdGgpOgogICAgICAgICAgICBjeCA9IGNlbnRlcl94ICsgKHggLSB3aWR0aCAqIDAuNSkgKiBzY2FsZQogICAgICAgICAgICB6eCA9IDAuMAogICAgICAgICAgICB6eSA9IDAuMAogICAgICAgICAgICBpID0gMAogICAgICAgICAgICB3aGlsZSBpIDwgbWF4X2l0ZXI6CiAgICAgICAgICAgICAgICB6eDIgPSB6eCAqIHp4CiAgICAgICAgICAgICAgICB6eTIgPSB6eSAqIHp5CiAgICAgICAgICAgICAgICBpZiB6eDIgKyB6eTIgPiA0LjA6CiAgICAgICAgICAgICAgICAgICAgYnJlYWsKICAgICAgICAgICAgICAgIHp5ID0gMi4wICogenggKiB6eSArIGN5CiAgICAgICAgICAgICAgICB6eCA9IHp4MiAtIHp5MiArIGN4CiAgICAgICAgICAgICAgICBpICs9IDEKICAgICAgICAgICAgZnJhbWVbaWR4XSA9IGludCgoMjU1LjAgKiBpKSAvIG1heF9pdGVyKQogICAgICAgICAgICBpZHggKz0gMQogICAgcmV0dXJuIGJ5dGVzKGZyYW1lKQoKCmRlZiBydW5fMDVfbWFuZGVsYnJvdF96b29tKCkgLT4gTm9uZToKICAgIHdpZHRoID0gMzIwCiAgICBoZWlnaHQgPSAyNDAKICAgIGZyYW1lX2NvdW50ID0gNDgKICAgIG1heF9pdGVyID0gMTEwCiAgICBjZW50ZXJfeCA9IC0wLjc0MzY0Mzg4NzAzNzE1MQogICAgY2VudGVyX3kgPSAwLjEzMTgyNTkwNDIwNTMzCiAgICBiYXNlX3NjYWxlID0gMy4yIC8gd2lkdGgKICAgIHpvb21fcGVyX2ZyYW1lID0gMC45MwogICAgb3V0X3BhdGggPSAic2FtcGxlL291dC8wNV9tYW5kZWxicm90X3pvb20uZ2lmIgoKICAgIHN0YXJ0ID0gcGVyZl9jb3VudGVyKCkKICAgIGZyYW1lczogbGlzdFtieXRlc10gPSBbXQogICAgc2NhbGUgPSBiYXNlX3NjYWxlCiAgICBmb3IgXyBpbiByYW5nZShmcmFtZV9jb3VudCk6CiAgICAgICAgZnJhbWVzLmFwcGVuZChyZW5kZXJfZnJhbWUod2lkdGgsIGhlaWdodCwgY2VudGVyX3gsIGNlbnRlcl95LCBzY2FsZSwgbWF4X2l0ZXIpKQogICAgICAgIHNjYWxlICo9IHpvb21fcGVyX2ZyYW1lCgogICAgc2F2ZV9naWYob3V0X3BhdGgsIHdpZHRoLCBoZWlnaHQsIGZyYW1lcywgZ3JheXNjYWxlX3BhbGV0dGUoKSwgZGVsYXlfY3M9NSwgbG9vcD0wKQogICAgZWxhcHNlZCA9IHBlcmZfY291bnRlcigpIC0gc3RhcnQKICAgIHByaW50KCJvdXRwdXQ6Iiwgb3V0X3BhdGgpCiAgICBwcmludCgiZnJhbWVzOiIsIGZyYW1lX2NvdW50KQogICAgcHJpbnQoImVsYXBzZWRfc2VjOiIsIGVsYXBzZWQpCgoKaWYgX19uYW1lX18gPT0gIl9fbWFpbl9fIjoKICAgIHJ1bl8wNV9tYW5kZWxicm90X3pvb20oKQo="

        // main は埋め込み Python を実行するエントリポイント。
        @JvmStatic
        fun main(args: Array<String>) {
            val code: Int = PyRuntime.runEmbeddedPython(PYTRA_EMBEDDED_SOURCE_BASE64, args)
            kotlin.system.exitProcess(code)
        }
    }
}
