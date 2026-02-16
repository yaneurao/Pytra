// このファイルは自動生成です（Python -> Java embedded mode）。

// Python 埋め込み実行向けの Java ランタイム補助。
// 生成された Java コードから呼び出し、Python ソースを一時ファイルに展開して実行する。

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Base64;
import java.util.List;
import java.util.Map;

final class PyRuntime {
    private PyRuntime() {
    }

    // runEmbeddedPython は、Base64 で埋め込まれた Python ソースを実行する。
    //
    // Args:
    //   sourceBase64: 埋め込み Python ソースコード（Base64 文字列）。
    //   args: Python スクリプトへ渡す引数。
    //
    // Returns:
    //   Python プロセスの終了コード。異常時は 1 を返す。
    static int runEmbeddedPython(String sourceBase64, String[] args) {
        byte[] sourceBytes;
        try {
            sourceBytes = Base64.getDecoder().decode(sourceBase64);
        } catch (IllegalArgumentException ex) {
            System.err.println("error: failed to decode embedded python source");
            return 1;
        }

        Path tempDir;
        try {
            tempDir = Files.createTempDirectory("pytra_java_");
        } catch (IOException ex) {
            System.err.println("error: failed to create temp directory");
            return 1;
        }

        Path scriptPath = tempDir.resolve("embedded.py");
        try {
            Files.writeString(scriptPath, new String(sourceBytes, StandardCharsets.UTF_8), StandardCharsets.UTF_8);
        } catch (IOException ex) {
            System.err.println("error: failed to write temp python script");
            return 1;
        }

        String pythonPath = "src";
        String currentPythonPath = System.getenv("PYTHONPATH");
        if (currentPythonPath != null && !currentPythonPath.isEmpty()) {
            pythonPath = pythonPath + System.getProperty("path.separator") + currentPythonPath;
        }

        int code = runInterpreter("python3", scriptPath, args, pythonPath);
        if (code != Integer.MIN_VALUE) {
            return code;
        }

        code = runInterpreter("python", scriptPath, args, pythonPath);
        if (code != Integer.MIN_VALUE) {
            return code;
        }

        System.err.println("error: python interpreter not found (python3/python)");
        return 1;
    }

    // runInterpreter は 1 つの Python 実行コマンドを試行する。
    //
    // Returns:
    //   実行できた場合は終了コード。
    //   コマンドが存在しない場合は Integer.MIN_VALUE。
    private static int runInterpreter(String interpreter, Path scriptPath, String[] args, String pythonPath) {
        List<String> command = new ArrayList<>();
        command.add(interpreter);
        command.add(scriptPath.toString());
        for (String arg : args) {
            command.add(arg);
        }

        ProcessBuilder builder = new ProcessBuilder(command);
        builder.inheritIO();
        Map<String, String> env = builder.environment();
        env.put("PYTHONPATH", pythonPath);

        Process process;
        try {
            process = builder.start();
        } catch (IOException ex) {
            return Integer.MIN_VALUE;
        }

        try {
            return process.waitFor();
        } catch (InterruptedException ex) {
            Thread.currentThread().interrupt();
            return 1;
        }
    }
}

final class pytra_07_game_of_life_loop {
    // 埋め込み Python ソース（Base64）。
    private static final String PYTRA_EMBEDDED_SOURCE_BASE64 = "IyAwNzogR2FtZSBvZiBMaWZlIOOBrumAsuWMluOCkkdJRuWHuuWKm+OBmeOCi+OCteODs+ODl+ODq+OAggoKZnJvbSBfX2Z1dHVyZV9fIGltcG9ydCBhbm5vdGF0aW9ucwoKZnJvbSB0aW1lIGltcG9ydCBwZXJmX2NvdW50ZXIKCmZyb20gcHlfbW9kdWxlLmdpZl9oZWxwZXIgaW1wb3J0IGdyYXlzY2FsZV9wYWxldHRlLCBzYXZlX2dpZgoKCmRlZiBuZXh0X3N0YXRlKGdyaWQ6IGxpc3RbbGlzdFtpbnRdXSwgdzogaW50LCBoOiBpbnQpIC0+IGxpc3RbbGlzdFtpbnRdXToKICAgIG54dDogbGlzdFtsaXN0W2ludF1dID0gW10KICAgIGZvciB5IGluIHJhbmdlKGgpOgogICAgICAgIHJvdzogbGlzdFtpbnRdID0gW10KICAgICAgICBmb3IgeCBpbiByYW5nZSh3KToKICAgICAgICAgICAgY250ID0gMAogICAgICAgICAgICBmb3IgZHkgaW4gcmFuZ2UoLTEsIDIpOgogICAgICAgICAgICAgICAgZm9yIGR4IGluIHJhbmdlKC0xLCAyKToKICAgICAgICAgICAgICAgICAgICBpZiBkeCAhPSAwIG9yIGR5ICE9IDA6CiAgICAgICAgICAgICAgICAgICAgICAgIG54ID0gKHggKyBkeCArIHcpICUgdwogICAgICAgICAgICAgICAgICAgICAgICBueSA9ICh5ICsgZHkgKyBoKSAlIGgKICAgICAgICAgICAgICAgICAgICAgICAgY250ICs9IGdyaWRbbnldW254XQogICAgICAgICAgICBhbGl2ZSA9IGdyaWRbeV1beF0KICAgICAgICAgICAgaWYgYWxpdmUgPT0gMSBhbmQgKGNudCA9PSAyIG9yIGNudCA9PSAzKToKICAgICAgICAgICAgICAgIHJvdy5hcHBlbmQoMSkKICAgICAgICAgICAgZWxpZiBhbGl2ZSA9PSAwIGFuZCBjbnQgPT0gMzoKICAgICAgICAgICAgICAgIHJvdy5hcHBlbmQoMSkKICAgICAgICAgICAgZWxzZToKICAgICAgICAgICAgICAgIHJvdy5hcHBlbmQoMCkKICAgICAgICBueHQuYXBwZW5kKHJvdykKICAgIHJldHVybiBueHQKCgpkZWYgcmVuZGVyKGdyaWQ6IGxpc3RbbGlzdFtpbnRdXSwgdzogaW50LCBoOiBpbnQsIGNlbGw6IGludCkgLT4gYnl0ZXM6CiAgICB3aWR0aCA9IHcgKiBjZWxsCiAgICBoZWlnaHQgPSBoICogY2VsbAogICAgZnJhbWUgPSBieXRlYXJyYXkod2lkdGggKiBoZWlnaHQpCiAgICBmb3IgeSBpbiByYW5nZShoKToKICAgICAgICBmb3IgeCBpbiByYW5nZSh3KToKICAgICAgICAgICAgdiA9IDI1NSBpZiBncmlkW3ldW3hdIGVsc2UgMAogICAgICAgICAgICBmb3IgeXkgaW4gcmFuZ2UoY2VsbCk6CiAgICAgICAgICAgICAgICBiYXNlID0gKHkgKiBjZWxsICsgeXkpICogd2lkdGggKyB4ICogY2VsbAogICAgICAgICAgICAgICAgZm9yIHh4IGluIHJhbmdlKGNlbGwpOgogICAgICAgICAgICAgICAgICAgIGZyYW1lW2Jhc2UgKyB4eF0gPSB2CiAgICByZXR1cm4gYnl0ZXMoZnJhbWUpCgoKZGVmIHJ1bl8wN19nYW1lX29mX2xpZmVfbG9vcCgpIC0+IE5vbmU6CiAgICB3ID0gMTQ0CiAgICBoID0gMTA4CiAgICBjZWxsID0gNAogICAgc3RlcHMgPSAyMTAKICAgIG91dF9wYXRoID0gInNhbXBsZS9vdXQvMDdfZ2FtZV9vZl9saWZlX2xvb3AuZ2lmIgoKICAgIHN0YXJ0ID0gcGVyZl9jb3VudGVyKCkKICAgIGdyaWQ6IGxpc3RbbGlzdFtpbnRdXSA9IFtdCiAgICBmb3IgXyBpbiByYW5nZShoKToKICAgICAgICByb3c6IGxpc3RbaW50XSA9IFtdCiAgICAgICAgZm9yIF8gaW4gcmFuZ2Uodyk6CiAgICAgICAgICAgIHJvdy5hcHBlbmQoMCkKICAgICAgICBncmlkLmFwcGVuZChyb3cpCgogICAgIyDnlo7jgarjg47jgqTjgrrjgpLmlbfjgYTjgabjgIHlhajkvZPjgYzml6nmnJ/jgavlm7rlrprljJbjgZfjgavjgY/jgYTlnJ/lj7DjgpLkvZzjgovjgIIKICAgICMg5aSn44GN44Gq5pW05pWw44Oq44OG44Op44Or44KS5L2/44KP44Gq44GE5byP44Gr44GX44Gm44CB5ZCE44OI44Op44Oz44K544OR44Kk44Op44Gn5ZCM5LiA44Gr5omx44GI44KL44KI44GG44Gr44GZ44KL44CCCiAgICBmb3IgeSBpbiByYW5nZShoKToKICAgICAgICBmb3IgeCBpbiByYW5nZSh3KToKICAgICAgICAgICAgbm9pc2UgPSAoeCAqIDM3ICsgeSAqIDczICsgKHggKiB5KSAlIDE5ICsgKHggKyB5KSAlIDExKSAlIDk3CiAgICAgICAgICAgIGlmIG5vaXNlIDwgMzoKICAgICAgICAgICAgICAgIGdyaWRbeV1beF0gPSAxCgogICAgIyDku6PooajnmoTjgarplbflr7/lkb3jg5Hjgr/jg7zjg7PjgpLopIfmlbDphY3nva7jgZnjgovjgIIKICAgIGdsaWRlciA9IFsKICAgICAgICBbMCwgMSwgMF0sCiAgICAgICAgWzAsIDAsIDFdLAogICAgICAgIFsxLCAxLCAxXSwKICAgIF0KICAgIHJfcGVudG9taW5vID0gWwogICAgICAgIFswLCAxLCAxXSwKICAgICAgICBbMSwgMSwgMF0sCiAgICAgICAgWzAsIDEsIDBdLAogICAgXQogICAgbHdzcyA9IFsKICAgICAgICBbMCwgMSwgMSwgMSwgMV0sCiAgICAgICAgWzEsIDAsIDAsIDAsIDFdLAogICAgICAgIFswLCAwLCAwLCAwLCAxXSwKICAgICAgICBbMSwgMCwgMCwgMSwgMF0sCiAgICBdCgogICAgZm9yIGd5IGluIHJhbmdlKDgsIGggLSA4LCAxOCk6CiAgICAgICAgZm9yIGd4IGluIHJhbmdlKDgsIHcgLSA4LCAyMik6CiAgICAgICAgICAgIGtpbmQgPSAoZ3ggKiA3ICsgZ3kgKiAxMSkgJSAzCiAgICAgICAgICAgIGlmIGtpbmQgPT0gMDoKICAgICAgICAgICAgICAgIHBoID0gbGVuKGdsaWRlcikKICAgICAgICAgICAgICAgIGZvciBweSBpbiByYW5nZShwaCk6CiAgICAgICAgICAgICAgICAgICAgcHcgPSBsZW4oZ2xpZGVyW3B5XSkKICAgICAgICAgICAgICAgICAgICBmb3IgcHggaW4gcmFuZ2UocHcpOgogICAgICAgICAgICAgICAgICAgICAgICBpZiBnbGlkZXJbcHldW3B4XSA9PSAxOgogICAgICAgICAgICAgICAgICAgICAgICAgICAgZ3JpZFsoZ3kgKyBweSkgJSBoXVsoZ3ggKyBweCkgJSB3XSA9IDEKICAgICAgICAgICAgZWxpZiBraW5kID09IDE6CiAgICAgICAgICAgICAgICBwaCA9IGxlbihyX3BlbnRvbWlubykKICAgICAgICAgICAgICAgIGZvciBweSBpbiByYW5nZShwaCk6CiAgICAgICAgICAgICAgICAgICAgcHcgPSBsZW4ocl9wZW50b21pbm9bcHldKQogICAgICAgICAgICAgICAgICAgIGZvciBweCBpbiByYW5nZShwdyk6CiAgICAgICAgICAgICAgICAgICAgICAgIGlmIHJfcGVudG9taW5vW3B5XVtweF0gPT0gMToKICAgICAgICAgICAgICAgICAgICAgICAgICAgIGdyaWRbKGd5ICsgcHkpICUgaF1bKGd4ICsgcHgpICUgd10gPSAxCiAgICAgICAgICAgIGVsc2U6CiAgICAgICAgICAgICAgICBwaCA9IGxlbihsd3NzKQogICAgICAgICAgICAgICAgZm9yIHB5IGluIHJhbmdlKHBoKToKICAgICAgICAgICAgICAgICAgICBwdyA9IGxlbihsd3NzW3B5XSkKICAgICAgICAgICAgICAgICAgICBmb3IgcHggaW4gcmFuZ2UocHcpOgogICAgICAgICAgICAgICAgICAgICAgICBpZiBsd3NzW3B5XVtweF0gPT0gMToKICAgICAgICAgICAgICAgICAgICAgICAgICAgIGdyaWRbKGd5ICsgcHkpICUgaF1bKGd4ICsgcHgpICUgd10gPSAxCgogICAgZnJhbWVzOiBsaXN0W2J5dGVzXSA9IFtdCiAgICBmb3IgXyBpbiByYW5nZShzdGVwcyk6CiAgICAgICAgZnJhbWVzLmFwcGVuZChyZW5kZXIoZ3JpZCwgdywgaCwgY2VsbCkpCiAgICAgICAgZ3JpZCA9IG5leHRfc3RhdGUoZ3JpZCwgdywgaCkKCiAgICBzYXZlX2dpZihvdXRfcGF0aCwgdyAqIGNlbGwsIGggKiBjZWxsLCBmcmFtZXMsIGdyYXlzY2FsZV9wYWxldHRlKCksIGRlbGF5X2NzPTQsIGxvb3A9MCkKICAgIGVsYXBzZWQgPSBwZXJmX2NvdW50ZXIoKSAtIHN0YXJ0CiAgICBwcmludCgib3V0cHV0OiIsIG91dF9wYXRoKQogICAgcHJpbnQoImZyYW1lczoiLCBzdGVwcykKICAgIHByaW50KCJlbGFwc2VkX3NlYzoiLCBlbGFwc2VkKQoKCmlmIF9fbmFtZV9fID09ICJfX21haW5fXyI6CiAgICBydW5fMDdfZ2FtZV9vZl9saWZlX2xvb3AoKQo=";

    // main は埋め込み Python を実行するエントリポイント。
    public static void main(String[] args) {
        int code = PyRuntime.runEmbeddedPython(PYTRA_EMBEDDED_SOURCE_BASE64, args);
        System.exit(code);
    }
}
