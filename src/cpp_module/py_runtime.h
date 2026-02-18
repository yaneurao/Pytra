#ifndef PYTRA_EAST_CPP_MODULE_PY_RUNTIME_H
#define PYTRA_EAST_CPP_MODULE_PY_RUNTIME_H

#include <algorithm>
#include <any>
#include <cctype>
#include <cmath>
#include <chrono>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <optional>
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

namespace py_math = pytra::cpp_module::math;
using PyObj = pytra::gc::PyObj;

template <class T>
using rc = pytra::gc::RcHandle<T>;
using object = rc<PyObj>;

template <class T, class... Args>
static inline rc<T> rc_new(Args&&... args) {
    return rc<T>::adopt(pytra::gc::rc_new<T>(std::forward<Args>(args)...));
}

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

class Path {
public:
    Path() = default;
    Path(const char* s) : p_(s) {}
    Path(const str& s) : p_(s) {}
    Path(const std::filesystem::path& p) : p_(p) {}

    Path operator/(const char* rhs) const { return Path(p_ / rhs); }
    Path operator/(const str& rhs) const { return Path(p_ / rhs); }
    Path operator/(const Path& rhs) const { return Path(p_ / rhs.p_); }

    Path parent() const { return Path(p_.parent_path()); }
    str name() const { return p_.filename().string(); }
    str stem() const { return p_.stem().string(); }
    bool exists() const { return std::filesystem::exists(p_); }
    void write_text(const str& s) const {
        std::ofstream ofs(p_);
        ofs << s;
    }
    str read_text() const {
        std::ifstream ifs(p_);
        std::stringstream ss;
        ss << ifs.rdbuf();
        return ss.str();
    }

    void mkdir(bool parents = false, bool exist_ok = false) const {
        std::error_code ec;
        bool created = parents ? std::filesystem::create_directories(p_, ec) : std::filesystem::create_directory(p_, ec);
        if (!created && !exist_ok && !std::filesystem::exists(p_)) {
            throw std::runtime_error("mkdir failed: " + p_.string());
        }
    }

    str string() const { return p_.string(); }
    const std::filesystem::path& native() const { return p_; }
    operator const std::filesystem::path&() const { return p_; }  // NOLINT(google-explicit-constructor)

private:
    std::filesystem::path p_;
};

template <class T>
class list : public std::vector<T> {
public:
    using std::vector<T>::vector;
    using typename std::vector<T>::const_iterator;
    using typename std::vector<T>::iterator;

    template <class U, std::enable_if_t<!std::is_same_v<U, T>, int> = 0>
    explicit list(const list<U>& other) {
        this->reserve(other.size());
        for (const auto& v : other) {
            this->push_back(static_cast<T>(v));
        }
    }

    void append(const T& value) { this->push_back(value); }
    void append(T&& value) { this->push_back(std::move(value)); }
    template <class U = T, std::enable_if_t<!std::is_same_v<U, std::any>, int> = 0>
    void append(const std::any& value) {
        if (const auto* p = std::any_cast<U>(&value)) {
            this->push_back(*p);
        }
    }

    template <class U>
    void extend(const U& values) {
        this->insert(this->end(), values.begin(), values.end());
    }

    T pop() {
        if (this->empty()) {
            throw std::out_of_range("pop from empty list");
        }
        T out = this->back();
        this->pop_back();
        return out;
    }

    T pop(int64 idx) {
        if (this->empty()) {
            throw std::out_of_range("pop from empty list");
        }
        if (idx < 0) idx += static_cast<int64>(this->size());
        if (idx < 0 || idx >= static_cast<int64>(this->size())) {
            throw std::out_of_range("pop index out of range");
        }
        T out = (*this)[static_cast<std::size_t>(idx)];
        this->erase(this->begin() + idx);
        return out;
    }
};

using bytearray = list<uint8>;
using bytes = bytearray;

template <class K, class V>
class dict : public std::unordered_map<K, V> {
public:
    using Base = std::unordered_map<K, V>;
    using std::unordered_map<K, V>::unordered_map;
    using typename std::unordered_map<K, V>::const_iterator;
    using typename std::unordered_map<K, V>::iterator;
    using value_type = typename Base::value_type;

    dict() = default;
    dict(std::initializer_list<value_type> init) : Base(init) {}

    V get(const K& key) const {
        auto it = this->find(key);
        if (it == this->end()) {
            throw std::out_of_range("dict.get missing key");
        }
        return it->second;
    }

    V get(const K& key, const V& default_value) const {
        auto it = this->find(key);
        if (it == this->end()) {
            return default_value;
        }
        return it->second;
    }

    list<K> keys() const {
        list<K> out{};
        out.reserve(this->size());
        for (const auto& kv : *this) out.push_back(kv.first);
        return out;
    }

    list<V> values() const {
        list<V> out{};
        out.reserve(this->size());
        for (const auto& kv : *this) out.push_back(kv.second);
        return out;
    }

    list<std::tuple<K, V>> items() const {
        list<std::tuple<K, V>> out{};
        out.reserve(this->size());
        for (const auto& kv : *this) out.push_back(std::make_tuple(kv.first, kv.second));
        return out;
    }
};

template <class T>
class set : public std::unordered_set<T> {
public:
    using Base = std::unordered_set<T>;
    using std::unordered_set<T>::unordered_set;
    using typename std::unordered_set<T>::const_iterator;
    using typename std::unordered_set<T>::iterator;
    using value_type = typename Base::value_type;

    set() = default;
    set(std::initializer_list<value_type> init) : Base(init) {}

    void add(const T& value) { this->insert(value); }

    void discard(const T& value) { this->erase(value); }

    void remove(const T& value) {
        if (this->erase(value) == 0) {
            throw std::out_of_range("set.remove missing value");
        }
    }
};

class PyIntObj : public PyObj {
public:
    explicit PyIntObj(int64 v) : value(v) {}
    int64 value;
};

class PyFloatObj : public PyObj {
public:
    explicit PyFloatObj(float64 v) : value(v) {}
    float64 value;
};

class PyBoolObj : public PyObj {
public:
    explicit PyBoolObj(bool v) : value(v) {}
    bool value;
};

class PyStrObj : public PyObj {
public:
    explicit PyStrObj(str v) : value(std::move(v)) {}
    str value;
};

class PyListObj : public PyObj {
public:
    explicit PyListObj(list<object> v) : value(std::move(v)) {}
    list<object> value;
};

class PyDictObj : public PyObj {
public:
    explicit PyDictObj(dict<str, object> v) : value(std::move(v)) {}
    dict<str, object> value;
};

template <class T>
static inline T* py_obj_cast(const object& obj) {
    if (!obj) return nullptr;
    return dynamic_cast<T*>(obj.get());
}

template <class T, class... Args>
static inline object object_new(Args&&... args) {
    return object::adopt(static_cast<PyObj*>(pytra::gc::rc_new<T>(std::forward<Args>(args)...)));
}

template <class T, std::enable_if_t<std::is_base_of_v<PyObj, T>, int> = 0>
static inline object make_object(const rc<T>& v) {
    if (!v) return object();
    return object(static_cast<PyObj*>(v.get()));
}

static inline object make_object(const object& v) { return v; }
static inline object make_object(std::nullptr_t) { return object(); }
static inline object make_object(const str& v) { return object_new<PyStrObj>(v); }
static inline object make_object(const char* v) { return object_new<PyStrObj>(str(v)); }
static inline object make_object(bool v) { return object_new<PyBoolObj>(v); }
static inline object make_object(float64 v) { return object_new<PyFloatObj>(v); }
static inline object make_object(float32 v) { return object_new<PyFloatObj>(static_cast<float64>(v)); }
static inline object make_object(int64 v) { return object_new<PyIntObj>(v); }
static inline object make_object(uint64 v) { return object_new<PyIntObj>(static_cast<int64>(v)); }
static inline object make_object(int32 v) { return object_new<PyIntObj>(static_cast<int64>(v)); }
static inline object make_object(uint32 v) { return object_new<PyIntObj>(static_cast<int64>(v)); }
static inline object make_object(int16 v) { return object_new<PyIntObj>(static_cast<int64>(v)); }
static inline object make_object(uint16 v) { return object_new<PyIntObj>(static_cast<int64>(v)); }
static inline object make_object(int8 v) { return object_new<PyIntObj>(static_cast<int64>(v)); }
static inline object make_object(uint8 v) { return object_new<PyIntObj>(static_cast<int64>(v)); }

static inline object make_object(const std::any& v) {
    if (!v.has_value()) return object();
    if (const auto* p = std::any_cast<object>(&v)) return *p;
    if (const auto* p = std::any_cast<str>(&v)) return make_object(*p);
    if (const auto* p = std::any_cast<const char*>(&v)) return make_object(*p);
    if (const auto* p = std::any_cast<bool>(&v)) return make_object(*p);
    if (const auto* p = std::any_cast<float64>(&v)) return make_object(*p);
    if (const auto* p = std::any_cast<float32>(&v)) return make_object(*p);
    if (const auto* p = std::any_cast<int64>(&v)) return make_object(*p);
    if (const auto* p = std::any_cast<uint64>(&v)) return make_object(*p);
    if (const auto* p = std::any_cast<int32>(&v)) return make_object(*p);
    if (const auto* p = std::any_cast<uint32>(&v)) return make_object(*p);
    if (const auto* p = std::any_cast<int16>(&v)) return make_object(*p);
    if (const auto* p = std::any_cast<uint16>(&v)) return make_object(*p);
    if (const auto* p = std::any_cast<int8>(&v)) return make_object(*p);
    if (const auto* p = std::any_cast<uint8>(&v)) return make_object(*p);
    if (const auto* p = std::any_cast<list<std::any>>(&v)) {
        list<object> out{};
        out.reserve(p->size());
        for (const auto& e : *p) out.append(make_object(e));
        return object_new<PyListObj>(out);
    }
    if (const auto* p = std::any_cast<dict<str, std::any>>(&v)) {
        dict<str, object> out{};
        for (const auto& kv : *p) out[kv.first] = make_object(kv.second);
        return object_new<PyDictObj>(out);
    }
    return object();
}

template <class T>
static inline object make_object(const list<T>& values) {
    list<object> out;
    out.reserve(values.size());
    for (const auto& v : values) out.append(make_object(v));
    return object_new<PyListObj>(std::move(out));
}

template <class V>
static inline object make_object(const dict<str, V>& values) {
    dict<str, object> out;
    for (const auto& kv : values) out[kv.first] = make_object(kv.second);
    return object_new<PyDictObj>(std::move(out));
}

static inline int64 obj_to_int64(const object& v) {
    if (!v) return 0;
    if (const auto* p = py_obj_cast<PyIntObj>(v)) return p->value;
    if (const auto* p = py_obj_cast<PyBoolObj>(v)) return p->value ? 1 : 0;
    if (const auto* p = py_obj_cast<PyFloatObj>(v)) return static_cast<int64>(p->value);
    if (const auto* p = py_obj_cast<PyStrObj>(v)) {
        try {
            return static_cast<int64>(std::stoll(p->value));
        } catch (...) {
            return 0;
        }
    }
    return 0;
}

static inline float64 obj_to_float64(const object& v) {
    if (!v) return 0.0;
    if (const auto* p = py_obj_cast<PyFloatObj>(v)) return p->value;
    if (const auto* p = py_obj_cast<PyIntObj>(v)) return static_cast<float64>(p->value);
    if (const auto* p = py_obj_cast<PyBoolObj>(v)) return p->value ? 1.0 : 0.0;
    if (const auto* p = py_obj_cast<PyStrObj>(v)) {
        try {
            return std::stod(p->value);
        } catch (...) {
            return 0.0;
        }
    }
    return 0.0;
}

static inline bool obj_to_bool(const object& v) {
    if (!v) return false;
    if (const auto* p = py_obj_cast<PyBoolObj>(v)) return p->value;
    if (const auto* p = py_obj_cast<PyIntObj>(v)) return p->value != 0;
    if (const auto* p = py_obj_cast<PyFloatObj>(v)) return p->value != 0.0;
    if (const auto* p = py_obj_cast<PyStrObj>(v)) return !p->value.empty();
    if (const auto* p = py_obj_cast<PyListObj>(v)) return !p->value.empty();
    if (const auto* p = py_obj_cast<PyDictObj>(v)) return !p->value.empty();
    return true;
}

static inline str obj_to_str(const object& v) {
    if (!v) return "None";
    if (const auto* p = py_obj_cast<PyStrObj>(v)) return p->value;
    if (const auto* p = py_obj_cast<PyIntObj>(v)) return std::to_string(p->value);
    if (const auto* p = py_obj_cast<PyFloatObj>(v)) return std::to_string(p->value);
    if (const auto* p = py_obj_cast<PyBoolObj>(v)) return p->value ? "True" : "False";
    if (const auto* p = py_obj_cast<PyListObj>(v)) return "<list>";
    if (const auto* p = py_obj_cast<PyDictObj>(v)) return "<dict>";
    return "<object>";
}

static inline const dict<str, object>* obj_to_dict_ptr(const object& v) {
    if (const auto* p = py_obj_cast<PyDictObj>(v)) return &(p->value);
    return nullptr;
}

static inline const list<object>* obj_to_list_ptr(const object& v) {
    if (const auto* p = py_obj_cast<PyListObj>(v)) return &(p->value);
    return nullptr;
}

static inline dict<str, object> obj_to_dict(const object& v) {
    if (const auto* p = obj_to_dict_ptr(v)) return *p;
    return {};
}

static inline bool operator==(const object& lhs, const object& rhs) {
    return lhs.get() == rhs.get();
}

static inline bool operator!=(const object& lhs, const object& rhs) {
    return !(lhs == rhs);
}

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

static inline std::string py_to_string(uint8 v) {
    return std::to_string(static_cast<int>(v));
}

static inline std::string py_to_string(int8 v) {
    return std::to_string(static_cast<int>(v));
}

static inline std::string py_to_string(const char* v) {
    return std::string(v);
}

template <class T>
static inline std::string py_to_string(const std::optional<T>& v) {
    if (!v.has_value()) return "None";
    return py_to_string(*v);
}

static inline std::string py_to_string(const std::any& v) {
    if (const auto* p = std::any_cast<str>(&v)) return *p;
    if (const auto* p = std::any_cast<int64>(&v)) return std::to_string(*p);
    if (const auto* p = std::any_cast<uint64>(&v)) return std::to_string(*p);
    if (const auto* p = std::any_cast<int>(&v)) return std::to_string(*p);
    if (const auto* p = std::any_cast<float64>(&v)) return std::to_string(*p);
    if (const auto* p = std::any_cast<float32>(&v)) return std::to_string(*p);
    if (const auto* p = std::any_cast<bool>(&v)) return *p ? "True" : "False";
    return "<any>";
}

static inline std::string py_to_string(const Path& v) {
    return v.string();
}

static inline std::string py_to_string(const object& v) {
    return obj_to_str(v);
}

static inline std::string py_bool_to_string(bool v) {
    return v ? "True" : "False";
}

static inline int64 py_to_int64(const str& v) {
    return static_cast<int64>(std::stoll(v));
}

template <class T, std::enable_if_t<std::is_arithmetic_v<T>, int> = 0>
static inline int64 py_to_int64(T v) {
    return static_cast<int64>(v);
}

static inline int64 py_to_int64(const object& v) {
    return obj_to_int64(v);
}

static inline float64 py_to_float64(const object& v) {
    return obj_to_float64(v);
}

static inline bool py_to_bool(const object& v) {
    return obj_to_bool(v);
}

static inline int64 py_to_int64(const std::any& v) {
    if (const auto* p = std::any_cast<int64>(&v)) return *p;
    if (const auto* p = std::any_cast<int>(&v)) return static_cast<int64>(*p);
    if (const auto* p = std::any_cast<uint8>(&v)) return static_cast<int64>(*p);
    if (const auto* p = std::any_cast<int8>(&v)) return static_cast<int64>(*p);
    if (const auto* p = std::any_cast<uint16>(&v)) return static_cast<int64>(*p);
    if (const auto* p = std::any_cast<int16>(&v)) return static_cast<int64>(*p);
    if (const auto* p = std::any_cast<uint32>(&v)) return static_cast<int64>(*p);
    if (const auto* p = std::any_cast<int32>(&v)) return static_cast<int64>(*p);
    if (const auto* p = std::any_cast<uint64>(&v)) return static_cast<int64>(*p);
    if (const auto* p = std::any_cast<float64>(&v)) return static_cast<int64>(*p);
    if (const auto* p = std::any_cast<float32>(&v)) return static_cast<int64>(*p);
    if (const auto* p = std::any_cast<bool>(&v)) return *p ? 1 : 0;
    if (const auto* p = std::any_cast<str>(&v)) {
        try {
            return static_cast<int64>(std::stoll(*p));
        } catch (...) {
            return 0;
        }
    }
    return 0;
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

static inline bool py_assert_true(bool cond, const str& label = "") {
    if (cond) return true;
    if (label != "") {
        std::cout << "[assert_true] " << label << ": False" << std::endl;
    } else {
        std::cout << "[assert_true] False" << std::endl;
    }
    return false;
}

template <class A, class B>
static inline bool py_assert_eq(const A& actual, const B& expected, const str& label = "") {
    const bool ok = (actual == expected);
    if (ok) return true;
    if (label != "") {
        std::cout << "[assert_eq] " << label << ": actual=" << py_to_string(actual)
                  << ", expected=" << py_to_string(expected) << std::endl;
    } else {
        std::cout << "[assert_eq] actual=" << py_to_string(actual)
                  << ", expected=" << py_to_string(expected) << std::endl;
    }
    return false;
}

static inline bool py_assert_all(const list<bool>& results, const str& label = "") {
    for (bool v : results) {
        if (!v) {
            if (label != "") {
                std::cout << "[assert_all] " << label << ": False" << std::endl;
            } else {
                std::cout << "[assert_all] False" << std::endl;
            }
            return false;
        }
    }
    return true;
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

template <class T>
static inline T& py_at(list<T>& v, int64 idx) {
    if (idx < 0) idx += static_cast<int64>(v.size());
    if (idx < 0 || idx >= static_cast<int64>(v.size())) {
        throw std::out_of_range("list index out of range");
    }
    return v[static_cast<std::size_t>(idx)];
}

template <class T>
static inline const T& py_at(const list<T>& v, int64 idx) {
    if (idx < 0) idx += static_cast<int64>(v.size());
    if (idx < 0 || idx >= static_cast<int64>(v.size())) {
        throw std::out_of_range("list index out of range");
    }
    return v[static_cast<std::size_t>(idx)];
}

template <class K, class V>
static inline const V& py_dict_get(const dict<K, V>& d, const K& key) {
    auto it = d.find(key);
    if (it == d.end()) {
        throw std::out_of_range("dict key not found");
    }
    return it->second;
}

template <class K, class V>
static inline const V& py_dict_get(const std::optional<dict<K, V>>& d, const K& key) {
    if (!d.has_value()) {
        throw std::out_of_range("dict key not found");
    }
    return py_dict_get(*d, key);
}

template <class V>
static inline const V& py_dict_get(const dict<str, V>& d, const char* key) {
    auto it = d.find(str(key));
    if (it == d.end()) {
        throw std::out_of_range("dict key not found");
    }
    return it->second;
}

template <class V>
static inline const V& py_dict_get(const std::optional<dict<str, V>>& d, const char* key) {
    if (!d.has_value()) {
        throw std::out_of_range("dict key not found");
    }
    return py_dict_get(*d, key);
}

static inline object py_dict_get(const dict<str, object>& d, const char* key) {
    auto it = d.find(str(key));
    if (it == d.end()) {
        throw std::out_of_range("dict key not found");
    }
    return it->second;
}

static inline object py_dict_get(const object& obj, const char* key) {
    if (const auto* p = obj_to_dict_ptr(obj)) {
        return py_dict_get(*p, key);
    }
    throw std::runtime_error("py_dict_get on non-dict object");
}

static inline std::any py_dict_get(const std::any& obj, const char* key) {
    if (const auto* p = std::any_cast<dict<str, std::any>>(&obj)) {
        auto it = p->find(str(key));
        if (it == p->end()) throw std::out_of_range("dict key not found");
        return it->second;
    }
    throw std::runtime_error("py_dict_get on non-dict any");
}

template <class K, class V>
static inline V py_dict_get_default(const dict<K, V>& d, const K& key, const V& defval) {
    auto it = d.find(key);
    if (it == d.end()) {
        return defval;
    }
    return it->second;
}

template <class K, class V>
static inline V py_dict_get_default(const std::optional<dict<K, V>>& d, const K& key, const V& defval) {
    if (!d.has_value()) {
        return defval;
    }
    return py_dict_get_default(*d, key, defval);
}

template <class V>
static inline V py_dict_get_default(const dict<str, V>& d, const char* key, const V& defval) {
    auto it = d.find(str(key));
    if (it == d.end()) {
        return defval;
    }
    return it->second;
}

template <class V>
static inline V py_dict_get_default(const std::optional<dict<str, V>>& d, const char* key, const V& defval) {
    if (!d.has_value()) {
        return defval;
    }
    return py_dict_get_default(*d, key, defval);
}

template <class K, class V, class D, std::enable_if_t<std::is_convertible_v<D, V>, int> = 0>
static inline V py_dict_get_default(const dict<K, V>& d, const K& key, const D& defval) {
    auto it = d.find(key);
    if (it == d.end()) {
        return static_cast<V>(defval);
    }
    return it->second;
}

template <class K, class V, class D, std::enable_if_t<std::is_convertible_v<D, V>, int> = 0>
static inline V py_dict_get_default(const std::optional<dict<K, V>>& d, const K& key, const D& defval) {
    if (!d.has_value()) {
        return static_cast<V>(defval);
    }
    return py_dict_get_default(*d, key, defval);
}

template <class V, class D, std::enable_if_t<std::is_convertible_v<D, V>, int> = 0>
static inline V py_dict_get_default(const dict<str, V>& d, const char* key, const D& defval) {
    auto it = d.find(str(key));
    if (it == d.end()) {
        return static_cast<V>(defval);
    }
    return it->second;
}

template <class V, class D, std::enable_if_t<std::is_convertible_v<D, V>, int> = 0>
static inline V py_dict_get_default(const std::optional<dict<str, V>>& d, const char* key, const D& defval) {
    if (!d.has_value()) {
        return static_cast<V>(defval);
    }
    return py_dict_get_default(*d, key, defval);
}

static inline object py_dict_get_default(const dict<str, object>& d, const char* key, const object& defval) {
    auto it = d.find(str(key));
    if (it == d.end()) {
        return defval;
    }
    return it->second;
}

static inline object py_dict_get_default(const dict<str, object>& d, const char* key, const char* defval) {
    auto it = d.find(str(key));
    if (it == d.end()) {
        return make_object(str(defval));
    }
    return it->second;
}

static inline dict<str, object> py_dict_get_default(
    const dict<str, object>& d, const char* key, const dict<str, object>& defval) {
    auto it = d.find(str(key));
    if (it == d.end()) {
        return defval;
    }
    if (const auto* p = obj_to_dict_ptr(it->second)) {
        return *p;
    }
    return defval;
}

static inline object py_dict_get_default(const dict<str, object>& d, const char* key, const str& defval) {
    auto it = d.find(str(key));
    if (it == d.end()) {
        return make_object(defval);
    }
    return it->second;
}

static inline object py_dict_get_default(const object& obj, const char* key, const object& defval) {
    if (const auto* p = obj_to_dict_ptr(obj)) {
        return py_dict_get_default(*p, key, defval);
    }
    return defval;
}

static inline object py_dict_get_default(const object& obj, const char* key, const char* defval) {
    if (const auto* p = obj_to_dict_ptr(obj)) {
        return py_dict_get_default(*p, key, defval);
    }
    return make_object(str(defval));
}

static inline object py_dict_get_default(const std::optional<dict<str, object>>& d, const char* key, const object& defval) {
    if (!d.has_value()) {
        return defval;
    }
    return py_dict_get_default(*d, key, defval);
}

static inline object py_dict_get_default(const std::optional<dict<str, object>>& d, const char* key, const char* defval) {
    if (!d.has_value()) {
        return make_object(str(defval));
    }
    return py_dict_get_default(*d, key, defval);
}

static inline object py_dict_get_default(const std::optional<dict<str, object>>& d, const char* key, const str& defval) {
    if (!d.has_value()) {
        return make_object(defval);
    }
    return py_dict_get_default(*d, key, defval);
}

template <class D>
static inline D py_dict_get_default(const dict<str, std::any>& d, const char* key, const D& defval) {
    auto it = d.find(str(key));
    if (it == d.end()) {
        return defval;
    }
    const D* p = std::any_cast<D>(&(it->second));
    if (p == nullptr) {
        return defval;
    }
    return *p;
}

template <class D>
static inline D py_dict_get_default(const std::any& obj, const char* key, const D& defval) {
    if (const auto* p = std::any_cast<dict<str, std::any>>(&obj)) {
        return py_dict_get_default(*p, key, defval);
    }
    return defval;
}

static inline str py_dict_get_default(const std::any& obj, const char* key, const char* defval) {
    if (const auto* p = std::any_cast<dict<str, std::any>>(&obj)) {
        auto it = p->find(str(key));
        if (it == p->end()) return str(defval);
        if (const auto* s = std::any_cast<str>(&(it->second))) return *s;
        return str(defval);
    }
    return str(defval);
}

static inline str py_dict_get_default(const dict<str, std::any>& d, const char* key, const char* defval) {
    auto it = d.find(str(key));
    if (it == d.end()) return str(defval);
    if (const auto* s = std::any_cast<str>(&(it->second))) return *s;
    return str(defval);
}

template <class T>
static inline bool py_is_none(const std::optional<T>& v) {
    return !v.has_value();
}

template <class T>
static inline bool py_is_none(const T&) {
    return false;
}

static inline bool py_is_none(const object& v) {
    return !static_cast<bool>(v);
}

static inline bool py_is_none(const std::any& v) {
    if (!v.has_value()) return true;
    if (v.type() == typeid(std::nullopt_t)) return true;
    return false;
}

template <class T>
static inline std::optional<T> py_any_to_optional(const std::any& v) {
    if (!v.has_value()) return std::nullopt;
    if (const auto* p = std::any_cast<T>(&v)) return *p;
    if (const auto* p = std::any_cast<std::optional<T>>(&v)) return *p;
    return std::nullopt;
}

template <class T>
static inline bool py_any(const T& values) {
    for (const auto& v : values) {
        if (static_cast<bool>(v)) return true;
    }
    return false;
}

template <class T>
static inline bool py_all(const T& values) {
    for (const auto& v : values) {
        if (!static_cast<bool>(v)) return false;
    }
    return true;
}

template <class T> static inline bool py_is_dict(const T&) { return false; }
template <class T> static inline bool py_is_list(const T&) { return false; }
template <class T> static inline bool py_is_set(const T&) { return false; }
template <class T> static inline bool py_is_str(const T&) { return false; }
template <class T> static inline bool py_is_bool(const T&) { return false; }

template <class K, class V> static inline bool py_is_dict(const dict<K, V>&) { return true; }
template <class U> static inline bool py_is_list(const list<U>&) { return true; }
template <class U> static inline bool py_is_set(const set<U>&) { return true; }
static inline bool py_is_str(const str&) { return true; }
template <class T> static inline bool py_is_int(const T&) { return std::is_integral_v<T> && !std::is_same_v<T, bool>; }
template <class T> static inline bool py_is_float(const T&) { return std::is_floating_point_v<T>; }
static inline bool py_is_bool(const bool&) { return true; }

static inline bool py_is_dict(const object& v) { return py_obj_cast<PyDictObj>(v) != nullptr; }
static inline bool py_is_list(const object& v) { return py_obj_cast<PyListObj>(v) != nullptr; }
static inline bool py_is_str(const object& v) { return py_obj_cast<PyStrObj>(v) != nullptr; }
static inline bool py_is_int(const object& v) { return py_obj_cast<PyIntObj>(v) != nullptr; }
static inline bool py_is_float(const object& v) { return py_obj_cast<PyFloatObj>(v) != nullptr; }
static inline bool py_is_bool(const object& v) { return py_obj_cast<PyBoolObj>(v) != nullptr; }

template <class T> static inline bool py_is_dict(const std::optional<T>& v) {
    if (!v.has_value()) return false;
    return py_is_dict(*v);
}
template <class T> static inline bool py_is_list(const std::optional<T>& v) {
    if (!v.has_value()) return false;
    return py_is_list(*v);
}
template <class T> static inline bool py_is_set(const std::optional<T>& v) {
    if (!v.has_value()) return false;
    return py_is_set(*v);
}
template <class T> static inline bool py_is_str(const std::optional<T>& v) {
    if (!v.has_value()) return false;
    return py_is_str(*v);
}
template <class T> static inline bool py_is_bool(const std::optional<T>& v) {
    if (!v.has_value()) return false;
    return py_is_bool(*v);
}

static inline bool py_is_dict(const std::any& v) { return v.type() == typeid(dict<str, std::any>); }
static inline bool py_is_list(const std::any& v) { return v.type() == typeid(list<std::any>); }
static inline bool py_is_set(const std::any& v) { return v.type() == typeid(set<str>) || v.type() == typeid(set<std::any>); }
static inline bool py_is_str(const std::any& v) { return v.type() == typeid(str); }
static inline bool py_is_int(const std::any& v) {
    return v.type() == typeid(int) || v.type() == typeid(int64) || v.type() == typeid(uint64);
}
static inline bool py_is_float(const std::any& v) { return v.type() == typeid(float32) || v.type() == typeid(float64); }
static inline bool py_is_bool(const std::any& v) { return v.type() == typeid(bool); }

static inline bool operator==(const std::any& lhs, const char* rhs) {
    if (const auto* p = std::any_cast<str>(&lhs)) return *p == str(rhs);
    return false;
}

static inline bool operator!=(const std::any& lhs, const char* rhs) {
    return !(lhs == rhs);
}

static inline bool operator>(const std::any& lhs, int rhs) {
    if (const auto* p = std::any_cast<int64>(&lhs)) return *p > static_cast<int64>(rhs);
    if (const auto* p = std::any_cast<int>(&lhs)) return *p > rhs;
    if (const auto* p = std::any_cast<uint64>(&lhs)) return *p > static_cast<uint64>(rhs);
    return false;
}

static inline bool operator<(int64 lhs, const std::any& rhs) {
    if (const auto* p = std::any_cast<int64>(&rhs)) return lhs < *p;
    if (const auto* p = std::any_cast<int>(&rhs)) return lhs < static_cast<int64>(*p);
    if (const auto* p = std::any_cast<uint64>(&rhs)) return lhs < static_cast<int64>(*p);
    return false;
}

static inline str operator+(const char* lhs, const std::any& rhs) {
    return str(lhs) + py_to_string(rhs);
}

static inline list<std::any>::iterator begin(std::any& v) {
    if (auto* p = std::any_cast<list<std::any>>(&v)) return p->begin();
    static list<std::any> empty;
    return empty.begin();
}

static inline list<std::any>::iterator end(std::any& v) {
    if (auto* p = std::any_cast<list<std::any>>(&v)) return p->end();
    static list<std::any> empty;
    return empty.end();
}

static inline list<std::any>::const_iterator begin(const std::any& v) {
    if (const auto* p = std::any_cast<list<std::any>>(&v)) return p->begin();
    static const list<std::any> empty;
    return empty.begin();
}

static inline list<std::any>::const_iterator end(const std::any& v) {
    if (const auto* p = std::any_cast<list<std::any>>(&v)) return p->end();
    static const list<std::any> empty;
    return empty.end();
}

static inline list<object>::const_iterator begin(const object& v) {
    if (const auto* p = obj_to_list_ptr(v)) return p->begin();
    static const list<object> empty;
    return empty.begin();
}

static inline list<object>::const_iterator end(const object& v) {
    if (const auto* p = obj_to_list_ptr(v)) return p->end();
    static const list<object> empty;
    return empty.end();
}

static inline list<object>::const_iterator begin(const std::optional<object>& v) {
    if (!v.has_value()) {
        static const list<object> empty;
        return empty.begin();
    }
    return begin(*v);
}

static inline list<object>::const_iterator end(const std::optional<object>& v) {
    if (!v.has_value()) {
        static const list<object> empty;
        return empty.end();
    }
    return end(*v);
}

// Selfhost-generated C++ can iterate std::any values that hold list<std::any>.
// Provide std::begin/std::end overloads so range-for resolves them.
namespace std {
static inline ::list<std::any>::iterator begin(std::any& v) {
    return ::begin(v);
}
static inline ::list<std::any>::iterator end(std::any& v) {
    return ::end(v);
}
static inline ::list<std::any>::const_iterator begin(const std::any& v) {
    return ::begin(v);
}
static inline ::list<std::any>::const_iterator end(const std::any& v) {
    return ::end(v);
}
}  // namespace std

template <class K, class V>
static inline list<K> py_dict_keys(const dict<K, V>& d) {
    list<K> out;
    out.reserve(d.size());
    for (const auto& kv : d) out.push_back(kv.first);
    return out;
}

template <class K, class V>
static inline list<V> py_dict_values(const dict<K, V>& d) {
    list<V> out;
    out.reserve(d.size());
    for (const auto& kv : d) out.push_back(kv.second);
    return out;
}

static inline str py_at(const str& v, int64 idx) {
    if (idx < 0) idx += static_cast<int64>(v.size());
    if (idx < 0 || idx >= static_cast<int64>(v.size())) {
        throw std::out_of_range("string index out of range");
    }
    return str(1, v[static_cast<std::size_t>(idx)]);
}

static inline str py_slice(const std::any& v, int64 lo, int64 up) {
    if (const auto* s = std::any_cast<str>(&v)) return py_slice(*s, lo, up);
    return "";
}

static inline void py_write_text(const Path& p, const str& s) {
    std::ofstream ofs(p.native());
    ofs << s;
}

static inline str py_read_text(const Path& p) {
    std::ifstream ifs(p.native());
    std::stringstream ss;
    ss << ifs.rdbuf();
    return ss.str();
}

static inline str py_lstrip(const str& s) {
    std::size_t i = 0;
    while (i < s.size() && std::isspace(static_cast<unsigned char>(s[i])) != 0) i++;
    return s.substr(i);
}

static inline str py_rstrip(const str& s) {
    if (s.empty()) return s;
    std::size_t i = s.size();
    while (i > 0 && std::isspace(static_cast<unsigned char>(s[i - 1])) != 0) i--;
    return s.substr(0, i);
}

static inline str py_strip(const str& s) {
    return py_rstrip(py_lstrip(s));
}

static inline bool py_startswith(const str& s, const str& prefix) {
    return s.rfind(prefix, 0) == 0;
}

static inline bool py_endswith(const str& s, const str& suffix) {
    if (suffix.size() > s.size()) return false;
    return s.compare(s.size() - suffix.size(), suffix.size(), suffix) == 0;
}

static inline str py_replace(const str& s, const str& oldv, const str& newv) {
    if (oldv.empty()) return s;
    str out = s;
    std::size_t pos = 0;
    while ((pos = out.find(oldv, pos)) != str::npos) {
        out.replace(pos, oldv.size(), newv);
        pos += newv.size();
    }
    return out;
}

template <class T>
static inline str py_join(const str& sep, const list<T>& values) {
    if (values.empty()) return "";
    str out = py_to_string(values[0]);
    for (std::size_t i = 1; i < values.size(); i++) {
        out += sep;
        out += py_to_string(values[i]);
    }
    return out;
}

static inline str py_join(const str& sep, const object& values) {
    if (const auto* p = obj_to_list_ptr(values)) {
        return py_join(sep, *p);
    }
    return "";
}

template <class T>
static inline list<T> py_reversed(const list<T>& values) {
    list<T> out(values.begin(), values.end());
    std::reverse(out.begin(), out.end());
    return out;
}

static inline list<std::any> py_reversed(const std::any& values) {
    if (const auto* p = std::any_cast<list<std::any>>(&values)) return py_reversed(*p);
    return {};
}

template <class T>
static inline list<std::tuple<int64, T>> py_enumerate(const list<T>& values) {
    list<std::tuple<int64, T>> out;
    out.reserve(values.size());
    for (std::size_t i = 0; i < values.size(); i++) {
        out.append(std::make_tuple(static_cast<int64>(i), values[i]));
    }
    return out;
}

static inline list<std::tuple<int64, std::any>> py_enumerate(const std::any& values) {
    if (const auto* p = std::any_cast<list<std::any>>(&values)) return py_enumerate(*p);
    return {};
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

template <class F>
class py_scope_exit {
public:
    explicit py_scope_exit(F&& fn) : fn_(std::forward<F>(fn)), active_(true) {}
    py_scope_exit(const py_scope_exit&) = delete;
    py_scope_exit& operator=(const py_scope_exit&) = delete;
    py_scope_exit(py_scope_exit&& other) noexcept : fn_(std::move(other.fn_)), active_(other.active_) {
        other.active_ = false;
    }
    ~py_scope_exit() {
        if (active_) fn_();
    }
    void release() { active_ = false; }

private:
    F fn_;
    bool active_;
};

template <class F>
static inline auto py_make_scope_exit(F&& fn) {
    return py_scope_exit<F>(std::forward<F>(fn));
}

enum class pytra_image_format_t {
    png,
    ppm,
};

inline pytra_image_format_t pytra_image_format = pytra_image_format_t::png;

static inline str pytra_resolve_image_path_for_write(const str& path) {
    if (pytra_image_format != pytra_image_format_t::ppm) {
        return path;
    }
    const std::size_t dot = path.find_last_of('.');
    if (dot == str::npos) {
        return path + ".ppm";
    }
    return path.substr(0, dot) + ".ppm";
}

static inline void pytra_set_image_format(pytra_image_format_t fmt) {
    pytra_image_format = fmt;
}

static inline void pytra_configure_from_argv(int argc, char** argv) {
    for (int i = 1; i < argc; ++i) {
        str arg = argv[i] != nullptr ? str(argv[i]) : str();
        if (arg.rfind("--pytra-image-format=", 0) == 0) {
            const str value = arg.substr(21);
            if (value == "png") {
                pytra_set_image_format(pytra_image_format_t::png);
            } else if (value == "ppm") {
                pytra_set_image_format(pytra_image_format_t::ppm);
            } else {
                throw std::runtime_error("unknown --pytra-image-format value: " + value);
            }
        }
    }
}

namespace png_helper {
static inline void write_rgb_png(const str& path, int64 width, int64 height, const list<uint8>& pixels) {
    const str out_path = pytra_resolve_image_path_for_write(path);
    if (pytra_image_format == pytra_image_format_t::ppm) {
        pytra::cpp_module::png::write_rgb_ppm(out_path, static_cast<int>(width), static_cast<int>(height), pixels);
    } else {
        pytra::cpp_module::png::write_rgb_png(out_path, static_cast<int>(width), static_cast<int>(height), pixels);
    }
}
}  // namespace png_helper

// Backward compatibility for previously generated C++.
static inline void write_rgb_png(const str& path, int64 width, int64 height, const list<uint8>& pixels) {
    png_helper::write_rgb_png(path, width, height, pixels);
}

static inline list<uint8> grayscale_palette() {
    auto raw = pytra::cpp_module::gif::grayscale_palette();
    return list<uint8>(raw.begin(), raw.end());
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
    std::vector<std::vector<uint8>> raw_frames;
    raw_frames.reserve(frames.size());
    for (const auto& frame : frames) {
        raw_frames.emplace_back(frame.begin(), frame.end());
    }
    std::vector<uint8> raw_pal;
    if (palette.empty()) {
        raw_pal = pytra::cpp_module::gif::grayscale_palette();
    } else {
        raw_pal.assign(palette.begin(), palette.end());
    }
    pytra::cpp_module::gif::save_gif(
        path,
        static_cast<int>(width),
        static_cast<int>(height),
        raw_frames,
        raw_pal,
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
    return v.pop();
}

template <class T>
static inline T py_pop(list<T>& v, int64 idx) {
    return v.pop(idx);
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
        for (int64 i = start; i < stop; i += step) out.append(i);
    } else {
        for (int64 i = start; i > stop; i += step) out.append(i);
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
