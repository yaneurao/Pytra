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

final class pytra_01_mandelbrot {
    // 埋め込み Python ソース（Base64）。
    private static final String PYTRA_EMBEDDED_SOURCE_BASE64 = "IyAwMTog44Oe44Oz44OH44Or44OW44Ot6ZuG5ZCI44KSIFBORyDnlLvlg4/jgajjgZfjgablh7rlipvjgZnjgovjgrXjg7Pjg5fjg6vjgafjgZnjgIIKIyDlsIbmnaXjga7jg4jjg6njg7Pjgrnjg5HjgqTjg6vjgpLmhI/orZjjgZfjgabjgIHmp4vmlofjga/jgarjgovjgbnjgY/ntKDnm7Tjgavmm7jjgYTjgabjgYTjgb7jgZnjgIIKCmZyb20gdGltZSBpbXBvcnQgcGVyZl9jb3VudGVyCmZyb20gcHlfbW9kdWxlIGltcG9ydCBwbmdfaGVscGVyCgoKZGVmIGVzY2FwZV9jb3VudChjeDogZmxvYXQsIGN5OiBmbG9hdCwgbWF4X2l0ZXI6IGludCkgLT4gaW50OgogICAgIiIiMeeCuSAoY3gsIGN5KSDjga7nmbrmlaPjgb7jgafjga7lj43lvqnlm57mlbDjgpLov5TjgZnjgIIiIiIKICAgIHg6IGZsb2F0ID0gMC4wCiAgICB5OiBmbG9hdCA9IDAuMAogICAgZm9yIGkgaW4gcmFuZ2UobWF4X2l0ZXIpOgogICAgICAgIHgyOiBmbG9hdCA9IHggKiB4CiAgICAgICAgeTI6IGZsb2F0ID0geSAqIHkKICAgICAgICBpZiB4MiArIHkyID4gNC4wOgogICAgICAgICAgICByZXR1cm4gaQogICAgICAgIHkgPSAyLjAgKiB4ICogeSArIGN5CiAgICAgICAgeCA9IHgyIC0geTIgKyBjeAogICAgcmV0dXJuIG1heF9pdGVyCgoKZGVmIGNvbG9yX21hcChpdGVyX2NvdW50OiBpbnQsIG1heF9pdGVyOiBpbnQpIC0+IHR1cGxlW2ludCwgaW50LCBpbnRdOgogICAgIiIi5Y+N5b6p5Zue5pWw44KSIFJHQiDjgavlpInmj5vjgZnjgovjgIIiIiIKICAgIGlmIGl0ZXJfY291bnQgPj0gbWF4X2l0ZXI6CiAgICAgICAgcmV0dXJuICgwLCAwLCAwKQoKICAgICMg57Ch5Y2Y44Gq44Kw44Op44OH44O844K344On44Oz77yI6Z2S57O7IC0+IOm7hOezu++8iQogICAgdDogZmxvYXQgPSBpdGVyX2NvdW50IC8gbWF4X2l0ZXIKICAgIHI6IGludCA9IGludCgyNTUuMCAqICh0ICogdCkpCiAgICBnOiBpbnQgPSBpbnQoMjU1LjAgKiB0KQogICAgYjogaW50ID0gaW50KDI1NS4wICogKDEuMCAtIHQpKQogICAgcmV0dXJuIChyLCBnLCBiKQoKCmRlZiByZW5kZXJfbWFuZGVsYnJvdCgKICAgIHdpZHRoOiBpbnQsCiAgICBoZWlnaHQ6IGludCwKICAgIG1heF9pdGVyOiBpbnQsCiAgICB4X21pbjogZmxvYXQsCiAgICB4X21heDogZmxvYXQsCiAgICB5X21pbjogZmxvYXQsCiAgICB5X21heDogZmxvYXQsCikgLT4gYnl0ZWFycmF5OgogICAgIiIi44Oe44Oz44OH44Or44OW44Ot55S75YOP44GuIFJHQiDjg5DjgqTjg4jliJfjgpLnlJ/miJDjgZnjgovjgIIiIiIKICAgIHBpeGVsczogYnl0ZWFycmF5ID0gYnl0ZWFycmF5KCkKCiAgICBmb3IgeSBpbiByYW5nZShoZWlnaHQpOgogICAgICAgIHB5OiBmbG9hdCA9IHlfbWluICsgKHlfbWF4IC0geV9taW4pICogKHkgLyAoaGVpZ2h0IC0gMSkpCgogICAgICAgIGZvciB4IGluIHJhbmdlKHdpZHRoKToKICAgICAgICAgICAgcHg6IGZsb2F0ID0geF9taW4gKyAoeF9tYXggLSB4X21pbikgKiAoeCAvICh3aWR0aCAtIDEpKQogICAgICAgICAgICBpdDogaW50ID0gZXNjYXBlX2NvdW50KHB4LCBweSwgbWF4X2l0ZXIpCiAgICAgICAgICAgIHI6IGludAogICAgICAgICAgICBnOiBpbnQKICAgICAgICAgICAgYjogaW50CiAgICAgICAgICAgIGlmIGl0ID49IG1heF9pdGVyOgogICAgICAgICAgICAgICAgciA9IDAKICAgICAgICAgICAgICAgIGcgPSAwCiAgICAgICAgICAgICAgICBiID0gMAogICAgICAgICAgICBlbHNlOgogICAgICAgICAgICAgICAgdDogZmxvYXQgPSBpdCAvIG1heF9pdGVyCiAgICAgICAgICAgICAgICByID0gaW50KDI1NS4wICogKHQgKiB0KSkKICAgICAgICAgICAgICAgIGcgPSBpbnQoMjU1LjAgKiB0KQogICAgICAgICAgICAgICAgYiA9IGludCgyNTUuMCAqICgxLjAgLSB0KSkKICAgICAgICAgICAgcGl4ZWxzLmFwcGVuZChyKQogICAgICAgICAgICBwaXhlbHMuYXBwZW5kKGcpCiAgICAgICAgICAgIHBpeGVscy5hcHBlbmQoYikKCiAgICByZXR1cm4gcGl4ZWxzCgoKZGVmIHJ1bl9tYW5kZWxicm90KCkgLT4gTm9uZToKICAgIHdpZHRoOiBpbnQgPSAxNjAwCiAgICBoZWlnaHQ6IGludCA9IDEyMDAKICAgIG1heF9pdGVyOiBpbnQgPSAxMDAwCiAgICBvdXRfcGF0aDogc3RyID0gInNhbXBsZS9vdXQvbWFuZGVsYnJvdF8wMS5wbmciCgogICAgc3RhcnQ6IGZsb2F0ID0gcGVyZl9jb3VudGVyKCkKCiAgICBwaXhlbHM6IGJ5dGVhcnJheSA9IHJlbmRlcl9tYW5kZWxicm90KAogICAgICAgIHdpZHRoLAogICAgICAgIGhlaWdodCwKICAgICAgICBtYXhfaXRlciwKICAgICAgICAtMi4yLAogICAgICAgIDEuMCwKICAgICAgICAtMS4yLAogICAgICAgIDEuMiwKICAgICkKICAgIHBuZ19oZWxwZXIud3JpdGVfcmdiX3BuZyhvdXRfcGF0aCwgd2lkdGgsIGhlaWdodCwgcGl4ZWxzKQoKICAgIGVsYXBzZWQ6IGZsb2F0ID0gcGVyZl9jb3VudGVyKCkgLSBzdGFydAogICAgcHJpbnQoIm91dHB1dDoiLCBvdXRfcGF0aCkKICAgIHByaW50KCJzaXplOiIsIHdpZHRoLCAieCIsIGhlaWdodCkKICAgIHByaW50KCJtYXhfaXRlcjoiLCBtYXhfaXRlcikKICAgIHByaW50KCJlbGFwc2VkX3NlYzoiLCBlbGFwc2VkKQoKCmlmIF9fbmFtZV9fID09ICJfX21haW5fXyI6CiAgICBydW5fbWFuZGVsYnJvdCgpCg==";

    // main は埋め込み Python を実行するエントリポイント。
    public static void main(String[] args) {
        int code = PyRuntime.runEmbeddedPython(PYTRA_EMBEDDED_SOURCE_BASE64, args);
        System.exit(code);
    }
}
