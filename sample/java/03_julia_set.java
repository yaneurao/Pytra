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

final class pytra_03_julia_set {
    // 埋め込み Python ソース（Base64）。
    private static final String PYTRA_EMBEDDED_SOURCE_BASE64 = "IyAwMzog44K444Ol44Oq44Ki6ZuG5ZCI44KSIFBORyDlvaLlvI/jgaflh7rlipvjgZnjgovjgrXjg7Pjg5fjg6vjgafjgZnjgIIKIyDjg4jjg6njg7Pjgrnjg5HjgqTjg6vkupLmj5vjgpLmhI/orZjjgZfjgIHljZjntJTjgarjg6vjg7zjg5fkuK3lv4Pjgaflrp/oo4XjgZfjgabjgYTjgb7jgZnjgIIKCmZyb20gdGltZSBpbXBvcnQgcGVyZl9jb3VudGVyCmZyb20gcHlfbW9kdWxlIGltcG9ydCBwbmdfaGVscGVyCgoKZGVmIHJlbmRlcl9qdWxpYSh3aWR0aDogaW50LCBoZWlnaHQ6IGludCwgbWF4X2l0ZXI6IGludCwgY3g6IGZsb2F0LCBjeTogZmxvYXQpIC0+IGJ5dGVhcnJheToKICAgIHBpeGVsczogYnl0ZWFycmF5ID0gYnl0ZWFycmF5KCkKCiAgICBmb3IgeSBpbiByYW5nZShoZWlnaHQpOgogICAgICAgIHp5MDogZmxvYXQgPSAtMS4yICsgMi40ICogKHkgLyAoaGVpZ2h0IC0gMSkpCgogICAgICAgIGZvciB4IGluIHJhbmdlKHdpZHRoKToKICAgICAgICAgICAgeng6IGZsb2F0ID0gLTEuOCArIDMuNiAqICh4IC8gKHdpZHRoIC0gMSkpCiAgICAgICAgICAgIHp5OiBmbG9hdCA9IHp5MAoKICAgICAgICAgICAgaTogaW50ID0gMAogICAgICAgICAgICB3aGlsZSBpIDwgbWF4X2l0ZXI6CiAgICAgICAgICAgICAgICB6eDI6IGZsb2F0ID0genggKiB6eAogICAgICAgICAgICAgICAgenkyOiBmbG9hdCA9IHp5ICogenkKICAgICAgICAgICAgICAgIGlmIHp4MiArIHp5MiA+IDQuMDoKICAgICAgICAgICAgICAgICAgICBicmVhawogICAgICAgICAgICAgICAgenkgPSAyLjAgKiB6eCAqIHp5ICsgY3kKICAgICAgICAgICAgICAgIHp4ID0gengyIC0genkyICsgY3gKICAgICAgICAgICAgICAgIGkgKz0gMQoKICAgICAgICAgICAgcjogaW50ID0gMAogICAgICAgICAgICBnOiBpbnQgPSAwCiAgICAgICAgICAgIGI6IGludCA9IDAKICAgICAgICAgICAgaWYgaSA+PSBtYXhfaXRlcjoKICAgICAgICAgICAgICAgIHIgPSAwCiAgICAgICAgICAgICAgICBnID0gMAogICAgICAgICAgICAgICAgYiA9IDAKICAgICAgICAgICAgZWxzZToKICAgICAgICAgICAgICAgIHQ6IGZsb2F0ID0gaSAvIG1heF9pdGVyCiAgICAgICAgICAgICAgICByID0gaW50KDI1NS4wICogKDAuMiArIDAuOCAqIHQpKQogICAgICAgICAgICAgICAgZyA9IGludCgyNTUuMCAqICgwLjEgKyAwLjkgKiAodCAqIHQpKSkKICAgICAgICAgICAgICAgIGIgPSBpbnQoMjU1LjAgKiAoMS4wIC0gdCkpCgogICAgICAgICAgICBwaXhlbHMuYXBwZW5kKHIpCiAgICAgICAgICAgIHBpeGVscy5hcHBlbmQoZykKICAgICAgICAgICAgcGl4ZWxzLmFwcGVuZChiKQoKICAgIHJldHVybiBwaXhlbHMKCgpkZWYgcnVuX2p1bGlhKCkgLT4gTm9uZToKICAgIHdpZHRoOiBpbnQgPSAzODQwCiAgICBoZWlnaHQ6IGludCA9IDIxNjAKICAgIG1heF9pdGVyOiBpbnQgPSAyMDAwMAogICAgb3V0X3BhdGg6IHN0ciA9ICJzYW1wbGUvb3V0L2p1bGlhXzAzLnBuZyIKCiAgICBzdGFydDogZmxvYXQgPSBwZXJmX2NvdW50ZXIoKQogICAgcGl4ZWxzOiBieXRlYXJyYXkgPSByZW5kZXJfanVsaWEod2lkdGgsIGhlaWdodCwgbWF4X2l0ZXIsIC0wLjgsIDAuMTU2KQogICAgcG5nX2hlbHBlci53cml0ZV9yZ2JfcG5nKG91dF9wYXRoLCB3aWR0aCwgaGVpZ2h0LCBwaXhlbHMpCiAgICBlbGFwc2VkOiBmbG9hdCA9IHBlcmZfY291bnRlcigpIC0gc3RhcnQKCiAgICBwcmludCgib3V0cHV0OiIsIG91dF9wYXRoKQogICAgcHJpbnQoInNpemU6Iiwgd2lkdGgsICJ4IiwgaGVpZ2h0KQogICAgcHJpbnQoIm1heF9pdGVyOiIsIG1heF9pdGVyKQogICAgcHJpbnQoImVsYXBzZWRfc2VjOiIsIGVsYXBzZWQpCgoKaWYgX19uYW1lX18gPT0gIl9fbWFpbl9fIjoKICAgIHJ1bl9qdWxpYSgpCg==";

    // main は埋め込み Python を実行するエントリポイント。
    public static void main(String[] args) {
        int code = PyRuntime.runEmbeddedPython(PYTRA_EMBEDDED_SOURCE_BASE64, args);
        System.exit(code);
    }
}
