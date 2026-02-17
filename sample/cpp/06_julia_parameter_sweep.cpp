#include "cpp_module/py_runtime.h"





list<uint8> julia_palette() {
    float64 t;
    int64 r;
    int64 g;
    int64 b;
    
    list<uint8> palette = list<uint8>(256 * 3);
    palette[0] = 0;
    palette[1] = 0;
    palette[2] = 0;
    for (int64 i = 1; i < 256; ++i) {
        t = (static_cast<float64>(i - 1)) / 254.0;
        r = int64(255.0 * 9.0 * (1.0 - t) * t * t * t);
        g = int64(255.0 * 15.0 * (1.0 - t) * (1.0 - t) * t * t);
        b = int64(255.0 * 8.5 * (1.0 - t) * (1.0 - t) * (1.0 - t) * t);
        palette[i * 3 + 0] = r;
        palette[i * 3 + 1] = g;
        palette[i * 3 + 2] = b;
    }
    return list<uint8>(palette);
}

list<uint8> render_frame(int64 width, int64 height, float64 cr, float64 ci, int64 max_iter, int64 phase) {
    float64 zy0;
    float64 zx;
    float64 zy;
    int64 i;
    float64 zx2;
    float64 zy2;
    int64 color_index;
    
    list<uint8> frame = list<uint8>(width * height);
    int64 idx = 0;
    for (int64 y = 0; y < height; ++y) {
        zy0 = -1.2 + 2.4 * static_cast<float64>(y) / (static_cast<float64>(height - 1));
        for (int64 x = 0; x < width; ++x) {
            zx = -1.8 + 3.6 * static_cast<float64>(x) / (static_cast<float64>(width - 1));
            zy = zy0;
            i = 0;
            while (i < max_iter) {
                zx2 = zx * zx;
                zy2 = zy * zy;
                if (zx2 + zy2 > 4.0)
                    break;
                zy = 2.0 * zx * zy + ci;
                zx = zx2 - zy2 + cr;
                i++;
            }
            if (i >= max_iter) {
                frame[idx] = 0;
            } else {
                color_index = 1 + (py_floordiv(i * 224, max_iter) + phase) % 255;
                frame[idx] = color_index;
            }
            idx++;
        }
    }
    return list<uint8>(frame);
}

void run_06_julia_parameter_sweep() {
    float64 t;
    float64 angle;
    float64 cr;
    float64 ci;
    int64 phase;
    
    int64 width = 320;
    int64 height = 240;
    int64 frames_n = 72;
    int64 max_iter = 180;
    str out_path = "sample/out/06_julia_parameter_sweep.gif";
    
    float64 start = perf_counter();
    list<list<uint8>> frames = list<list<uint8>>{};
    
    float64 center_cr = -0.745;
    float64 center_ci = 0.186;
    float64 radius_cr = 0.12;
    float64 radius_ci = 0.1;
    
    
    int64 start_offset = 20;
    int64 phase_offset = 180;
    for (int64 i = 0; i < frames_n; ++i) {
        t = static_cast<float64>((i + start_offset) % frames_n) / static_cast<float64>(frames_n);
        angle = 2.0 * py_math::pi * t;
        cr = center_cr + radius_cr * py_math::cos(angle);
        ci = center_ci + radius_ci * py_math::sin(angle);
        phase = (phase_offset + i * 5) % 255;
        frames.push_back(render_frame(width, height, cr, ci, max_iter, phase));
    }
    
    save_gif(out_path, width, height, frames, julia_palette(), 8, 0);
    float64 elapsed = perf_counter() - start;
    py_print("output:", out_path);
    py_print("frames:", frames_n);
    py_print("elapsed_sec:", elapsed);
}

int main() {
    run_06_julia_parameter_sweep();
    return 0;
}
