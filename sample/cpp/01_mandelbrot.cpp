#include "cpp_module/py_runtime.h"

// 01: マンデルブロ集合を PNG 画像として出力するサンプルです。
// 将来のトランスパイルを意識して、構文はなるべく素直に書いています。

int64 escape_count(float64 cx, float64 cy, int64 max_iter) {
    float64 x2;
    float64 y2;
    
    /* ""1点 (cx, cy) の発散までの反復回数を返す。"" */
    float64 x = 0.0;
    float64 y = 0.0;
    for (int64 i = 0; i < max_iter; ++i) {
        x2 = x * x;
        y2 = y * y;
        if (x2 + y2 > 4.0)
            return i;
        y = 2.0 * x * y + cy;
        x = x2 - y2 + cx;
    }
    return max_iter;
}

std::tuple<int64, int64, int64> color_map(int64 iter_count, int64 max_iter) {
    /* ""反復回数を RGB に変換する。"" */
    if (iter_count >= max_iter)
        return std::make_tuple(0, 0, 0);
    
    // 簡単なグラデーション（青系 -> 黄系）
    float64 t = static_cast<float64>(iter_count) / static_cast<float64>(max_iter);
    int64 r = int64(255.0 * t * t);
    int64 g = int64(255.0 * t);
    int64 b = int64(255.0 * (1.0 - t));
    return std::make_tuple(r, g, b);
}

list<uint8> render_mandelbrot(int64 width, int64 height, int64 max_iter, float64 x_min, float64 x_max, float64 y_min, float64 y_max) {
    float64 py;
    float64 px;
    int64 it;
    int64 r;
    int64 g;
    int64 b;
    float64 t;
    
    /* ""マンデルブロ画像の RGB バイト列を生成する。"" */
    list<uint8> pixels = list<uint8>{};
    
    for (int64 y = 0; y < height; ++y) {
        py = y_min + (y_max - y_min) * static_cast<float64>(y) / (static_cast<float64>(height - 1));
        
        for (int64 x = 0; x < width; ++x) {
            px = x_min + (x_max - x_min) * static_cast<float64>(x) / (static_cast<float64>(width - 1));
            it = escape_count(px, py, max_iter);
            if (it >= max_iter) {
                r = 0;
                g = 0;
                b = 0;
            } else {
                t = static_cast<float64>(it) / static_cast<float64>(max_iter);
                r = int64(255.0 * t * t);
                g = int64(255.0 * t);
                b = int64(255.0 * (1.0 - t));
            }
            pixels.push_back(r);
            pixels.push_back(g);
            pixels.push_back(b);
        }
    }
    
    return pixels;
}

void run_mandelbrot() {
    int64 width = 1600;
    int64 height = 1200;
    int64 max_iter = 1000;
    str out_path = "sample/out/mandelbrot_01.png";
    
    float64 start = perf_counter();
    
    list<uint8> pixels = render_mandelbrot(width, height, max_iter, -2.2, 1.0, -1.2, 1.2);
    png_helper::write_rgb_png(out_path, width, height, pixels);
    
    float64 elapsed = perf_counter() - start;
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
