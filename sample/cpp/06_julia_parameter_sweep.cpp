#include "cpp_module/py_runtime.h"


// 06: ジュリア集合のパラメータを回してGIF出力するサンプル。

bytes julia_palette() {
    // 先頭色は集合内部用に黒固定、残りは高彩度グラデーションを作る。
    bytearray palette = bytearray(256 * 3);
    palette[0] = 0;
    palette[1] = 0;
    palette[2] = 0;
    for (int64 i = 1; i < 256; ++i) {
        float64 t = (static_cast<float64>(i - 1)) / 254.0;
        int64 r = int64(255.0 * 9.0 * (1.0 - t) * t * t * t);
        int64 g = int64(255.0 * 15.0 * (1.0 - t) * (1.0 - t) * t * t);
        int64 b = int64(255.0 * 8.5 * (1.0 - t) * (1.0 - t) * (1.0 - t) * t);
        palette[i * 3 + 0] = r;
        palette[i * 3 + 1] = g;
        palette[i * 3 + 2] = b;
    }
    return bytes(palette);
}

bytes render_frame(int64 width, int64 height, float64 cr, float64 ci, int64 max_iter, int64 phase) {
    bytearray frame = bytearray(width * height);
    int64 idx = 0;
    for (int64 y = 0; y < height; ++y) {
        float64 zy0 = -1.2 + 2.4 * (static_cast<float64>(y) / (static_cast<float64>(height - 1)));
        for (int64 x = 0; x < width; ++x) {
            float64 zx = -1.8 + 3.6 * (static_cast<float64>(x) / (static_cast<float64>(width - 1)));
            float64 zy = zy0;
            int64 i = 0;
            while (i < max_iter) {
                float64 zx2 = zx * zx;
                float64 zy2 = zy * zy;
                if (zx2 + zy2 > 4.0)
                    break;
                zy = 2.0 * zx * zy + ci;
                zx = zx2 - zy2 + cr;
                i++;
            }
            if (i >= max_iter) {
                frame[idx] = 0;
            } else {
                // フレーム位相を少し加えて色が滑らかに流れるようにする。
                int64 color_index = 1 + (py_floordiv(i * 224, max_iter) + phase) % 255;
                frame[idx] = color_index;
            }
            idx++;
        }
    }
    return bytes(frame);
}

void run_06_julia_parameter_sweep() {
    int64 width = 320;
    int64 height = 240;
    int64 frames_n = 72;
    int64 max_iter = 180;
    str out_path = "sample/out/06_julia_parameter_sweep.gif";
    
    std::any start = make_object(perf_counter());
    list<bytes> frames = list<bytes>{};
    // 既知の見栄えが良い近傍を楕円軌道で巡回し、単調な白飛びを抑える。
    float64 center_cr = -0.745;
    float64 center_ci = 0.186;
    float64 radius_cr = 0.12;
    float64 radius_ci = 0.1;
    // GitHub上のサムネイルで暗く見えないよう、開始位置と色位相にオフセットを入れる。
    // 赤みが強い色域から始まるように調整する。
    int64 start_offset = 20;
    int64 phase_offset = 180;
    for (int64 i = 0; i < frames_n; ++i) {
        float64 t = static_cast<float64>((i + start_offset) % frames_n) / static_cast<float64>(frames_n);
        std::any angle = make_object(2.0 * py_math::pi * t);
        std::any cr = make_object(center_cr + radius_cr * py_math::cos(angle));
        std::any ci = make_object(center_ci + radius_ci * py_math::sin(angle));
        int64 phase = (phase_offset + i * 5) % 255;
        frames.append(render_frame(width, height, cr, ci, max_iter, phase));
    }
    
    // bridge: Python gif.save_gif -> C++ runtime save_gif
    save_gif(out_path, width, height, frames, julia_palette(), 8, 0);
    std::any elapsed = make_object(perf_counter() - start);
    py_print("output:", out_path);
    py_print("frames:", frames_n);
    py_print("elapsed_sec:", elapsed);
}

int main(int argc, char** argv) {
    pytra_configure_from_argv(argc, argv);
    run_06_julia_parameter_sweep();
    return 0;
}
