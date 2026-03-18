#include "runtime/cpp/native/core/py_runtime.h"
#include "runtime/cpp/native/core/process_runtime.h"
#include "runtime/cpp/native/core/scope_exit.h"
#include "generated/built_in/io_ops.h"
#include "generated/std/time.h"
#include "generated/utils/gif.h"

// 12: Sample that outputs intermediate states of bubble sort as a GIF.

bytes render(const rc<list<int64>>& values, int64 w, int64 h) {
    bytearray frame = bytearray(w * h);
    int64 n = (rc_list_ref(values)).size();
    float64 bar_w = float64(w) / float64(n);
    float64 __hoisted_cast_1 = float64(n);
    float64 __hoisted_cast_2 = float64(h);
    for (int64 i = 0; i < n; ++i) {
        int64 x0 = int64(float64(i) * bar_w);
        int64 x1 = int64((float64(i + 1)) * bar_w);
        if (x1 <= x0)
            x1 = x0 + 1;
        int64 bh = int64((float64(py_list_at_ref(rc_list_ref(values), i)) / __hoisted_cast_1) * __hoisted_cast_2);
        int64 y = h - bh;
        auto __for_start_1 = y;
        for (int64 y = __for_start_1; y < h; ++y) {
            for (int64 x = x0; x < x1; ++x)
                frame[y * w + x] = 255;
        }
    }
    return frame;
}

void run_12_sort_visualizer() {
    int64 w = 320;
    int64 h = 180;
    int64 n = 124;
    str out_path = "sample/out/12_sort_visualizer.gif";
    
    float64 start = pytra::std::time::perf_counter();
    rc<list<int64>> values = rc_list_from_value(list<int64>{});
    rc_list_ref(values).reserve((n <= 0) ? 0 : n);
    for (int64 i = 0; i < n; ++i)
        rc_list_ref(values).append((i * 37 + 19) % n);
    rc<list<bytes>> frames = rc_list_from_value(list<bytes>{render(values, w, h)});
    int64 frame_stride = 16;
    
    int64 op = 0;
    for (int64 i = 0; i < n; ++i) {
        bool swapped = false;
        for (int64 j = 0; j < n - i - 1; ++j) {
            if (py_list_at_ref(rc_list_ref(values), j) > py_list_at_ref(rc_list_ref(values), j + 1)) {
                ::std::swap(py_list_at_ref(rc_list_ref(values), j), py_list_at_ref(rc_list_ref(values), j + 1));
                swapped = true;
            }
            if (op % frame_stride == 0)
                rc_list_ref(frames).append(render(values, w, h));
            op++;
        }
        if (!(swapped))
            break;
    }
    pytra::utils::gif::save_gif(out_path, w, h, rc_list_ref(frames), pytra::utils::gif::grayscale_palette(), 3, 0);
    float64 elapsed = pytra::std::time::perf_counter() - start;
    py_print("output:", out_path);
    py_print("frames:", (rc_list_ref(frames)).size());
    py_print("elapsed_sec:", elapsed);
}

int main(int argc, char** argv) {
    pytra_configure_from_argv(argc, argv);
    run_12_sort_visualizer();
    return 0;
}
