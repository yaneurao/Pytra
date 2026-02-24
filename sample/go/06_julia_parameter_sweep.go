// このファイルは EAST ベース Go プレビュー出力です。
// TODO: 専用 GoEmitter 実装へ段階移行する。
package main

func main() {
    // C# ベース中間出力のシグネチャ要約:
    // public static class Program
    // // 06: Sample that sweeps Julia-set parameters and outputs a GIF.
    //
    // public static List<byte> julia_palette()
    // // Keep index 0 black for points inside the set; build a high-saturation gradient for the rest.
    //
    // public static List<byte> render_frame(long width, long height, double cr, double ci, long max_iter, long phase)
    // // Add a small frame phase so colors flow smoothly.
    //
    // public static void run_06_julia_parameter_sweep()
    //
    // // Orbit an ellipse around a known visually good region to reduce flat blown highlights.
    // // Add start and phase offsets so GitHub thumbnails do not appear too dark.
    // // Tune it to start in a red-leaning color range.
    //
    // public static void Main(string[] args)
}
