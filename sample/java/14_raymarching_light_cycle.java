// このファイルは EAST -> JS bridge 用の Java 実行ラッパです。
import java.util.ArrayList;
import java.util.List;

public final class Pytra_14_raymarching_light_cycle {
    private Pytra_14_raymarching_light_cycle() {
    }

    public static void main(String[] args) throws Exception {
        List<String> command = new ArrayList<>();
        command.add("node");
        command.add("sample/java/14_raymarching_light_cycle.js");
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
