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

1.
src/runtime/cpp/py_runtime.h についてです。

```
#include "runtime/cpp/pytra/built_in/bytes_util.h"
#include "runtime/cpp/pytra/built_in/exceptions.h"
#include "runtime/cpp/pytra/built_in/io.h"
#include "runtime/cpp/pytra/utils/gif.h"
#include "runtime/cpp/pytra/built_in/gc.h"
#include "runtime/cpp/pytra/std/math.h"
#include "runtime/cpp/pytra/utils/png.h"
```

このようにありますが、std/math.h と png.h, gif.h は、Pythonの組み込みモジュールではないので
ここにあるのは不適(トランスパイル対象のコードでimport mathとしたときにそこでincludeすべき)ではないですか？

2.
src/runtime/cpp/py_runtime.h は、
src/runtime/cpp/built-in/ にあるべきではないですか？

3.
py_runtime.h の
py_sys_write_stdout
など `sys_` がつくものは、src/runtime/cpp/pytra/std/sys.h に展開されるべきではないですか？

4.
py_runtime.h の
perf_counter は ここにあるのはおかしいです。std/time.h にあるべきではないですか？

5.
py_runtime.h の
py_gif_grayscale_palette_list は ここにあるのはおかしいです。

py_pop は list.h にあるべきではないでしょうか。listのメソッドなので…。

6.
src/pytra/runtime/cpp/py_runtime.h は、互換用ヘッダーであるなら、要らないです。削除してください。

7.
src/pytra/runtime/cpp/built_in/containers.h ですが
```
#ifndef PYTRA_RUNTIME_CPP_BASE_CONTAINERS_H
#define PYTRA_RUNTIME_CPP_BASE_CONTAINERS_H
```
のように古い名前(CPP_BASE)になっています。また、PYTRA_RUNTIME_CPP の部分は要らず、単に
PYTRA_BUILT_IN_CONTAINERS_H
と、src/pytra/runtime/cpp/ 以降のPATH名から生成すれば良いと思います。

他の headerファイルの先頭の二重include防止のシンボルについても同様です。

src/pytra/runtime/cpp/ 以降のPATH名から生成するというのは、ルールとしてdocs/に記載しておいてください。

8.

containers.h ですが、PATHの位置がおかしいようにおもいます。
```
#include "runtime/cpp/pytra/built_in/str.h"
#include "runtime/cpp/pytra/built_in/path.h"
#include "runtime/cpp/pytra/built_in/list.h"
#include "runtime/cpp/pytra/built_in/dict.h"
#include "runtime/cpp/pytra/built_in/set.h"
```

-I で、"runtime/cpp/pytra" が指定されている前提で良いので、

#include "built_in/str.h"
であるか、あるいは同一フォルダなので単に
#include "str.h"
でいいように思います。

-I で、"runtime/cpp/pytra" が指定されている前提で良いというのは
docs/ の然るべき場所に追記しておいてください。

9.
containers.h は py_runtime.hからしか読み込まないので、containers.hを削除して
py_runtime.h に直接書いてください。

10.
py2cpp.py に 以下の記述があるが、これは 最優先TODO に違反している。
py2cpp.py に事前に png モジュール(png.py)などの情報を事前に埋め込んではならない。
以下の記述は丸ごと削除されなければならない。

```
def _default_cpp_module_attr_call_map() -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    out["pytra.utils.png"] = {
        "write_rgb_png": "pytra::utils::png::write_rgb_png_py",
    }
    out["pytra.utils.gif"] = {
        "save_gif": "pytra::utils::gif::save_gif_py",
        "grayscale_palette": "pytra::utils::gif::grayscale_palette_py",
    }
    out["os.path"] = {
        "join": "py_os_path_join",
        "dirname": "py_os_path_dirname",
        "basename": "py_os_path_basename",
        "splitext": "py_os_path_splitext",
        "abspath": "py_os_path_abspath",
        "exists": "py_os_path_exists",
    }
    out["glob"] = {
        "glob": "py_glob_glob",
    }
    out["pytra.std.glob"] = {
        "glob": "py_glob_glob",
    }
    out["time"] = {
        "perf_counter": "pytra::std::time::perf_counter",
    }
    out["pytra.std.time"] = {
        "perf_counter": "pytra::std::time::perf_counter",
    }
    out["pathlib"] = {
        "Path": "Path",
    }
    out["pytra.std.pathlib"] = {
        "Path": "Path",
    }
    out["sys"] = {
        "set_argv": "pytra::std::sys::set_argv",
        "set_path": "pytra::std::sys::set_path",
        "write_stderr": "pytra::std::sys::write_stderr",
        "write_stdout": "pytra::std::sys::write_stdout",
        "exit": "pytra::std::sys::exit",
    }
    out["pytra.std.sys"] = {
        "set_argv": "pytra::std::sys::set_argv",
        "set_path": "pytra::std::sys::set_path",
        "write_stderr": "pytra::std::sys::write_stderr",
        "write_stdout": "pytra::std::sys::write_stdout",
        "exit": "pytra::std::sys::exit",
        "argv": "pytra::std::sys::argv",
        "path": "pytra::std::sys::path",
        "stderr": "pytra::std::sys::stderr",
        "stdout": "pytra::std::sys::stdout",
    }
    out["pytra.std.os.path"] = {
        "join": "py_os_path_join",
        "dirname": "py_os_path_dirname",
        "basename": "py_os_path_basename",
        "splitext": "py_os_path_splitext",
        "abspath": "py_os_path_abspath",
        "exists": "py_os_path_exists",
    }
    out["pytra.std.argparse"] = {
        "ArgumentParser": "py_argparse_argument_parser",
    }
    return out
```
