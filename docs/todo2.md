# このファイルについて

このファイルは、編集しないでください。


# 最優先TODO

ここに書くものは、docs/todo.md の 一番上のタスクより優先して処理しなければならない。

py2cpp.py によって src/pytra/runtime/std/math.py から src/runtime/cpp/pytra/std/math.h , math.cpp  を生成し、これを用いて、test/fixtures/stdlib/math_extended.py が py2cpp.py で C++ のコードに変換し、実行できるか。

# MUST

src/runtime/cpp/pytra/ にあるすべてのファイルは、src/pytra/runtime/ から py2cpp.py によって生成されなければならない。

例)
src/runtime/cpp/pytra/png.h , png.cpp は、
src/pytra/runtime/png.py から py2cpp.py によって生成される。
