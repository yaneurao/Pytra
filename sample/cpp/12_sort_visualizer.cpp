#include "cpp_module/py_runtime.h"


// 12: バブルソートの途中状態をGIF出力するサンプル。

bytes render(const list<int64>& values, int64 w, int64 h) {
    bytearray frame = bytearray(w * h);
    int64 n = py_len(values);
    float64 bar_w = static_cast<float64>(w) / static_cast<float64>(n);
    for (int64 i = 0; i < n; ++i) {
        int64 x0 = int64(static_cast<float64>(i) * bar_w);
        int64 x1 = int64((static_cast<float64>(i + 1)) * bar_w);
        if (x1 <= x0)
            x1 = x0 + 1;
        int64 bh = int64((static_cast<float64>(values[i]) / static_cast<float64>(n)) * static_cast<float64>(h));
        int64 y = h - bh;
        for (int64 y = y; y < h; ++y) {
            for (int64 x = x0; x < x1; ++x)
                frame[y * w + x] = 255;
        }
    }
    return bytes(frame);
}

void run_12_sort_visualizer() {
    int64 w = 320;
    int64 h = 180;
    int64 n = 124;
    str out_path = "sample/out/12_sort_visualizer.gif";
    
    std::any start = make_object(perf_counter());
    list<int64> values = list<int64>{};
    for (int64 i = 0; i < n; ++i)
        values.append((i * 37 + 19) % n);
    
    list<bytes> frames = list<bytes>{render(values, w, h)};
    
    int64 op = 0;
    for (int64 i = 0; i < n; ++i) {
        bool swapped = false;
        for (int64 j = 0; j < n - i - 1; ++j) {
            if (values[j] > values[j + 1]) {
                std::swap(values[j], values[j + 1]);
                swapped = true;
            }
            if (op % 8 == 0)
                frames.append(render(values, w, h));
            op++;
        }
        if (!(swapped))
            break;
    }
    
    // bridge: Python gif.save_gif -> C++ runtime save_gif
    save_gif(out_path, w, h, frames, grayscale_palette(), 3, 0);
    std::any elapsed = make_object(perf_counter() - start);
    py_print("output:", out_path);
    py_print("frames:", py_len(frames));
    py_print("elapsed_sec:", elapsed);
}

int main(int argc, char** argv) {
    pytra_configure_from_argv(argc, argv);
    run_12_sort_visualizer();
    return 0;
}
