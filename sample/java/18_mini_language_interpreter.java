// このファイルは EAST -> JS bridge 用の Java 実行ラッパです。
import java.util.ArrayList;
import java.util.List;

public final class Pytra_18_mini_language_interpreter {
    private Pytra_18_mini_language_interpreter() {
    }

    public static void main(String[] args) throws Exception {
        List<String> command = new ArrayList<>();
        command.add("node");
        command.add("sample/java/18_mini_language_interpreter.js");
        for (String arg : args) {
            command.add(arg);
        }
        Process process = new ProcessBuilder(command)
            .inheritIO()
            .start();
        int code = process.waitFor();
        if (code != 0) {
            System.exit(code);
        }
    }
}
