#include "cpp_module/gc.h"
#include "cpp_module/py_runtime_modules.h"
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

bool has_key_53(string k)
{
    unordered_map<string, int> d = {{ "a", 1 }, { "b", 2 }};
    if (py_in(k, d))
    {
        return true;
    }
    else
    {
        return false;
    }
}

int main()
{
    py_print(has_key_53("a"));
    return 0;
}
