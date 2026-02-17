#include "cpp_module/gc.h"
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
    vector<long long> nums = {10, 20, 30, 40, 50};
    string text = "abcdef";
    vector<long long> mid_nums = py_slice(nums, true, 1, true, 4);
    string mid_text = py_slice(text, true, 2, true, 5);
    py_print(mid_nums[0]);
    py_print(mid_nums[2]);
    py_print(mid_text);
}

int main()
{
    py_main();
    return 0;
}
