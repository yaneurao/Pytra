// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/random.py
// generated-by: src/py2cpp.py

#ifndef PYTRA_STD_RANDOM_H
#define PYTRA_STD_RANDOM_H

namespace pytra::std::random {

extern list<int64> _state_box;
extern list<int64> _gauss_has_spare;
extern list<float64> _gauss_spare;
extern list<str> __all__;

void seed(int64 value);
int64 _next_u31();
float64 random();
int64 randint(int64 a, int64 b);
list<int64> choices(const list<int64>& population, const list<float64>& weights);
list<int64> choices(const list<int64>& population, const list<float64>& weights, int64 k);
float64 gauss(float64 mu, float64 sigma);
void shuffle(list<int64>& xs);
template <class T>
void shuffle(list<T>& xs) {
    int64 i = py_len(xs) - 1;
    while (i > 0) {
        int64 j = randint(0, i);
        if (j != i) {
            T tmp = xs[static_cast<::std::size_t>(i)];
            xs[static_cast<::std::size_t>(i)] = xs[static_cast<::std::size_t>(j)];
            xs[static_cast<::std::size_t>(j)] = tmp;
        }
        i--;
    }
}

}  // namespace pytra::std::random

#endif  // PYTRA_STD_RANDOM_H
