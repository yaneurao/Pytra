#include "runtime/cpp/pytra/built_in/py_runtime.h"

#include "pytra/std/time.h"
#include "pytra/utils/png.h"

// 03: Sample that outputs a Julia set as a PNG image.
// Implemented with simple loop-centric logic for transpilation compatibility.

bytearray render_julia(int64 width, int64 height, int64 max_iter, float64 cx, float64 cy) {
    bytearray pixels = bytearray{};
    float64 __hoisted_cast_1 = float64(height - 1);
    float64 __hoisted_cast_2 = float64(width - 1);
    float64 __hoisted_cast_3 = float64(max_iter);
    
    for (int64 y = 0; y < height; ++y) {
        float64 zy0 = -1.2 + 2.4 * (py_to<float64>(y) / __hoisted_cast_1);
        
        for (int64 x = 0; x < width; ++x) {
            float64 zx = -1.8 + 3.6 * (py_to<float64>(x) / __hoisted_cast_2);
            float64 zy = zy0;
            
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
            int64 r = 0;
            int64 g = 0;
            int64 b = 0;
            if (i >= max_iter) {
                r = 0;
                g = 0;
                b = 0;
            } else {
                float64 t = py_to<float64>(i) / __hoisted_cast_3;
                r = int64(255.0 * (0.2 + 0.8 * t));
                g = int64(255.0 * (0.1 + 0.9 * t * t));
                b = int64(255.0 * (1.0 - t));
            }
            pixels.append(r);
            pixels.append(g);
            pixels.append(b);
        }
    }
    return pixels;
}

void run_julia() {
    int64 width = 3840;
    int64 height = 2160;
    int64 max_iter = 20000;
    str out_path = "sample/out/03_julia_set.png";
    
    float64 start = pytra::std::time::perf_counter();
    bytearray pixels = render_julia(width, height, max_iter, -0.8, 0.156);
    pytra::utils::png::write_rgb_png(out_path, width, height, pixels);
    float64 elapsed = pytra::std::time::perf_counter() - start;
    
    py_print("output:", out_path);
    py_print("size:", width, "x", height);
    py_print("max_iter:", max_iter);
    py_print("elapsed_sec:", elapsed);
}

int main(int argc, char** argv) {
    pytra_configure_from_argv(argc, argv);
    run_julia();
    return 0;
}
