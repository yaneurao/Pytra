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

class pytra_01_mandelbrot {
    companion object {
        // 埋め込み Python ソース（Base64）。
        private const val PYTRA_EMBEDDED_SOURCE_BASE64: String = "IyAwMTog44Oe44Oz44OH44Or44OW44Ot6ZuG5ZCI44KSIFBORyDnlLvlg4/jgajjgZfjgablh7rlipvjgZnjgovjgrXjg7Pjg5fjg6vjgafjgZnjgIIKIyDlsIbmnaXjga7jg4jjg6njg7Pjgrnjg5HjgqTjg6vjgpLmhI/orZjjgZfjgabjgIHmp4vmlofjga/jgarjgovjgbnjgY/ntKDnm7Tjgavmm7jjgYTjgabjgYTjgb7jgZnjgIIKCmZyb20gdGltZSBpbXBvcnQgcGVyZl9jb3VudGVyCmZyb20gcHlfbW9kdWxlIGltcG9ydCBwbmdfaGVscGVyCgoKZGVmIGVzY2FwZV9jb3VudChjeDogZmxvYXQsIGN5OiBmbG9hdCwgbWF4X2l0ZXI6IGludCkgLT4gaW50OgogICAgIiIiMeeCuSAoY3gsIGN5KSDjga7nmbrmlaPjgb7jgafjga7lj43lvqnlm57mlbDjgpLov5TjgZnjgIIiIiIKICAgIHg6IGZsb2F0ID0gMC4wCiAgICB5OiBmbG9hdCA9IDAuMAogICAgZm9yIGkgaW4gcmFuZ2UobWF4X2l0ZXIpOgogICAgICAgIHgyOiBmbG9hdCA9IHggKiB4CiAgICAgICAgeTI6IGZsb2F0ID0geSAqIHkKICAgICAgICBpZiB4MiArIHkyID4gNC4wOgogICAgICAgICAgICByZXR1cm4gaQogICAgICAgIHkgPSAyLjAgKiB4ICogeSArIGN5CiAgICAgICAgeCA9IHgyIC0geTIgKyBjeAogICAgcmV0dXJuIG1heF9pdGVyCgoKZGVmIGNvbG9yX21hcChpdGVyX2NvdW50OiBpbnQsIG1heF9pdGVyOiBpbnQpIC0+IHR1cGxlW2ludCwgaW50LCBpbnRdOgogICAgIiIi5Y+N5b6p5Zue5pWw44KSIFJHQiDjgavlpInmj5vjgZnjgovjgIIiIiIKICAgIGlmIGl0ZXJfY291bnQgPj0gbWF4X2l0ZXI6CiAgICAgICAgcmV0dXJuICgwLCAwLCAwKQoKICAgICMg57Ch5Y2Y44Gq44Kw44Op44OH44O844K344On44Oz77yI6Z2S57O7IC0+IOm7hOezu++8iQogICAgdDogZmxvYXQgPSBpdGVyX2NvdW50IC8gbWF4X2l0ZXIKICAgIHI6IGludCA9IGludCgyNTUuMCAqICh0ICogdCkpCiAgICBnOiBpbnQgPSBpbnQoMjU1LjAgKiB0KQogICAgYjogaW50ID0gaW50KDI1NS4wICogKDEuMCAtIHQpKQogICAgcmV0dXJuIChyLCBnLCBiKQoKCmRlZiByZW5kZXJfbWFuZGVsYnJvdCgKICAgIHdpZHRoOiBpbnQsCiAgICBoZWlnaHQ6IGludCwKICAgIG1heF9pdGVyOiBpbnQsCiAgICB4X21pbjogZmxvYXQsCiAgICB4X21heDogZmxvYXQsCiAgICB5X21pbjogZmxvYXQsCiAgICB5X21heDogZmxvYXQsCikgLT4gYnl0ZWFycmF5OgogICAgIiIi44Oe44Oz44OH44Or44OW44Ot55S75YOP44GuIFJHQiDjg5DjgqTjg4jliJfjgpLnlJ/miJDjgZnjgovjgIIiIiIKICAgIHBpeGVsczogYnl0ZWFycmF5ID0gYnl0ZWFycmF5KCkKCiAgICBmb3IgeSBpbiByYW5nZShoZWlnaHQpOgogICAgICAgIHB5OiBmbG9hdCA9IHlfbWluICsgKHlfbWF4IC0geV9taW4pICogKHkgLyAoaGVpZ2h0IC0gMSkpCgogICAgICAgIGZvciB4IGluIHJhbmdlKHdpZHRoKToKICAgICAgICAgICAgcHg6IGZsb2F0ID0geF9taW4gKyAoeF9tYXggLSB4X21pbikgKiAoeCAvICh3aWR0aCAtIDEpKQogICAgICAgICAgICBpdDogaW50ID0gZXNjYXBlX2NvdW50KHB4LCBweSwgbWF4X2l0ZXIpCiAgICAgICAgICAgIHI6IGludAogICAgICAgICAgICBnOiBpbnQKICAgICAgICAgICAgYjogaW50CiAgICAgICAgICAgIGlmIGl0ID49IG1heF9pdGVyOgogICAgICAgICAgICAgICAgciA9IDAKICAgICAgICAgICAgICAgIGcgPSAwCiAgICAgICAgICAgICAgICBiID0gMAogICAgICAgICAgICBlbHNlOgogICAgICAgICAgICAgICAgdDogZmxvYXQgPSBpdCAvIG1heF9pdGVyCiAgICAgICAgICAgICAgICByID0gaW50KDI1NS4wICogKHQgKiB0KSkKICAgICAgICAgICAgICAgIGcgPSBpbnQoMjU1LjAgKiB0KQogICAgICAgICAgICAgICAgYiA9IGludCgyNTUuMCAqICgxLjAgLSB0KSkKICAgICAgICAgICAgcGl4ZWxzLmFwcGVuZChyKQogICAgICAgICAgICBwaXhlbHMuYXBwZW5kKGcpCiAgICAgICAgICAgIHBpeGVscy5hcHBlbmQoYikKCiAgICByZXR1cm4gcGl4ZWxzCgoKZGVmIHJ1bl9tYW5kZWxicm90KCkgLT4gTm9uZToKICAgIHdpZHRoOiBpbnQgPSAxNjAwCiAgICBoZWlnaHQ6IGludCA9IDEyMDAKICAgIG1heF9pdGVyOiBpbnQgPSAxMDAwCiAgICBvdXRfcGF0aDogc3RyID0gInNhbXBsZS9vdXQvbWFuZGVsYnJvdF8wMS5wbmciCgogICAgc3RhcnQ6IGZsb2F0ID0gcGVyZl9jb3VudGVyKCkKCiAgICBwaXhlbHM6IGJ5dGVhcnJheSA9IHJlbmRlcl9tYW5kZWxicm90KAogICAgICAgIHdpZHRoLAogICAgICAgIGhlaWdodCwKICAgICAgICBtYXhfaXRlciwKICAgICAgICAtMi4yLAogICAgICAgIDEuMCwKICAgICAgICAtMS4yLAogICAgICAgIDEuMiwKICAgICkKICAgIHBuZ19oZWxwZXIud3JpdGVfcmdiX3BuZyhvdXRfcGF0aCwgd2lkdGgsIGhlaWdodCwgcGl4ZWxzKQoKICAgIGVsYXBzZWQ6IGZsb2F0ID0gcGVyZl9jb3VudGVyKCkgLSBzdGFydAogICAgcHJpbnQoIm91dHB1dDoiLCBvdXRfcGF0aCkKICAgIHByaW50KCJzaXplOiIsIHdpZHRoLCAieCIsIGhlaWdodCkKICAgIHByaW50KCJtYXhfaXRlcjoiLCBtYXhfaXRlcikKICAgIHByaW50KCJlbGFwc2VkX3NlYzoiLCBlbGFwc2VkKQoKCmlmIF9fbmFtZV9fID09ICJfX21haW5fXyI6CiAgICBydW5fbWFuZGVsYnJvdCgpCg=="

        // main は埋め込み Python を実行するエントリポイント。
        @JvmStatic
        fun main(args: Array<String>) {
            val code: Int = PyRuntime.runEmbeddedPython(PYTRA_EMBEDDED_SOURCE_BASE64, args)
            kotlin.system.exitProcess(code)
        }
    }
}
