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

final class pytra_14_raymarching_light_cycle {
    // 埋め込み Python ソース（Base64）。
    private static final String PYTRA_EMBEDDED_SOURCE_BASE64 = "IyAxNDog57Ch5piT44Os44Kk44Oe44O844OB6aKo44Gu5YWJ5rqQ56e75YuV44K344O844Oz44KSR0lG5Ye65Yqb44GZ44KL44K144Oz44OX44Or44CCCgpmcm9tIF9fZnV0dXJlX18gaW1wb3J0IGFubm90YXRpb25zCgppbXBvcnQgbWF0aApmcm9tIHRpbWUgaW1wb3J0IHBlcmZfY291bnRlcgoKZnJvbSBweV9tb2R1bGUuZ2lmX2hlbHBlciBpbXBvcnQgc2F2ZV9naWYKCgpkZWYgcGFsZXR0ZSgpIC0+IGJ5dGVzOgogICAgcCA9IGJ5dGVhcnJheSgpCiAgICBmb3IgaSBpbiByYW5nZSgyNTYpOgogICAgICAgIHIgPSBpbnQoMjAgKyBpICogMC45KQogICAgICAgIGlmIHIgPiAyNTU6CiAgICAgICAgICAgIHIgPSAyNTUKICAgICAgICBnID0gaW50KDEwICsgaSAqIDAuNykKICAgICAgICBpZiBnID4gMjU1OgogICAgICAgICAgICBnID0gMjU1CiAgICAgICAgYiA9IGludCgzMCArIGkpCiAgICAgICAgaWYgYiA+IDI1NToKICAgICAgICAgICAgYiA9IDI1NQogICAgICAgIHAuYXBwZW5kKHIpCiAgICAgICAgcC5hcHBlbmQoZykKICAgICAgICBwLmFwcGVuZChiKQogICAgcmV0dXJuIGJ5dGVzKHApCgoKZGVmIHNjZW5lKHg6IGZsb2F0LCB5OiBmbG9hdCwgbGlnaHRfeDogZmxvYXQsIGxpZ2h0X3k6IGZsb2F0KSAtPiBpbnQ6CiAgICB4MSA9IHggKyAwLjQ1CiAgICB5MSA9IHkgKyAwLjIKICAgIHgyID0geCAtIDAuMzUKICAgIHkyID0geSAtIDAuMTUKICAgIHIxID0gbWF0aC5zcXJ0KHgxICogeDEgKyB5MSAqIHkxKQogICAgcjIgPSBtYXRoLnNxcnQoeDIgKiB4MiArIHkyICogeTIpCiAgICBibG9iID0gbWF0aC5leHAoLTcuMCAqIHIxICogcjEpICsgbWF0aC5leHAoLTguMCAqIHIyICogcjIpCgogICAgbHggPSB4IC0gbGlnaHRfeAogICAgbHkgPSB5IC0gbGlnaHRfeQogICAgbCA9IG1hdGguc3FydChseCAqIGx4ICsgbHkgKiBseSkKICAgIGxpdCA9IDEuMCAvICgxLjAgKyAzLjUgKiBsICogbCkKCiAgICB2ID0gaW50KDI1NS4wICogYmxvYiAqIGxpdCAqIDUuMCkKICAgIGlmIHYgPCAwOgogICAgICAgIHJldHVybiAwCiAgICBpZiB2ID4gMjU1OgogICAgICAgIHJldHVybiAyNTUKICAgIHJldHVybiB2CgoKZGVmIHJ1bl8xNF9yYXltYXJjaGluZ19saWdodF9jeWNsZSgpIC0+IE5vbmU6CiAgICB3ID0gMzIwCiAgICBoID0gMjQwCiAgICBmcmFtZXNfbiA9IDg0CiAgICBvdXRfcGF0aCA9ICJzYW1wbGUvb3V0LzE0X3JheW1hcmNoaW5nX2xpZ2h0X2N5Y2xlLmdpZiIKCiAgICBzdGFydCA9IHBlcmZfY291bnRlcigpCiAgICBmcmFtZXM6IGxpc3RbYnl0ZXNdID0gW10KCiAgICBmb3IgdCBpbiByYW5nZShmcmFtZXNfbik6CiAgICAgICAgZnJhbWUgPSBieXRlYXJyYXkodyAqIGgpCiAgICAgICAgYSA9ICh0IC8gZnJhbWVzX24pICogbWF0aC5waSAqIDIuMAogICAgICAgIGxpZ2h0X3ggPSAwLjc1ICogbWF0aC5jb3MoYSkKICAgICAgICBsaWdodF95ID0gMC41NSAqIG1hdGguc2luKGEgKiAxLjIpCgogICAgICAgIGkgPSAwCiAgICAgICAgZm9yIHkgaW4gcmFuZ2UoaCk6CiAgICAgICAgICAgIHB5ID0gKHkgLyAoaCAtIDEpKSAqIDIuMCAtIDEuMAogICAgICAgICAgICBmb3IgeCBpbiByYW5nZSh3KToKICAgICAgICAgICAgICAgIHB4ID0gKHggLyAodyAtIDEpKSAqIDIuMCAtIDEuMAogICAgICAgICAgICAgICAgZnJhbWVbaV0gPSBzY2VuZShweCwgcHksIGxpZ2h0X3gsIGxpZ2h0X3kpCiAgICAgICAgICAgICAgICBpICs9IDEKCiAgICAgICAgZnJhbWVzLmFwcGVuZChieXRlcyhmcmFtZSkpCgogICAgc2F2ZV9naWYob3V0X3BhdGgsIHcsIGgsIGZyYW1lcywgcGFsZXR0ZSgpLCBkZWxheV9jcz0zLCBsb29wPTApCiAgICBlbGFwc2VkID0gcGVyZl9jb3VudGVyKCkgLSBzdGFydAogICAgcHJpbnQoIm91dHB1dDoiLCBvdXRfcGF0aCkKICAgIHByaW50KCJmcmFtZXM6IiwgZnJhbWVzX24pCiAgICBwcmludCgiZWxhcHNlZF9zZWM6IiwgZWxhcHNlZCkKCgppZiBfX25hbWVfXyA9PSAiX19tYWluX18iOgogICAgcnVuXzE0X3JheW1hcmNoaW5nX2xpZ2h0X2N5Y2xlKCkK";

    // main は埋め込み Python を実行するエントリポイント。
    public static void main(String[] args) {
        int code = PyRuntime.runEmbeddedPython(PYTRA_EMBEDDED_SOURCE_BASE64, args);
        System.exit(code);
    }
}
