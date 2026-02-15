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

class Animal : public pycs::gc::PyObj
{
public:
    string sound()
    {
        return "generic";
    }
};

class Dog : public Animal
{
public:
    string bark()
    {
        return (this->sound() + "-bark");
    }
};

int main()
{
    pycs::gc::RcHandle<Dog> d = pycs::gc::RcHandle<Dog>::adopt(pycs::gc::rc_new<Dog>());
    py_print(d->bark());
    return 0;
}
