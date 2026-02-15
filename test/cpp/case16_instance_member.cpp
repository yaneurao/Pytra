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

class Point : public pycs::gc::PyObj
{
public:
    int x;
    int y;
    Point(int x, int y)
    {
        this->x = x;
        this->y = y;
    }
    int total()
    {
        return (this->x + this->y);
    }
};

int main()
{
    pycs::gc::RcHandle<Point> p = pycs::gc::RcHandle<Point>::adopt(pycs::gc::rc_new<Point>(2, 5));
    py_print(p->total());
    return 0;
}
