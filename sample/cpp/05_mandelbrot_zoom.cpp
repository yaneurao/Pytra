#include "cpp_module/py_runtime.h"


// 05: マンデルブロ集合ズームをアニメーションGIFとして出力するサンプル。

bytes render_frame(int64 width, int64 height, float64 center_x, float64 center_y, float64 scale, int64 max_iter) {
    bytearray frame = bytearray(width * height);
    int64 idx = 0;
    for (int64 y = 0; y < height; ++y) {
        float64 cy = center_y + (static_cast<float64>(y) - static_cast<float64>(height) * 0.5) * scale;
        for (int64 x = 0; x < width; ++x) {
            float64 cx = center_x + (static_cast<float64>(x) - static_cast<float64>(width) * 0.5) * scale;
            float64 zx = 0.0;
            float64 zy = 0.0;
            int64 i = 0;
            while (i < max_iter) {
                float64 zx2 = zx * zx;
                float64 zy2 = zy * zy;
                if (zx2 + zy2 > 4.0)
                    break;
                zy = 2.0 * zx * zy + cy;
                zx = zx2 - zy2 + cx;
                i++;
            }
            frame[idx] = int64(255.0 * static_cast<float64>(i) / static_cast<float64>(max_iter));
            idx++;
        }
    }
    return bytes(frame);
}

void run_05_mandelbrot_zoom() {
    int64 width = 320;
    int64 height = 240;
    int64 frame_count = 48;
    int64 max_iter = 110;
    float64 center_x = -0.743643887037151;
    float64 center_y = 0.13182590420533;
    float64 base_scale = 3.2 / static_cast<float64>(width);
    float64 zoom_per_frame = 0.93;
    str out_path = "sample/out/05_mandelbrot_zoom.gif";
    
    std::any start = make_object(perf_counter());
    list<bytes> frames = list<bytes>{};
    float64 scale = base_scale;
    for (int64 _ = 0; _ < frame_count; ++_) {
        frames.append(render_frame(width, height, center_x, center_y, scale, max_iter));
        scale *= zoom_per_frame;
    }
    
    // bridge: Python gif.save_gif -> C++ runtime save_gif
    save_gif(out_path, width, height, frames, grayscale_palette(), 5, 0);
    std::any elapsed = make_object(perf_counter() - start);
    py_print("output:", out_path);
    py_print("frames:", frame_count);
    py_print("elapsed_sec:", elapsed);
}

int main(int argc, char** argv) {
    pytra_configure_from_argv(argc, argv);
    run_05_mandelbrot_zoom();
    return 0;
}
