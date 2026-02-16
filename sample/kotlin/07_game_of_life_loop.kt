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

class pytra_07_game_of_life_loop {
    companion object {
        // 埋め込み Python ソース（Base64）。
        private const val PYTRA_EMBEDDED_SOURCE_BASE64: String = "IyAwNzogR2FtZSBvZiBMaWZlIOOBrumAsuWMluOCkkdJRuWHuuWKm+OBmeOCi+OCteODs+ODl+ODq+OAggoKZnJvbSBfX2Z1dHVyZV9fIGltcG9ydCBhbm5vdGF0aW9ucwoKZnJvbSB0aW1lIGltcG9ydCBwZXJmX2NvdW50ZXIKCmZyb20gcHlfbW9kdWxlLmdpZl9oZWxwZXIgaW1wb3J0IGdyYXlzY2FsZV9wYWxldHRlLCBzYXZlX2dpZgoKCmRlZiBuZXh0X3N0YXRlKGdyaWQ6IGxpc3RbbGlzdFtpbnRdXSwgdzogaW50LCBoOiBpbnQpIC0+IGxpc3RbbGlzdFtpbnRdXToKICAgIG54dDogbGlzdFtsaXN0W2ludF1dID0gW10KICAgIGZvciB5IGluIHJhbmdlKGgpOgogICAgICAgIHJvdzogbGlzdFtpbnRdID0gW10KICAgICAgICBmb3IgeCBpbiByYW5nZSh3KToKICAgICAgICAgICAgY250ID0gMAogICAgICAgICAgICBmb3IgZHkgaW4gcmFuZ2UoLTEsIDIpOgogICAgICAgICAgICAgICAgZm9yIGR4IGluIHJhbmdlKC0xLCAyKToKICAgICAgICAgICAgICAgICAgICBpZiBkeCAhPSAwIG9yIGR5ICE9IDA6CiAgICAgICAgICAgICAgICAgICAgICAgIG54ID0gKHggKyBkeCArIHcpICUgdwogICAgICAgICAgICAgICAgICAgICAgICBueSA9ICh5ICsgZHkgKyBoKSAlIGgKICAgICAgICAgICAgICAgICAgICAgICAgY250ICs9IGdyaWRbbnldW254XQogICAgICAgICAgICBhbGl2ZSA9IGdyaWRbeV1beF0KICAgICAgICAgICAgaWYgYWxpdmUgPT0gMSBhbmQgKGNudCA9PSAyIG9yIGNudCA9PSAzKToKICAgICAgICAgICAgICAgIHJvdy5hcHBlbmQoMSkKICAgICAgICAgICAgZWxpZiBhbGl2ZSA9PSAwIGFuZCBjbnQgPT0gMzoKICAgICAgICAgICAgICAgIHJvdy5hcHBlbmQoMSkKICAgICAgICAgICAgZWxzZToKICAgICAgICAgICAgICAgIHJvdy5hcHBlbmQoMCkKICAgICAgICBueHQuYXBwZW5kKHJvdykKICAgIHJldHVybiBueHQKCgpkZWYgcmVuZGVyKGdyaWQ6IGxpc3RbbGlzdFtpbnRdXSwgdzogaW50LCBoOiBpbnQsIGNlbGw6IGludCkgLT4gYnl0ZXM6CiAgICB3aWR0aCA9IHcgKiBjZWxsCiAgICBoZWlnaHQgPSBoICogY2VsbAogICAgZnJhbWUgPSBieXRlYXJyYXkod2lkdGggKiBoZWlnaHQpCiAgICBmb3IgeSBpbiByYW5nZShoKToKICAgICAgICBmb3IgeCBpbiByYW5nZSh3KToKICAgICAgICAgICAgdiA9IDI1NSBpZiBncmlkW3ldW3hdIGVsc2UgMAogICAgICAgICAgICBmb3IgeXkgaW4gcmFuZ2UoY2VsbCk6CiAgICAgICAgICAgICAgICBiYXNlID0gKHkgKiBjZWxsICsgeXkpICogd2lkdGggKyB4ICogY2VsbAogICAgICAgICAgICAgICAgZm9yIHh4IGluIHJhbmdlKGNlbGwpOgogICAgICAgICAgICAgICAgICAgIGZyYW1lW2Jhc2UgKyB4eF0gPSB2CiAgICByZXR1cm4gYnl0ZXMoZnJhbWUpCgoKZGVmIHJ1bl8wN19nYW1lX29mX2xpZmVfbG9vcCgpIC0+IE5vbmU6CiAgICB3ID0gMTQ0CiAgICBoID0gMTA4CiAgICBjZWxsID0gNAogICAgc3RlcHMgPSAyMTAKICAgIG91dF9wYXRoID0gInNhbXBsZS9vdXQvMDdfZ2FtZV9vZl9saWZlX2xvb3AuZ2lmIgoKICAgIHN0YXJ0ID0gcGVyZl9jb3VudGVyKCkKICAgIGdyaWQ6IGxpc3RbbGlzdFtpbnRdXSA9IFtdCiAgICBmb3IgXyBpbiByYW5nZShoKToKICAgICAgICByb3c6IGxpc3RbaW50XSA9IFtdCiAgICAgICAgZm9yIF8gaW4gcmFuZ2Uodyk6CiAgICAgICAgICAgIHJvdy5hcHBlbmQoMCkKICAgICAgICBncmlkLmFwcGVuZChyb3cpCgogICAgIyDnlo7jgarjg47jgqTjgrrjgpLmlbfjgYTjgabjgIHlhajkvZPjgYzml6nmnJ/jgavlm7rlrprljJbjgZfjgavjgY/jgYTlnJ/lj7DjgpLkvZzjgovjgIIKICAgICMg5aSn44GN44Gq5pW05pWw44Oq44OG44Op44Or44KS5L2/44KP44Gq44GE5byP44Gr44GX44Gm44CB5ZCE44OI44Op44Oz44K544OR44Kk44Op44Gn5ZCM5LiA44Gr5omx44GI44KL44KI44GG44Gr44GZ44KL44CCCiAgICBmb3IgeSBpbiByYW5nZShoKToKICAgICAgICBmb3IgeCBpbiByYW5nZSh3KToKICAgICAgICAgICAgbm9pc2UgPSAoeCAqIDM3ICsgeSAqIDczICsgKHggKiB5KSAlIDE5ICsgKHggKyB5KSAlIDExKSAlIDk3CiAgICAgICAgICAgIGlmIG5vaXNlIDwgMzoKICAgICAgICAgICAgICAgIGdyaWRbeV1beF0gPSAxCgogICAgIyDku6PooajnmoTjgarplbflr7/lkb3jg5Hjgr/jg7zjg7PjgpLopIfmlbDphY3nva7jgZnjgovjgIIKICAgIGdsaWRlciA9IFsKICAgICAgICBbMCwgMSwgMF0sCiAgICAgICAgWzAsIDAsIDFdLAogICAgICAgIFsxLCAxLCAxXSwKICAgIF0KICAgIHJfcGVudG9taW5vID0gWwogICAgICAgIFswLCAxLCAxXSwKICAgICAgICBbMSwgMSwgMF0sCiAgICAgICAgWzAsIDEsIDBdLAogICAgXQogICAgbHdzcyA9IFsKICAgICAgICBbMCwgMSwgMSwgMSwgMV0sCiAgICAgICAgWzEsIDAsIDAsIDAsIDFdLAogICAgICAgIFswLCAwLCAwLCAwLCAxXSwKICAgICAgICBbMSwgMCwgMCwgMSwgMF0sCiAgICBdCgogICAgZm9yIGd5IGluIHJhbmdlKDgsIGggLSA4LCAxOCk6CiAgICAgICAgZm9yIGd4IGluIHJhbmdlKDgsIHcgLSA4LCAyMik6CiAgICAgICAgICAgIGtpbmQgPSAoZ3ggKiA3ICsgZ3kgKiAxMSkgJSAzCiAgICAgICAgICAgIGlmIGtpbmQgPT0gMDoKICAgICAgICAgICAgICAgIHBoID0gbGVuKGdsaWRlcikKICAgICAgICAgICAgICAgIGZvciBweSBpbiByYW5nZShwaCk6CiAgICAgICAgICAgICAgICAgICAgcHcgPSBsZW4oZ2xpZGVyW3B5XSkKICAgICAgICAgICAgICAgICAgICBmb3IgcHggaW4gcmFuZ2UocHcpOgogICAgICAgICAgICAgICAgICAgICAgICBpZiBnbGlkZXJbcHldW3B4XSA9PSAxOgogICAgICAgICAgICAgICAgICAgICAgICAgICAgZ3JpZFsoZ3kgKyBweSkgJSBoXVsoZ3ggKyBweCkgJSB3XSA9IDEKICAgICAgICAgICAgZWxpZiBraW5kID09IDE6CiAgICAgICAgICAgICAgICBwaCA9IGxlbihyX3BlbnRvbWlubykKICAgICAgICAgICAgICAgIGZvciBweSBpbiByYW5nZShwaCk6CiAgICAgICAgICAgICAgICAgICAgcHcgPSBsZW4ocl9wZW50b21pbm9bcHldKQogICAgICAgICAgICAgICAgICAgIGZvciBweCBpbiByYW5nZShwdyk6CiAgICAgICAgICAgICAgICAgICAgICAgIGlmIHJfcGVudG9taW5vW3B5XVtweF0gPT0gMToKICAgICAgICAgICAgICAgICAgICAgICAgICAgIGdyaWRbKGd5ICsgcHkpICUgaF1bKGd4ICsgcHgpICUgd10gPSAxCiAgICAgICAgICAgIGVsc2U6CiAgICAgICAgICAgICAgICBwaCA9IGxlbihsd3NzKQogICAgICAgICAgICAgICAgZm9yIHB5IGluIHJhbmdlKHBoKToKICAgICAgICAgICAgICAgICAgICBwdyA9IGxlbihsd3NzW3B5XSkKICAgICAgICAgICAgICAgICAgICBmb3IgcHggaW4gcmFuZ2UocHcpOgogICAgICAgICAgICAgICAgICAgICAgICBpZiBsd3NzW3B5XVtweF0gPT0gMToKICAgICAgICAgICAgICAgICAgICAgICAgICAgIGdyaWRbKGd5ICsgcHkpICUgaF1bKGd4ICsgcHgpICUgd10gPSAxCgogICAgZnJhbWVzOiBsaXN0W2J5dGVzXSA9IFtdCiAgICBmb3IgXyBpbiByYW5nZShzdGVwcyk6CiAgICAgICAgZnJhbWVzLmFwcGVuZChyZW5kZXIoZ3JpZCwgdywgaCwgY2VsbCkpCiAgICAgICAgZ3JpZCA9IG5leHRfc3RhdGUoZ3JpZCwgdywgaCkKCiAgICBzYXZlX2dpZihvdXRfcGF0aCwgdyAqIGNlbGwsIGggKiBjZWxsLCBmcmFtZXMsIGdyYXlzY2FsZV9wYWxldHRlKCksIGRlbGF5X2NzPTQsIGxvb3A9MCkKICAgIGVsYXBzZWQgPSBwZXJmX2NvdW50ZXIoKSAtIHN0YXJ0CiAgICBwcmludCgib3V0cHV0OiIsIG91dF9wYXRoKQogICAgcHJpbnQoImZyYW1lczoiLCBzdGVwcykKICAgIHByaW50KCJlbGFwc2VkX3NlYzoiLCBlbGFwc2VkKQoKCmlmIF9fbmFtZV9fID09ICJfX21haW5fXyI6CiAgICBydW5fMDdfZ2FtZV9vZl9saWZlX2xvb3AoKQo="

        // main は埋め込み Python を実行するエントリポイント。
        @JvmStatic
        fun main(args: Array<String>) {
            val code: Int = PyRuntime.runEmbeddedPython(PYTRA_EMBEDDED_SOURCE_BASE64, args)
            kotlin.system.exitProcess(code)
        }
    }
}
