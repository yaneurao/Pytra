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

class Box20 : public pycs::gc::PyObj
{
public:
    int seed;
    Box20(int seed)
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
    pycs::gc::RcHandle<Box20> b = pycs::gc::RcHandle<Box20>::adopt(pycs::gc::rc_new<Box20>(3));
    py_print(b->next());
    return 0;
}
