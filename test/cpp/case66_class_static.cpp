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

class Counter66 : public pycs::gc::PyObj
{
public:
    inline static int total = 0;
    int add(int x)
    {
        Counter66::total = (Counter66::total + x);
        return Counter66::total;
    }
};

int main()
{
    pycs::gc::RcHandle<Counter66> c = pycs::gc::RcHandle<Counter66>::adopt(pycs::gc::rc_new<Counter66>());
    py_print(c.insert(5));
    return 0;
}
