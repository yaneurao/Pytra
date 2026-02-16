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

final class pytra_04_monte_carlo_pi {
    // 埋め込み Python ソース（Base64）。
    private static final String PYTRA_EMBEDDED_SOURCE_BASE64 = "IyAxMDog44Oi44Oz44OG44Kr44Or44Ot5rOV44Gn5YaG5ZGo546H44KS5o6o5a6a44GZ44KL44K144Oz44OX44Or44Gn44GZ44CCCiMgaW1wb3J0IHJhbmRvbSDjgpLkvb/jgo/jgZrjgIFMQ0cg44KS6Ieq5YmN5a6f6KOF44GX44Gm44OI44Op44Oz44K544OR44Kk44Or5LqS5o+b5oCn44KS6auY44KB44Gm44GE44G+44GZ44CCCgpmcm9tIHRpbWUgaW1wb3J0IHBlcmZfY291bnRlcgoKCmRlZiBsY2dfbmV4dChzdGF0ZTogaW50KSAtPiBpbnQ6CiAgICAjIDMyYml0IExDRwogICAgcmV0dXJuICgxNjY0NTI1ICogc3RhdGUgKyAxMDEzOTA0MjIzKSAlIDQyOTQ5NjcyOTYKCgpkZWYgcnVuX3BpX3RyaWFsKHRvdGFsX3NhbXBsZXM6IGludCwgc2VlZDogaW50KSAtPiBmbG9hdDoKICAgIGluc2lkZTogaW50ID0gMAogICAgc3RhdGU6IGludCA9IHNlZWQKCiAgICBmb3IgXyBpbiByYW5nZSh0b3RhbF9zYW1wbGVzKToKICAgICAgICBzdGF0ZSA9IGxjZ19uZXh0KHN0YXRlKQogICAgICAgIHg6IGZsb2F0ID0gc3RhdGUgLyA0Mjk0OTY3Mjk2LjAKCiAgICAgICAgc3RhdGUgPSBsY2dfbmV4dChzdGF0ZSkKICAgICAgICB5OiBmbG9hdCA9IHN0YXRlIC8gNDI5NDk2NzI5Ni4wCgogICAgICAgIGR4OiBmbG9hdCA9IHggLSAwLjUKICAgICAgICBkeTogZmxvYXQgPSB5IC0gMC41CiAgICAgICAgaWYgZHggKiBkeCArIGR5ICogZHkgPD0gMC4yNToKICAgICAgICAgICAgaW5zaWRlICs9IDEKCiAgICByZXR1cm4gNC4wICogaW5zaWRlIC8gdG90YWxfc2FtcGxlcwoKCmRlZiBydW5fbW9udGVfY2FybG9fcGkoKSAtPiBOb25lOgogICAgc2FtcGxlczogaW50ID0gNTQwMDAwMDAKICAgIHNlZWQ6IGludCA9IDEyMzQ1Njc4OQoKICAgIHN0YXJ0OiBmbG9hdCA9IHBlcmZfY291bnRlcigpCiAgICBwaV9lc3Q6IGZsb2F0ID0gcnVuX3BpX3RyaWFsKHNhbXBsZXMsIHNlZWQpCiAgICBlbGFwc2VkOiBmbG9hdCA9IHBlcmZfY291bnRlcigpIC0gc3RhcnQKCiAgICBwcmludCgic2FtcGxlczoiLCBzYW1wbGVzKQogICAgcHJpbnQoInBpX2VzdGltYXRlOiIsIHBpX2VzdCkKICAgIHByaW50KCJlbGFwc2VkX3NlYzoiLCBlbGFwc2VkKQoKCmlmIF9fbmFtZV9fID09ICJfX21haW5fXyI6CiAgICBydW5fbW9udGVfY2FybG9fcGkoKQo=";

    // main は埋め込み Python を実行するエントリポイント。
    public static void main(String[] args) {
        int code = PyRuntime.runEmbeddedPython(PYTRA_EMBEDDED_SOURCE_BASE64, args);
        System.exit(code);
    }
}
