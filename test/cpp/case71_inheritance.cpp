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

class Base71 : public pycs::gc::PyObj
{
public:
    int value()
    {
        return 71;
    }
};

class Child71 : public Base71
{
public:
    int value2()
    {
        return (this->value() + 1);
    }
};

int main()
{
    pycs::gc::RcHandle<Child71> c = pycs::gc::RcHandle<Child71>::adopt(pycs::gc::rc_new<Child71>());
    py_print(c->value2());
    return 0;
}
