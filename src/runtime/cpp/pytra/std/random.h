// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/random.py
// generated-by: src/py2cpp.py

#ifndef PYTRA_STD_RANDOM_H
#define PYTRA_STD_RANDOM_H

namespace pytra::std::random {

extern list<int64> _state_box;
extern list<str> __all__;

void seed(int64 value);
int64 _next_u31();
float64 random();
int64 randint(int64 a, int64 b);

}  // namespace pytra::std::random

#endif  // PYTRA_STD_RANDOM_H
