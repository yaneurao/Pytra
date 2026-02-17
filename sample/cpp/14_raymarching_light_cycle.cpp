#include "cpp_module/py_runtime.h"





list<uint8> palette() {
    int64 r;
    int64 g;
    int64 b;
    
    list<uint8> p = list<uint8>{};
    for (int64 i = 0; i < 256; ++i) {
        r = std::min<int64>(static_cast<int64>(255), static_cast<int64>(int64(static_cast<float64>(20) + static_cast<float64>(i) * 0.9)));
        g = std::min<int64>(static_cast<int64>(255), static_cast<int64>(int64(static_cast<float64>(10) + static_cast<float64>(i) * 0.7)));
        b = std::min<int64>(static_cast<int64>(255), static_cast<int64>(int64(30 + i)));
        p.push_back(r);
        p.push_back(g);
        p.push_back(b);
    }
    return list<uint8>(p);
}

int64 scene(float64 x, float64 y, float64 light_x, float64 light_y) {
    float64 x1 = x + 0.45;
    float64 y1 = y + 0.2;
    float64 x2 = x - 0.35;
    float64 y2 = y - 0.15;
    float64 r1 = py_math::sqrt(x1 * x1 + y1 * y1);
    float64 r2 = py_math::sqrt(x2 * x2 + y2 * y2);
    float64 blob = py_math::exp(-7.0 * r1 * r1) + py_math::exp(-8.0 * r2 * r2);
    
    float64 lx = x - light_x;
    float64 ly = y - light_y;
    float64 l = py_math::sqrt(lx * lx + ly * ly);
    float64 lit = 1.0 / (1.0 + 3.5 * l * l);
    
    int64 v = int64(255.0 * blob * lit * 5.0);
    return std::min<int64>(static_cast<int64>(255), static_cast<int64>(std::max<int64>(static_cast<int64>(0), static_cast<int64>(v))));
}

void run_14_raymarching_light_cycle() {
    list<uint8> frame;
    float64 a;
    float64 light_x;
    float64 light_y;
    int64 i;
    float64 py;
    float64 px;
    
    int64 w = 320;
    int64 h = 240;
    int64 frames_n = 84;
    str out_path = "sample/out/14_raymarching_light_cycle.gif";
    
    float64 start = perf_counter();
    list<list<uint8>> frames = list<list<uint8>>{};
    
    for (int64 t = 0; t < frames_n; ++t) {
        frame = list<uint8>(w * h);
        a = static_cast<float64>(t) / static_cast<float64>(frames_n) * py_math::pi * 2.0;
        light_x = 0.75 * py_math::cos(a);
        light_y = 0.55 * py_math::sin(a * 1.2);
        
        i = 0;
        for (int64 y = 0; y < h; ++y) {
            py = static_cast<float64>(y) / (static_cast<float64>(h - 1)) * 2.0 - 1.0;
            for (int64 x = 0; x < w; ++x) {
                px = static_cast<float64>(x) / (static_cast<float64>(w - 1)) * 2.0 - 1.0;
                frame[i] = scene(px, py, light_x, light_y);
                i++;
            }
        }
        
        frames.push_back(list<uint8>(frame));
    }
    
    save_gif(out_path, w, h, frames, palette(), 3, 0);
    float64 elapsed = perf_counter() - start;
    py_print("output:", out_path);
    py_print("frames:", frames_n);
    py_print("elapsed_sec:", elapsed);
}

int main() {
    run_14_raymarching_light_cycle();
    return 0;
}
