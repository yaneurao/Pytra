#include "cpp_module/gc.h"
#include "cpp_module/pathlib.h"
#include "cpp_module/py_runtime.h"
#include <algorithm>
#include <any>
#include <cstdint>
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

void py_main()
{
    Path root = Path("test/obj/pathlib_case32");
    root->mkdir(true, true);
    Path child = ((root) / ("values.txt"));
    child->write_text("42");
    py_print(child->exists());
    py_print(child->name());
    py_print(child->stem());
    py_print(((child->parent()) / ("values.txt"))->exists());
    py_print(child->read_text());
}

int main()
{
    py_main();
    return 0;
}
