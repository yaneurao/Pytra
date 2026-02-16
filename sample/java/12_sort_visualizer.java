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

final class pytra_12_sort_visualizer {
    // 埋め込み Python ソース（Base64）。
    private static final String PYTRA_EMBEDDED_SOURCE_BASE64 = "IyAxMjog44OQ44OW44Or44K944O844OI44Gu6YCU5Lit54q25oWL44KSR0lG5Ye65Yqb44GZ44KL44K144Oz44OX44Or44CCCgpmcm9tIF9fZnV0dXJlX18gaW1wb3J0IGFubm90YXRpb25zCgpmcm9tIHRpbWUgaW1wb3J0IHBlcmZfY291bnRlcgoKZnJvbSBweV9tb2R1bGUuZ2lmX2hlbHBlciBpbXBvcnQgZ3JheXNjYWxlX3BhbGV0dGUsIHNhdmVfZ2lmCgoKZGVmIHJlbmRlcih2YWx1ZXM6IGxpc3RbaW50XSwgdzogaW50LCBoOiBpbnQpIC0+IGJ5dGVzOgogICAgZnJhbWUgPSBieXRlYXJyYXkodyAqIGgpCiAgICBuID0gbGVuKHZhbHVlcykKICAgIGJhcl93ID0gdyAvIG4KICAgIGZvciBpIGluIHJhbmdlKG4pOgogICAgICAgIHgwID0gaW50KGkgKiBiYXJfdykKICAgICAgICB4MSA9IGludCgoaSArIDEpICogYmFyX3cpCiAgICAgICAgaWYgeDEgPD0geDA6CiAgICAgICAgICAgIHgxID0geDAgKyAxCiAgICAgICAgYmggPSBpbnQoKCh2YWx1ZXNbaV0gLyBuKSAqIGgpKQogICAgICAgIHkgPSBoIC0gYmgKICAgICAgICBmb3IgeSBpbiByYW5nZSh5LCBoKToKICAgICAgICAgICAgZm9yIHggaW4gcmFuZ2UoeDAsIHgxKToKICAgICAgICAgICAgICAgIGZyYW1lW3kgKiB3ICsgeF0gPSAyNTUKICAgIHJldHVybiBieXRlcyhmcmFtZSkKCgpkZWYgcnVuXzEyX3NvcnRfdmlzdWFsaXplcigpIC0+IE5vbmU6CiAgICB3ID0gMzIwCiAgICBoID0gMTgwCiAgICBuID0gMTI0CiAgICBvdXRfcGF0aCA9ICJzYW1wbGUvb3V0LzEyX3NvcnRfdmlzdWFsaXplci5naWYiCgogICAgc3RhcnQgPSBwZXJmX2NvdW50ZXIoKQogICAgdmFsdWVzOiBsaXN0W2ludF0gPSBbXQogICAgZm9yIGkgaW4gcmFuZ2Uobik6CiAgICAgICAgdmFsdWVzLmFwcGVuZCgoaSAqIDM3ICsgMTkpICUgbikKCiAgICBmcmFtZXM6IGxpc3RbYnl0ZXNdID0gW3JlbmRlcih2YWx1ZXMsIHcsIGgpXQoKICAgIG9wID0gMAogICAgZm9yIGkgaW4gcmFuZ2Uobik6CiAgICAgICAgc3dhcHBlZCA9IEZhbHNlCiAgICAgICAgZm9yIGogaW4gcmFuZ2UobiAtIGkgLSAxKToKICAgICAgICAgICAgaWYgdmFsdWVzW2pdID4gdmFsdWVzW2ogKyAxXToKICAgICAgICAgICAgICAgIHRtcCA9IHZhbHVlc1tqXQogICAgICAgICAgICAgICAgdmFsdWVzW2pdID0gdmFsdWVzW2ogKyAxXQogICAgICAgICAgICAgICAgdmFsdWVzW2ogKyAxXSA9IHRtcAogICAgICAgICAgICAgICAgc3dhcHBlZCA9IFRydWUKICAgICAgICAgICAgaWYgb3AgJSA4ID09IDA6CiAgICAgICAgICAgICAgICBmcmFtZXMuYXBwZW5kKHJlbmRlcih2YWx1ZXMsIHcsIGgpKQogICAgICAgICAgICBvcCArPSAxCiAgICAgICAgaWYgbm90IHN3YXBwZWQ6CiAgICAgICAgICAgIGJyZWFrCgogICAgc2F2ZV9naWYob3V0X3BhdGgsIHcsIGgsIGZyYW1lcywgZ3JheXNjYWxlX3BhbGV0dGUoKSwgZGVsYXlfY3M9MywgbG9vcD0wKQogICAgZWxhcHNlZCA9IHBlcmZfY291bnRlcigpIC0gc3RhcnQKICAgIHByaW50KCJvdXRwdXQ6Iiwgb3V0X3BhdGgpCiAgICBwcmludCgiZnJhbWVzOiIsIGxlbihmcmFtZXMpKQogICAgcHJpbnQoImVsYXBzZWRfc2VjOiIsIGVsYXBzZWQpCgoKaWYgX19uYW1lX18gPT0gIl9fbWFpbl9fIjoKICAgIHJ1bl8xMl9zb3J0X3Zpc3VhbGl6ZXIoKQo=";

    // main は埋め込み Python を実行するエントリポイント。
    public static void main(String[] args) {
        int code = PyRuntime.runEmbeddedPython(PYTRA_EMBEDDED_SOURCE_BASE64, args);
        System.exit(code);
    }
}
