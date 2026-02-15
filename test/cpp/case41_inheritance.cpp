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

class Base41 : public pycs::gc::PyObj
{
public:
    int value()
    {
        return 41;
    }
};

class Child41 : public Base41
{
public:
    int value2()
    {
        return (this->value() + 1);
    }
};

int main()
{
    pycs::gc::RcHandle<Child41> c = pycs::gc::RcHandle<Child41>::adopt(pycs::gc::rc_new<Child41>());
    py_print(c->value2());
    return 0;
}
