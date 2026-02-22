#include "runtime/cpp/pytra/built_in/py_runtime.h"

#include "pytra/std/random.h"

#include "pytra/std/math.h"

namespace pytra::std::random {

    /* pytra.std.random: minimal deterministic random helpers.

This module is intentionally self-contained and avoids Python stdlib imports,
so it can be transpiled to target runtimes.
 */
    
    
    
    list<int64> _state_box = list<int64>{2463534242};
    
    list<int64> _gauss_has_spare = list<int64>{0};
    
    list<float64> _gauss_spare = list<float64>{0.0};
    
    void seed(int64 value) {
        /* Set generator seed (32-bit). */
        int64 v = int64(value) & 2147483647;
        if (v == 0)
            v = 1;
        _state_box[0] = v;
        _gauss_has_spare[0] = 0;
    }
    
    int64 _next_u31() {
        /* Advance internal LCG and return a 31-bit value. */
        auto s = py_at(_state_box, py_to_int64(0));
        s = 1103515245 * s + 12345 & 2147483647;
        _state_box[0] = s;
        return s;
    }
    
    float64 random() {
        /* Return pseudo-random float in [0.0, 1.0). */
        return py_to_float64(_next_u31()) / 2147483648.0;
    }
    
    int64 randint(int64 a, int64 b) {
        /* Return pseudo-random integer in [a, b]. */
        int64 lo = int64(a);
        int64 hi = int64(b);
        if (hi < lo)
            ::std::swap(lo, hi);
        int64 span = hi - lo + 1;
        return lo + int64(random() * py_to_float64(span));
    }
    
    list<int64> choices(const list<int64>& population, const list<float64>& weights, int64 k) {
        /* Return k sampled elements with replacement.

    Supported call forms:
    - choices(population, weights)
    - choices(population, weights, k)
     */
        int64 n = py_len(population);
        if (n <= 0)
            return list<object>{};
        int64 draws = int64(k);
        if (draws < 0)
            draws = 0;
        list<float64> weight_vals = list<float64>{};
        for (float64 w : weights)
            weight_vals.append(float64(static_cast<float64>(w)));
        list<int64> out = list<int64>{};
        if (py_len(weight_vals) == n) {
            float64 total = 0.0;
            for (float64 w : weight_vals) {
                if (w > 0.0)
                    total += w;
            }
            if (total > 0.0) {
                for (int64 _ = 0; _ < draws; ++_) {
                    float64 r = random() * total;
                    float64 acc = 0.0;
                    int64 picked_i = n - 1;
                    for (int64 i = 0; i < n; ++i) {
                        float64 w = weight_vals[i];
                        if (w > 0.0)
                            acc += w;
                        if (r < acc) {
                            picked_i = i;
                            break;
                        }
                    }
                    out.append(int64(population[picked_i]));
                }
                return out;
            }
        }
        for (int64 _ = 0; _ < draws; ++_)
            out.append(int64(population[randint(0, n - 1)]));
        return out;
    }

    list<int64> choices(const list<int64>& population, const list<float64>& weights) {
        return choices(population, weights, 1);
    }
    
    float64 gauss(float64 mu = 0.0, float64 sigma = 1.0) {
        /* Return a pseudo-random Gaussian sample. */
        if (py_at(_gauss_has_spare, py_to_int64(0)) != 0) {
            _gauss_has_spare[0] = 0;
            return static_cast<float64>(mu) + static_cast<float64>(sigma) * py_at(_gauss_spare, py_to_int64(0));
        }
        float64 u1 = 0.0;
        while (u1 <= 1.0e-12) {
            u1 = random();
        }
        float64 u2 = random();
        auto mag = pytra::std::math::sqrt(-2.0 * pytra::std::math::log(u1));
        auto z0 = mag * pytra::std::math::cos(2.0 * pytra::std::math::pi * u2);
        auto z1 = mag * pytra::std::math::sin(2.0 * pytra::std::math::pi * u2);
        _gauss_spare[0] = z1;
        _gauss_has_spare[0] = 1;
        return static_cast<float64>(mu) + static_cast<float64>(sigma) * z0;
    }
    
    void shuffle(list<int64>& xs) {
        /* Shuffle list in place. */
        int64 i = py_len(xs) - 1;
        while (i > 0) {
            int64 j = randint(0, i);
            if (j != i) {
                int64 tmp = xs[i];
                xs[i] = xs[j];
                xs[j] = tmp;
            }
            i--;
        }
    }
    
    list<str> __all__ = list<str>{"seed", "random", "randint", "choices", "gauss", "shuffle"};
    
}  // namespace pytra::std::random
