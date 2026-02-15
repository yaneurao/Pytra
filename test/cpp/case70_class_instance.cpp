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

class Box70 : public pycs::gc::PyObj
{
public:
    int seed;
    Box70(int seed)
    {
        this->seed = seed;
    }
    int next()
    {
        this->seed = (this->seed + 1);
        return this->seed;
    }
};

int main()
{
    pycs::gc::RcHandle<Box70> b = pycs::gc::RcHandle<Box70>::adopt(pycs::gc::rc_new<Box70>(3));
    py_print(b->next());
    return 0;
}
