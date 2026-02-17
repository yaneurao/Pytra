#include "cpp_module/py_runtime.h"




list<uint8> render(list<int64> values, int64 w, int64 h) {
    int64 x0;
    int64 x1;
    int64 bh;
    int64 y;
    
    list<uint8> frame = list<uint8>(w * h);
    int64 n = py_len(values);
    float64 bar_w = static_cast<float64>(w) / static_cast<float64>(n);
    for (int64 i = 0; i < n; ++i) {
        x0 = int64(static_cast<float64>(i) * bar_w);
        x1 = int64((static_cast<float64>(i + 1)) * bar_w);
        if (x1 <= x0)
            x1 = x0 + 1;
        bh = int64(static_cast<float64>(values[i]) / static_cast<float64>(n) * static_cast<float64>(h));
        y = h - bh;
        for (y = y; y < h; ++y) {
            for (int64 x = x0; x < x1; ++x)
                frame[y * w + x] = 255;
        }
    }
    return list<uint8>(frame);
}

void run_12_sort_visualizer() {
    bool swapped;
    int64 i;
    
    int64 w = 320;
    int64 h = 180;
    int64 n = 124;
    str out_path = "sample/out/12_sort_visualizer.gif";
    
    float64 start = perf_counter();
    list<int64> values = list<int64>{};
    for (i = 0; i < n; ++i)
        values.push_back((i * 37 + 19) % n);
    
    list<list<uint8>> frames = list<list<uint8>>{render(values, w, h)};
    
    int64 op = 0;
    for (i = 0; i < n; ++i) {
        swapped = false;
        for (int64 j = 0; j < n - i - 1; ++j) {
            if (values[j] > values[j + 1]) {
                auto __tuple_1 = std::make_tuple(values[j + 1], values[j]);
                values[j] = std::get<0>(__tuple_1);
                values[j + 1] = std::get<1>(__tuple_1);
                swapped = true;
            }
            if (op % 8 == 0)
                frames.push_back(render(values, w, h));
            op++;
        }
        if (!(swapped))
            break;
    }
    
    save_gif(out_path, w, h, frames, grayscale_palette(), 3, 0);
    float64 elapsed = perf_counter() - start;
    py_print("output:", out_path);
    py_print("frames:", py_len(frames));
    py_print("elapsed_sec:", elapsed);
}

int main() {
    run_12_sort_visualizer();
    return 0;
}
