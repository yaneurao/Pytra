#include "cpp_module/py_runtime.h"



list<uint8> render_julia(int64 width, int64 height, int64 max_iter, float64 cx, float64 cy) {
    float64 zy0;
    float64 zx;
    float64 zy;
    int64 i;
    float64 zx2;
    float64 zy2;
    int64 r;
    int64 g;
    int64 b;
    float64 t;
    
    list<uint8> pixels = list<uint8>{};
    
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
                zy = 2.0 * zx * zy + cy;
                zx = zx2 - zy2 + cx;
                i++;
            }
            
            r = 0;
            g = 0;
            b = 0;
            if (i >= max_iter) {
                r = 0;
                g = 0;
                b = 0;
            } else {
                t = static_cast<float64>(i) / static_cast<float64>(max_iter);
                r = int64(255.0 * (0.2 + 0.8 * t));
                g = int64(255.0 * (0.1 + 0.9 * t * t));
                b = int64(255.0 * (1.0 - t));
            }
            
            pixels.push_back(r);
            pixels.push_back(g);
            pixels.push_back(b);
        }
    }
    
    return pixels;
}

void run_julia() {
    int64 width = 3840;
    int64 height = 2160;
    int64 max_iter = 20000;
    str out_path = "sample/out/julia_03.png";
    
    float64 start = perf_counter();
    list<uint8> pixels = render_julia(width, height, max_iter, -0.8, 0.156);
    png_helper::write_rgb_png(out_path, width, height, pixels);
    float64 elapsed = perf_counter() - start;
    
    py_print("output:", out_path);
    py_print("size:", width, "x", height);
    py_print("max_iter:", max_iter);
    py_print("elapsed_sec:", elapsed);
}

int main() {
    run_julia();
    return 0;
}
