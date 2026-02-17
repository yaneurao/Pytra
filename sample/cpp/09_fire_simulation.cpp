#include "cpp_module/py_runtime.h"




list<uint8> fire_palette() {
    int64 r;
    int64 g;
    int64 b;
    
    list<uint8> p = list<uint8>{};
    for (int64 i = 0; i < 256; ++i) {
        r = 0;
        g = 0;
        b = 0;
        if (i < 85) {
            r = i * 3;
            g = 0;
            b = 0;
        } else {
            if (i < 170) {
                r = 255;
                g = (i - 85) * 3;
                b = 0;
            } else {
                r = 255;
                g = 255;
                b = (i - 170) * 3;
            }
        }
        p.push_back(r);
        p.push_back(g);
        p.push_back(b);
    }
    return list<uint8>(p);
}

void run_09_fire_simulation() {
    int64 val;
    int64 a;
    int64 b;
    int64 c;
    int64 d;
    int64 v;
    int64 cool;
    int64 nv;
    list<uint8> frame;
    int64 i;
    int64 x;
    
    int64 w = 380;
    int64 h = 260;
    int64 steps = 420;
    str out_path = "sample/out/09_fire_simulation.gif";
    
    float64 start = perf_counter();
    list<list<int64>> heat = [&]() -> list<list<int64>> {     list<list<int64>> __out;     for (int64 _ = 0; (_ < h); _ += (1)) {         __out.push_back(py_repeat(list<int64>{0}, w));     }     return __out; }();
    list<list<uint8>> frames = list<list<uint8>>{};
    
    for (int64 t = 0; t < steps; ++t) {
        for (x = 0; x < w; ++x) {
            val = 170 + (x * 13 + t * 17) % 86;
            heat[h - 1][x] = val;
        }
        
        for (int64 y = 1; y < h; ++y) {
            for (x = 0; x < w; ++x) {
                a = heat[y][x];
                b = heat[y][(x - 1 + w) % w];
                c = heat[y][(x + 1) % w];
                d = heat[(y + 1) % h][x];
                v = py_floordiv((a + b + c + d), 4);
                cool = 1 + (x + y + t) % 3;
                nv = v - cool;
                heat[y - 1][x] = (nv > 0 ? nv : 0);
            }
        }
        
        frame = list<uint8>(w * h);
        i = 0;
        for (int64 yy = 0; yy < h; ++yy) {
            for (int64 xx = 0; xx < w; ++xx) {
                frame[i] = heat[yy][xx];
                i++;
            }
        }
        frames.push_back(list<uint8>(frame));
    }
    
    save_gif(out_path, w, h, frames, fire_palette(), 4, 0);
    float64 elapsed = perf_counter() - start;
    py_print("output:", out_path);
    py_print("frames:", steps);
    py_print("elapsed_sec:", elapsed);
}

int main() {
    run_09_fire_simulation();
    return 0;
}
