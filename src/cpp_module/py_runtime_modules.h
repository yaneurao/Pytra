// このファイルは Python 由来の補助モジュールの共通公開ヘッダです。
// 各モジュールの実体は専用ファイル（例: sys.h / sys.cpp）へ分離します。

#ifndef PYCS_CPP_MODULE_PY_RUNTIME_MODULES_H
#define PYCS_CPP_MODULE_PY_RUNTIME_MODULES_H

#include <algorithm>
#include <any>
#include <fstream>
#include <iostream>
#include <memory>
#include <sstream>
#include <string>
#include <tuple>
#include <type_traits>
#include <unordered_map>
#include <unordered_set>
#include <vector>

#include "cpp_module/ast.h"
#include "cpp_module/pathlib.h"
#include "cpp_module/sys.h"

#ifndef __file__
#define __file__ __FILE__
#endif

template <typename T>
std::string py_to_string(const T& value) {
    std::ostringstream oss;
    oss << value;
    return oss.str();
}

template <typename T>
std::string py_to_string(const pycs::cpp_module::ast::PyPtr<T>&) {
    return "<node>";
}

inline std::string py_to_string(const pycs::cpp_module::Path& value) {
    return pycs::cpp_module::str(value);
}

inline std::string py_to_string(const std::any& value) {
    if (const auto* v = std::any_cast<bool>(&value)) {
        return *v ? "True" : "False";
    }
    if (const auto* v = std::any_cast<int>(&value)) {
        return py_to_string(*v);
    }
    if (const auto* v = std::any_cast<double>(&value)) {
        return py_to_string(*v);
    }
    if (const auto* v = std::any_cast<std::string>(&value)) {
        return *v;
    }
    return "<any>";
}

template <typename T>
bool py_in(const T& key, const std::unordered_set<T>& s) {
    return s.find(key) != s.end();
}

template <typename K, typename V>
bool py_in(const K& key, const std::unordered_map<K, V>& m) {
    return m.find(key) != m.end();
}

template <typename T>
bool py_in(const T& key, const std::vector<T>& v) {
    for (const auto& item : v) {
        if (item == key) {
            return true;
        }
    }
    return false;
}

inline void py_print() {
    std::cout << std::endl;
}

template <typename T>
void py_print_one(const T& value) {
    std::cout << value;
}

template <typename T>
void py_extend(std::vector<T>& dst, const std::vector<T>& src) {
    dst.insert(dst.end(), src.begin(), src.end());
}

template <typename T>
void py_extend(std::vector<T>& dst, std::initializer_list<T> src) {
    dst.insert(dst.end(), src.begin(), src.end());
}

inline void py_print_one(bool value) {
    std::cout << (value ? "True" : "False");
}

template <typename T, typename... Rest>
void py_print(const T& first, const Rest&... rest) {
    py_print_one(first);
    ((std::cout << " ", py_print_one(rest)), ...);
    std::cout << std::endl;
}

inline void py_write(std::ofstream& fs, const std::string& data) {
    fs.write(data.data(), static_cast<std::streamsize>(data.size()));
}

template <typename T>
inline void py_write(std::ofstream& fs, const T& data) {
    auto s = py_to_string(data);
    fs.write(s.data(), static_cast<std::streamsize>(s.size()));
}

template <typename T, typename U>
std::shared_ptr<T> py_cast(const pycs::cpp_module::ast::PyPtr<U>& value) {
    return std::dynamic_pointer_cast<T>(static_cast<std::shared_ptr<U>>(value));
}

template <typename T>
std::shared_ptr<T> py_cast(const std::any& value) {
    if (const auto* p = std::any_cast<T>(&value)) {
        return std::make_shared<T>(*p);
    }
    return nullptr;
}

template <typename T, typename U>
std::shared_ptr<T> py_cast(const U& value) {
    if constexpr (requires { value.template cast<T>(); }) {
        return value.template cast<T>();
    }
    return std::dynamic_pointer_cast<T>(value);
}

template <typename T, typename U>
bool py_isinstance(const U& value) {
    return py_cast<T>(value) != nullptr;
}

template <typename U, typename... Ts>
bool py_isinstance_any(const U& value) {
    return (py_isinstance<Ts>(value) || ...);
}

template <typename T>
std::size_t py_len(const T& value) {
    return value.size();
}

template <typename T>
std::vector<T> py_sorted(const std::unordered_set<T>& s) {
    std::vector<T> out(s.begin(), s.end());
    std::sort(out.begin(), out.end());
    return out;
}

template <typename T>
std::vector<T> py_sorted(const std::vector<T>& v) {
    std::vector<T> out = v;
    std::sort(out.begin(), out.end());
    return out;
}

template <typename T>
std::unordered_set<T> py_set_union(const std::unordered_set<T>& a, const std::unordered_set<T>& b) {
    std::unordered_set<T> out = a;
    out.insert(b.begin(), b.end());
    return out;
}

inline std::vector<std::string> py_splitlines(const std::string& s) {
    std::vector<std::string> out;
    std::stringstream ss(s);
    std::string line;
    while (std::getline(ss, line)) {
        out.push_back(line);
    }
    return out;
}

template <typename T>
std::string py_join(const std::string& sep, const std::vector<T>& parts) {
    std::ostringstream oss;
    for (std::size_t i = 0; i < parts.size(); ++i) {
        if (i > 0) {
            oss << sep;
        }
        oss << parts[i];
    }
    return oss.str();
}

inline std::string py_replace(const std::string& s, const std::string& from, const std::string& to) {
    if (from.empty()) {
        return s;
    }
    std::string out = s;
    std::size_t pos = 0;
    while ((pos = out.find(from, pos)) != std::string::npos) {
        out.replace(pos, from.size(), to);
        pos += to.size();
    }
    return out;
}

template <typename A, typename B>
std::vector<std::tuple<A, B>> py_zip(const std::vector<A>& a, const std::vector<B>& b) {
    std::vector<std::tuple<A, B>> out;
    const std::size_t n = std::min(a.size(), b.size());
    out.reserve(n);
    for (std::size_t i = 0; i < n; ++i) {
        out.push_back(std::make_tuple(a[i], b[i]));
    }
    return out;
}

#endif  // PYCS_CPP_MODULE_PY_RUNTIME_MODULES_H
