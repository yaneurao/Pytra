#include "cpp_module/gc.h"
#include "cpp_module/py_runtime_modules.h"
#include <algorithm>
#include <any>
#include <fstream>
#include <ios>
#include <iostream>
#include <sstream>
#include <stdexcept>
#include <string>
#include <tuple>
#include <type_traits>
#include <unordered_map>
#include <unordered_set>
#include <vector>

using namespace std;
using namespace pycs::gc;

class Base31 : public pycs::gc::PyObj
{
public:
    int value()
    {
        return 31;
    }
};

class Child31 : public Base31
{
public:
    int value2()
    {
        return (this->value() + 1);
    }
};

int main()
{
    pycs::gc::RcHandle<Child31> c = pycs::gc::RcHandle<Child31>::adopt(pycs::gc::rc_new<Child31>());
    py_print(c->value2());
    return 0;
}
