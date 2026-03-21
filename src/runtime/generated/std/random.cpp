#include "core/py_runtime.h"
#include "core/process_runtime.h"
#include "std/math.h"

list<int64> _state_box;
list<int64> _gauss_has_spare;
list<float64> _gauss_spare;

/* pytra.std.random: minimal deterministic random helpers.

This module is intentionally self-contained and avoids Python stdlib imports,
so it can be transpiled to target runtimes.
 */

void seed(int64 value) {
    /* Set generator seed (32-bit). */
    int64 v = value & 2147483647;
    if (v == 0)
        v = 1;
    _state_box[0] = v;
    _gauss_has_spare[0] = 0;
}

int64 _next_u31() {
    /* Advance internal LCG and return a 31-bit value. */
    int64 s = _state_box[0];
    s = 1103515245 * s + 12345 & 2147483647;
    _state_box[0] = s;
    return s;
}

float64 random() {
    /* Return pseudo-random float in [0.0, 1.0). */
    return float64(_next_u31()) / 2147483648.0;
}

int64 randint(int64 a, int64 b) {
    /* Return pseudo-random integer in [a, b]. */
    int64 lo = a;
    int64 hi = b;
    if (hi < lo)
        ::std::swap(lo, hi);
    int64 span = hi - lo + 1;
    return lo + int64(random() * float64(span));
}

rc<list<int64>> choices(const rc<list<int64>>& population, const rc<list<float64>>& weights, int64 k = 1) {
    /* Return k sampled elements with replacement.

    Supported call forms:
    - choices(population, weights)
    - choices(population, weights, k)
     */
    int64 n = (rc_list_ref(population)).size();
    if (n <= 0)
        return rc_list_from_value(list<int64>{});
    int64 draws = k;
    if (draws < 0)
        draws = 0;
    rc<list<float64>> weight_vals = rc_list_from_value(list<float64>{});
    for (float64 w : rc_list_ref(weights)) {
        rc_list_ref(weight_vals).append(w);
    }
    rc<list<int64>> out = rc_list_from_value(list<int64>{});
    if ((rc_list_ref(weight_vals)).size() == n) {
        float64 total = 0.0;
        for (float64 w : rc_list_ref(weight_vals)) {
            if (w > 0.0)
                total += w;
        }
        if (total > 0.0) {
            for (int64 _ = 0; _ < draws; ++_) {
                float64 r = random() * total;
                float64 acc = 0.0;
                int64 picked_i = n - 1;
                for (int64 i = 0; i < n; ++i) {
                    float64 w = py_list_at_ref(rc_list_ref(weight_vals), i);
                    if (w > 0.0)
                        acc += w;
                    if (r < acc) {
                        picked_i = i;
                        break;
                    }
                }
                rc_list_ref(out).append(py_list_at_ref(rc_list_ref(population), picked_i));
            }
            return out;
        }
    }
    rc_list_ref(out).reserve((draws <= 0) ? 0 : draws);
    for (int64 _ = 0; _ < draws; ++_)
        rc_list_ref(out).append(py_list_at_ref(rc_list_ref(population), randint(0, n - 1)));
    return out;
}

float64 gauss(float64 mu = 0.0, float64 sigma = 1.0) {
    /* Return a pseudo-random Gaussian sample. */
    if (_gauss_has_spare[0] != 0) {
        _gauss_has_spare[0] = 0;
        return mu + sigma * _gauss_spare[0];
    }
    float64 u1 = 0.0;
    while (u1 <= 1.0e-12) {
        u1 = random();
    }
    float64 u2 = random();
    float64 mag = pytra::std::math::sqrt(-(2.0) * pytra::std::math::log(u1));
    float64 z0 = mag * pytra::std::math::cos(2.0 * pytra::std::math::pi * u2);
    float64 z1 = mag * pytra::std::math::sin(2.0 * pytra::std::math::pi * u2);
    _gauss_spare[0] = z1;
    _gauss_has_spare[0] = 1;
    return mu + sigma * z0;
}

void shuffle(rc<list<int64>>& xs) {
    /* Shuffle list in place. */
    int64 i = (rc_list_ref(xs)).size() - 1;
    while (i > 0) {
        int64 j = randint(0, i);
        if (j != i) {
            int64 tmp = py_list_at_ref(rc_list_ref(xs), i);
            py_list_at_ref(rc_list_ref(xs), i) = py_list_at_ref(rc_list_ref(xs), j);
            py_list_at_ref(rc_list_ref(xs), j) = tmp;
        }
        i--;
    }
}

static void __pytra_module_init() {
    static bool __initialized = false;
    if (__initialized) return;
    __initialized = true;
    _state_box = list<int64>{2463534242};
    _gauss_has_spare = list<int64>{0};
    _gauss_spare = list<float64>{0.0};
}
