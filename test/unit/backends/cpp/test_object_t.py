"""Tests for Object<T> — ControlBlock + templated view (core/object.h)."""

from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src").exists())
PYTRA_TEST_COMPILE_TIMEOUT_SEC = float(os.environ.get("PYTRA_TEST_COMPILE_TIMEOUT_SEC", "120"))
PYTRA_TEST_RUN_TIMEOUT_SEC = float(os.environ.get("PYTRA_TEST_RUN_TIMEOUT_SEC", "2"))


class ObjectTTest(unittest.TestCase):
    def _compile_and_run(self, cpp_src: str, label: str, extra_srcs: list[str] | None = None) -> str:
        with tempfile.TemporaryDirectory() as tmpdir:
            work = Path(tmpdir)
            src = work / f"{label}.cpp"
            exe = work / f"{label}.out"
            src.write_text(cpp_src, encoding="utf-8")
            compile_cmd = [
                "g++", "-std=c++20", "-O2",
                "-I", "src", "-I", "src/runtime/cpp", "-I", "src/runtime/generated",
                str(src),
            ]
            if extra_srcs:
                compile_cmd.extend(extra_srcs)
            compile_cmd.extend(["-o", str(exe)])
            comp = subprocess.run(compile_cmd, cwd=ROOT, capture_output=True, text=True, timeout=PYTRA_TEST_COMPILE_TIMEOUT_SEC)
            self.assertEqual(comp.returncode, 0, msg=f"compile failed:\n{comp.stderr}")
            run = subprocess.run([str(exe)], cwd=work, capture_output=True, text=True, timeout=PYTRA_TEST_RUN_TIMEOUT_SEC)
            self.assertEqual(run.returncode, 0, msg=f"run failed:\n{run.stderr}")
            return run.stdout.strip()

    def test_upcast_preserves_type_id_and_shares_control_block(self) -> None:
        out = self._compile_and_run(r'''
#include "core/object.h"
#include <cassert>
#include <iostream>

TypeInfo* g_type_table[16] = {};
uint32_t g_type_table_size = 0;

struct Base {
    virtual ~Base() {}
    virtual int value() { return 0; }
};

struct Derived : Base {
    int val;
    Derived(int v) : val(v) {}
    int value() override { return val; }
};

enum { TID_BASE = 0, TID_DERIVED = 1 };
TypeInfo ti_base    = {TID_BASE,    0, 2, &deleter_impl<Base>};
TypeInfo ti_derived = {TID_DERIVED, 1, 2, &deleter_impl<Derived>};

int main() {
    g_type_table[TID_BASE] = &ti_base;
    g_type_table[TID_DERIVED] = &ti_derived;

    Object<Derived> d = make_object<Derived>(TID_DERIVED, 42);
    Object<Base> b = d;  // implicit upcast

    // type_id stays Derived even after upcast
    assert(d.type_id() == TID_DERIVED);
    assert(b.type_id() == TID_DERIVED);

    // ControlBlock is shared
    assert(d.cb == b.cb);

    // Virtual dispatch works through base view
    assert(b->value() == 42);

    std::cout << "upcast ok" << std::endl;
    return 0;
}
''', "upcast")
        self.assertEqual(out, "upcast ok")

    def test_downcast_returns_null_on_type_mismatch(self) -> None:
        out = self._compile_and_run(r'''
#include "core/object.h"
#include <cassert>
#include <iostream>

TypeInfo* g_type_table[16] = {};
uint32_t g_type_table_size = 0;

struct Animal { virtual ~Animal() {} };
struct Dog : Animal {};
struct Cat : Animal {};

enum { TID_ANIMAL = 0, TID_DOG = 1, TID_CAT = 2 };
TypeInfo ti_animal = {TID_ANIMAL, 0, 3, &deleter_impl<Animal>};
TypeInfo ti_dog    = {TID_DOG,    1, 2, &deleter_impl<Dog>};
TypeInfo ti_cat    = {TID_CAT,    2, 3, &deleter_impl<Cat>};

int main() {
    g_type_table[TID_ANIMAL] = &ti_animal;
    g_type_table[TID_DOG] = &ti_dog;
    g_type_table[TID_CAT] = &ti_cat;

    Object<Animal> animal = make_object<Dog>(TID_DOG);

    // downcast to Dog succeeds
    Object<Dog> dog = animal.downcast<Dog>(&ti_dog);
    assert(dog);

    // downcast to Cat fails
    Object<Cat> cat = animal.downcast<Cat>(&ti_cat);
    assert(!cat);

    std::cout << "downcast ok" << std::endl;
    return 0;
}
''', "downcast")
        self.assertEqual(out, "downcast ok")

    def test_isinstance_uses_interval_subtype(self) -> None:
        out = self._compile_and_run(r'''
#include "core/object.h"
#include <cassert>
#include <iostream>

TypeInfo* g_type_table[16] = {};
uint32_t g_type_table_size = 0;

struct A { virtual ~A() {} };
struct B : A {};
struct C : B {};

enum { TID_A = 0, TID_B = 1, TID_C = 2 };
TypeInfo ti_a = {TID_A, 0, 3, &deleter_impl<A>};
TypeInfo ti_b = {TID_B, 1, 3, &deleter_impl<B>};
TypeInfo ti_c = {TID_C, 2, 3, &deleter_impl<C>};

int main() {
    g_type_table[TID_A] = &ti_a;
    g_type_table[TID_B] = &ti_b;
    g_type_table[TID_C] = &ti_c;

    Object<C> c = make_object<C>(TID_C);
    Object<A> a = c;  // upcast to A

    // C is instance of A, B, and C
    assert(a.isinstance(&ti_a));
    assert(a.isinstance(&ti_b));
    assert(a.isinstance(&ti_c));

    Object<B> b = make_object<B>(TID_B);
    Object<A> a2 = b;

    // B is instance of A and B, but not C
    assert(a2.isinstance(&ti_a));
    assert(a2.isinstance(&ti_b));
    assert(!a2.isinstance(&ti_c));

    std::cout << "isinstance ok" << std::endl;
    return 0;
}
''', "isinstance")
        self.assertEqual(out, "isinstance ok")

    def test_rc_is_shared_across_copies(self) -> None:
        out = self._compile_and_run(r'''
#include "core/object.h"
#include <cassert>
#include <iostream>

TypeInfo* g_type_table[16] = {};
uint32_t g_type_table_size = 0;

struct Widget { int data = 99; };

enum { TID_WIDGET = 0 };
TypeInfo ti_widget = {TID_WIDGET, 0, 1, &deleter_impl<Widget>};

int main() {
    g_type_table[TID_WIDGET] = &ti_widget;

    Object<Widget> a = make_object<Widget>(TID_WIDGET);
    assert(a.cb->rc == 1);

    Object<Widget> b = a;  // copy
    assert(a.cb->rc == 2);
    assert(a.cb == b.cb);

    {
        Object<Widget> c = b;  // another copy
        assert(a.cb->rc == 3);
    }
    // c is destroyed, rc back to 2
    assert(a.cb->rc == 2);

    std::cout << "rc shared ok" << std::endl;
    return 0;
}
''', "rc_shared")
        self.assertEqual(out, "rc shared ok")

    def test_object_with_list_and_dict(self) -> None:
        out = self._compile_and_run(r'''
#include "core/py_types.h"
#include "core/object.h"
#include <cassert>
#include <iostream>

TypeInfo* g_type_table[16] = {};
uint32_t g_type_table_size = 0;

enum { TID_LIST_INT = 0, TID_DICT_STR_INT = 1 };
TypeInfo ti_list = {TID_LIST_INT, 0, 1, &deleter_impl<list<int64>>};
TypeInfo ti_dict = {TID_DICT_STR_INT, 1, 2, &deleter_impl<dict<str, int64>>};

int main() {
    g_type_table[TID_LIST_INT] = &ti_list;
    g_type_table[TID_DICT_STR_INT] = &ti_dict;

    auto lst = make_object<list<int64>>(TID_LIST_INT, ::std::initializer_list<int64>{10, 20, 30});
    assert(lst->size() == 3);
    lst->append(40);
    assert(lst->size() == 4);

    auto d = make_object<dict<str, int64>>(TID_DICT_STR_INT);
    (*d)["x"] = 7;
    assert(d->at("x") == 7);

    std::cout << "object list/dict ok" << std::endl;
    return 0;
}
''', "object_list_dict", extra_srcs=["src/runtime/cpp/core/gc.cpp"])
        self.assertEqual(out, "object list/dict ok")


if __name__ == "__main__":
    unittest.main()
