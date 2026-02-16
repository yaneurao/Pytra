#include "cpp_module/gc.h"
#include "cpp_module/py_runtime.h"
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

class Counter26 : public pycs::gc::PyObj
{
public:
    inline static int total = 0;
    int add(int x)
    {
        Counter26::total = (Counter26::total + x);
        return Counter26::total;
    }
};

int main()
{
    pycs::gc::RcHandle<Counter26> c = pycs::gc::RcHandle<Counter26>::adopt(pycs::gc::rc_new<Counter26>());
    py_print(c.insert(5));
    return 0;
}
