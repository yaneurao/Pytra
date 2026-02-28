#include "runtime/cpp/pytra/built_in/py_runtime.h"

#include "pytra/std/time.h"
#include "pytra/utils/png.h"

// 01: Sample that outputs the Mandelbrot set as a PNG image.
// Syntax is kept straightforward with future transpilation in mind.

int64 escape_count(float64 cx, float64 cy, int64 max_iter) {
    /* Return the iteration count until divergence for one point (cx, cy). */
    float64 x = 0.0;
    float64 y = 0.0;
    for (int64 i = 0; i < max_iter; ++i) {
        float64 x2 = x * x;
        float64 y2 = y * y;
        if (x2 + y2 > 4.0)
            return i;
        y = 2.0 * x * y + cy;
        x = x2 - y2 + cx;
    }
    return max_iter;
}

::std::tuple<int64, int64, int64> color_map(int64 iter_count, int64 max_iter) {
    /* Convert an iteration count to RGB. */
    if (iter_count >= max_iter)
        return ::std::make_tuple(0, 0, 0);
    float64 t = py_div(py_to<float64>(iter_count), py_to<float64>(max_iter));
    int64 r = int64(255.0 * t * t);
    int64 g = int64(255.0 * t);
    int64 b = int64(255.0 * (1.0 - t));
    return ::std::make_tuple(r, g, b);
}

bytearray render_mandelbrot(int64 width, int64 height, int64 max_iter, float64 x_min, float64 x_max, float64 y_min, float64 y_max) {
    /* Generate RGB bytes for a Mandelbrot image. */
    bytearray pixels = bytearray{};
    float64 __hoisted_cast_1 = static_cast<float64>(height - 1);
    float64 __hoisted_cast_2 = static_cast<float64>(width - 1);
    float64 __hoisted_cast_3 = static_cast<float64>(max_iter);
    
    for (int64 y = 0; y < height; ++y) {
        float64 py = y_min + (y_max - y_min) * (py_div(py_to<float64>(y), __hoisted_cast_1));
        
        for (int64 x = 0; x < width; ++x) {
            float64 px = x_min + (x_max - x_min) * (py_div(py_to<float64>(x), __hoisted_cast_2));
            int64 it = escape_count(px, py, max_iter);
            int64 r;
            int64 g;
            int64 b;
            if (it >= max_iter) {
                r = 0;
                g = 0;
                b = 0;
            } else {
                float64 t = py_div(py_to<float64>(it), __hoisted_cast_3);
                r = int64(255.0 * t * t);
                g = int64(255.0 * t);
                b = int64(255.0 * (1.0 - t));
            }
            pixels.append(r);
            pixels.append(g);
            pixels.append(b);
        }
    }
    return pixels;
}

void run_mandelbrot() {
    int64 width = 1600;
    int64 height = 1200;
    int64 max_iter = 1000;
    str out_path = "sample/out/01_mandelbrot.png";
    
    float64 start = pytra::std::time::perf_counter();
    
    bytearray pixels = render_mandelbrot(width, height, max_iter, -2.2, 1.0, -1.2, 1.2);
    pytra::utils::png::write_rgb_png(out_path, width, height, pixels);
    
    float64 elapsed = pytra::std::time::perf_counter() - start;
    py_print("output:", out_path);
    py_print("size:", width, "x", height);
    py_print("max_iter:", max_iter);
    py_print("elapsed_sec:", elapsed);
}

int main(int argc, char** argv) {
    pytra_configure_from_argv(argc, argv);
    run_mandelbrot();
    return 0;
}
