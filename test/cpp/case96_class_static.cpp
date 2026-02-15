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

class Counter96 : public pycs::gc::PyObj
{
public:
    inline static int total = 0;
    int add(int x)
    {
        Counter96::total = (Counter96::total + x);
        return Counter96::total;
    }
};

int main()
{
    pycs::gc::RcHandle<Counter96> c = pycs::gc::RcHandle<Counter96>::adopt(pycs::gc::rc_new<Counter96>());
    py_print(c.insert(5));
    return 0;
}
