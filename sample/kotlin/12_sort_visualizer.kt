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

class pytra_12_sort_visualizer {
    companion object {
        // 埋め込み Python ソース（Base64）。
        private const val PYTRA_EMBEDDED_SOURCE_BASE64: String = "IyAxMjog44OQ44OW44Or44K944O844OI44Gu6YCU5Lit54q25oWL44KSR0lG5Ye65Yqb44GZ44KL44K144Oz44OX44Or44CCCgpmcm9tIF9fZnV0dXJlX18gaW1wb3J0IGFubm90YXRpb25zCgpmcm9tIHRpbWUgaW1wb3J0IHBlcmZfY291bnRlcgoKZnJvbSBweV9tb2R1bGUuZ2lmX2hlbHBlciBpbXBvcnQgZ3JheXNjYWxlX3BhbGV0dGUsIHNhdmVfZ2lmCgoKZGVmIHJlbmRlcih2YWx1ZXM6IGxpc3RbaW50XSwgdzogaW50LCBoOiBpbnQpIC0+IGJ5dGVzOgogICAgZnJhbWUgPSBieXRlYXJyYXkodyAqIGgpCiAgICBuID0gbGVuKHZhbHVlcykKICAgIGJhcl93ID0gdyAvIG4KICAgIGZvciBpIGluIHJhbmdlKG4pOgogICAgICAgIHgwID0gaW50KGkgKiBiYXJfdykKICAgICAgICB4MSA9IGludCgoaSArIDEpICogYmFyX3cpCiAgICAgICAgaWYgeDEgPD0geDA6CiAgICAgICAgICAgIHgxID0geDAgKyAxCiAgICAgICAgYmggPSBpbnQoKCh2YWx1ZXNbaV0gLyBuKSAqIGgpKQogICAgICAgIHkgPSBoIC0gYmgKICAgICAgICBmb3IgeSBpbiByYW5nZSh5LCBoKToKICAgICAgICAgICAgZm9yIHggaW4gcmFuZ2UoeDAsIHgxKToKICAgICAgICAgICAgICAgIGZyYW1lW3kgKiB3ICsgeF0gPSAyNTUKICAgIHJldHVybiBieXRlcyhmcmFtZSkKCgpkZWYgcnVuXzEyX3NvcnRfdmlzdWFsaXplcigpIC0+IE5vbmU6CiAgICB3ID0gMzIwCiAgICBoID0gMTgwCiAgICBuID0gMTI0CiAgICBvdXRfcGF0aCA9ICJzYW1wbGUvb3V0LzEyX3NvcnRfdmlzdWFsaXplci5naWYiCgogICAgc3RhcnQgPSBwZXJmX2NvdW50ZXIoKQogICAgdmFsdWVzOiBsaXN0W2ludF0gPSBbXQogICAgZm9yIGkgaW4gcmFuZ2Uobik6CiAgICAgICAgdmFsdWVzLmFwcGVuZCgoaSAqIDM3ICsgMTkpICUgbikKCiAgICBmcmFtZXM6IGxpc3RbYnl0ZXNdID0gW3JlbmRlcih2YWx1ZXMsIHcsIGgpXQoKICAgIG9wID0gMAogICAgZm9yIGkgaW4gcmFuZ2Uobik6CiAgICAgICAgc3dhcHBlZCA9IEZhbHNlCiAgICAgICAgZm9yIGogaW4gcmFuZ2UobiAtIGkgLSAxKToKICAgICAgICAgICAgaWYgdmFsdWVzW2pdID4gdmFsdWVzW2ogKyAxXToKICAgICAgICAgICAgICAgIHRtcCA9IHZhbHVlc1tqXQogICAgICAgICAgICAgICAgdmFsdWVzW2pdID0gdmFsdWVzW2ogKyAxXQogICAgICAgICAgICAgICAgdmFsdWVzW2ogKyAxXSA9IHRtcAogICAgICAgICAgICAgICAgc3dhcHBlZCA9IFRydWUKICAgICAgICAgICAgaWYgb3AgJSA4ID09IDA6CiAgICAgICAgICAgICAgICBmcmFtZXMuYXBwZW5kKHJlbmRlcih2YWx1ZXMsIHcsIGgpKQogICAgICAgICAgICBvcCArPSAxCiAgICAgICAgaWYgbm90IHN3YXBwZWQ6CiAgICAgICAgICAgIGJyZWFrCgogICAgc2F2ZV9naWYob3V0X3BhdGgsIHcsIGgsIGZyYW1lcywgZ3JheXNjYWxlX3BhbGV0dGUoKSwgZGVsYXlfY3M9MywgbG9vcD0wKQogICAgZWxhcHNlZCA9IHBlcmZfY291bnRlcigpIC0gc3RhcnQKICAgIHByaW50KCJvdXRwdXQ6Iiwgb3V0X3BhdGgpCiAgICBwcmludCgiZnJhbWVzOiIsIGxlbihmcmFtZXMpKQogICAgcHJpbnQoImVsYXBzZWRfc2VjOiIsIGVsYXBzZWQpCgoKaWYgX19uYW1lX18gPT0gIl9fbWFpbl9fIjoKICAgIHJ1bl8xMl9zb3J0X3Zpc3VhbGl6ZXIoKQo="

        // main は埋め込み Python を実行するエントリポイント。
        @JvmStatic
        fun main(args: Array<String>) {
            val code: Int = PyRuntime.runEmbeddedPython(PYTRA_EMBEDDED_SOURCE_BASE64, args)
            kotlin.system.exitProcess(code)
        }
    }
}
