#include "runtime/cpp/pytra/built_in/py_runtime.h"

#include "pytra/std/math.h"
#include "pytra/std/time.h"
#include "pytra/utils/gif.h"





bytes julia_palette() {
    bytearray palette = bytearray(256 * 3);
    palette[0] = 0;
    palette[1] = 0;
    palette[2] = 0;
    for (int64 i = 1; i < 256; ++i) {
        float64 t = (py_to_float64(i - 1)) / 254.0;
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
    for (int64 y = 0; y < height; ++y) {
        int64 row_base = y * width;
        float64 zy0 = -1.2 + 2.4 * (py_to_float64(y) / (py_to_float64(height - 1)));
        for (int64 x = 0; x < width; ++x) {
            float64 zx = -1.8 + 3.6 * (py_to_float64(x) / (py_to_float64(width - 1)));
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
                frame[row_base + x] = 0;
            } else {
                int64 color_index = 1 + (i * 224 / max_iter + phase) % 255;
                frame[row_base + x] = color_index;
            }
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
    auto start = pytra::std::time::perf_counter();
    list<bytes> frames = list<bytes>{};
    float64 center_cr = -0.745;
    float64 center_ci = 0.186;
    float64 radius_cr = 0.12;
    float64 radius_ci = 0.10;
    int64 start_offset = 20;
    int64 phase_offset = 180;
    for (int64 i = 0; i < frames_n; ++i) {
        float64 t = py_to_float64((i + start_offset) % frames_n) / py_to_float64(frames_n);
        float64 angle = 2.0 * pytra::std::math::pi * t;
        float64 cr = center_cr + radius_cr * pytra::std::math::cos(angle);
        float64 ci = center_ci + radius_ci * pytra::std::math::sin(angle);
        int64 phase = (phase_offset + i * 5) % 255;
        frames.append(bytes(render_frame(width, height, cr, ci, max_iter, phase)));
    }
    pytra::utils::gif::save_gif(out_path, width, height, frames, julia_palette(), int64(py_to_int64(8)), int64(py_to_int64(0)));
    auto elapsed = pytra::std::time::perf_counter() - start;
    py_print("output:", out_path);
    py_print("frames:", frames_n);
    py_print("elapsed_sec:", elapsed);
}

int main(int argc, char** argv) {
    pytra_configure_from_argv(argc, argv);
    run_06_julia_parameter_sweep();
    return 0;
}
