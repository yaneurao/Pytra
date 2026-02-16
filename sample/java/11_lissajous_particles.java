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

final class pytra_11_lissajous_particles {
    // 埋め込み Python ソース（Base64）。
    private static final String PYTRA_EMBEDDED_SOURCE_BASE64 = "IyAxMTog44Oq44K144O844K444Ol6YGL5YuV44GZ44KL57KS5a2Q44KSR0lG5Ye65Yqb44GZ44KL44K144Oz44OX44Or44CCCgpmcm9tIF9fZnV0dXJlX18gaW1wb3J0IGFubm90YXRpb25zCgppbXBvcnQgbWF0aApmcm9tIHRpbWUgaW1wb3J0IHBlcmZfY291bnRlcgoKZnJvbSBweV9tb2R1bGUuZ2lmX2hlbHBlciBpbXBvcnQgc2F2ZV9naWYKCgpkZWYgY29sb3JfcGFsZXR0ZSgpIC0+IGJ5dGVzOgogICAgcCA9IGJ5dGVhcnJheSgpCiAgICBmb3IgaSBpbiByYW5nZSgyNTYpOgogICAgICAgIHIgPSBpCiAgICAgICAgZyA9IChpICogMykgJSAyNTYKICAgICAgICBiID0gMjU1IC0gaQogICAgICAgIHAuYXBwZW5kKHIpCiAgICAgICAgcC5hcHBlbmQoZykKICAgICAgICBwLmFwcGVuZChiKQogICAgcmV0dXJuIGJ5dGVzKHApCgoKZGVmIHJ1bl8xMV9saXNzYWpvdXNfcGFydGljbGVzKCkgLT4gTm9uZToKICAgIHcgPSAzMjAKICAgIGggPSAyNDAKICAgIGZyYW1lc19uID0gMzYwCiAgICBwYXJ0aWNsZXMgPSA0OAogICAgb3V0X3BhdGggPSAic2FtcGxlL291dC8xMV9saXNzYWpvdXNfcGFydGljbGVzLmdpZiIKCiAgICBzdGFydCA9IHBlcmZfY291bnRlcigpCiAgICBmcmFtZXM6IGxpc3RbYnl0ZXNdID0gW10KCiAgICBmb3IgdCBpbiByYW5nZShmcmFtZXNfbik6CiAgICAgICAgZnJhbWUgPSBieXRlYXJyYXkodyAqIGgpCgogICAgICAgIGZvciBwIGluIHJhbmdlKHBhcnRpY2xlcyk6CiAgICAgICAgICAgIHBoYXNlID0gcCAqIDAuMjYxNzk5CiAgICAgICAgICAgIHggPSBpbnQoKHcgKiAwLjUpICsgKHcgKiAwLjM4KSAqIG1hdGguc2luKDAuMTEgKiB0ICsgcGhhc2UgKiAyLjApKQogICAgICAgICAgICB5ID0gaW50KChoICogMC41KSArIChoICogMC4zOCkgKiBtYXRoLnNpbigwLjE3ICogdCArIHBoYXNlICogMy4wKSkKICAgICAgICAgICAgY29sb3IgPSAzMCArIChwICogOSkgJSAyMjAKCiAgICAgICAgICAgIGZvciBkeSBpbiByYW5nZSgtMiwgMyk6CiAgICAgICAgICAgICAgICBmb3IgZHggaW4gcmFuZ2UoLTIsIDMpOgogICAgICAgICAgICAgICAgICAgIHh4ID0geCArIGR4CiAgICAgICAgICAgICAgICAgICAgeXkgPSB5ICsgZHkKICAgICAgICAgICAgICAgICAgICBpZiB4eCA+PSAwIGFuZCB4eCA8IHcgYW5kIHl5ID49IDAgYW5kIHl5IDwgaDoKICAgICAgICAgICAgICAgICAgICAgICAgZDIgPSBkeCAqIGR4ICsgZHkgKiBkeQogICAgICAgICAgICAgICAgICAgICAgICBpZiBkMiA8PSA0OgogICAgICAgICAgICAgICAgICAgICAgICAgICAgaWR4ID0geXkgKiB3ICsgeHgKICAgICAgICAgICAgICAgICAgICAgICAgICAgIHYgPSBjb2xvciAtIGQyICogMjAKICAgICAgICAgICAgICAgICAgICAgICAgICAgIGlmIHYgPCAwOgogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIHYgPSAwCiAgICAgICAgICAgICAgICAgICAgICAgICAgICBpZiB2ID4gZnJhbWVbaWR4XToKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICBmcmFtZVtpZHhdID0gdgoKICAgICAgICBmcmFtZXMuYXBwZW5kKGJ5dGVzKGZyYW1lKSkKCiAgICBzYXZlX2dpZihvdXRfcGF0aCwgdywgaCwgZnJhbWVzLCBjb2xvcl9wYWxldHRlKCksIGRlbGF5X2NzPTMsIGxvb3A9MCkKICAgIGVsYXBzZWQgPSBwZXJmX2NvdW50ZXIoKSAtIHN0YXJ0CiAgICBwcmludCgib3V0cHV0OiIsIG91dF9wYXRoKQogICAgcHJpbnQoImZyYW1lczoiLCBmcmFtZXNfbikKICAgIHByaW50KCJlbGFwc2VkX3NlYzoiLCBlbGFwc2VkKQoKCmlmIF9fbmFtZV9fID09ICJfX21haW5fXyI6CiAgICBydW5fMTFfbGlzc2Fqb3VzX3BhcnRpY2xlcygpCg==";

    // main は埋め込み Python を実行するエントリポイント。
    public static void main(String[] args) {
        int code = PyRuntime.runEmbeddedPython(PYTRA_EMBEDDED_SOURCE_BASE64, args);
        System.exit(code);
    }
}
