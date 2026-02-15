// このファイルは Python の dataclasses 互換の最小スタブです。
// 現状のトランスパイラでは @dataclass は変換時に展開されるため、
// ランタイムとしては識別用の軽量APIのみ定義します。

#ifndef PYCS_CPP_MODULE_DATACLASSES_H
#define PYCS_CPP_MODULE_DATACLASSES_H

#include <type_traits>

namespace pycs::cpp_module::dataclasses {

struct DataclassTag {};

template <typename T>
constexpr T dataclass(T value) {
    return value;
}

template <typename T>
constexpr bool is_dataclass_v = std::is_base_of_v<DataclassTag, T>;

}  // namespace pycs::cpp_module::dataclasses

#endif  // PYCS_CPP_MODULE_DATACLASSES_H
