#include "runtime/cpp/pytra/built_in/py_runtime.h"

#include "pytra/std/time.h"
#include "pytra/utils/png.h"

// 04: Sample that renders an orbit-trap Julia set and writes a PNG image.

bytearray render_orbit_trap_julia(int64 width, int64 height, int64 max_iter, float64 cx, float64 cy) {
    bytearray pixels = bytearray{};
    float64 __hoisted_cast_1 = static_cast<float64>(height - 1);
    float64 __hoisted_cast_2 = static_cast<float64>(width - 1);
    float64 __hoisted_cast_3 = static_cast<float64>(max_iter);
    
    for (int64 y = 0; y < height; ++y) {
        float64 zy0 = -1.3 + 2.6 * (py_to<float64>(y) / __hoisted_cast_1);
        for (int64 x = 0; x < width; ++x) {
            float64 zx = -1.9 + 3.8 * (py_to<float64>(x) / __hoisted_cast_2);
            float64 zy = zy0;
            
            float64 trap = 1.0e9;
            int64 i = 0;
            while (i < max_iter) {
                float64 ax = zx;
                if (ax < 0.0)
                    ax = -ax;
                float64 ay = zy;
                if (ay < 0.0)
                    ay = -ay;
                float64 dxy = zx - zy;
                if (dxy < 0.0)
                    dxy = -dxy;
                if (ax < trap)
                    trap = ax;
                if (ay < trap)
                    trap = ay;
                if (dxy < trap)
                    trap = dxy;
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
                float64 trap_scaled = trap * 3.2;
                if (trap_scaled > 1.0)
                    trap_scaled = 1.0;
                if (trap_scaled < 0.0)
                    trap_scaled = 0.0;
                float64 t = py_to<float64>(i) / __hoisted_cast_3;
                int64 tone = int64(255.0 * (1.0 - trap_scaled));
                r = int64(py_to<float64>(tone) * (0.35 + 0.65 * t));
                g = int64(py_to<float64>(tone) * (0.15 + 0.85 * (1.0 - t)));
                b = int64(255.0 * (0.25 + 0.75 * t));
                if (r > 255)
                    r = 255;
                if (g > 255)
                    g = 255;
                if (b > 255)
                    b = 255;
            }
            pixels.append(r);
            pixels.append(g);
            pixels.append(b);
        }
    }
    return pixels;
}

void run_04_orbit_trap_julia() {
    int64 width = 1920;
    int64 height = 1080;
    int64 max_iter = 1400;
    str out_path = "sample/out/04_orbit_trap_julia.png";
    
    float64 start = pytra::std::time::perf_counter();
    bytearray pixels = render_orbit_trap_julia(width, height, max_iter, -0.7269, 0.1889);
    pytra::utils::png::write_rgb_png(out_path, width, height, pixels);
    float64 elapsed = pytra::std::time::perf_counter() - start;
    
    py_print("output:", out_path);
    py_print("size:", width, "x", height);
    py_print("max_iter:", max_iter);
    py_print("elapsed_sec:", elapsed);
}

int main(int argc, char** argv) {
    pytra_configure_from_argv(argc, argv);
    run_04_orbit_trap_julia();
    return 0;
}
