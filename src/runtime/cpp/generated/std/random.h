// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/random.py
// generated-by: src/backends/cpp/cli.py

#ifndef PYTRA_GENERATED_STD_RANDOM_H
#define PYTRA_GENERATED_STD_RANDOM_H

#include "runtime/cpp/native/core/py_types.h"

namespace pytra::std::random {

extern list<int64> _state_box;
extern list<int64> _gauss_has_spare;
extern list<float64> _gauss_spare;

void seed(int64 value);
int64 _next_u31();
float64 random();
int64 randint(int64 a, int64 b);
rc<list<int64>> choices(const rc<list<int64>>& population, const rc<list<float64>>& weights, int64 k = 1);
float64 gauss(float64 mu = 0.0, float64 sigma = 1.0);
void shuffle(rc<list<int64>>& xs);

}  // namespace pytra::std::random

#endif  // PYTRA_GENERATED_STD_RANDOM_H
