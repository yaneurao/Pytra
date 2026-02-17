#ifndef PYTRA_EAST_CPP_MODULE_PY_RUNTIME_H
#define PYTRA_EAST_CPP_MODULE_PY_RUNTIME_H

#include <algorithm>
#include <cctype>
#include <cmath>
#include <chrono>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <sstream>
#include <stdexcept>
#include <string>
#include <type_traits>
#include <tuple>
#include <unordered_map>
#include <unordered_set>
#include <utility>
#include <vector>

#include "cpp_module/gif.h"
#include "cpp_module/gc.h"
#include "cpp_module/math.h"
#include "cpp_module/png.h"

using int8 = std::int8_t;
using uint8 = std::uint8_t;
using int16 = std::int16_t;
using uint16 = std::uint16_t;
using int32 = std::int32_t;
using uint32 = std::uint32_t;
using int64 = std::int64_t;
using uint64 = std::uint64_t;
using float32 = float;
using float64 = double;
using str = std::string;
using Path = std::filesystem::path;

template <class T>
using list = std::vector<T>;

template <class K, class V>
using dict = std::unordered_map<K, V>;

template <class T>
using set = std::unordered_set<T>;

template <class T>
static inline int64 py_len(const T& v) {
    return static_cast<int64>(v.size());
}

template <class T>
static inline std::string py_to_string(const T& v) {
    std::ostringstream oss;
    oss << v;
    return oss.str();
}

static inline std::string py_to_string(const std::string& v) {
    return v;
}

static inline std::string py_to_string(const char* v) {
    return std::string(v);
}

static inline std::string py_to_string(bool v) {
    return v ? "True" : "False";
}

static inline int64 py_to_int64(const str& v) {
    return static_cast<int64>(std::stoll(v));
}

template <class T>
static inline void py_print(const T& v) {
    std::cout << v << std::endl;
}

static inline void py_print(bool v) {
    std::cout << (v ? "True" : "False") << std::endl;
}

template <class T, class... Rest>
static inline void py_print(const T& first, const Rest&... rest) {
    std::cout << py_to_string(first);
    ((std::cout << " " << py_to_string(rest)), ...);
    std::cout << std::endl;
}

template <class T>
static inline list<T> py_slice(const list<T>& v, int64 lo, int64 up) {
    const int64 n = static_cast<int64>(v.size());
    if (lo < 0) lo += n;
    if (up < 0) up += n;
    lo = std::max<int64>(0, std::min<int64>(lo, n));
    up = std::max<int64>(0, std::min<int64>(up, n));
    if (up < lo) up = lo;
    return list<T>(v.begin() + lo, v.begin() + up);
}

static inline str py_slice(const str& v, int64 lo, int64 up) {
    const int64 n = static_cast<int64>(v.size());
    if (lo < 0) lo += n;
    if (up < 0) up += n;
    lo = std::max<int64>(0, std::min<int64>(lo, n));
    up = std::max<int64>(0, std::min<int64>(up, n));
    if (up < lo) up = lo;
    return v.substr(static_cast<std::size_t>(lo), static_cast<std::size_t>(up - lo));
}

static inline void py_write_text(const Path& p, const str& s) {
    std::ofstream ofs(p);
    ofs << s;
}

static inline str py_read_text(const Path& p) {
    std::ifstream ifs(p);
    std::stringstream ss;
    ss << ifs.rdbuf();
    return ss.str();
}

template <class A, class B>
static inline float64 py_div(A lhs, B rhs) {
    return static_cast<float64>(lhs) / static_cast<float64>(rhs);
}

template <class A, class B>
static inline auto py_floordiv(A lhs, B rhs) {
    using R = std::common_type_t<A, B>;
    if constexpr (std::is_integral_v<A> && std::is_integral_v<B>) {
        if (rhs == 0) throw std::runtime_error("division by zero");
        R q = static_cast<R>(lhs / rhs);
        R r = static_cast<R>(lhs % rhs);
        if (r != 0 && ((r > 0) != (rhs > 0))) q -= 1;
        return q;
    } else {
        return std::floor(static_cast<float64>(lhs) / static_cast<float64>(rhs));
    }
}

template <class A, class B>
static inline auto py_mod(A lhs, B rhs) {
    using R = std::common_type_t<A, B>;
    if constexpr (std::is_integral_v<A> && std::is_integral_v<B>) {
        if (rhs == 0) throw std::runtime_error("integer modulo by zero");
        R r = static_cast<R>(lhs % rhs);
        if (r != 0 && ((r > 0) != (rhs > 0))) r += static_cast<R>(rhs);
        return r;
    } else {
        float64 x = std::fmod(static_cast<float64>(lhs), static_cast<float64>(rhs));
        if (x != 0.0 && ((x > 0.0) != (static_cast<float64>(rhs) > 0.0))) x += static_cast<float64>(rhs);
        return x;
    }
}

static inline void write_rgb_png(const str& path, int64 width, int64 height, const list<uint8>& pixels) {
    pycs::cpp_module::png::write_rgb_png(path, static_cast<int>(width), static_cast<int>(height), pixels);
}

static inline list<uint8> grayscale_palette() {
    return pycs::cpp_module::gif::grayscale_palette();
}

static inline void save_gif(
    const str& path,
    int64 width,
    int64 height,
    const list<list<uint8>>& frames,
    const list<uint8>& palette,
    int64 delay_cs = 4,
    int64 loop = 0
) {
    const auto pal = palette.empty() ? pycs::cpp_module::gif::grayscale_palette() : palette;
    pycs::cpp_module::gif::save_gif(
        path,
        static_cast<int>(width),
        static_cast<int>(height),
        frames,
        pal,
        static_cast<int>(delay_cs),
        static_cast<int>(loop)
    );
}

static inline float64 perf_counter() {
    using clock = std::chrono::steady_clock;
    const auto now = clock::now().time_since_epoch();
    return std::chrono::duration_cast<std::chrono::duration<float64>>(now).count();
}

template <class T>
static inline T py_pop(list<T>& v) {
    if (v.empty()) {
        throw std::out_of_range("pop from empty list");
    }
    T out = v.back();
    v.pop_back();
    return out;
}

template <class T>
static inline T py_pop(list<T>& v, int64 idx) {
    if (v.empty()) {
        throw std::out_of_range("pop from empty list");
    }
    if (idx < 0) idx += static_cast<int64>(v.size());
    if (idx < 0 || idx >= static_cast<int64>(v.size())) {
        throw std::out_of_range("pop index out of range");
    }
    T out = v[static_cast<std::size_t>(idx)];
    v.erase(v.begin() + idx);
    return out;
}

template <class A, class B>
static inline auto py_min(const A& a, const B& b) -> std::common_type_t<A, B> {
    using R = std::common_type_t<A, B>;
    return std::min<R>(static_cast<R>(a), static_cast<R>(b));
}

template <class A, class B, class... Rest>
static inline auto py_min(const A& a, const B& b, const Rest&... rest) -> std::common_type_t<A, B, Rest...> {
    return py_min(py_min(a, b), rest...);
}

template <class A, class B>
static inline auto py_max(const A& a, const B& b) -> std::common_type_t<A, B> {
    using R = std::common_type_t<A, B>;
    return std::max<R>(static_cast<R>(a), static_cast<R>(b));
}

template <class A, class B, class... Rest>
static inline auto py_max(const A& a, const B& b, const Rest&... rest) -> std::common_type_t<A, B, Rest...> {
    return py_max(py_max(a, b), rest...);
}

static inline list<int64> py_range(int64 start, int64 stop, int64 step) {
    list<int64> out;
    if (step == 0) return out;
    if (step > 0) {
        for (int64 i = start; i < stop; i += step) out.push_back(i);
    } else {
        for (int64 i = start; i > stop; i += step) out.push_back(i);
    }
    return out;
}

template <class T>
static inline list<T> py_repeat(const list<T>& v, int64 n) {
    list<T> out;
    if (n <= 0) return out;
    out.reserve(v.size() * static_cast<std::size_t>(n));
    for (int64 i = 0; i < n; ++i) {
        out.insert(out.end(), v.begin(), v.end());
    }
    return out;
}

static inline str py_repeat(const str& v, int64 n) {
    if (n <= 0) return "";
    str out;
    out.reserve(v.size() * static_cast<std::size_t>(n));
    for (int64 i = 0; i < n; ++i) {
        out += v;
    }
    return out;
}

static inline bool py_isdigit(const str& ch) {
    return ch.size() == 1 && std::isdigit(static_cast<unsigned char>(ch[0])) != 0;
}

static inline bool py_isalpha(const str& ch) {
    return ch.size() == 1 && std::isalpha(static_cast<unsigned char>(ch[0])) != 0;
}

#endif
