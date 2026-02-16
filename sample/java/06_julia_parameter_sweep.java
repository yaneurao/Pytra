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

final class pytra_06_julia_parameter_sweep {
    // 埋め込み Python ソース（Base64）。
    private static final String PYTRA_EMBEDDED_SOURCE_BASE64 = "IyAwNjog44K444Ol44Oq44Ki6ZuG5ZCI44Gu44OR44Op44Oh44O844K/44KS5Zue44GX44GmR0lG5Ye65Yqb44GZ44KL44K144Oz44OX44Or44CCCgpmcm9tIF9fZnV0dXJlX18gaW1wb3J0IGFubm90YXRpb25zCgppbXBvcnQgbWF0aApmcm9tIHRpbWUgaW1wb3J0IHBlcmZfY291bnRlcgoKZnJvbSBweV9tb2R1bGUuZ2lmX2hlbHBlciBpbXBvcnQgc2F2ZV9naWYKCgpkZWYganVsaWFfcGFsZXR0ZSgpIC0+IGJ5dGVzOgogICAgIyDlhYjpoK3oibLjga/pm4blkIjlhoXpg6jnlKjjgavpu5Llm7rlrprjgIHmrovjgorjga/pq5jlvanluqbjgrDjg6njg4fjg7zjgrfjg6fjg7PjgpLkvZzjgovjgIIKICAgIHBhbGV0dGUgPSBieXRlYXJyYXkoMjU2ICogMykKICAgIHBhbGV0dGVbMF0gPSAwCiAgICBwYWxldHRlWzFdID0gMAogICAgcGFsZXR0ZVsyXSA9IDAKICAgIGZvciBpIGluIHJhbmdlKDEsIDI1Nik6CiAgICAgICAgdCA9IChpIC0gMSkgLyAyNTQuMAogICAgICAgIHIgPSBpbnQoMjU1LjAgKiAoOS4wICogKDEuMCAtIHQpICogdCAqIHQgKiB0KSkKICAgICAgICBnID0gaW50KDI1NS4wICogKDE1LjAgKiAoMS4wIC0gdCkgKiAoMS4wIC0gdCkgKiB0ICogdCkpCiAgICAgICAgYiA9IGludCgyNTUuMCAqICg4LjUgKiAoMS4wIC0gdCkgKiAoMS4wIC0gdCkgKiAoMS4wIC0gdCkgKiB0KSkKICAgICAgICBwYWxldHRlW2kgKiAzICsgMF0gPSByCiAgICAgICAgcGFsZXR0ZVtpICogMyArIDFdID0gZwogICAgICAgIHBhbGV0dGVbaSAqIDMgKyAyXSA9IGIKICAgIHJldHVybiBieXRlcyhwYWxldHRlKQoKCmRlZiByZW5kZXJfZnJhbWUod2lkdGg6IGludCwgaGVpZ2h0OiBpbnQsIGNyOiBmbG9hdCwgY2k6IGZsb2F0LCBtYXhfaXRlcjogaW50LCBwaGFzZTogaW50KSAtPiBieXRlczoKICAgIGZyYW1lID0gYnl0ZWFycmF5KHdpZHRoICogaGVpZ2h0KQogICAgaWR4ID0gMAogICAgZm9yIHkgaW4gcmFuZ2UoaGVpZ2h0KToKICAgICAgICB6eTAgPSAtMS4yICsgMi40ICogKHkgLyAoaGVpZ2h0IC0gMSkpCiAgICAgICAgZm9yIHggaW4gcmFuZ2Uod2lkdGgpOgogICAgICAgICAgICB6eCA9IC0xLjggKyAzLjYgKiAoeCAvICh3aWR0aCAtIDEpKQogICAgICAgICAgICB6eSA9IHp5MAogICAgICAgICAgICBpID0gMAogICAgICAgICAgICB3aGlsZSBpIDwgbWF4X2l0ZXI6CiAgICAgICAgICAgICAgICB6eDIgPSB6eCAqIHp4CiAgICAgICAgICAgICAgICB6eTIgPSB6eSAqIHp5CiAgICAgICAgICAgICAgICBpZiB6eDIgKyB6eTIgPiA0LjA6CiAgICAgICAgICAgICAgICAgICAgYnJlYWsKICAgICAgICAgICAgICAgIHp5ID0gMi4wICogenggKiB6eSArIGNpCiAgICAgICAgICAgICAgICB6eCA9IHp4MiAtIHp5MiArIGNyCiAgICAgICAgICAgICAgICBpICs9IDEKICAgICAgICAgICAgaWYgaSA+PSBtYXhfaXRlcjoKICAgICAgICAgICAgICAgIGZyYW1lW2lkeF0gPSAwCiAgICAgICAgICAgIGVsc2U6CiAgICAgICAgICAgICAgICAjIOODleODrOODvOODoOS9jeebuOOCkuWwkeOBl+WKoOOBiOOBpuiJsuOBjOa7keOCieOBi+OBq+a1geOCjOOCi+OCiOOBhuOBq+OBmeOCi+OAggogICAgICAgICAgICAgICAgY29sb3JfaW5kZXggPSAxICsgKCgoaSAqIDIyNCkgLy8gbWF4X2l0ZXIgKyBwaGFzZSkgJSAyNTUpCiAgICAgICAgICAgICAgICBmcmFtZVtpZHhdID0gY29sb3JfaW5kZXgKICAgICAgICAgICAgaWR4ICs9IDEKICAgIHJldHVybiBieXRlcyhmcmFtZSkKCgpkZWYgcnVuXzA2X2p1bGlhX3BhcmFtZXRlcl9zd2VlcCgpIC0+IE5vbmU6CiAgICB3aWR0aCA9IDMyMAogICAgaGVpZ2h0ID0gMjQwCiAgICBmcmFtZXNfbiA9IDcyCiAgICBtYXhfaXRlciA9IDE4MAogICAgb3V0X3BhdGggPSAic2FtcGxlL291dC8wNl9qdWxpYV9wYXJhbWV0ZXJfc3dlZXAuZ2lmIgoKICAgIHN0YXJ0ID0gcGVyZl9jb3VudGVyKCkKICAgIGZyYW1lczogbGlzdFtieXRlc10gPSBbXQogICAgIyDml6Lnn6Xjga7opovmoITjgYjjgYzoia/jgYTov5Hlgo3jgpLmpZXlhobou4zpgZPjgaflt6Hlm57jgZfjgIHljZjoqr/jgarnmb3po5vjgbPjgpLmipHjgYjjgovjgIIKICAgIGNlbnRlcl9jciA9IC0wLjc0NQogICAgY2VudGVyX2NpID0gMC4xODYKICAgIHJhZGl1c19jciA9IDAuMTIKICAgIHJhZGl1c19jaSA9IDAuMTAKICAgIGZvciBpIGluIHJhbmdlKGZyYW1lc19uKToKICAgICAgICB0ID0gaSAvIGZyYW1lc19uCiAgICAgICAgYW5nbGUgPSAyLjAgKiBtYXRoLnBpICogdAogICAgICAgIGNyID0gY2VudGVyX2NyICsgcmFkaXVzX2NyICogbWF0aC5jb3MoYW5nbGUpCiAgICAgICAgY2kgPSBjZW50ZXJfY2kgKyByYWRpdXNfY2kgKiBtYXRoLnNpbihhbmdsZSkKICAgICAgICBwaGFzZSA9IChpICogNSkgJSAyNTUKICAgICAgICBmcmFtZXMuYXBwZW5kKHJlbmRlcl9mcmFtZSh3aWR0aCwgaGVpZ2h0LCBjciwgY2ksIG1heF9pdGVyLCBwaGFzZSkpCgogICAgc2F2ZV9naWYob3V0X3BhdGgsIHdpZHRoLCBoZWlnaHQsIGZyYW1lcywganVsaWFfcGFsZXR0ZSgpLCBkZWxheV9jcz04LCBsb29wPTApCiAgICBlbGFwc2VkID0gcGVyZl9jb3VudGVyKCkgLSBzdGFydAogICAgcHJpbnQoIm91dHB1dDoiLCBvdXRfcGF0aCkKICAgIHByaW50KCJmcmFtZXM6IiwgZnJhbWVzX24pCiAgICBwcmludCgiZWxhcHNlZF9zZWM6IiwgZWxhcHNlZCkKCgppZiBfX25hbWVfXyA9PSAiX19tYWluX18iOgogICAgcnVuXzA2X2p1bGlhX3BhcmFtZXRlcl9zd2VlcCgpCg==";

    // main は埋め込み Python を実行するエントリポイント。
    public static void main(String[] args) {
        int code = PyRuntime.runEmbeddedPython(PYTRA_EMBEDDED_SOURCE_BASE64, args);
        System.exit(code);
    }
}
