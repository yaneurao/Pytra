#include "cpp_module/dataclasses.h"
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

class Point99 : public pycs::gc::PyObj
{
public:
    int x;
    int y = 10;
    Point99(int x, int y = 10)
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
    pycs::gc::RcHandle<Point99> p = pycs::gc::RcHandle<Point99>::adopt(pycs::gc::rc_new<Point99>(3));
    py_print(p->total());
    return 0;
}
