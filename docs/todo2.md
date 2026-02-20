# このファイルについて

このファイルは、編集しないでください。

# 最優先TODO

ここに書くものは、docs/todo.md の 一番上のタスクより優先して処理しなければならない。

py2cpp.py によって src/pytra/std/math.py から src/runtime/cpp/pytra/std/math.h, math.cpp  を生成し、
これを用いて、test/fixtures/stdlib/math_extended.py が py2cpp.py で C++ のコードに変換し、実行できるか。

# 禁止事項

最優先TODOの変換の時に、math.h, math.cpp を手で出力してはなりません。
あくまで、math.pyをparseして、その内容に基づいて出力しなければなりません。
math.h / math.cpp に対する固有の処理をどこかに書いてはいけません。
もちろん、py2cpp.pyにもmath.py , math.h , math.cpp 固有の処理を書いてはなりません。
math.py というモジュールが存在することを仮定してはなりません。
src/profiles/cpp/runtime_calls.json にも math.py , math.h , math.cpp 固有の処理を書いてはなりません。
いかなるところにもmath固有の処理を書いてはなりません。
docs/spec-runtime.md のルールに従ってください。

math.py だけでなく、Python標準モジュールについても同様で、
それが存在することを仮定するコードをpy2cpp.pyに書いてはなりません。
gif.pyやpng.pyに関しても同様です。
それが存在することを仮定するコードをpy2cpp.pyに書いてはなりません。
つまり、py2cpp.pyに"gif", "png"という文字列が一度でも出現していてはいけません。


# 優先TODO

