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

class Multiplier : public pycs::gc::PyObj
{
public:
    int mul(int x, int y)
    {
        return (x * y);
    }
};

int main()
{
    pycs::gc::RcHandle<Multiplier> m = pycs::gc::RcHandle<Multiplier>::adopt(pycs::gc::rc_new<Multiplier>());
    py_print(m->mul(6, 7));
    return 0;
}
