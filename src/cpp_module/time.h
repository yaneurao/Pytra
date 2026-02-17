// このファイルは Python の `time` モジュール互換の最小実装です。
// 現時点では `perf_counter()` を提供します。

#ifndef PYCS_CPP_MODULE_TIME_H
#define PYCS_CPP_MODULE_TIME_H

namespace pytra::cpp_module {

/**
 * @brief 単調増加クロックに基づく高分解能時刻を秒で返します。
 * @return 起点不定の経過秒。差分を実行時間計測に利用します。
 */
double perf_counter();

}  // namespace pytra::cpp_module

using pytra::cpp_module::perf_counter;

#endif  // PYCS_CPP_MODULE_TIME_H
