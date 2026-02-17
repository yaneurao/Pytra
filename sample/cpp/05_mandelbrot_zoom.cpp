#include "cpp_module/py_runtime.h"




list<uint8> render_frame(int64 width, int64 height, float64 center_x, float64 center_y, float64 scale, int64 max_iter) {
    float64 cy;
    float64 cx;
    float64 zx;
    float64 zy;
    int64 i;
    float64 zx2;
    float64 zy2;
    
    list<uint8> frame = list<uint8>(width * height);
    int64 idx = 0;
    for (int64 y = 0; y < height; ++y) {
        cy = center_y + (static_cast<float64>(y) - static_cast<float64>(height) * 0.5) * scale;
        for (int64 x = 0; x < width; ++x) {
            cx = center_x + (static_cast<float64>(x) - static_cast<float64>(width) * 0.5) * scale;
            zx = 0.0;
            zy = 0.0;
            i = 0;
            while (i < max_iter) {
                zx2 = zx * zx;
                zy2 = zy * zy;
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
    return list<uint8>(frame);
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
    
    float64 start = perf_counter();
    list<list<uint8>> frames = list<list<uint8>>{};
    float64 scale = base_scale;
    for (int64 _ = 0; _ < frame_count; ++_) {
        frames.push_back(render_frame(width, height, center_x, center_y, scale, max_iter));
        scale *= zoom_per_frame;
    }
    
    save_gif(out_path, width, height, frames, grayscale_palette(), 5, 0);
    float64 elapsed = perf_counter() - start;
    py_print("output:", out_path);
    py_print("frames:", frame_count);
    py_print("elapsed_sec:", elapsed);
}

int main() {
    run_05_mandelbrot_zoom();
    return 0;
}
