// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/random.py
// generated-by: tools/gen_runtime_from_manifest.py

#ifndef PYTRA_GEN_STD_RANDOM_H
#define PYTRA_GEN_STD_RANDOM_H

// forward declarations
void seed(int64 value);
int64 _next_u31();
float64 random();
int64 randint(int64 a, int64 b);
list<int64> choices(const list<int64>& population, const list<float64>& weights, int64 k = 1);
float64 gauss(float64 mu = 0.0, float64 sigma = 1.0);
void shuffle(list<int64>& xs);

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

list<int64> choices(const list<int64>& population, const list<float64>& weights, int64 k = 1) {
    /* Return k sampled elements with replacement.

    Supported call forms:
    - choices(population, weights)
    - choices(population, weights, k)
     */
    int64 n = population.size();
    if (n <= 0)
        return list<int64>{};
    int64 draws = k;
    if (draws < 0)
        draws = 0;
    list<float64> weight_vals = {};
    for (float64 w : weights) {
        weight_vals.append(w);
    }
    list<int64> out = {};
    if (weight_vals.size() == n) {
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
                out.append(population[picked_i]);
            }
            return out;
        }
    }
    out.reserve((draws <= 0) ? 0 : draws);
    for (int64 _ = 0; _ < draws; ++_)
        out.append(population[randint(0, n - 1)]);
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

void shuffle(list<int64>& xs) {
    /* Shuffle list in place. */
    int64 i = xs.size() - 1;
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

#endif  // PYTRA_GEN_STD_RANDOM_H
