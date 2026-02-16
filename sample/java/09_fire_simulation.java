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

final class pytra_09_fire_simulation {
    // 埋め込み Python ソース（Base64）。
    private static final String PYTRA_EMBEDDED_SOURCE_BASE64 = "IyAwOTog57Ch5piT44OV44Kh44Kk44Ki44Ko44OV44Kn44Kv44OI44KSR0lG5Ye65Yqb44GZ44KL44K144Oz44OX44Or44CCCgpmcm9tIF9fZnV0dXJlX18gaW1wb3J0IGFubm90YXRpb25zCgpmcm9tIHRpbWUgaW1wb3J0IHBlcmZfY291bnRlcgoKZnJvbSBweV9tb2R1bGUuZ2lmX2hlbHBlciBpbXBvcnQgc2F2ZV9naWYKCgpkZWYgZmlyZV9wYWxldHRlKCkgLT4gYnl0ZXM6CiAgICBwID0gYnl0ZWFycmF5KCkKICAgIGZvciBpIGluIHJhbmdlKDI1Nik6CiAgICAgICAgciA9IDAKICAgICAgICBnID0gMAogICAgICAgIGIgPSAwCiAgICAgICAgaWYgaSA8IDg1OgogICAgICAgICAgICByID0gaSAqIDMKICAgICAgICAgICAgZyA9IDAKICAgICAgICAgICAgYiA9IDAKICAgICAgICBlbGlmIGkgPCAxNzA6CiAgICAgICAgICAgIHIgPSAyNTUKICAgICAgICAgICAgZyA9IChpIC0gODUpICogMwogICAgICAgICAgICBiID0gMAogICAgICAgIGVsc2U6CiAgICAgICAgICAgIHIgPSAyNTUKICAgICAgICAgICAgZyA9IDI1NQogICAgICAgICAgICBiID0gKGkgLSAxNzApICogMwogICAgICAgIHAuYXBwZW5kKHIpCiAgICAgICAgcC5hcHBlbmQoZykKICAgICAgICBwLmFwcGVuZChiKQogICAgcmV0dXJuIGJ5dGVzKHApCgoKZGVmIHJ1bl8wOV9maXJlX3NpbXVsYXRpb24oKSAtPiBOb25lOgogICAgdyA9IDM4MAogICAgaCA9IDI2MAogICAgc3RlcHMgPSA0MjAKICAgIG91dF9wYXRoID0gInNhbXBsZS9vdXQvMDlfZmlyZV9zaW11bGF0aW9uLmdpZiIKCiAgICBzdGFydCA9IHBlcmZfY291bnRlcigpCiAgICBoZWF0OiBsaXN0W2xpc3RbaW50XV0gPSBbXQogICAgZm9yIF8gaW4gcmFuZ2UoaCk6CiAgICAgICAgcm93OiBsaXN0W2ludF0gPSBbXQogICAgICAgIGZvciBfIGluIHJhbmdlKHcpOgogICAgICAgICAgICByb3cuYXBwZW5kKDApCiAgICAgICAgaGVhdC5hcHBlbmQocm93KQogICAgZnJhbWVzOiBsaXN0W2J5dGVzXSA9IFtdCgogICAgZm9yIHQgaW4gcmFuZ2Uoc3RlcHMpOgogICAgICAgIGZvciB4IGluIHJhbmdlKHcpOgogICAgICAgICAgICB2YWwgPSAxNzAgKyAoKHggKiAxMyArIHQgKiAxNykgJSA4NikKICAgICAgICAgICAgaGVhdFtoIC0gMV1beF0gPSB2YWwKCiAgICAgICAgZm9yIHkgaW4gcmFuZ2UoMSwgaCk6CiAgICAgICAgICAgIGZvciB4IGluIHJhbmdlKHcpOgogICAgICAgICAgICAgICAgYSA9IGhlYXRbeV1beF0KICAgICAgICAgICAgICAgIGIgPSBoZWF0W3ldWyh4IC0gMSArIHcpICUgd10KICAgICAgICAgICAgICAgIGMgPSBoZWF0W3ldWyh4ICsgMSkgJSB3XQogICAgICAgICAgICAgICAgZCA9IGhlYXRbKHkgKyAxKSAlIGhdW3hdCiAgICAgICAgICAgICAgICB2ID0gKGEgKyBiICsgYyArIGQpIC8vIDQKICAgICAgICAgICAgICAgIGNvb2wgPSAxICsgKCh4ICsgeSArIHQpICUgMykKICAgICAgICAgICAgICAgIG52ID0gdiAtIGNvb2wKICAgICAgICAgICAgICAgIGhlYXRbeSAtIDFdW3hdID0gbnYgaWYgbnYgPiAwIGVsc2UgMAoKICAgICAgICBmcmFtZSA9IGJ5dGVhcnJheSh3ICogaCkKICAgICAgICBpID0gMAogICAgICAgIGZvciB5eSBpbiByYW5nZShoKToKICAgICAgICAgICAgZm9yIHh4IGluIHJhbmdlKHcpOgogICAgICAgICAgICAgICAgZnJhbWVbaV0gPSBoZWF0W3l5XVt4eF0KICAgICAgICAgICAgICAgIGkgKz0gMQogICAgICAgIGZyYW1lcy5hcHBlbmQoYnl0ZXMoZnJhbWUpKQoKICAgIHNhdmVfZ2lmKG91dF9wYXRoLCB3LCBoLCBmcmFtZXMsIGZpcmVfcGFsZXR0ZSgpLCBkZWxheV9jcz00LCBsb29wPTApCiAgICBlbGFwc2VkID0gcGVyZl9jb3VudGVyKCkgLSBzdGFydAogICAgcHJpbnQoIm91dHB1dDoiLCBvdXRfcGF0aCkKICAgIHByaW50KCJmcmFtZXM6Iiwgc3RlcHMpCiAgICBwcmludCgiZWxhcHNlZF9zZWM6IiwgZWxhcHNlZCkKCgppZiBfX25hbWVfXyA9PSAiX19tYWluX18iOgogICAgcnVuXzA5X2ZpcmVfc2ltdWxhdGlvbigpCg==";

    // main は埋め込み Python を実行するエントリポイント。
    public static void main(String[] args) {
        int code = PyRuntime.runEmbeddedPython(PYTRA_EMBEDDED_SOURCE_BASE64, args);
        System.exit(code);
    }
}
