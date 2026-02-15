#include "cpp_module/gc.h"
#include "cpp_module/py_runtime_modules.h"
#include <filesystem>
#include <iostream>
#include <sstream>
#include <stdexcept>
#include <string>
#include <tuple>
#include <unordered_map>
#include <unordered_set>
#include <vector>

using namespace std;
using namespace pycs::gc;

template <typename T>
string py_to_string(const T& value)
{
    std::ostringstream oss;
    oss << value;
    return oss.str();
}

template <typename T>
bool py_in(const T& key, const unordered_set<T>& s)
{
    return s.find(key) != s.end();
}

template <typename K, typename V>
bool py_in(const K& key, const unordered_map<K, V>& m)
{
    return m.find(key) != m.end();
}

template <typename T>
bool py_in(const T& key, const vector<T>& v)
{
    for (const auto& item : v) {
        if (item == key) {
            return true;
        }
    }
    return false;
}

inline void py_print()
{
    std::cout << std::endl;
}

template <typename T>
void py_print_one(const T& value)
{
    std::cout << value;
}

inline void py_print_one(bool value)
{
    std::cout << (value ? "True" : "False");
}

template <typename T, typename... Rest>
void py_print(const T& first, const Rest&... rest)
{
    py_print_one(first);
    ((std::cout << " ", py_print_one(rest)), ...);
    std::cout << std::endl;
}

int main()
{
    Path root = Path(__file__)->resolve()->parents[2];
    sys->path->insert(0, str(root));
    Path src_file = ((root / "src") / "pycpp_transpiler.py");
    Path out_file = (((root / "test") / "cpp") / "case1001_pycpp_transpiler.cpp");
    out_file->parent->mkdir(true, true);
    transpile(str(src_file), str(out_file));
    py_print("ok");
    return 0;
}
