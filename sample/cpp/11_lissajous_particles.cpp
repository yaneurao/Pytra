#include "cpp_module/py_runtime.h"





list<uint8> color_palette() {
    int64 r;
    int64 g;
    int64 b;
    
    list<uint8> p = list<uint8>{};
    for (int64 i = 0; i < 256; ++i) {
        r = i;
        g = i * 3 % 256;
        b = 255 - i;
        p.push_back(r);
        p.push_back(g);
        p.push_back(b);
    }
    return list<uint8>(p);
}

void run_11_lissajous_particles() {
    list<uint8> frame;
    float64 phase;
    int64 x;
    int64 y;
    int64 color;
    int64 xx;
    int64 yy;
    int64 d2;
    int64 idx;
    int64 v;
    
    int64 w = 320;
    int64 h = 240;
    int64 frames_n = 360;
    int64 particles = 48;
    str out_path = "sample/out/11_lissajous_particles.gif";
    
    float64 start = perf_counter();
    list<list<uint8>> frames = list<list<uint8>>{};
    
    for (int64 t = 0; t < frames_n; ++t) {
        frame = list<uint8>(w * h);
        
        for (int64 p = 0; p < particles; ++p) {
            phase = static_cast<float64>(p) * 0.261799;
            x = int64(static_cast<float64>(w) * 0.5 + static_cast<float64>(w) * 0.38 * py_math::sin(0.11 * static_cast<float64>(t) + phase * 2.0));
            y = int64(static_cast<float64>(h) * 0.5 + static_cast<float64>(h) * 0.38 * py_math::sin(0.17 * static_cast<float64>(t) + phase * 3.0));
            color = 30 + p * 9 % 220;
            
            for (int64 dy = -2; dy < 3; ++dy) {
                for (int64 dx = -2; dx < 3; ++dx) {
                    xx = x + dx;
                    yy = y + dy;
                    if ((xx >= 0) && (xx < w) && (yy >= 0) && (yy < h)) {
                        d2 = dx * dx + dy * dy;
                        if (d2 <= 4) {
                            idx = yy * w + xx;
                            v = color - d2 * 20;
                            v = std::max<int64>(static_cast<int64>(0), static_cast<int64>(v));
                            if (v > frame[idx])
                                frame[idx] = v;
                        }
                    }
                }
            }
        }
        
        frames.push_back(list<uint8>(frame));
    }
    
    save_gif(out_path, w, h, frames, color_palette(), 3, 0);
    float64 elapsed = perf_counter() - start;
    py_print("output:", out_path);
    py_print("frames:", frames_n);
    py_print("elapsed_sec:", elapsed);
}

int main() {
    run_11_lissajous_particles();
    return 0;
}
