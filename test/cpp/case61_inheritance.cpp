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

class Base61 : public pycs::gc::PyObj
{
public:
    int value()
    {
        return 61;
    }
};

class Child61 : public Base61
{
public:
    int value2()
    {
        return (this->value() + 1);
    }
};

int main()
{
    pycs::gc::RcHandle<Child61> c = pycs::gc::RcHandle<Child61>::adopt(pycs::gc::rc_new<Child61>());
    py_print(c->value2());
    return 0;
}
