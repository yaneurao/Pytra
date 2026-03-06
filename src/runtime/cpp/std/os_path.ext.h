#pragma once

#include "runtime/cpp/std/os_path.gen.h"

str py_os_path_join(const str& a, const str& b);
str py_os_path_dirname(const str& p);
str py_os_path_basename(const str& p);
::std::tuple<str, str> py_os_path_splitext(const str& p);
str py_os_path_abspath(const str& p);
bool py_os_path_exists(const str& p);
