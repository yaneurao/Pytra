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

final class pytra_08_langtons_ant {
    // 埋め込み Python ソース（Base64）。
    private static final String PYTRA_EMBEDDED_SOURCE_BASE64 = "IyAwODog44Op44Oz44Kw44OI44Oz44Gu44Ki44Oq44Gu6LuM6Leh44KSR0lG5Ye65Yqb44GZ44KL44K144Oz44OX44Or44CCCgpmcm9tIF9fZnV0dXJlX18gaW1wb3J0IGFubm90YXRpb25zCgpmcm9tIHRpbWUgaW1wb3J0IHBlcmZfY291bnRlcgoKZnJvbSBweV9tb2R1bGUuZ2lmX2hlbHBlciBpbXBvcnQgZ3JheXNjYWxlX3BhbGV0dGUsIHNhdmVfZ2lmCgoKZGVmIGNhcHR1cmUoZ3JpZDogbGlzdFtsaXN0W2ludF1dLCB3OiBpbnQsIGg6IGludCkgLT4gYnl0ZXM6CiAgICBmcmFtZSA9IGJ5dGVhcnJheSh3ICogaCkKICAgIGkgPSAwCiAgICBmb3IgeSBpbiByYW5nZShoKToKICAgICAgICBmb3IgeCBpbiByYW5nZSh3KToKICAgICAgICAgICAgZnJhbWVbaV0gPSAyNTUgaWYgZ3JpZFt5XVt4XSBlbHNlIDAKICAgICAgICAgICAgaSArPSAxCiAgICByZXR1cm4gYnl0ZXMoZnJhbWUpCgoKZGVmIHJ1bl8wOF9sYW5ndG9uc19hbnQoKSAtPiBOb25lOgogICAgdyA9IDQyMAogICAgaCA9IDQyMAogICAgb3V0X3BhdGggPSAic2FtcGxlL291dC8wOF9sYW5ndG9uc19hbnQuZ2lmIgoKICAgIHN0YXJ0ID0gcGVyZl9jb3VudGVyKCkKCiAgICBncmlkOiBsaXN0W2xpc3RbaW50XV0gPSBbXQogICAgZm9yIGd5IGluIHJhbmdlKGgpOgogICAgICAgIHJvdzogbGlzdFtpbnRdID0gW10KICAgICAgICBmb3IgZ3ggaW4gcmFuZ2Uodyk6CiAgICAgICAgICAgIHJvdy5hcHBlbmQoMCkKICAgICAgICBncmlkLmFwcGVuZChyb3cpCiAgICB4ID0gdyAvLyAyCiAgICB5ID0gaCAvLyAyCiAgICBkID0gMAoKICAgIHN0ZXBzX3RvdGFsID0gNjAwMDAwCiAgICBjYXB0dXJlX2V2ZXJ5ID0gMzAwMAogICAgZnJhbWVzOiBsaXN0W2J5dGVzXSA9IFtdCgogICAgZm9yIGkgaW4gcmFuZ2Uoc3RlcHNfdG90YWwpOgogICAgICAgIGlmIGdyaWRbeV1beF0gPT0gMDoKICAgICAgICAgICAgZCA9IChkICsgMSkgJSA0CiAgICAgICAgICAgIGdyaWRbeV1beF0gPSAxCiAgICAgICAgZWxzZToKICAgICAgICAgICAgZCA9IChkICsgMykgJSA0CiAgICAgICAgICAgIGdyaWRbeV1beF0gPSAwCgogICAgICAgIGlmIGQgPT0gMDoKICAgICAgICAgICAgeSA9ICh5IC0gMSArIGgpICUgaAogICAgICAgIGVsaWYgZCA9PSAxOgogICAgICAgICAgICB4ID0gKHggKyAxKSAlIHcKICAgICAgICBlbGlmIGQgPT0gMjoKICAgICAgICAgICAgeSA9ICh5ICsgMSkgJSBoCiAgICAgICAgZWxzZToKICAgICAgICAgICAgeCA9ICh4IC0gMSArIHcpICUgdwoKICAgICAgICBpZiBpICUgY2FwdHVyZV9ldmVyeSA9PSAwOgogICAgICAgICAgICBmcmFtZXMuYXBwZW5kKGNhcHR1cmUoZ3JpZCwgdywgaCkpCgogICAgc2F2ZV9naWYob3V0X3BhdGgsIHcsIGgsIGZyYW1lcywgZ3JheXNjYWxlX3BhbGV0dGUoKSwgZGVsYXlfY3M9NSwgbG9vcD0wKQogICAgZWxhcHNlZCA9IHBlcmZfY291bnRlcigpIC0gc3RhcnQKICAgIHByaW50KCJvdXRwdXQ6Iiwgb3V0X3BhdGgpCiAgICBwcmludCgiZnJhbWVzOiIsIGxlbihmcmFtZXMpKQogICAgcHJpbnQoImVsYXBzZWRfc2VjOiIsIGVsYXBzZWQpCgoKaWYgX19uYW1lX18gPT0gIl9fbWFpbl9fIjoKICAgIHJ1bl8wOF9sYW5ndG9uc19hbnQoKQo=";

    // main は埋め込み Python を実行するエントリポイント。
    public static void main(String[] args) {
        int code = PyRuntime.runEmbeddedPython(PYTRA_EMBEDDED_SOURCE_BASE64, args);
        System.exit(code);
    }
}
