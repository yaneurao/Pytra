#include "runtime/cpp/pytra/built_in/py_runtime.h"

#include "pytra/std/time.h"
#include "pytra/utils/gif.h"

// 05: Sample that outputs a Mandelbrot zoom as an animated GIF.

bytes render_frame(int64 width, int64 height, float64 center_x, float64 center_y, float64 scale, int64 max_iter) {
    bytearray frame = bytearray(width * height);
    float64 __hoisted_cast_1 = float64(max_iter);
    for (int64 y = 0; y < height; ++y) {
        int64 row_base = y * width;
        float64 cy = center_y + (py_to<float64>(y) - py_to<float64>(height) * 0.5) * scale;
        for (int64 x = 0; x < width; ++x) {
            float64 cx = center_x + (py_to<float64>(x) - py_to<float64>(width) * 0.5) * scale;
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
            frame[row_base + x] = int64(255.0 * py_to<float64>(i) / __hoisted_cast_1);
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
    float64 base_scale = 3.2 / py_to<float64>(width);
    float64 zoom_per_frame = 0.93;
    str out_path = "sample/out/05_mandelbrot_zoom.gif";
    
    float64 start = pytra::std::time::perf_counter();
    list<bytes> frames = list<bytes>{};
    float64 scale = base_scale;
    for (int64 _ = 0; _ < frame_count; ++_) {
        frames.append(render_frame(width, height, center_x, center_y, scale, max_iter));
        scale *= zoom_per_frame;
    }
    pytra::utils::gif::save_gif(out_path, width, height, frames, pytra::utils::gif::grayscale_palette(), 5, 0);
    float64 elapsed = pytra::std::time::perf_counter() - start;
    py_print("output:", out_path);
    py_print("frames:", frame_count);
    py_print("elapsed_sec:", elapsed);
}

int main(int argc, char** argv) {
    pytra_configure_from_argv(argc, argv);
    run_05_mandelbrot_zoom();
    return 0;
}
