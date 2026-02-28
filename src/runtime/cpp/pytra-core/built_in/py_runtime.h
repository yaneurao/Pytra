#ifndef PYTRA_BUILT_IN_PY_RUNTIME_H
#define PYTRA_BUILT_IN_PY_RUNTIME_H

#include <algorithm>
#include <any>
#include <cctype>
#include <cmath>
#include <cstdint>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <functional>
#include <iostream>
#include <optional>
#include <regex>
#include <sstream>
#include <stdexcept>
#include <string>
#include <type_traits>
#include <tuple>
#include <typeinfo>
#include <unordered_map>
#include <unordered_set>
#include <utility>
#include <vector>

using int8 = ::std::int8_t;
using uint8 = ::std::uint8_t;
using int16 = ::std::int16_t;
using uint16 = ::std::uint16_t;
using int32 = ::std::int32_t;
using uint32 = ::std::uint32_t;
using int64 = ::std::int64_t;
using uint64 = ::std::uint64_t;
using float32 = float;
using float64 = double;
// 上の型エイリアスは EAST 側の固定幅型名（int64 など）を C++ 基本型へ対応付ける。

#include "bytes_util.h"
#include "exceptions.h"
#include "gc.h"
#include "io.h"
using PyObj = pytra::gc::PyObj;
using PyFile = pytra::runtime::cpp::base::PyFile;

template <class T>
using rc = pytra::gc::RcHandle<T>;
using object = rc<PyObj>;

template <class T, class... Args>
static inline rc<T> rc_new(Args&&... args) {
    return rc<T>::adopt(pytra::gc::rc_new<T>(::std::forward<Args>(args)...));
}

class str;
class PyListObj;
template <class T> class list;
template <class K, class V> class dict;
static inline str obj_to_str(const object& v);
static inline dict<str, object> obj_to_dict(const object& v);
static inline const dict<str, object>* obj_to_dict_ptr(const object& v);
static inline const list<object>* obj_to_list_ptr(const object& v);
static inline const list<object>* obj_to_set_ptr(const object& v);
template <class T> static inline object make_object(const T& v);
template <class T, class... Args> static inline object object_new(Args&&... args);

#include "str.h"
#include "path.h"
#include "list.h"
#include "dict.h"
#include "set.h"

// type_id は target 非依存で stable な型判定キーとして扱う。
// 予約領域（0-999）は runtime 組み込み型に割り当てる。
static constexpr uint32 PYTRA_TID_NONE = 0;
static constexpr uint32 PYTRA_TID_BOOL = 1;
static constexpr uint32 PYTRA_TID_INT = 2;
static constexpr uint32 PYTRA_TID_FLOAT = 3;
static constexpr uint32 PYTRA_TID_STR = 4;
static constexpr uint32 PYTRA_TID_LIST = 5;
static constexpr uint32 PYTRA_TID_DICT = 6;
static constexpr uint32 PYTRA_TID_SET = 7;
static constexpr uint32 PYTRA_TID_OBJECT = 8;
static constexpr uint32 PYTRA_TID_USER_BASE = 1000;

inline list<str> str::split(const str& sep, int64 maxsplit) const {
    list<str> out = list<str>{};
    const ::std::string& s = data_;
    const ::std::string& token = sep.std();
    if (token.empty()) {
        out.append(*this);
        return out;
    }
    ::std::size_t pos = 0;
    int64 splits = 0;
    const bool unlimited = maxsplit < 0;
    while (true) {
        if (!unlimited && splits >= maxsplit) {
            out.append(str(s.substr(pos)));
            break;
        }
        ::std::size_t at = s.find(token, pos);
        if (at == ::std::string::npos) {
            out.append(str(s.substr(pos)));
            break;
        }
        out.append(str(s.substr(pos, at - pos)));
        pos = at + token.size();
        splits += 1;
    }
    return out;
}

inline list<str> str::split(const str& sep) const {
    return split(sep, -1);
}

inline list<str> str::splitlines() const {
    list<str> out = list<str>{};
    ::std::size_t i = 0;
    const ::std::size_t n = data_.size();
    while (i < n) {
        ::std::size_t j = i;
        while (j < n && data_[j] != '\n' && data_[j] != '\r') j += 1;
        out.append(str(data_.substr(i, j - i)));
        if (j < n && data_[j] == '\r' && j + 1 < n && data_[j + 1] == '\n') {
            j += 2;
        } else if (j < n) {
            j += 1;
        }
        i = j;
    }
    if (n > 0) {
        char last = data_[n - 1];
        if (last == '\n' || last == '\r') out.append(str(""));
    }
    return out;
}

inline int64 str::count(const str& needle) const {
    if (needle.empty()) {
        return static_cast<int64>(data_.size() + 1);
    }
    int64 out = 0;
    ::std::size_t pos = 0;
    const ::std::string nn = needle.std();
    while (true) {
        ::std::size_t at = data_.find(nn, pos);
        if (at == ::std::string::npos) break;
        out += 1;
        pos = at + nn.size();
    }
    return out;
}

inline str str::join(const list<str>& parts) const {
    if (parts.empty()) return str("");
    ::std::string out;
    ::std::size_t i = 0;
    while (i < parts.size()) {
        if (i > 0) out += data_;
        out += parts[i].std();
        i += 1;
    }
    return str(out);
}

// Python の動的 object を C++ 側で保持するための最小ラッパクラス群。
// 各 Py*Obj は値を保持するだけで、振る舞いは下のヘルパ関数側で提供する。
class PyIntObj : public PyObj {
public:
    explicit PyIntObj(int64 v) : PyObj(PYTRA_TID_INT), value(v) {}
    int64 value;

    bool py_truthy() const override {
        return value != 0;
    }

    ::std::string py_str() const override {
        return ::std::to_string(value);
    }
};

class PyFloatObj : public PyObj {
public:
    explicit PyFloatObj(float64 v) : PyObj(PYTRA_TID_FLOAT), value(v) {}
    float64 value;

    bool py_truthy() const override {
        return value != 0.0;
    }

    ::std::string py_str() const override {
        return ::std::to_string(value);
    }
};

class PyBoolObj : public PyObj {
public:
    explicit PyBoolObj(bool v) : PyObj(PYTRA_TID_BOOL), value(v) {}
    bool value;

    bool py_truthy() const override {
        return value;
    }

    ::std::string py_str() const override {
        return value ? "True" : "False";
    }
};

class PyStrObj : public PyObj {
public:
    explicit PyStrObj(str v) : PyObj(PYTRA_TID_STR), value(::std::move(v)) {}
    str value;

    bool py_truthy() const override {
        return !value.empty();
    }

    ::std::optional<int64> py_try_len() const override {
        return static_cast<int64>(value.size());
    }

    ::std::string py_str() const override {
        return value.std();
    }

    object py_iter_or_raise() const override;
};

class PyListObj : public PyObj {
public:
    explicit PyListObj(list<object> v) : PyObj(PYTRA_TID_LIST), value(::std::move(v)) {}
    list<object> value;

    bool py_truthy() const override {
        return !value.empty();
    }

    ::std::optional<int64> py_try_len() const override {
        return static_cast<int64>(value.size());
    }

    ::std::string py_str() const override {
        return "<list>";
    }

    object py_iter_or_raise() const override;
};

class PyDictObj : public PyObj {
public:
    explicit PyDictObj(dict<str, object> v) : PyObj(PYTRA_TID_DICT), value(::std::move(v)) {}
    dict<str, object> value;

    bool py_truthy() const override {
        return !value.empty();
    }

    ::std::optional<int64> py_try_len() const override {
        return static_cast<int64>(value.size());
    }

    ::std::string py_str() const override {
        return "<dict>";
    }

    object py_iter_or_raise() const override;
};

class PySetObj : public PyObj {
public:
    explicit PySetObj(list<object> v) : PyObj(PYTRA_TID_SET), value(::std::move(v)) {}
    list<object> value;

    bool py_truthy() const override {
        return !value.empty();
    }

    ::std::optional<int64> py_try_len() const override {
        return static_cast<int64>(value.size());
    }

    ::std::string py_str() const override {
        return "<set>";
    }

    object py_iter_or_raise() const override;
};

class PyListIterObj : public PyObj {
public:
    explicit PyListIterObj(object owner_list)
        : PyObj(PYTRA_TID_OBJECT), owner_list_(::std::move(owner_list)), use_owner_(true), index_(0) {}

    explicit PyListIterObj(list<object> values)
        : PyObj(PYTRA_TID_OBJECT), values_(::std::move(values)), use_owner_(false), index_(0) {}

    object py_iter_or_raise() const override {
        return object(static_cast<PyObj*>(const_cast<PyListIterObj*>(this)));
    }

    ::std::optional<object> py_next_or_stop() override {
        const list<object>* values_ptr = nullptr;
        if (use_owner_) {
            const auto* owner = dynamic_cast<const PyListObj*>(owner_list_.get());
            if (owner == nullptr) return ::std::nullopt;
            values_ptr = &(owner->value);
        } else {
            values_ptr = &values_;
        }
        if (values_ptr == nullptr || index_ >= static_cast<int64>(values_ptr->size())) return ::std::nullopt;
        object out = (*values_ptr)[static_cast<::std::size_t>(index_)];
        index_ += 1;
        return out;
    }

private:
    object owner_list_;
    list<object> values_;
    bool use_owner_;
    int64 index_;
};

class PyDictKeyIterObj : public PyObj {
public:
    explicit PyDictKeyIterObj(list<object> keys)
        : PyObj(PYTRA_TID_OBJECT), keys_(::std::move(keys)), index_(0) {}

    object py_iter_or_raise() const override {
        return object(static_cast<PyObj*>(const_cast<PyDictKeyIterObj*>(this)));
    }

    ::std::optional<object> py_next_or_stop() override {
        if (index_ >= static_cast<int64>(keys_.size())) return ::std::nullopt;
        object out = keys_[static_cast<::std::size_t>(index_)];
        index_ += 1;
        return out;
    }

private:
    list<object> keys_;
    int64 index_;
};

class PyStrIterObj : public PyObj {
public:
    explicit PyStrIterObj(str value)
        : PyObj(PYTRA_TID_OBJECT), value_(::std::move(value)), index_(0) {}

    object py_iter_or_raise() const override {
        return object(static_cast<PyObj*>(const_cast<PyStrIterObj*>(this)));
    }

    ::std::optional<object> py_next_or_stop() override {
        if (index_ >= static_cast<int64>(value_.size())) return ::std::nullopt;
        str ch = value_[index_];
        index_ += 1;
        return make_object(ch);
    }

private:
    str value_;
    int64 index_;
};

inline object PyStrObj::py_iter_or_raise() const {
    return object_new<PyStrIterObj>(value);
}

inline object PyListObj::py_iter_or_raise() const {
    return object_new<PyListIterObj>(object(static_cast<PyObj*>(const_cast<PyListObj*>(this))));
}

inline object PyDictObj::py_iter_or_raise() const {
    list<object> keys{};
    keys.reserve(value.size());
    for (const auto& kv : value) {
        keys.append(make_object(kv.first));
    }
    return object_new<PyDictKeyIterObj>(::std::move(keys));
}

inline object PySetObj::py_iter_or_raise() const {
    return object_new<PyListIterObj>(value);
}

template <class T>
static inline T* py_obj_cast(const object& obj) {
    if (!obj) return nullptr;
    return dynamic_cast<T*>(obj.get());
}

template <class T>
static inline rc<T> obj_to_rc(const object& v) {
    static_assert(::std::is_base_of_v<PyObj, T>, "obj_to_rc<T>: T must derive from PyObj");
    if (!v) return rc<T>();
    if (auto* p = dynamic_cast<T*>(v.get())) return rc<T>(p);
    return rc<T>();
}

template <class T>
static inline rc<T> obj_to_rc_or_raise(const object& v, const char* ctx = "obj_to_rc_or_raise") {
    rc<T> out = obj_to_rc<T>(v);
    if (out) return out;
    const char* label = ctx != nullptr ? ctx : "obj_to_rc_or_raise";
    throw ::std::runtime_error(::std::string(label) + ": type mismatch");
}

template <class T, class... Args>
static inline object object_new(Args&&... args) {
    return object::adopt(static_cast<PyObj*>(pytra::gc::rc_new<T>(::std::forward<Args>(args)...)));
}

// C++ 値 -> Python object への昇格ヘルパ。
template <class T, ::std::enable_if_t<::std::is_base_of_v<PyObj, T>, int> = 0>
static inline object make_object(const rc<T>& v) {
    if (!v) return object();
    return object(static_cast<PyObj*>(v.get()));
}

static inline object make_object(const object& v) { return v; }
static inline object make_object(::std::nullptr_t) { return object(); }
static inline object make_object(const str& v) { return object_new<PyStrObj>(v); }
static inline object make_object(const ::std::string& v) { return object_new<PyStrObj>(str(v)); }
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

static inline object make_object(const ::std::any& v) {
    if (!v.has_value()) return object();
    if (const auto* p = ::std::any_cast<object>(&v)) return *p;
    if (const auto* p = ::std::any_cast<str>(&v)) return make_object(*p);
    if (const auto* p = ::std::any_cast<::std::string>(&v)) return make_object(*p);
    if (const auto* p = ::std::any_cast<const char*>(&v)) return make_object(*p);
    if (const auto* p = ::std::any_cast<bool>(&v)) return make_object(*p);
    if (const auto* p = ::std::any_cast<float64>(&v)) return make_object(*p);
    if (const auto* p = ::std::any_cast<float32>(&v)) return make_object(*p);
    if (const auto* p = ::std::any_cast<int64>(&v)) return make_object(*p);
    if (const auto* p = ::std::any_cast<uint64>(&v)) return make_object(*p);
    if (const auto* p = ::std::any_cast<int32>(&v)) return make_object(*p);
    if (const auto* p = ::std::any_cast<uint32>(&v)) return make_object(*p);
    if (const auto* p = ::std::any_cast<int16>(&v)) return make_object(*p);
    if (const auto* p = ::std::any_cast<uint16>(&v)) return make_object(*p);
    if (const auto* p = ::std::any_cast<int8>(&v)) return make_object(*p);
    if (const auto* p = ::std::any_cast<uint8>(&v)) return make_object(*p);
    if (const auto* p = ::std::any_cast<list<::std::any>>(&v)) {
        list<object> out{};
        out.reserve(p->size());
        for (const auto& e : *p) out.append(make_object(e));
        return object_new<PyListObj>(out);
    }
    if (const auto* p = ::std::any_cast<dict<str, ::std::any>>(&v)) {
        dict<str, object> out{};
        for (const auto& kv : *p) out[kv.first] = make_object(kv.second);
        return object_new<PyDictObj>(out);
    }
    if (const auto* p = ::std::any_cast<set<str>>(&v)) {
        list<object> out{};
        out.reserve(p->size());
        for (const auto& e : *p) out.append(make_object(e));
        return object_new<PySetObj>(out);
    }
    return object();
}

template <class T>
static inline object make_object(const list<T>& values) {
    list<object> out;
    out.reserve(values.size());
    for (const auto& v : values) out.append(make_object(v));
    return object_new<PyListObj>(::std::move(out));
}

static inline object make_object(const list<object>& values) {
    return object_new<PyListObj>(values);
}

static inline object make_object(list<object>&& values) {
    return object_new<PyListObj>(::std::move(values));
}

template <class V>
static inline object make_object(const dict<str, V>& values) {
    dict<str, object> out;
    for (const auto& kv : values) out[kv.first] = make_object(kv.second);
    return object_new<PyDictObj>(::std::move(out));
}

template <class T>
static inline object make_object(const set<T>& values) {
    list<object> out;
    out.reserve(values.size());
    for (const auto& v : values) out.append(make_object(v));
    return object_new<PySetObj>(::std::move(out));
}

template <class... Ts>
static inline object make_object(const ::std::tuple<Ts...>& values) {
    list<object> out{};
    out.reserve(sizeof...(Ts));
    ::std::apply(
        [&](const auto&... elems) {
            (out.append(make_object(elems)), ...);
        },
        values);
    return object_new<PyListObj>(::std::move(out));
}

template <class T>
struct _py_is_optional : ::std::false_type {};

template <class U>
struct _py_is_optional<::std::optional<U>> : ::std::true_type {};

template <class T>
static inline object make_object(const T& v) {
    if constexpr (::std::is_same_v<T, object>) {
        return v;
    } else if constexpr (::std::is_same_v<T, ::std::nullopt_t>) {
        return object();
    } else if constexpr (_py_is_optional<T>::value) {
        if (!v.has_value()) return object();
        return make_object(v.value());
    } else if constexpr (::std::is_integral_v<T> && !::std::is_same_v<T, bool>) {
        return object_new<PyIntObj>(static_cast<int64>(v));
    } else if constexpr (::std::is_floating_point_v<T>) {
        return object_new<PyFloatObj>(static_cast<float64>(v));
    } else if constexpr (::std::is_same_v<T, bool>) {
        return object_new<PyBoolObj>(v);
    } else if constexpr (::std::is_convertible_v<T, str>) {
        return object_new<PyStrObj>(str(v));
    } else {
        return object();
    }
}

// Python object -> C++ 値の基本変換。
static inline bool obj_try_to_int64(const object& v, int64& out) {
    if (!v) return false;
    if (const auto* p = py_obj_cast<PyIntObj>(v)) {
        out = p->value;
        return true;
    }
    if (const auto* p = py_obj_cast<PyBoolObj>(v)) {
        out = p->value ? 1 : 0;
        return true;
    }
    if (const auto* p = py_obj_cast<PyFloatObj>(v)) {
        out = static_cast<int64>(p->value);
        return true;
    }
    if (const auto* p = py_obj_cast<PyStrObj>(v)) {
        try {
            const ::std::string txt = p->value.std();
            ::std::size_t idx = 0;
            const int64 parsed = static_cast<int64>(::std::stoll(txt, &idx));
            if (idx == txt.size()) {
                out = parsed;
                return true;
            }
        } catch (...) {
            return false;
        }
    }
    return false;
}

static inline bool obj_try_to_float64(const object& v, float64& out) {
    if (!v) return false;
    if (const auto* p = py_obj_cast<PyFloatObj>(v)) {
        out = p->value;
        return true;
    }
    if (const auto* p = py_obj_cast<PyIntObj>(v)) {
        out = static_cast<float64>(p->value);
        return true;
    }
    if (const auto* p = py_obj_cast<PyBoolObj>(v)) {
        out = p->value ? 1.0 : 0.0;
        return true;
    }
    if (const auto* p = py_obj_cast<PyStrObj>(v)) {
        try {
            const ::std::string txt = p->value.std();
            ::std::size_t idx = 0;
            const float64 parsed = ::std::stod(txt, &idx);
            if (idx == txt.size()) {
                out = parsed;
                return true;
            }
        } catch (...) {
            return false;
        }
    }
    return false;
}

static inline int64 obj_to_int64(const object& v) {
    int64 out = 0;
    if (obj_try_to_int64(v, out)) return out;
    return 0;
}

static inline float64 obj_to_float64(const object& v) {
    float64 out = 0.0;
    if (obj_try_to_float64(v, out)) return out;
    return 0.0;
}

static inline int64 obj_to_int64_or_raise(const object& v, const char* ctx = "obj_to_int64_or_raise") {
    int64 out = 0;
    if (obj_try_to_int64(v, out)) return out;
    const char* label = ctx != nullptr ? ctx : "obj_to_int64_or_raise";
    throw ::std::runtime_error(::std::string(label) + ": cannot convert object to int64");
}

static inline float64 obj_to_float64_or_raise(const object& v, const char* ctx = "obj_to_float64_or_raise") {
    float64 out = 0.0;
    if (obj_try_to_float64(v, out)) return out;
    const char* label = ctx != nullptr ? ctx : "obj_to_float64_or_raise";
    throw ::std::runtime_error(::std::string(label) + ": cannot convert object to float64");
}

static inline bool obj_to_bool(const object& v) {
    if (!v) return false;
    return v->py_truthy();
}

static inline str obj_to_str(const object& v) {
    if (!v) return "None";
    return str(v->py_str());
}

static inline str obj_to_str_or_raise(const object& v, const char* ctx = "obj_to_str_or_raise") {
    if (!v) {
        const char* label = ctx != nullptr ? ctx : "obj_to_str_or_raise";
        throw ::std::runtime_error(::std::string(label) + ": cannot convert null object to str");
    }
    return obj_to_str(v);
}

static inline const dict<str, object>* obj_to_dict_ptr(const object& v) {
    if (const auto* p = py_obj_cast<PyDictObj>(v)) return &(p->value);
    return nullptr;
}

static inline const list<object>* obj_to_list_ptr(const object& v) {
    const auto p = obj_to_rc<PyListObj>(v);
    if (p) return &(p->value);
    return nullptr;
}

static inline rc<PyListObj> obj_to_list_obj(const object& v) {
    return obj_to_rc<PyListObj>(v);
}

static inline const list<object>* obj_to_set_ptr(const object& v) {
    if (const auto* p = py_obj_cast<PySetObj>(v)) return &(p->value);
    return nullptr;
}

static inline dict<str, object> obj_to_dict(const object& v) {
    if (const auto* p = obj_to_dict_ptr(v)) return *p;
    return {};
}

static inline int64 py_len(const object& v) {
    if (!v) return 0;
    const auto len = v->py_try_len();
    if (len.has_value()) return *len;
    return 0;
}

// Python 組み込み相当の基本ユーティリティ（len / 文字列化）。
template <class T>
static inline int64 py_len(const T& v) {
    return static_cast<int64>(v.size());
}

template <class T>
static inline int64 py_len(const ::std::optional<T>& v) {
    if (!v.has_value()) return 0;
    return py_len(*v);
}

template <::std::size_t N>
static inline int64 py_len(const char (&)[N]) {
    return N > 0 ? static_cast<int64>(N - 1) : 0;
}

static inline int64 py_len(const ::std::any& v) {
    if (const auto* p = ::std::any_cast<str>(&v)) return static_cast<int64>(p->size());
    if (const auto* p = ::std::any_cast<::std::string>(&v)) return static_cast<int64>(p->size());
    if (const auto* p = ::std::any_cast<list<::std::any>>(&v)) return static_cast<int64>(p->size());
    if (const auto* p = ::std::any_cast<list<object>>(&v)) return static_cast<int64>(p->size());
    if (const auto* p = ::std::any_cast<dict<str, ::std::any>>(&v)) return static_cast<int64>(p->size());
    if (const auto* p = ::std::any_cast<dict<str, object>>(&v)) return static_cast<int64>(p->size());
    if (const auto* p = ::std::any_cast<object>(&v)) {
        if (const auto* d = obj_to_dict_ptr(*p)) return static_cast<int64>(d->size());
        if (const auto* lst = obj_to_list_ptr(*p)) return static_cast<int64>(lst->size());
        if (const auto* st = obj_to_set_ptr(*p)) return static_cast<int64>(st->size());
        return 0;
    }
    return 0;
}

// selfhost 段階で一時的に残る `len(x)` を受ける互換エイリアス。
template <class T>
static inline int64 len(const T& v) {
    return py_len(v);
}

static inline ::std::string py_to_string(const object& v);

template <class T>
static inline ::std::string py_to_string(const T& v) {
    ::std::ostringstream oss;
    oss << v;
    return oss.str();
}

static inline ::std::string py_to_string(const ::std::string& v) {
    return v;
}

static inline ::std::string py_to_string(const ::std::exception& v) {
    return ::std::string(v.what());
}

static inline ::std::string py_to_string(uint8 v) {
    return ::std::to_string(static_cast<int>(v));
}

static inline ::std::string py_to_string(int8 v) {
    return ::std::to_string(static_cast<int>(v));
}

static inline ::std::string py_to_string(const char* v) {
    return ::std::string(v);
}

template <class T>
static inline ::std::string py_to_string(const ::std::optional<T>& v) {
    if (!v.has_value()) return "None";
    return py_to_string(*v);
}

static inline ::std::string py_to_string(const ::std::any& v) {
    if (const auto* p = ::std::any_cast<object>(&v)) return py_to_string(*p);
    if (const auto* p = ::std::any_cast<str>(&v)) return *p;
    if (const auto* p = ::std::any_cast<int64>(&v)) return ::std::to_string(*p);
    if (const auto* p = ::std::any_cast<uint64>(&v)) return ::std::to_string(*p);
    if (const auto* p = ::std::any_cast<int>(&v)) return ::std::to_string(*p);
    if (const auto* p = ::std::any_cast<float64>(&v)) return ::std::to_string(*p);
    if (const auto* p = ::std::any_cast<float32>(&v)) return ::std::to_string(*p);
    if (const auto* p = ::std::any_cast<bool>(&v)) return *p ? "True" : "False";
    return "<any>";
}

static inline ::std::string py_to_string(const Path& v) {
    return v.string();
}

static inline ::std::string py_to_string(const object& v) {
    return obj_to_str(v);
}

// `re.sub` の最小互換実装で使用する空白判定と置換ヘルパ。
static inline bool _py_is_ws(char ch) {
    return ch == ' ' || ch == '\t' || ch == '\n' || ch == '\r' || ch == '\f' || ch == '\v';
}

static inline str sub(const str& pattern, const str& repl, const str& text) {
    const ::std::string pat = py_to_string(pattern);
    const ::std::string rep = py_to_string(repl);
    const ::std::string src = py_to_string(text);
    if (pat == "\\s+") {
        ::std::string out;
        out.reserve(src.size());
        bool in_ws = false;
        for (char ch : src) {
            if (_py_is_ws(ch)) {
                if (!in_ws) out += rep;
                in_ws = true;
            } else {
                out.push_back(ch);
                in_ws = false;
            }
        }
        return str(out);
    }
    try {
        return str(::std::regex_replace(src, ::std::regex(pat), rep));
    } catch (...) {
        return text;
    }
}

struct ArgumentParser {
    struct _OptSpec {
        list<str> names;
        str dest;
        bool takes_value;
        bool store_true;
        list<str> choices;
        bool has_default;
        object default_value;
    };

    str _description;
    list<str> _positionals;
    list<_OptSpec> _options;

    explicit ArgumentParser(const str& description = "") : _description(description), _positionals{}, _options{} {}

    void add_argument(const str& a0) {
        const ::std::string n0 = py_to_string(a0);
        if (!n0.empty() && n0[0] == '-') {
            _OptSpec sp{};
            sp.names = list<str>{a0};
            sp.dest = (n0.size() > 2 && n0[0] == '-' && n0[1] == '-') ? str(n0.substr(2)) : a0;
            sp.takes_value = false;
            sp.store_true = false;
            sp.choices = list<str>{};
            sp.has_default = false;
            sp.default_value = object{};
            _options.append(sp);
            return;
        }
        _positionals.append(a0);
    }

    void add_argument(const str& a0, const str& a1) {
        const ::std::string n0 = py_to_string(a0);
        const ::std::string n1 = py_to_string(a1);
        if ((!n0.empty() && n0[0] == '-') && n1 == "store_true") {
            _OptSpec sp{};
            sp.names = list<str>{a0};
            if (n0.size() > 2 && n0[0] == '-' && n0[1] == '-') sp.dest = str(n0.substr(2));
            else sp.dest = a0;
            sp.takes_value = false;
            sp.store_true = true;
            sp.choices = list<str>{};
            sp.has_default = false;
            sp.default_value = object{};
            _options.append(sp);
            return;
        }
        if ((!n0.empty() && n0[0] == '-') || (!n1.empty() && n1[0] == '-')) {
            _OptSpec sp{};
            sp.names = list<str>{a0, a1};
            if (!n1.empty() && n1.size() > 2 && n1[0] == '-' && n1[1] == '-') sp.dest = str(n1.substr(2));
            else if (!n0.empty() && n0.size() > 2 && n0[0] == '-' && n0[1] == '-') sp.dest = str(n0.substr(2));
            else sp.dest = a1;
            sp.takes_value = true;
            sp.store_true = false;
            sp.choices = list<str>{};
            sp.has_default = false;
            sp.default_value = object{};
            _options.append(sp);
            return;
        }
        _positionals.append(a0);
        _positionals.append(a1);
    }

    void add_argument(const str& a0, const str& a1, const list<str>& choices, const str& default_value) {
        const ::std::string n0 = py_to_string(a0);
        const ::std::string n1 = py_to_string(a1);
        _OptSpec sp{};
        sp.names = list<str>{a0, a1};
        if (!n1.empty() && n1.size() > 2 && n1[0] == '-' && n1[1] == '-') sp.dest = str(n1.substr(2));
        else if (!n0.empty() && n0.size() > 2 && n0[0] == '-' && n0[1] == '-') sp.dest = str(n0.substr(2));
        else sp.dest = a1;
        sp.takes_value = true;
        sp.store_true = false;
        sp.choices = choices;
        sp.has_default = true;
        sp.default_value = make_object(default_value);
        _options.append(sp);
    }

    dict<str, object> parse_args(const list<str>& argv) const {
        dict<str, object> out{};
        for (const _OptSpec& sp : _options) {
            if (sp.has_default) out[sp.dest] = sp.default_value;
            else if (sp.takes_value) out[sp.dest] = object{};
            else out[sp.dest] = make_object(false);
        }
        int64 pos_i = 0;
        int64 i = 0;
        while (i < py_len(argv)) {
            const str tok = argv[i];
            const ::std::string tok_s = py_to_string(tok);
            if (!tok_s.empty() && tok_s[0] == '-') {
                const _OptSpec* hit = nullptr;
                for (const _OptSpec& sp : _options) {
                    for (const str& name : sp.names) {
                        if (name == tok) {
                            hit = &sp;
                            break;
                        }
                    }
                    if (hit != nullptr) break;
                }
                if (hit == nullptr) throw ::std::runtime_error("argparse: unknown option");
                if (hit->takes_value) {
                    if (i + 1 >= py_len(argv)) throw ::std::runtime_error("argparse: missing option value");
                    const str val = argv[i + 1];
                    if (py_len(hit->choices) > 0) {
                        bool ok = false;
                        for (const str& choice : hit->choices) {
                            if (choice == val) {
                                ok = true;
                                break;
                            }
                        }
                        if (!ok) throw ::std::runtime_error("argparse: invalid choice");
                    }
                    out[hit->dest] = make_object(val);
                    i += 2;
                } else {
                    out[hit->dest] = make_object(true);
                    i += 1;
                }
                continue;
            }
            if (pos_i < py_len(_positionals)) {
                out[_positionals[pos_i]] = make_object(tok);
                pos_i += 1;
            }
            i += 1;
        }
        return out;
    }
};

// `object` / `any` に入った値を型付きで取り出す補助キャスト群。
template <class D>
static inline ::std::optional<D> py_object_try_cast(const object& v) {
    if constexpr (::std::is_same_v<D, object>) {
        return v;
    } else if constexpr (::std::is_same_v<D, str>) {
        return obj_to_str(v);
    } else if constexpr (::std::is_same_v<D, bool>) {
        return obj_to_bool(v);
    } else if constexpr (::std::is_same_v<D, int64>) {
        return obj_to_int64(v);
    } else if constexpr (::std::is_same_v<D, float64>) {
        return obj_to_float64(v);
    } else if constexpr (::std::is_same_v<D, dict<str, object>>) {
        if (const auto* p = obj_to_dict_ptr(v)) return *p;
        return ::std::nullopt;
    } else if constexpr (::std::is_same_v<D, list<object>>) {
        if (const auto* p = obj_to_list_ptr(v)) return *p;
        return ::std::nullopt;
    } else {
        return ::std::nullopt;
    }
}

static inline ::std::string py_bool_to_string(bool v) {
    return v ? "True" : "False";
}

template <class T>
static inline T py_to(const object& v);

template <class T>
static inline T py_to(const ::std::any& v);

template <class T, ::std::enable_if_t<!::std::is_same_v<T, object> && !::std::is_same_v<T, ::std::any>, int> = 0>
static inline T py_to(const T& v);

static inline int64 py_to_int64(const str& v) {
    return static_cast<int64>(::std::stoll(v));
}

static inline int64 py_to_int64_base(const str& v, int64 base) {
    int b = static_cast<int>(base);
    if (b < 2 || b > 36) b = 10;
    return static_cast<int64>(::std::stoll(static_cast<::std::string>(v), nullptr, b));
}

static inline int64 py_to_int64_base(const ::std::string& v, int64 base) {
    return py_to_int64_base(str(v), base);
}

template <class T, ::std::enable_if_t<::std::is_arithmetic_v<T>, int> = 0>
static inline int64 py_to_int64(T v) {
    return py_to<int64>(v);
}

static inline int64 py_to_int64(const object& v) {
    return py_to<int64>(v);
}

static inline int64 py_to_int64_base(const object& v, int64 base) {
    return py_to_int64_base(obj_to_str(v), base);
}

static inline float64 py_to_float64(const object& v) {
    return py_to<float64>(v);
}

template <class T, ::std::enable_if_t<::std::is_arithmetic_v<T>, int> = 0>
static inline float64 py_to_float64(T v) {
    return py_to<float64>(v);
}

static inline bool py_to_bool(const object& v) {
    return py_to<bool>(v);
}

static inline bool py_to_bool(bool v) {
    return py_to<bool>(v);
}

static inline int64 py_to_int64(const ::std::any& v) {
    if (const auto* p = ::std::any_cast<int64>(&v)) return *p;
    if (const auto* p = ::std::any_cast<int>(&v)) return static_cast<int64>(*p);
    if (const auto* p = ::std::any_cast<uint8>(&v)) return static_cast<int64>(*p);
    if (const auto* p = ::std::any_cast<int8>(&v)) return static_cast<int64>(*p);
    if (const auto* p = ::std::any_cast<uint16>(&v)) return static_cast<int64>(*p);
    if (const auto* p = ::std::any_cast<int16>(&v)) return static_cast<int64>(*p);
    if (const auto* p = ::std::any_cast<uint32>(&v)) return static_cast<int64>(*p);
    if (const auto* p = ::std::any_cast<int32>(&v)) return static_cast<int64>(*p);
    if (const auto* p = ::std::any_cast<uint64>(&v)) return static_cast<int64>(*p);
    if (const auto* p = ::std::any_cast<float64>(&v)) return static_cast<int64>(*p);
    if (const auto* p = ::std::any_cast<float32>(&v)) return static_cast<int64>(*p);
    if (const auto* p = ::std::any_cast<bool>(&v)) return *p ? 1 : 0;
    if (const auto* p = ::std::any_cast<str>(&v)) {
        try {
            return static_cast<int64>(::std::stoll(*p));
        } catch (...) {
            return 0;
        }
    }
    return 0;
}

static inline int64 py_to_int64_base(const ::std::any& v, int64 base) {
    if (const auto* p = ::std::any_cast<str>(&v)) return py_to_int64_base(*p, base);
    if (const auto* p = ::std::any_cast<object>(&v)) return py_to_int64_base(*p, base);
    return py_to_int64(v);
}

static inline int64 py_ord(const str& ch) {
    const ::std::string& s = ch;
    if (s.empty()) return 0;
    const auto b0 = static_cast<unsigned char>(s[0]);
    if ((b0 & 0x80) == 0) return static_cast<int64>(b0);
    if ((b0 & 0xE0) == 0xC0 && s.size() >= 2) {
        const auto b1 = static_cast<unsigned char>(s[1]);
        return static_cast<int64>(((b0 & 0x1F) << 6) | (b1 & 0x3F));
    }
    if ((b0 & 0xF0) == 0xE0 && s.size() >= 3) {
        const auto b1 = static_cast<unsigned char>(s[1]);
        const auto b2 = static_cast<unsigned char>(s[2]);
        return static_cast<int64>(((b0 & 0x0F) << 12) | ((b1 & 0x3F) << 6) | (b2 & 0x3F));
    }
    if ((b0 & 0xF8) == 0xF0 && s.size() >= 4) {
        const auto b1 = static_cast<unsigned char>(s[1]);
        const auto b2 = static_cast<unsigned char>(s[2]);
        const auto b3 = static_cast<unsigned char>(s[3]);
        return static_cast<int64>(((b0 & 0x07) << 18) | ((b1 & 0x3F) << 12) | ((b2 & 0x3F) << 6) | (b3 & 0x3F));
    }
    return static_cast<int64>(b0);
}

static inline int64 py_ord(const object& v) {
    return py_ord(obj_to_str(v));
}

static inline int64 py_ord(const ::std::any& v) {
    if (const auto* p = ::std::any_cast<str>(&v)) return py_ord(*p);
    if (const auto* p = ::std::any_cast<object>(&v)) return py_ord(*p);
    return 0;
}

static inline str py_chr(int64 codepoint) {
    int64 cp = codepoint;
    if (cp < 0) cp = 0;
    if (cp > 0x10FFFF) cp = 0x10FFFF;
    ::std::string out;
    if (cp <= 0x7F) {
        out.push_back(static_cast<char>(cp));
    } else if (cp <= 0x7FF) {
        out.push_back(static_cast<char>(0xC0 | ((cp >> 6) & 0x1F)));
        out.push_back(static_cast<char>(0x80 | (cp & 0x3F)));
    } else if (cp <= 0xFFFF) {
        out.push_back(static_cast<char>(0xE0 | ((cp >> 12) & 0x0F)));
        out.push_back(static_cast<char>(0x80 | ((cp >> 6) & 0x3F)));
        out.push_back(static_cast<char>(0x80 | (cp & 0x3F)));
    } else {
        out.push_back(static_cast<char>(0xF0 | ((cp >> 18) & 0x07)));
        out.push_back(static_cast<char>(0x80 | ((cp >> 12) & 0x3F)));
        out.push_back(static_cast<char>(0x80 | ((cp >> 6) & 0x3F)));
        out.push_back(static_cast<char>(0x80 | (cp & 0x3F)));
    }
    return str(out);
}

static inline str py_chr(const object& v) {
    return py_chr(obj_to_int64(v));
}

static inline str py_chr(const ::std::any& v) {
    if (const auto* p = ::std::any_cast<int64>(&v)) return py_chr(*p);
    if (const auto* p = ::std::any_cast<int>(&v)) return py_chr(static_cast<int64>(*p));
    if (const auto* p = ::std::any_cast<object>(&v)) return py_chr(*p);
    return "";
}

static inline float64 py_to_float64(const ::std::any& v) {
    if (const auto* p = ::std::any_cast<float64>(&v)) return *p;
    if (const auto* p = ::std::any_cast<float32>(&v)) return static_cast<float64>(*p);
    if (const auto* p = ::std::any_cast<int64>(&v)) return static_cast<float64>(*p);
    if (const auto* p = ::std::any_cast<int>(&v)) return static_cast<float64>(*p);
    if (const auto* p = ::std::any_cast<uint64>(&v)) return static_cast<float64>(*p);
    if (const auto* p = ::std::any_cast<bool>(&v)) return *p ? 1.0 : 0.0;
    if (const auto* p = ::std::any_cast<str>(&v)) {
        try {
            return ::std::stod(*p);
        } catch (...) {
            return 0.0;
        }
    }
    if (const auto* p = ::std::any_cast<object>(&v)) return obj_to_float64(*p);
    return 0.0;
}

static inline bool py_to_bool(const ::std::any& v) {
    if (const auto* p = ::std::any_cast<bool>(&v)) return *p;
    if (const auto* p = ::std::any_cast<int64>(&v)) return *p != 0;
    if (const auto* p = ::std::any_cast<int32>(&v)) return *p != 0;
    if (const auto* p = ::std::any_cast<uint64>(&v)) return *p != 0;
    if (const auto* p = ::std::any_cast<uint32>(&v)) return *p != 0;
    if (const auto* p = ::std::any_cast<float64>(&v)) return *p != 0.0;
    if (const auto* p = ::std::any_cast<float32>(&v)) return *p != 0.0f;
    if (const auto* p = ::std::any_cast<str>(&v)) return !p->empty();
    if (const auto* p = ::std::any_cast<::std::string>(&v)) return !p->empty();
    if (const auto* p = ::std::any_cast<object>(&v)) return obj_to_bool(*p);
    return false;
}

template <class T, ::std::enable_if_t<!::std::is_same_v<T, object> && !::std::is_same_v<T, ::std::any>, int>>
static inline T py_to(const T& v) {
    return v;
}

template <class T>
static inline T py_to(const object& v) {
    if constexpr (::std::is_same_v<T, object>) {
        return v;
    } else if constexpr (::std::is_same_v<T, str>) {
        return obj_to_str(v);
    } else if constexpr (::std::is_same_v<T, bool>) {
        return obj_to_bool(v);
    } else if constexpr (::std::is_integral_v<T> && !::std::is_same_v<T, bool>) {
        return static_cast<T>(obj_to_int64(v));
    } else if constexpr (::std::is_floating_point_v<T>) {
        return static_cast<T>(obj_to_float64(v));
    } else {
        static_assert(!::std::is_same_v<T, T>, "py_to<T>(object): unsupported target type");
    }
}

template <class T>
static inline T py_to(const ::std::any& v) {
    if constexpr (::std::is_same_v<T, ::std::any>) {
        return v;
    } else if constexpr (::std::is_same_v<T, object>) {
        if (const auto* p = ::std::any_cast<object>(&v)) return *p;
        return make_object(v);
    } else if constexpr (::std::is_same_v<T, str>) {
        if (const auto* p = ::std::any_cast<str>(&v)) return *p;
        if (const auto* p = ::std::any_cast<::std::string>(&v)) return str(*p);
        if (const auto* p = ::std::any_cast<const char*>(&v)) return str(*p);
        if (const auto* p = ::std::any_cast<object>(&v)) return obj_to_str(*p);
        return str(py_to_string(v));
    } else if constexpr (::std::is_same_v<T, bool>) {
        return py_to_bool(v);
    } else if constexpr (::std::is_integral_v<T> && !::std::is_same_v<T, bool>) {
        return static_cast<T>(py_to_int64(v));
    } else if constexpr (::std::is_floating_point_v<T>) {
        return static_cast<T>(py_to_float64(v));
    } else {
        static_assert(!::std::is_same_v<T, T>, "py_to<T>(any): unsupported target type");
    }
}

// Python の print 互換（bool 表記や複数引数の空白区切りを吸収）。
template <class T>
static inline void py_print(const T& v) {
    ::std::cout << v << ::std::endl;
}

static inline void py_print(const ::std::any& v) {
    ::std::cout << py_to_string(v) << ::std::endl;
}

static inline void py_print(bool v) {
    ::std::cout << (v ? "True" : "False") << ::std::endl;
}

template <class T, class... Rest>
static inline void py_print(const T& first, const Rest&... rest) {
    ::std::cout << py_to_string(first);
    ((::std::cout << " " << py_to_string(rest)), ...);
    ::std::cout << ::std::endl;
}

// os.path / glob の最小互換ヘルパ。
static inline str py_os_path_join(const str& a, const str& b) {
    if (a.empty()) return b;
    if (b.empty()) return a;
    const char tail = a.std().back();
    if (tail == '/' || tail == '\\') return a + b;
    return a + "/" + b;
}

static inline str py_str_from_any_like(const ::std::any& v) {
    if (const auto* p = ::std::any_cast<str>(&v)) return *p;
    if (const auto* p = ::std::any_cast<const char*>(&v)) return str(*p);
    if (const auto* p = ::std::any_cast<::std::string>(&v)) return str(*p);
    if (const auto* p = ::std::any_cast<object>(&v)) return obj_to_str(*p);
    return str(py_to_string(v));
}

static inline str py_os_path_join(const ::std::any& a, const ::std::any& b) {
    return py_os_path_join(py_str_from_any_like(a), py_str_from_any_like(b));
}

static inline str py_os_path_join(const char* a, const char* b) {
    return py_os_path_join(str(a), str(b));
}

static inline str py_os_path_join(const object& a, const object& b) {
    return py_os_path_join(obj_to_str(a), obj_to_str(b));
}

static inline str py_os_path_basename(const str& p) {
    const ::std::string s = p.std();
    const ::std::size_t pos = s.find_last_of("/\\");
    if (pos == ::std::string::npos) return str(s);
    return str(s.substr(pos + 1));
}

static inline str py_os_path_basename(const ::std::any& p) {
    return py_os_path_basename(py_str_from_any_like(p));
}

static inline str py_os_path_basename(const object& p) {
    return py_os_path_basename(obj_to_str(p));
}

static inline str py_os_path_dirname(const str& p) {
    const ::std::string s = p.std();
    const ::std::size_t pos = s.find_last_of("/\\");
    if (pos == ::std::string::npos) return str("");
    return str(s.substr(0, pos));
}

static inline str py_os_path_dirname(const ::std::any& p) {
    return py_os_path_dirname(py_str_from_any_like(p));
}

static inline str py_os_path_dirname(const object& p) {
    return py_os_path_dirname(obj_to_str(p));
}

static inline ::std::tuple<str, str> py_os_path_splitext(const str& p) {
    const ::std::string s = p.std();
    const ::std::size_t sep = s.find_last_of("/\\");
    const ::std::size_t dot = s.find_last_of('.');
    if (dot == ::std::string::npos) return ::std::tuple<str, str>{str(s), str("")};
    if (sep != ::std::string::npos && dot < sep + 1) return ::std::tuple<str, str>{str(s), str("")};
    return ::std::tuple<str, str>{str(s.substr(0, dot)), str(s.substr(dot))};
}

static inline ::std::tuple<str, str> py_os_path_splitext(const ::std::any& p) {
    return py_os_path_splitext(py_str_from_any_like(p));
}

static inline ::std::tuple<str, str> py_os_path_splitext(const object& p) {
    return py_os_path_splitext(obj_to_str(p));
}

static inline str py_os_path_abspath(const str& p) {
    return str(::std::filesystem::absolute(::std::filesystem::path(p.std())).generic_string());
}

static inline str py_os_path_abspath(const ::std::any& p) {
    return py_os_path_abspath(py_str_from_any_like(p));
}

static inline str py_os_path_abspath(const object& p) {
    return py_os_path_abspath(obj_to_str(p));
}

static inline bool py_os_path_exists(const str& p) {
    return ::std::filesystem::exists(::std::filesystem::path(p.std()));
}

static inline bool py_os_path_exists(const ::std::any& p) {
    return py_os_path_exists(py_str_from_any_like(p));
}

static inline bool py_os_path_exists(const char* p) {
    return py_os_path_exists(str(p));
}

static inline bool py_os_path_exists(const object& p) {
    return py_os_path_exists(obj_to_str(p));
}

static inline str py_os_getcwd() {
    return str(::std::filesystem::current_path().generic_string());
}

static inline void py_os_mkdir(const str& p) {
    const ::std::filesystem::path target(p.std());
    ::std::error_code ec;
    const bool created = ::std::filesystem::create_directory(target, ec);
    if (!created && !::std::filesystem::exists(target, ec)) {
        throw ::std::runtime_error("mkdir failed: " + p.std());
    }
}

static inline void py_os_makedirs(const str& p, bool exist_ok = false) {
    const ::std::filesystem::path target(p.std());
    ::std::error_code ec;
    const bool created = ::std::filesystem::create_directories(target, ec);
    if (!created && !exist_ok && !::std::filesystem::exists(target, ec)) {
        throw ::std::runtime_error("makedirs failed: " + p.std());
    }
}

// minimal urllib shim (compile-compat). no network transfer is performed.
struct _PyUrllibRequestCompat {
    void urlretrieve(const str& _url, const str& _path) const {
        (void)_url;
        (void)_path;
    }
};

struct _PyUrllibCompat {
    _PyUrllibRequestCompat request{};
};

inline _PyUrllibCompat urllib{};

static inline bool py_glob_match_simple(const str& text, const str& pattern) {
    const ::std::string s = text.std();
    const ::std::string p = pattern.std();
    ::std::size_t si = 0;
    ::std::size_t pi = 0;
    ::std::size_t star = ::std::string::npos;
    ::std::size_t mark = 0;
    while (si < s.size()) {
        if (pi < p.size() && (p[pi] == '?' || p[pi] == s[si])) {
            ++si;
            ++pi;
            continue;
        }
        if (pi < p.size() && p[pi] == '*') {
            star = pi++;
            mark = si;
            continue;
        }
        if (star != ::std::string::npos) {
            pi = star + 1;
            si = ++mark;
            continue;
        }
        return false;
    }
    while (pi < p.size() && p[pi] == '*') ++pi;
    return pi == p.size();
}

static inline list<str> py_glob_glob(const str& pattern) {
    const ::std::string pat = pattern.std();
    const ::std::size_t sep = pat.find_last_of("/\\");
    const ::std::string dir = (sep == ::std::string::npos) ? "." : pat.substr(0, sep);
    const ::std::string mask = (sep == ::std::string::npos) ? pat : pat.substr(sep + 1);
    list<str> out{};
    ::std::error_code ec{};
    if (mask.find('*') == ::std::string::npos && mask.find('?') == ::std::string::npos) {
        const ::std::filesystem::path single = ::std::filesystem::path(pat);
        if (::std::filesystem::exists(single, ec)) out.append(str(single.generic_string()));
        return out;
    }
    for (const auto& ent : ::std::filesystem::directory_iterator(::std::filesystem::path(dir), ec)) {
        if (ec) break;
        const str name(ent.path().filename().generic_string());
        if (!py_glob_match_simple(name, str(mask))) continue;
        out.append(str(ent.path().generic_string()));
    }
    return out;
}

// list / str の添字・スライス互換ヘルパ。
template <class T>
static inline list<T> py_slice(const list<T>& v, int64 lo, int64 up) {
    const int64 n = static_cast<int64>(v.size());
    if (lo < 0) lo += n;
    if (up < 0) up += n;
    lo = ::std::max<int64>(0, ::std::min<int64>(lo, n));
    up = ::std::max<int64>(0, ::std::min<int64>(up, n));
    if (up < lo) up = lo;
    return list<T>(v.begin() + lo, v.begin() + up);
}

static inline str py_slice(const str& v, int64 lo, int64 up) {
    const int64 n = static_cast<int64>(v.size());
    if (lo < 0) lo += n;
    if (up < 0) up += n;
    lo = ::std::max<int64>(0, ::std::min<int64>(lo, n));
    up = ::std::max<int64>(0, ::std::min<int64>(up, n));
    if (up < lo) up = lo;
    return v.substr(static_cast<::std::size_t>(lo), static_cast<::std::size_t>(up - lo));
}

static inline str py_slice(const str& v, int64 lo, const ::std::any& up) {
    return py_slice(v, lo, py_to_int64(up));
}

template <class T>
static inline T& py_at(list<T>& v, int64 idx) {
    if (idx < 0) idx += static_cast<int64>(v.size());
    if (idx < 0 || idx >= static_cast<int64>(v.size())) {
        throw ::std::out_of_range("list index out of range");
    }
    return v[static_cast<::std::size_t>(idx)];
}

template <class T>
static inline const T& py_at(const list<T>& v, int64 idx) {
    if (idx < 0) idx += static_cast<int64>(v.size());
    if (idx < 0 || idx >= static_cast<int64>(v.size())) {
        throw ::std::out_of_range("list index out of range");
    }
    return v[static_cast<::std::size_t>(idx)];
}

static inline object py_at(const object& v, int64 idx) {
    if (const auto* lst = obj_to_list_ptr(v)) {
        return py_at(*lst, idx);
    }
    if (const auto* s = py_obj_cast<PyStrObj>(v)) {
        return make_object(s->value[idx]);
    }
    throw ::std::runtime_error("index access on non-indexable object");
}

static inline object py_slice(const object& v, int64 lo, int64 up) {
    if (const auto* lst = obj_to_list_ptr(v)) {
        return make_object(py_slice(*lst, lo, up));
    }
    if (const auto* s = py_obj_cast<PyStrObj>(v)) {
        return make_object(py_slice(s->value, lo, up));
    }
    throw ::std::runtime_error("slice access on non-sliceable object");
}

static inline object py_slice(const object& v, int64 lo, const object& up) {
    return py_slice(v, lo, py_to_int64(up));
}

static inline object py_slice(const object& v, int64 lo, const ::std::any& up) {
    return py_slice(v, lo, py_to_int64(up));
}

static inline void py_append(const object& v, const object& item) {
    auto p = obj_to_list_obj(v);
    if (p) {
        p->value.append(item);
        return;
    }
    throw ::std::runtime_error("append on non-list object");
}

static inline int64 py_index(const object& v, const object& item) {
    if (const auto* p = obj_to_list_ptr(v)) {
        const int64 n = static_cast<int64>(p->size());
        int64 i = 0;
        while (i < n) {
            if ((*p)[static_cast<::std::size_t>(i)] == item) {
                return i;
            }
            i += 1;
        }
        throw ::std::out_of_range("list.index(x): x not in list");
    }
    if (const auto* s = py_obj_cast<PyStrObj>(v)) {
        const int64 pos = s->value.find(obj_to_str(item));
        if (pos >= 0) {
            return pos;
        }
        throw ::std::out_of_range("str.index(x): substring not found");
    }
    throw ::std::runtime_error("index on non-indexable object");
}

template <class T>
static inline int64 py_index(const list<T>& v, const T& item) {
    return v.index(item);
}

template <class T>
static inline int64 py_index(const list<T>& v, const object& item) {
    if constexpr (::std::is_constructible_v<T, object>) {
        return v.index(T(item));
    }
    auto casted = py_object_try_cast<T>(item);
    if (casted.has_value()) {
        return v.index(*casted);
    }
    throw ::std::out_of_range("list.index(x): x not in list");
}

template <::std::size_t I = 0, class... Ts>
static inline object _py_tuple_at_impl(const ::std::tuple<Ts...>& tup, int64 idx) {
    constexpr int64 N = static_cast<int64>(sizeof...(Ts));
    if constexpr (I < sizeof...(Ts)) {
        int64 cur = static_cast<int64>(I);
        if (idx == cur || idx == (cur - N)) {
            return make_object(::std::get<I>(tup));
        }
        return _py_tuple_at_impl<I + 1>(tup, idx);
    }
    throw ::std::out_of_range("tuple index out of range");
}

template <class... Ts>
static inline object py_at(const ::std::tuple<Ts...>& tup, int64 idx) {
    return _py_tuple_at_impl(tup, idx);
}

template <class Seq>
static inline decltype(auto) py_at_bounds(Seq& v, int64 idx) {
    const int64 n = py_len(v);
    if (idx < 0 || idx >= n) throw ::std::out_of_range("index out of range");
    return v[static_cast<::std::size_t>(idx)];
}

template <class Seq>
static inline decltype(auto) py_at_bounds(const Seq& v, int64 idx) {
    const int64 n = py_len(v);
    if (idx < 0 || idx >= n) throw ::std::out_of_range("index out of range");
    return v[static_cast<::std::size_t>(idx)];
}

template <class Seq>
static inline decltype(auto) py_at_bounds_debug(Seq& v, int64 idx) {
#ifndef NDEBUG
    return py_at_bounds(v, idx);
#else
    return v[static_cast<::std::size_t>(idx)];
#endif
}

template <class Seq>
static inline decltype(auto) py_at_bounds_debug(const Seq& v, int64 idx) {
#ifndef NDEBUG
    return py_at_bounds(v, idx);
#else
    return v[static_cast<::std::size_t>(idx)];
#endif
}

// dict 取得ヘルパ群。`get` の既定値付きと例外送出版の両方を提供する。
template <class K, class V>
static inline const V& py_dict_get(const dict<K, V>& d, const K& key) {
    auto it = d.find(key);
    if (it == d.end()) {
        throw ::std::out_of_range("dict key not found");
    }
    return it->second;
}

template <class K, class V>
static inline V py_dict_get(const ::std::optional<dict<K, V>>& d, const K& key) {
    if (!d.has_value()) {
        throw ::std::out_of_range("dict key not found");
    }
    const dict<K, V>& dv = d.value();
    return py_dict_get(dv, key);
}

template <class V>
static inline const V& py_dict_get(const dict<str, V>& d, const char* key) {
    auto it = d.find(str(key));
    if (it == d.end()) {
        if (::std::string(key) == "lowered_kind") {
            static const V k_empty_value{};
            return k_empty_value;
        }
        str keys_txt = "";
        bool first = true;
        for (const auto& kv : d) {
            if (!first) keys_txt += ", ";
            keys_txt += kv.first;
            first = false;
        }
        throw ::std::out_of_range(
            ::std::string("dict key not found: ")
            + key
            + " available_keys=["
            + keys_txt.c_str()
            + "] value_type="
            + typeid(V).name());
    }
    return it->second;
}

template <class V>
static inline const V& py_dict_get(const dict<str, V>& d, const str& key) {
    auto it = d.find(key);
    if (it == d.end()) {
        if (key == str("lowered_kind")) {
            static const V k_empty_value{};
            return k_empty_value;
        }
        str keys_txt = "";
        bool first = true;
        for (const auto& kv : d) {
            if (!first) keys_txt += ", ";
            keys_txt += kv.first;
            first = false;
        }
        throw ::std::out_of_range(
            ::std::string("dict key not found: ")
            + key.c_str()
            + " available_keys=["
            + keys_txt.c_str()
            + "] value_type="
            + typeid(V).name());
    }
    return it->second;
}

template <class V>
static inline const V& py_dict_get(const dict<str, V>& d, const ::std::string& key) {
    return py_dict_get(d, str(key));
}

template <class V>
static inline const V& py_dict_get(const dict<str, V>& d, const object& key) {
    return py_dict_get(d, str(key));
}

template <class V>
static inline V py_dict_get(const ::std::optional<dict<str, V>>& d, const char* key) {
    if (!d.has_value()) {
        throw ::std::out_of_range("dict key not found");
    }
    const dict<str, V>& dv = d.value();
    return py_dict_get(dv, key);
}

static inline object py_dict_get(const dict<str, object>& d, const char* key) {
    auto it = d.find(str(key));
    if (it == d.end()) {
        str kind = "";
        auto kind_it = d.find(str("kind"));
        if (kind_it != d.end()) {
            kind = obj_to_str(kind_it->second);
        }
        str keys_txt = "";
        bool first = true;
        for (const auto& kv : d) {
            if (!first) {
                keys_txt += ", ";
            }
            keys_txt += kv.first;
            first = false;
        }
        auto caller_addr0 = reinterpret_cast<::std::uintptr_t>(__builtin_return_address(0));
        auto caller_addr1 = reinterpret_cast<::std::uintptr_t>(__builtin_return_address(1));
        auto caller_addr2 = reinterpret_cast<::std::uintptr_t>(__builtin_return_address(2));
        ::std::ostringstream caller_hex0;
        caller_hex0 << ::std::hex << caller_addr0;
        ::std::ostringstream caller_hex1;
        caller_hex1 << ::std::hex << caller_addr1;
        ::std::ostringstream caller_hex2;
        caller_hex2 << ::std::hex << caller_addr2;
        throw ::std::out_of_range(
            ::std::string("dict key not found: ")
            + key
            + " kind=" + py_to_string(kind)
            + " keys=[" + py_to_string(keys_txt) + "]"
            + " caller0=0x" + caller_hex0.str()
            + " caller1=0x" + caller_hex1.str()
            + " caller2=0x" + caller_hex2.str()
        );
    }
    return it->second;
}

static inline object py_dict_get(const dict<str, object>& d, const ::std::string& key) {
    return py_dict_get(d, key.c_str());
}

static inline object py_dict_get(const object& obj, const char* key) {
    if (const auto* p = obj_to_dict_ptr(obj)) {
        return py_dict_get(*p, key);
    }
    throw ::std::runtime_error("py_dict_get on non-dict object");
}

static inline ::std::any py_dict_get(const ::std::any& obj, const char* key) {
    if (const auto* p = ::std::any_cast<dict<str, ::std::any>>(&obj)) {
        auto it = p->find(str(key));
        if (it == p->end()) throw ::std::out_of_range("dict key not found");
        return it->second;
    }
    if (const auto* p = ::std::any_cast<dict<str, object>>(&obj)) {
        auto it = p->find(str(key));
        if (it == p->end()) throw ::std::out_of_range(::std::string("dict key not found: ") + key);
        return ::std::any(it->second);
    }
    if (const auto* p = ::std::any_cast<object>(&obj)) {
        if (const auto* d = obj_to_dict_ptr(*p)) {
            auto it = d->find(str(key));
            if (it == d->end()) throw ::std::out_of_range(::std::string("dict key not found: ") + key);
            return ::std::any(it->second);
        }
    }
    throw ::std::runtime_error("py_dict_get on non-dict any");
}

// `dict.get(key)`（default 省略）相当。未キー時は Python の `None` 相当（object{}）を返す。
template <class K, class V>
static inline object py_dict_get_maybe(const dict<K, V>& d, const K& key) {
    auto it = d.find(key);
    if (it == d.end()) {
        return object{};
    }
    return make_object(it->second);
}

template <class V>
static inline object py_dict_get_maybe(const dict<str, V>& d, const char* key) {
    return py_dict_get_maybe(d, str(key));
}

template <class V>
static inline object py_dict_get_maybe(const dict<str, V>& d, const str& key) {
    auto it = d.find(key);
    if (it == d.end()) {
        return object{};
    }
    return make_object(it->second);
}

template <class V>
static inline object py_dict_get_maybe(const dict<str, V>& d, const ::std::string& key) {
    return py_dict_get_maybe(d, str(key));
}

template <class K, class V>
static inline object py_dict_get_maybe(const ::std::optional<dict<K, V>>& d, const K& key) {
    if (!d.has_value()) {
        return object{};
    }
    return py_dict_get_maybe(*d, key);
}

template <class V>
static inline object py_dict_get_maybe(const ::std::optional<dict<str, V>>& d, const char* key) {
    if (!d.has_value()) {
        return object{};
    }
    return py_dict_get_maybe(*d, key);
}

template <class V>
static inline object py_dict_get_maybe(const ::std::optional<dict<str, V>>& d, const str& key) {
    if (!d.has_value()) {
        return object{};
    }
    return py_dict_get_maybe(*d, key);
}

static inline object py_dict_get_maybe(const object& obj, const char* key) {
    if (const auto* p = obj_to_dict_ptr(obj)) {
        return py_dict_get_maybe(*p, key);
    }
    return object{};
}

static inline object py_dict_get_maybe(const object& obj, const str& key) {
    if (const auto* p = obj_to_dict_ptr(obj)) {
        return py_dict_get_maybe(*p, key);
    }
    return object{};
}

static inline object py_dict_get_maybe(const ::std::any& obj, const char* key) {
    if (const auto* p = ::std::any_cast<dict<str, object>>(&obj)) {
        return py_dict_get_maybe(*p, key);
    }
    if (const auto* p = ::std::any_cast<dict<str, ::std::any>>(&obj)) {
        auto it = p->find(str(key));
        if (it == p->end()) return object{};
        return make_object(it->second);
    }
    return object{};
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
static inline V py_dict_get_default(const ::std::optional<dict<K, V>>& d, const K& key, const V& defval) {
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
static inline V py_dict_get_default(const dict<str, V>& d, const str& key, const V& defval) {
    return py_dict_get_default(d, key.c_str(), defval);
}

template <class V>
static inline V py_dict_get_default(const dict<str, V>& d, const ::std::string& key, const V& defval) {
    return py_dict_get_default(d, key.c_str(), defval);
}

template <class V>
static inline V py_dict_get_default(const ::std::optional<dict<str, V>>& d, const char* key, const V& defval) {
    if (!d.has_value()) {
        return defval;
    }
    return py_dict_get_default(*d, key, defval);
}

template <class K, class V, class D, ::std::enable_if_t<::std::is_convertible_v<D, V>, int> = 0>
static inline V py_dict_get_default(const dict<K, V>& d, const K& key, const D& defval) {
    auto it = d.find(key);
    if (it == d.end()) {
        return static_cast<V>(defval);
    }
    return it->second;
}

template <class K, class V, class D, ::std::enable_if_t<::std::is_convertible_v<D, V>, int> = 0>
static inline V py_dict_get_default(const ::std::optional<dict<K, V>>& d, const K& key, const D& defval) {
    if (!d.has_value()) {
        return static_cast<V>(defval);
    }
    return py_dict_get_default(*d, key, defval);
}

template <class V, class D, ::std::enable_if_t<::std::is_convertible_v<D, V>, int> = 0>
static inline V py_dict_get_default(const dict<str, V>& d, const char* key, const D& defval) {
    auto it = d.find(str(key));
    if (it == d.end()) {
        return static_cast<V>(defval);
    }
    return it->second;
}

template <class V, class D, ::std::enable_if_t<::std::is_convertible_v<D, V>, int> = 0>
static inline V py_dict_get_default(const dict<str, V>& d, const str& key, const D& defval) {
    return py_dict_get_default(d, key.c_str(), defval);
}

template <class V, class D, ::std::enable_if_t<::std::is_convertible_v<D, V>, int> = 0>
static inline V py_dict_get_default(const ::std::optional<dict<str, V>>& d, const char* key, const D& defval) {
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

static inline object py_dict_get_default(const dict<str, object>& d, const str& key, const object& defval) {
    return py_dict_get_default(d, key.c_str(), defval);
}

static inline object py_dict_get_default(const dict<str, object>& d, const str& key, const char* defval) {
    return py_dict_get_default(d, key.c_str(), defval);
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

static inline object py_dict_get_default(const dict<str, object>& d, const str& key, const str& defval) {
    return py_dict_get_default(d, key.c_str(), defval);
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

static inline object py_dict_get_default(const object& obj, const str& key, const object& defval) {
    return py_dict_get_default(obj, key.c_str(), defval);
}

static inline object py_dict_get_default(const object& obj, const str& key, const char* defval) {
    return py_dict_get_default(obj, key.c_str(), defval);
}

static inline object py_dict_get_default(const ::std::optional<dict<str, object>>& d, const char* key, const object& defval) {
    if (!d.has_value()) {
        return defval;
    }
    return py_dict_get_default(*d, key, defval);
}

static inline object py_dict_get_default(const ::std::optional<dict<str, object>>& d, const char* key, const char* defval) {
    if (!d.has_value()) {
        return make_object(str(defval));
    }
    return py_dict_get_default(*d, key, defval);
}

static inline object py_dict_get_default(const ::std::optional<dict<str, object>>& d, const char* key, const str& defval) {
    if (!d.has_value()) {
        return make_object(defval);
    }
    return py_dict_get_default(*d, key, defval);
}

static inline object py_dict_get_default(const ::std::optional<dict<str, object>>& d, const str& key, const object& defval) {
    return py_dict_get_default(d, key.c_str(), defval);
}

static inline object py_dict_get_default(const ::std::optional<dict<str, object>>& d, const str& key, const char* defval) {
    return py_dict_get_default(d, key.c_str(), defval);
}

static inline object py_dict_get_default(const ::std::optional<dict<str, object>>& d, const str& key, const str& defval) {
    return py_dict_get_default(d, key.c_str(), defval);
}

template <class D>
static inline D py_dict_get_default(const dict<str, object>& d, const char* key, const D& defval) {
    auto it = d.find(str(key));
    if (it == d.end()) {
        return defval;
    }
    if constexpr (::std::is_same_v<D, object>) {
        return it->second;
    } else if constexpr (::std::is_same_v<D, str>) {
        return py_to_string(it->second);
    } else {
        if (auto q = py_object_try_cast<D>(it->second)) return *q;
        return defval;
    }
}

template <class D>
static inline D py_dict_get_default(const dict<str, object>& d, const str& key, const D& defval) {
    return py_dict_get_default(d, key.c_str(), defval);
}

template <class D>
static inline D py_dict_get_default(const dict<str, object>& d, const ::std::string& key, const D& defval) {
    return py_dict_get_default(d, key.c_str(), defval);
}

template <class D>
static inline D py_dict_get_default(const dict<str, ::std::any>& d, const char* key, const D& defval) {
    auto it = d.find(str(key));
    if (it == d.end()) {
        return defval;
    }
    const D* p = ::std::any_cast<D>(&(it->second));
    if (p == nullptr) {
        return defval;
    }
    return *p;
}

template <class D>
static inline D py_dict_get_default(const dict<str, ::std::any>& d, const str& key, const D& defval) {
    return py_dict_get_default(d, key.c_str(), defval);
}

template <class D>
static inline D py_dict_get_default(const ::std::any& obj, const char* key, const D& defval) {
    if (const auto* p = ::std::any_cast<dict<str, ::std::any>>(&obj)) {
        return py_dict_get_default(*p, key, defval);
    }
    if (const auto* p = ::std::any_cast<dict<str, object>>(&obj)) {
        auto it = p->find(str(key));
        if (it == p->end()) return defval;
        if (auto q = py_object_try_cast<D>(it->second)) return *q;
        return defval;
    }
    if (const auto* p = ::std::any_cast<object>(&obj)) {
        if (const auto* d = obj_to_dict_ptr(*p)) {
            auto it = d->find(str(key));
            if (it == d->end()) return defval;
            if (auto q = py_object_try_cast<D>(it->second)) return *q;
        }
    }
    return defval;
}

template <class D>
static inline D py_dict_get_default(const ::std::any& obj, const str& key, const D& defval) {
    return py_dict_get_default(obj, key.c_str(), defval);
}

static inline str py_dict_get_default(const ::std::any& obj, const char* key, const char* defval) {
    if (const auto* p = ::std::any_cast<dict<str, ::std::any>>(&obj)) {
        auto it = p->find(str(key));
        if (it == p->end()) return str(defval);
        if (const auto* s = ::std::any_cast<str>(&(it->second))) return *s;
        return str(defval);
    }
    if (const auto* p = ::std::any_cast<dict<str, object>>(&obj)) {
        auto it = p->find(str(key));
        if (it == p->end()) return str(defval);
        return py_to_string(it->second);
    }
    if (const auto* p = ::std::any_cast<object>(&obj)) {
        if (const auto* d = obj_to_dict_ptr(*p)) {
            auto it = d->find(str(key));
            if (it == d->end()) return str(defval);
            return py_to_string(it->second);
        }
    }
    return str(defval);
}

static inline str py_dict_get_default(const ::std::any& obj, const str& key, const char* defval) {
    return py_dict_get_default(obj, key.c_str(), defval);
}

static inline str py_dict_get_default(const dict<str, ::std::any>& d, const char* key, const char* defval) {
    auto it = d.find(str(key));
    if (it == d.end()) return str(defval);
    if (const auto* s = ::std::any_cast<str>(&(it->second))) return *s;
    return str(defval);
}

static inline str py_dict_get_default(const dict<str, ::std::any>& d, const str& key, const char* defval) {
    return py_dict_get_default(d, key.c_str(), defval);
}

static inline bool dict_get_bool(const object& obj, const char* key, bool defval) {
    return py_to_bool(py_dict_get_default(obj, key, make_object(defval)));
}

static inline bool dict_get_bool(const ::std::optional<dict<str, object>>& d, const char* key, bool defval) {
    return py_to_bool(py_dict_get_default(d, key, make_object(defval)));
}

static inline str dict_get_str(const object& obj, const char* key, const str& defval) {
    return py_to_string(py_dict_get_default(obj, key, make_object(defval)));
}

static inline str dict_get_str(const ::std::optional<dict<str, object>>& d, const char* key, const str& defval) {
    return py_to_string(py_dict_get_default(d, key, make_object(defval)));
}

// object 系 dict.get で数値既定値を使うとき、object 経由の戻り値を
// 直接数値へ落として py_dict_get_default 直呼び出しを避ける。
static inline int64 dict_get_int(const object& obj, const char* key, int64 defval) {
    return py_to_int64(py_dict_get_default(obj, key, make_object(defval)));
}

static inline int64 dict_get_int(const ::std::optional<dict<str, object>>& d, const char* key, int64 defval) {
    return py_to_int64(py_dict_get_default(d, key, make_object(defval)));
}

static inline float64 dict_get_float(const object& obj, const char* key, float64 defval) {
    return py_to_float64(py_dict_get_default(obj, key, make_object(defval)));
}

static inline float64 dict_get_float(const ::std::optional<dict<str, object>>& d, const char* key, float64 defval) {
    return py_to_float64(py_dict_get_default(d, key, make_object(defval)));
}

static inline list<object> dict_get_list(
    const object& obj, const char* key, const list<object>& defval = list<object>{}) {
    object got = py_dict_get_default(obj, key, make_object(defval));
    if (const auto* p = obj_to_list_ptr(got)) return *p;
    return defval;
}

static inline list<object> dict_get_list(
    const ::std::optional<dict<str, object>>& d, const char* key, const list<object>& defval = list<object>{}) {
    object got = py_dict_get_default(d, key, make_object(defval));
    if (const auto* p = obj_to_list_ptr(got)) return *p;
    return defval;
}

static inline object dict_get_node(const object& obj, const char* key, const object& defval = object{}) {
    return py_dict_get_default(obj, key, defval);
}

static inline object dict_get_node(
    const ::std::optional<dict<str, object>>& d, const char* key, const object& defval = object{}) {
    return py_dict_get_default(d, key, defval);
}

template <class D>
static inline D dict_get_node(const dict<str, object>& d, const char* key, const D& defval) {
    return py_dict_get_default(d, key, defval);
}

template <class D>
static inline D dict_get_node(const dict<str, object>& d, const str& key, const D& defval) {
    return py_dict_get_default(d, key.c_str(), defval);
}

static inline str dict_get_node(const dict<str, str>& d, const str& key, const str& defval = "") {
    if (d.find(key) != d.end()) {
        return py_dict_get(d, key);
    }
    return defval;
}

static inline str dict_get_node(const dict<str, str>& d, const str& key, const char* defval) {
    if (d.find(key) != d.end()) {
        return py_dict_get(d, key);
    }
    return str(defval);
}

static inline str dict_get_node(const dict<str, str>& d, const char* key, const str& defval = "") {
    str k = str(key);
    if (d.find(k) != d.end()) {
        return py_dict_get(d, k);
    }
    return defval;
}

static inline str dict_get_node(const dict<str, str>& d, const char* key, const char* defval) {
    str k = str(key);
    if (d.find(k) != d.end()) {
        return py_dict_get(d, k);
    }
    return str(defval);
}

// Python の型判定（isinstance 的な分岐）で使う述語群。
template <class T>
static inline bool py_is_none(const ::std::optional<T>& v) {
    return !v.has_value();
}

template <class T>
static inline bool py_is_none(const T&) {
    return false;
}

static inline bool py_is_none(const object& v) {
    return !static_cast<bool>(v);
}

static inline bool py_is_none(const ::std::any& v) {
    if (!v.has_value()) return true;
    if (v.type() == typeid(::std::nullopt_t)) return true;
    return false;
}

template <class T>
static inline ::std::optional<T> py_any_to_optional(const ::std::any& v) {
    if (!v.has_value()) return ::std::nullopt;
    if (const auto* p = ::std::any_cast<T>(&v)) return *p;
    if (const auto* p = ::std::any_cast<::std::optional<T>>(&v)) return *p;
    return ::std::nullopt;
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
template <class T> static inline bool py_is_int(const T&) { return ::std::is_integral_v<T> && !::std::is_same_v<T, bool>; }
template <class T> static inline bool py_is_float(const T&) { return ::std::is_floating_point_v<T>; }
static inline bool py_is_bool(const bool&) { return true; }

static inline bool py_is_dict(const object& v) { return py_obj_cast<PyDictObj>(v) != nullptr; }
static inline bool py_is_list(const object& v) { return py_obj_cast<PyListObj>(v) != nullptr; }
static inline bool py_is_str(const object& v) { return py_obj_cast<PyStrObj>(v) != nullptr; }
static inline bool py_is_int(const object& v) { return py_obj_cast<PyIntObj>(v) != nullptr; }
static inline bool py_is_float(const object& v) { return py_obj_cast<PyFloatObj>(v) != nullptr; }
static inline bool py_is_bool(const object& v) { return py_obj_cast<PyBoolObj>(v) != nullptr; }

template <class T> static inline bool py_is_dict(const ::std::optional<T>& v) {
    if (!v.has_value()) return false;
    return py_is_dict(*v);
}
template <class T> static inline bool py_is_list(const ::std::optional<T>& v) {
    if (!v.has_value()) return false;
    return py_is_list(*v);
}
template <class T> static inline bool py_is_set(const ::std::optional<T>& v) {
    if (!v.has_value()) return false;
    return py_is_set(*v);
}
template <class T> static inline bool py_is_str(const ::std::optional<T>& v) {
    if (!v.has_value()) return false;
    return py_is_str(*v);
}
template <class T> static inline bool py_is_bool(const ::std::optional<T>& v) {
    if (!v.has_value()) return false;
    return py_is_bool(*v);
}

static inline bool py_is_dict(const ::std::any& v) {
    if (v.type() == typeid(dict<str, ::std::any>) || v.type() == typeid(dict<str, object>)) return true;
    if (const auto* p = ::std::any_cast<object>(&v)) return py_is_dict(*p);
    return false;
}
static inline bool py_is_list(const ::std::any& v) {
    if (v.type() == typeid(list<::std::any>) || v.type() == typeid(list<object>)) return true;
    if (const auto* p = ::std::any_cast<object>(&v)) return py_is_list(*p);
    return false;
}
static inline bool py_is_set(const ::std::any& v) { return v.type() == typeid(set<str>) || v.type() == typeid(set<::std::any>); }
static inline bool py_is_str(const ::std::any& v) {
    if (v.type() == typeid(str)) return true;
    if (const auto* p = ::std::any_cast<object>(&v)) return py_is_str(*p);
    return false;
}
static inline bool py_is_int(const ::std::any& v) {
    return v.type() == typeid(int) || v.type() == typeid(int64) || v.type() == typeid(uint64);
}
static inline bool py_is_float(const ::std::any& v) { return v.type() == typeid(float32) || v.type() == typeid(float64); }
static inline bool py_is_bool(const ::std::any& v) { return v.type() == typeid(bool); }

// type_id 判定ロジックは generated built_in 層（py_tid_*）を正本とする。
#include "runtime/cpp/pytra/built_in/type_id.h"

static inline uint32 py_register_class_type(uint32 base_type_id = PYTRA_TID_OBJECT) {
    return static_cast<uint32>(py_tid_register_class_type(static_cast<int64>(base_type_id)));
}

// Backward-compatible overload for pre-migration generated sources.
static inline uint32 py_register_class_type(const list<uint32>& bases) {
    if (py_len(bases) == 0) {
        return py_register_class_type(PYTRA_TID_OBJECT);
    }
    if (py_len(bases) == 1) {
        return py_register_class_type(bases[0]);
    }
    throw ValueError("multiple inheritance is not supported");
}

static inline bool py_is_subtype(uint32 actual_type_id, uint32 expected_type_id) {
    return py_tid_is_subtype(static_cast<int64>(actual_type_id), static_cast<int64>(expected_type_id));
}

static inline bool py_issubclass(uint32 actual_type_id, uint32 expected_type_id) {
    return py_tid_issubclass(static_cast<int64>(actual_type_id), static_cast<int64>(expected_type_id));
}

static inline uint32 py_runtime_type_id(const object& v) {
    if (!v) {
        return PYTRA_TID_NONE;
    }
    uint32 out = v->type_id();
    if (out == 0) {
        return PYTRA_TID_OBJECT;
    }
    return out;
}

template <class T>
static inline uint32 py_runtime_type_id(const T& v) {
    if (py_is_none(v)) return PYTRA_TID_NONE;
    if (py_is_bool(v)) return PYTRA_TID_BOOL;
    if (py_is_int(v)) return PYTRA_TID_INT;
    if (py_is_float(v)) return PYTRA_TID_FLOAT;
    if (py_is_str(v)) return PYTRA_TID_STR;
    if (py_is_list(v)) return PYTRA_TID_LIST;
    if (py_is_dict(v)) return PYTRA_TID_DICT;
    if (py_is_set(v)) return PYTRA_TID_SET;
    if constexpr (::std::is_same_v<T, object>) {
        return py_runtime_type_id(static_cast<const object&>(v));
    }
    return PYTRA_TID_OBJECT;
}

template <class T>
static inline bool py_isinstance(const T& value, uint32 expected_type_id) {
    if constexpr (::std::is_same_v<T, object>) {
        if (!value) {
            return expected_type_id == PYTRA_TID_NONE;
        }
        if (value->py_isinstance_of(expected_type_id)) {
            return true;
        }
        return py_is_subtype(py_runtime_type_id(value), expected_type_id);
    }
    return py_is_subtype(py_runtime_type_id(value), expected_type_id);
}

static inline object py_iter_or_raise(const object& value) {
    if (!value) {
        throw TypeError("NoneType is not iterable");
    }
    return value->py_iter_or_raise();
}

template <class T>
static inline object py_iter_or_raise(const T& value) {
    return py_iter_or_raise(make_object(value));
}

static inline ::std::optional<object> py_next_or_stop(const object& iter_obj) {
    if (!iter_obj) {
        throw TypeError("NoneType is not an iterator");
    }
    return iter_obj->py_next_or_stop();
}

class py_dyn_range_iter {
public:
    py_dyn_range_iter() : is_end_(true) {}
    explicit py_dyn_range_iter(object iter_obj, bool is_end = false)
        : iter_obj_(::std::move(iter_obj)), is_end_(is_end) {
        if (!is_end_) {
            pull_next();
        }
    }

    const object& operator*() const {
        return current_;
    }

    py_dyn_range_iter& operator++() {
        pull_next();
        return *this;
    }

    bool operator!=(const py_dyn_range_iter& other) const {
        return is_end_ != other.is_end_;
    }

private:
    void pull_next() {
        if (is_end_) {
            return;
        }
        ::std::optional<object> nxt = py_next_or_stop(iter_obj_);
        if (!nxt.has_value()) {
            is_end_ = true;
            current_ = object();
            return;
        }
        current_ = *nxt;
    }

    object iter_obj_;
    object current_;
    bool is_end_ = true;
};

class py_dyn_range_view {
public:
    explicit py_dyn_range_view(object iterable)
        : iter_obj_(py_iter_or_raise(iterable)) {}

    py_dyn_range_iter begin() const {
        return py_dyn_range_iter(iter_obj_, false);
    }

    py_dyn_range_iter end() const {
        return py_dyn_range_iter(iter_obj_, true);
    }

private:
    object iter_obj_;
};

static inline py_dyn_range_view py_dyn_range(const object& iterable) {
    return py_dyn_range_view(iterable);
}

template <class T>
static inline py_dyn_range_view py_dyn_range(const T& iterable) {
    return py_dyn_range(make_object(iterable));
}

// selfhost 由来の `obj == std::nullopt` 比較（None 判定）互換。
static inline bool operator==(const object& lhs, const ::std::nullopt_t&) { return !lhs; }
static inline bool operator!=(const object& lhs, const ::std::nullopt_t&) { return !!lhs; }
static inline bool operator==(const ::std::nullopt_t&, const object& rhs) { return !rhs; }
static inline bool operator!=(const ::std::nullopt_t&, const object& rhs) { return !!rhs; }

// selfhost 由来の `std::any` 比較式をそのまま通すための演算子補助。
static inline bool operator==(const ::std::any& lhs, const char* rhs) {
    if (const auto* p = ::std::any_cast<str>(&lhs)) return *p == str(rhs);
    if (const auto* p = ::std::any_cast<object>(&lhs)) return obj_to_str(*p) == str(rhs);
    return false;
}

static inline bool operator!=(const ::std::any& lhs, const char* rhs) {
    return !(lhs == rhs);
}

static inline bool operator==(const object& lhs, const char* rhs) {
    return obj_to_str(lhs) == str(rhs);
}

static inline bool operator==(const char* lhs, const object& rhs) {
    return str(lhs) == obj_to_str(rhs);
}

static inline bool operator==(const object& lhs, const str& rhs) {
    return obj_to_str(lhs) == rhs;
}

static inline bool operator==(const str& lhs, const object& rhs) {
    return lhs == obj_to_str(rhs);
}

static inline bool operator!=(const object& lhs, const char* rhs) {
    return !(lhs == rhs);
}

static inline bool operator!=(const char* lhs, const object& rhs) {
    return !(lhs == rhs);
}

static inline bool operator>(const ::std::any& lhs, int rhs) {
    if (const auto* p = ::std::any_cast<int64>(&lhs)) return *p > static_cast<int64>(rhs);
    if (const auto* p = ::std::any_cast<int>(&lhs)) return *p > rhs;
    if (const auto* p = ::std::any_cast<uint64>(&lhs)) return *p > static_cast<uint64>(rhs);
    return false;
}

static inline bool operator<(int64 lhs, const ::std::any& rhs) {
    if (const auto* p = ::std::any_cast<int64>(&rhs)) return lhs < *p;
    if (const auto* p = ::std::any_cast<int>(&rhs)) return lhs < static_cast<int64>(*p);
    if (const auto* p = ::std::any_cast<uint64>(&rhs)) return lhs < static_cast<int64>(*p);
    return false;
}

static inline bool operator<(const ::std::any& lhs, const ::std::any& rhs) {
    return py_to_float64(lhs) < py_to_float64(rhs);
}

static inline bool operator>(const ::std::any& lhs, const ::std::any& rhs) {
    return py_to_float64(lhs) > py_to_float64(rhs);
}

static inline bool operator<=(const ::std::any& lhs, const ::std::any& rhs) {
    return py_to_float64(lhs) <= py_to_float64(rhs);
}

static inline bool operator>=(const ::std::any& lhs, const ::std::any& rhs) {
    return py_to_float64(lhs) >= py_to_float64(rhs);
}

template <class T, ::std::enable_if_t<::std::is_arithmetic_v<T>, int> = 0>
static inline bool operator<(const ::std::any& lhs, T rhs) {
    return py_to_float64(lhs) < static_cast<float64>(rhs);
}

template <class T, ::std::enable_if_t<::std::is_arithmetic_v<T>, int> = 0>
static inline bool operator>(const ::std::any& lhs, T rhs) {
    return py_to_float64(lhs) > static_cast<float64>(rhs);
}

template <class T, ::std::enable_if_t<::std::is_arithmetic_v<T>, int> = 0>
static inline bool operator<=(const ::std::any& lhs, T rhs) {
    return py_to_float64(lhs) <= static_cast<float64>(rhs);
}

template <class T, ::std::enable_if_t<::std::is_arithmetic_v<T>, int> = 0>
static inline bool operator>=(const ::std::any& lhs, T rhs) {
    return py_to_float64(lhs) >= static_cast<float64>(rhs);
}

template <class T, ::std::enable_if_t<::std::is_arithmetic_v<T>, int> = 0>
static inline bool operator<(T lhs, const ::std::any& rhs) {
    return static_cast<float64>(lhs) < py_to_float64(rhs);
}

template <class T, ::std::enable_if_t<::std::is_arithmetic_v<T>, int> = 0>
static inline bool operator>(T lhs, const ::std::any& rhs) {
    return static_cast<float64>(lhs) > py_to_float64(rhs);
}

template <class T, ::std::enable_if_t<::std::is_arithmetic_v<T>, int> = 0>
static inline bool operator<=(T lhs, const ::std::any& rhs) {
    return static_cast<float64>(lhs) <= py_to_float64(rhs);
}

template <class T, ::std::enable_if_t<::std::is_arithmetic_v<T>, int> = 0>
static inline bool operator>=(T lhs, const ::std::any& rhs) {
    return static_cast<float64>(lhs) >= py_to_float64(rhs);
}

static inline str operator+(const char* lhs, const ::std::any& rhs) {
    return str(lhs) + py_to_string(rhs);
}

template <class T, ::std::enable_if_t<::std::is_arithmetic_v<T>, int> = 0>
static inline float64 operator+(T lhs, const object& rhs) {
    return static_cast<float64>(lhs) + py_to_float64(rhs);
}

template <class T, ::std::enable_if_t<::std::is_arithmetic_v<T>, int> = 0>
static inline float64 operator+(const object& lhs, T rhs) {
    return py_to_float64(lhs) + static_cast<float64>(rhs);
}

static inline float64 operator+(const object& lhs, const object& rhs) {
    return py_to_float64(lhs) + py_to_float64(rhs);
}

template <class T, ::std::enable_if_t<::std::is_arithmetic_v<T>, int> = 0>
static inline float64 operator+(T lhs, const ::std::any& rhs) {
    return static_cast<float64>(lhs) + py_to_float64(rhs);
}

template <class T, ::std::enable_if_t<::std::is_arithmetic_v<T>, int> = 0>
static inline float64 operator+(const ::std::any& lhs, T rhs) {
    return py_to_float64(lhs) + static_cast<float64>(rhs);
}

static inline float64 operator+(const ::std::any& lhs, const ::std::any& rhs) {
    return py_to_float64(lhs) + py_to_float64(rhs);
}

template <class T, ::std::enable_if_t<::std::is_arithmetic_v<T>, int> = 0>
static inline float64 operator-(T lhs, const object& rhs) {
    return static_cast<float64>(lhs) - py_to_float64(rhs);
}

template <class T, ::std::enable_if_t<::std::is_arithmetic_v<T>, int> = 0>
static inline float64 operator-(const object& lhs, T rhs) {
    return py_to_float64(lhs) - static_cast<float64>(rhs);
}

static inline float64 operator-(const object& lhs, const object& rhs) {
    return py_to_float64(lhs) - py_to_float64(rhs);
}

template <class T>
static inline auto operator-(const rc<T>& v) -> decltype(v->__neg__()) {
    return v->__neg__();
}

static inline float64 operator-(const object& v) {
    return -py_to_float64(v);
}

template <class T, ::std::enable_if_t<::std::is_arithmetic_v<T>, int> = 0>
static inline float64 operator-(T lhs, const ::std::any& rhs) {
    return static_cast<float64>(lhs) - py_to_float64(rhs);
}

template <class T, ::std::enable_if_t<::std::is_arithmetic_v<T>, int> = 0>
static inline float64 operator-(const ::std::any& lhs, T rhs) {
    return py_to_float64(lhs) - static_cast<float64>(rhs);
}

static inline float64 operator-(const ::std::any& lhs, const ::std::any& rhs) {
    return py_to_float64(lhs) - py_to_float64(rhs);
}

template <class T, ::std::enable_if_t<::std::is_arithmetic_v<T>, int> = 0>
static inline float64 operator*(T lhs, const object& rhs) {
    return static_cast<float64>(lhs) * py_to_float64(rhs);
}

template <class T, ::std::enable_if_t<::std::is_arithmetic_v<T>, int> = 0>
static inline float64 operator*(const object& lhs, T rhs) {
    return py_to_float64(lhs) * static_cast<float64>(rhs);
}

static inline float64 operator*(const object& lhs, const object& rhs) {
    return py_to_float64(lhs) * py_to_float64(rhs);
}

template <class T, ::std::enable_if_t<::std::is_arithmetic_v<T>, int> = 0>
static inline float64 operator*(T lhs, const ::std::any& rhs) {
    return static_cast<float64>(lhs) * py_to_float64(rhs);
}

template <class T, ::std::enable_if_t<::std::is_arithmetic_v<T>, int> = 0>
static inline float64 operator*(const ::std::any& lhs, T rhs) {
    return py_to_float64(lhs) * static_cast<float64>(rhs);
}

static inline float64 operator*(const ::std::any& lhs, const ::std::any& rhs) {
    return py_to_float64(lhs) * py_to_float64(rhs);
}

template <class T, ::std::enable_if_t<::std::is_arithmetic_v<T>, int> = 0>
static inline float64 operator/(T lhs, const object& rhs) {
    return static_cast<float64>(lhs) / py_to_float64(rhs);
}

template <class T, ::std::enable_if_t<::std::is_arithmetic_v<T>, int> = 0>
static inline float64 operator/(const object& lhs, T rhs) {
    return py_to_float64(lhs) / static_cast<float64>(rhs);
}

static inline float64 operator/(const object& lhs, const object& rhs) {
    return py_to_float64(lhs) / py_to_float64(rhs);
}

template <class T, ::std::enable_if_t<::std::is_arithmetic_v<T>, int> = 0>
static inline float64 operator/(T lhs, const ::std::any& rhs) {
    return static_cast<float64>(lhs) / py_to_float64(rhs);
}

template <class T, ::std::enable_if_t<::std::is_arithmetic_v<T>, int> = 0>
static inline float64 operator/(const ::std::any& lhs, T rhs) {
    return py_to_float64(lhs) / static_cast<float64>(rhs);
}

static inline float64 operator/(const ::std::any& lhs, const ::std::any& rhs) {
    return py_to_float64(lhs) / py_to_float64(rhs);
}

template <class T>
static inline object& operator+=(object& lhs, const T& rhs) {
    lhs = make_object(py_to_float64(lhs) + py_to_float64(rhs));
    return lhs;
}

template <class T>
static inline object& operator-=(object& lhs, const T& rhs) {
    lhs = make_object(py_to_float64(lhs) - py_to_float64(rhs));
    return lhs;
}

template <class T>
static inline object& operator*=(object& lhs, const T& rhs) {
    lhs = make_object(py_to_float64(lhs) * py_to_float64(rhs));
    return lhs;
}

template <class T>
static inline object& operator/=(object& lhs, const T& rhs) {
    lhs = make_object(py_to_float64(lhs) / py_to_float64(rhs));
    return lhs;
}

// `for x in any_value` を成立させるための begin/end ブリッジ。
static inline list<::std::any>::iterator begin(::std::any& v) {
    if (auto* p = ::std::any_cast<list<::std::any>>(&v)) return p->begin();
    static list<::std::any> empty;
    return empty.begin();
}

static inline list<::std::any>::iterator end(::std::any& v) {
    if (auto* p = ::std::any_cast<list<::std::any>>(&v)) return p->end();
    static list<::std::any> empty;
    return empty.end();
}

static inline list<::std::any>::const_iterator begin(const ::std::any& v) {
    if (const auto* p = ::std::any_cast<list<::std::any>>(&v)) return p->begin();
    static const list<::std::any> empty;
    return empty.begin();
}

static inline list<::std::any>::const_iterator end(const ::std::any& v) {
    if (const auto* p = ::std::any_cast<list<::std::any>>(&v)) return p->end();
    static const list<::std::any> empty;
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

// range-for は ADL で begin/end を解決するため、object 実体型の名前空間にも置く。
namespace pytra::gc {
static inline list<object>::const_iterator begin(const RcHandle<PyObj>& v) {
    return ::begin(::object(v));
}

static inline list<object>::const_iterator end(const RcHandle<PyObj>& v) {
    return ::end(::object(v));
}
}  // namespace pytra::gc

static inline list<object>::const_iterator begin(const ::std::optional<object>& v) {
    if (!v.has_value()) {
        static const list<object> empty;
        return empty.begin();
    }
    return ::begin(*v);
}

static inline list<object>::const_iterator end(const ::std::optional<object>& v) {
    if (!v.has_value()) {
        static const list<object> empty;
        return empty.end();
    }
    return ::end(*v);
}

// Selfhost-generated C++ can iterate ::std::any values that hold list<::std::any>.
// Provide ::std::begin/::std::end overloads so range-for resolves them.
namespace std {
static inline ::list<::std::any>::iterator begin(::std::any& v) {
    return ::begin(v);
}
static inline ::list<::std::any>::iterator end(::std::any& v) {
    return ::end(v);
}
static inline ::list<::std::any>::const_iterator begin(const ::std::any& v) {
    return ::begin(v);
}
static inline ::list<::std::any>::const_iterator end(const ::std::any& v) {
    return ::end(v);
}
}  // namespace std

// dict.keys / dict.values の Python 互換。
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
        throw ::std::out_of_range("string index out of range");
    }
    return str(1, static_cast<const ::std::string&>(v)[static_cast<::std::size_t>(idx)]);
}

static inline str py_slice(const ::std::any& v, int64 lo, int64 up) {
    if (const auto* s = ::std::any_cast<str>(&v)) return py_slice(*s, lo, up);
    return "";
}

static inline str py_slice(const ::std::any& v, int64 lo, const ::std::any& up) {
    return py_slice(v, lo, py_to_int64(up));
}

// Path 読み書き・文字列メソッド互換ヘルパ。
static inline void py_write_text(const Path& p, const str& s) {
    ::std::ofstream ofs(p.native());
    ofs << s;
}

static inline str py_read_text(const Path& p) {
    ::std::ifstream ifs(p.native());
    ::std::stringstream ss;
    ss << ifs.rdbuf();
    return ss.str();
}

static inline str py_lstrip(const str& s) {
    ::std::size_t i = 0;
    while (i < s.size() && ::std::isspace(static_cast<unsigned char>(static_cast<const ::std::string&>(s)[i])) != 0) i++;
    return s.substr(i);
}

static inline str py_lstrip(const str& s, const str& chars) {
    return s.lstrip(chars);
}

static inline str py_lstrip(const object& s) {
    return py_lstrip(str(py_to_string(s)));
}

static inline str py_lstrip(const object& s, const str& chars) {
    return py_lstrip(str(py_to_string(s)), chars);
}

static inline str py_lstrip(const ::std::any& s) {
    return py_lstrip(str(py_to_string(s)));
}

static inline str py_lstrip(const ::std::any& s, const str& chars) {
    return py_lstrip(str(py_to_string(s)), chars);
}

static inline str py_rstrip(const str& s) {
    if (s.empty()) return s;
    ::std::size_t i = s.size();
    while (i > 0 && ::std::isspace(static_cast<unsigned char>(static_cast<const ::std::string&>(s)[i - 1])) != 0) i--;
    return s.substr(0, i);
}

static inline str py_rstrip(const str& s, const str& chars) {
    return s.rstrip(chars);
}

static inline str py_rstrip(const object& s) {
    return py_rstrip(str(py_to_string(s)));
}

static inline str py_rstrip(const object& s, const str& chars) {
    return py_rstrip(str(py_to_string(s)), chars);
}

static inline str py_rstrip(const ::std::any& s) {
    return py_rstrip(str(py_to_string(s)));
}

static inline str py_rstrip(const ::std::any& s, const str& chars) {
    return py_rstrip(str(py_to_string(s)), chars);
}

static inline str py_strip(const str& s) {
    return py_rstrip(py_lstrip(s));
}

static inline str py_strip(const str& s, const str& chars) {
    return s.strip(chars);
}

static inline str py_strip(const ::std::string& s) {
    return py_strip(str(s));
}

static inline str py_strip(const ::std::string& s, const str& chars) {
    return py_strip(str(s), chars);
}

static inline str py_strip(const object& s) {
    return py_strip(str(py_to_string(s)));
}

static inline str py_strip(const object& s, const str& chars) {
    return py_strip(str(py_to_string(s)), chars);
}

static inline str py_strip(const ::std::any& s) {
    return py_strip(str(py_to_string(s)));
}

static inline str py_strip(const ::std::any& s, const str& chars) {
    return py_strip(str(py_to_string(s)), chars);
}

static inline bool py_startswith(const str& s, const str& prefix) {
    return s.rfind(prefix, 0) == 0;
}

static inline bool py_startswith(const object& s, const str& prefix) {
    return py_startswith(str(py_to_string(s)), prefix);
}

static inline bool py_startswith(const ::std::any& s, const str& prefix) {
    return py_startswith(str(py_to_string(s)), prefix);
}

static inline bool py_endswith(const str& s, const str& suffix) {
    if (suffix.size() > s.size()) return false;
    return s.compare(s.size() - suffix.size(), suffix.size(), suffix) == 0;
}

static inline bool py_endswith(const object& s, const str& suffix) {
    return py_endswith(str(py_to_string(s)), suffix);
}

static inline bool py_endswith(const ::std::any& s, const str& suffix) {
    return py_endswith(str(py_to_string(s)), suffix);
}

static inline int64 _py_find_norm_index(int64 idx, int64 n) {
    if (idx < 0) idx += n;
    idx = ::std::max<int64>(0, ::std::min<int64>(idx, n));
    return idx;
}

static inline int64 py_find(const str& s, const str& needle) {
    return s.find(needle);
}

static inline int64 py_find(const str& s, const str& needle, int64 start, int64 end) {
    const int64 n = static_cast<int64>(s.size());
    const int64 lo = _py_find_norm_index(start, n);
    const int64 up = _py_find_norm_index(end, n);
    if (up <= lo) return -1;
    str clipped = py_slice(s, lo, up);
    int64 pos = clipped.find(needle);
    if (pos < 0) return -1;
    return lo + pos;
}

static inline int64 py_find(const str& s, const str& needle, int64 start) {
    return py_find(s, needle, start, static_cast<int64>(s.size()));
}

static inline int64 py_find(const object& s, const str& needle) {
    return py_find(str(py_to_string(s)), needle);
}

static inline int64 py_find(const object& s, const str& needle, int64 start) {
    return py_find(str(py_to_string(s)), needle, start);
}

static inline int64 py_find(const object& s, const str& needle, int64 start, int64 end) {
    return py_find(str(py_to_string(s)), needle, start, end);
}

static inline int64 py_find(const ::std::any& s, const str& needle) {
    return py_find(str(py_to_string(s)), needle);
}

static inline int64 py_find(const ::std::any& s, const str& needle, int64 start) {
    return py_find(str(py_to_string(s)), needle, start);
}

static inline int64 py_find(const ::std::any& s, const str& needle, int64 start, int64 end) {
    return py_find(str(py_to_string(s)), needle, start, end);
}

static inline int64 py_rfind(const str& s, const str& needle) {
    return s.rfind(needle);
}

static inline int64 py_rfind(const str& s, const str& needle, int64 start, int64 end) {
    const int64 n = static_cast<int64>(s.size());
    const int64 lo = _py_find_norm_index(start, n);
    const int64 up = _py_find_norm_index(end, n);
    if (up <= lo) return -1;
    str clipped = py_slice(s, lo, up);
    int64 pos = clipped.rfind(needle);
    if (pos < 0) return -1;
    return lo + pos;
}

static inline int64 py_rfind(const str& s, const str& needle, int64 start) {
    return py_rfind(s, needle, start, static_cast<int64>(s.size()));
}

static inline int64 py_rfind(const object& s, const str& needle) {
    return py_rfind(str(py_to_string(s)), needle);
}

static inline int64 py_rfind(const object& s, const str& needle, int64 start) {
    return py_rfind(str(py_to_string(s)), needle, start);
}

static inline int64 py_rfind(const object& s, const str& needle, int64 start, int64 end) {
    return py_rfind(str(py_to_string(s)), needle, start, end);
}

static inline int64 py_rfind(const ::std::any& s, const str& needle) {
    return py_rfind(str(py_to_string(s)), needle);
}

static inline int64 py_rfind(const ::std::any& s, const str& needle, int64 start) {
    return py_rfind(str(py_to_string(s)), needle, start);
}

static inline int64 py_rfind(const ::std::any& s, const str& needle, int64 start, int64 end) {
    return py_rfind(str(py_to_string(s)), needle, start, end);
}

static inline str py_replace(const str& s, const str& oldv, const str& newv) {
    if (oldv.empty()) return s;
    str out = s;
    ::std::size_t pos = 0;
    while ((pos = out.find(oldv, pos)) != str::npos) {
        out.replace(pos, oldv.size(), newv);
        pos += newv.size();
    }
    return out;
}

static inline str py_replace(const object& s, const str& oldv, const str& newv) {
    return py_replace(str(py_to_string(s)), oldv, newv);
}

static inline str py_replace(const ::std::any& s, const str& oldv, const str& newv) {
    return py_replace(str(py_to_string(s)), oldv, newv);
}

// reversed / enumerate / tuple in 判定の互換実装。
template <class T>
static inline list<T> py_reversed(const list<T>& values) {
    list<T> out(values.begin(), values.end());
    ::std::reverse(out.begin(), out.end());
    return out;
}

static inline list<::std::any> py_reversed(const ::std::any& values) {
    if (const auto* p = ::std::any_cast<list<::std::any>>(&values)) return py_reversed(*p);
    return {};
}

template <class T>
static inline list<::std::tuple<int64, T>> py_enumerate(const list<T>& values) {
    list<::std::tuple<int64, T>> out;
    out.reserve(values.size());
    for (::std::size_t i = 0; i < values.size(); i++) {
        out.append(::std::make_tuple(static_cast<int64>(i), values[i]));
    }
    return out;
}

template <class T>
static inline list<::std::tuple<int64, T>> py_enumerate(const list<T>& values, int64 start) {
    list<::std::tuple<int64, T>> out;
    out.reserve(values.size());
    for (::std::size_t i = 0; i < values.size(); i++) {
        out.append(::std::make_tuple(start + static_cast<int64>(i), values[i]));
    }
    return out;
}

static inline list<::std::tuple<int64, str>> py_enumerate(const str& values) {
    list<::std::tuple<int64, str>> out;
    out.reserve(values.size());
    for (::std::size_t i = 0; i < values.size(); i++) {
        out.append(::std::make_tuple(static_cast<int64>(i), values[i]));
    }
    return out;
}

static inline list<::std::tuple<int64, str>> py_enumerate(const str& values, int64 start) {
    list<::std::tuple<int64, str>> out;
    out.reserve(values.size());
    for (::std::size_t i = 0; i < values.size(); i++) {
        out.append(::std::make_tuple(start + static_cast<int64>(i), values[i]));
    }
    return out;
}

static inline list<::std::tuple<int64, ::std::any>> py_enumerate(const ::std::any& values) {
    if (const auto* p = ::std::any_cast<list<::std::any>>(&values)) return py_enumerate(*p);
    if (const auto* p = ::std::any_cast<str>(&values)) return py_enumerate(*p);
    return {};
}

static inline list<::std::tuple<int64, ::std::any>> py_enumerate(const ::std::any& values, int64 start) {
    if (const auto* p = ::std::any_cast<list<::std::any>>(&values)) return py_enumerate(*p, start);
    if (const auto* p = ::std::any_cast<str>(&values)) return py_enumerate(*p, start);
    return {};
}

template <class A, class B>
static inline list<::std::tuple<A, B>> zip(const list<A>& lhs, const list<B>& rhs) {
    list<::std::tuple<A, B>> out;
    const ::std::size_t n = ::std::min(lhs.size(), rhs.size());
    out.reserve(n);
    for (::std::size_t i = 0; i < n; i++) {
        out.append(::std::make_tuple(lhs[i], rhs[i]));
    }
    return out;
}

static inline list<::std::tuple<object, object>> zip(const object& lhs, const object& rhs) {
    if (const auto* l = obj_to_list_ptr(lhs)) {
        if (const auto* r = obj_to_list_ptr(rhs)) {
            return zip(*l, *r);
        }
    }
    return {};
}

template <class T>
static inline list<T> sorted(const list<T>& values) {
    list<T> out = values;
    out.sort();
    return out;
}

template <class T>
static inline list<T> sorted(const set<T>& values) {
    list<T> out(values.begin(), values.end());
    out.sort();
    return out;
}

template <class T, ::std::enable_if_t<::std::is_arithmetic_v<T>, int> = 0>
static inline T sum(const list<T>& values) {
    T acc = static_cast<T>(0);
    for (const auto& v : values) acc += v;
    return acc;
}

static inline object sum(const list<object>& values) {
    float64 acc = 0.0;
    for (const auto& v : values) {
        acc += py_to_float64(v);
    }
    return make_object(acc);
}

static inline object sum(const object& values) {
    if (const auto* lst = obj_to_list_ptr(values)) return sum(*lst);
    return make_object(0);
}

template <class K, class V, class Q>
static inline bool py_contains(const dict<K, V>& d, const Q& key) {
    return d.find(static_cast<K>(key)) != d.end();
}

template <class V, class Q>
static inline bool py_contains(const dict<str, V>& d, const Q& key) {
    return d.find(str(py_to_string(key))) != d.end();
}

template <class T, class Q>
static inline bool py_contains(const list<T>& values, const Q& key) {
    return ::std::find(values.begin(), values.end(), key) != values.end();
}

template <class T, class Q>
static inline bool py_contains(const set<T>& values, const Q& key) {
    return values.find(static_cast<T>(key)) != values.end();
}

template <class Q>
static inline bool py_contains(const str& values, const Q& key) {
    return values.find(str(py_to_string(key))) != str::npos;
}

template <class Tup, class V>
static inline bool py_tuple_contains(const Tup& tup, const V& value) {
    bool found = false;
    ::std::apply(
        [&](const auto&... elems) {
            ((found = found || (elems == value)), ...);
        },
        tup);
    return found;
}

template <class... Ts, class V>
static inline bool py_contains(const ::std::tuple<Ts...>& values, const V& key) {
    return py_tuple_contains(values, key);
}

template <class Q>
static inline bool py_contains(const object& values, const Q& key) {
    if (const auto* d = obj_to_dict_ptr(values)) {
        return py_contains(*d, key);
    }
    if (const auto* lst = obj_to_list_ptr(values)) {
        return py_contains(*lst, make_object(key));
    }
    if (const auto* s = py_obj_cast<PyStrObj>(values)) {
        return py_contains(s->value, key);
    }
    return false;
}

// `/` / `//` / `%` の Python 互換セマンティクス（とくに負数時の扱い）を提供する。
template <class A, class B>
static inline float64 py_div(A lhs, B rhs) {
    return py_to_float64(lhs) / py_to_float64(rhs);
}

template <class A, class B>
static inline auto py_floordiv(A lhs, B rhs) {
    using R = ::std::common_type_t<A, B>;
    if constexpr (::std::is_integral_v<A> && ::std::is_integral_v<B>) {
        if (rhs == 0) throw ::std::runtime_error("division by zero");
        R q = static_cast<R>(lhs / rhs);
        R r = static_cast<R>(lhs % rhs);
        if (r != 0 && ((r > 0) != (rhs > 0))) q -= 1;
        return q;
    } else {
        return ::std::floor(static_cast<float64>(lhs) / static_cast<float64>(rhs));
    }
}

template <class A, class B>
static inline auto py_mod(A lhs, B rhs) {
    using R = ::std::common_type_t<A, B>;
    if constexpr (::std::is_integral_v<A> && ::std::is_integral_v<B>) {
        if (rhs == 0) throw ::std::runtime_error("integer modulo by zero");
        R r = static_cast<R>(lhs % rhs);
        if (r != 0 && ((r > 0) != (rhs > 0))) r += static_cast<R>(rhs);
        return r;
    } else {
        float64 lf = static_cast<float64>(lhs);
        float64 rf = static_cast<float64>(rhs);
        if (rf == 0.0) throw ::std::runtime_error("float modulo");
        float64 r = ::std::fmod(lf, rf);
        if (r != 0.0 && ((r > 0.0) != (rf > 0.0))) r += rf;
        return r;
    }
}

// try/finally を C++ で再現するための scope-exit ガード。
template <class F>
class py_scope_exit {
public:
    explicit py_scope_exit(F&& fn) : fn_(::std::forward<F>(fn)), active_(true) {}
    py_scope_exit(const py_scope_exit&) = delete;
    py_scope_exit& operator=(const py_scope_exit&) = delete;
    py_scope_exit(py_scope_exit&& other) noexcept : fn_(::std::move(other.fn_)), active_(other.active_) {
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
    return py_scope_exit<F>(::std::forward<F>(fn));
}

// 実行時引数・標準出力入出力の最小ランタイム状態。
static inline list<str>& py_runtime_argv_storage();
static inline void py_runtime_set_argv(const list<str>& values);

static inline void pytra_configure_from_argv(int argc, char** argv) {
    list<str> args{};
    args.reserve(static_cast<::std::size_t>(argc));
    for (int i = 0; i < argc; ++i) {
        args.append(str(argv[i]));
    }
    py_runtime_set_argv(args);
}

static inline list<str>& py_runtime_argv_storage() {
    static list<str> v{};
    return v;
}

static inline list<str> py_runtime_argv() {
    return py_runtime_argv_storage();
}

static inline void py_runtime_set_argv(const list<str>& values) {
    py_runtime_argv_storage() = values;
}

static inline list<str> py_to_str_list_from_object(const object& obj) {
    list<str> out{};
    const list<object>* p = obj_to_list_ptr(obj);
    if (p == nullptr) return out;
    out.reserve(p->size());
    for (const object& v : *p) out.append(obj_to_str(v));
    return out;
}

static inline list<str> py_to_str_list_from_any(const ::std::any& value) {
    if (!value.has_value()) return {};
    if (const auto* p = ::std::any_cast<list<str>>(&value)) return *p;
    if (const auto* p = ::std::any_cast<object>(&value)) return py_to_str_list_from_object(*p);
    return {};
}

static inline void py_runtime_write_stderr(const str& text) {
    ::std::cerr << text;
}

static inline void py_runtime_write_stdout(const str& text) {
    ::std::cout << text;
}

[[noreturn]] static inline void py_runtime_exit(int64 code = 0) {
    ::std::exit(static_cast<int>(code));
}

template <class A, class B>
static inline auto py_min(const A& a, const B& b) -> ::std::common_type_t<A, B> {
    using R = ::std::common_type_t<A, B>;
    return ::std::min<R>(static_cast<R>(a), static_cast<R>(b));
}

template <class A, class B, class... Rest>
static inline auto py_min(const A& a, const B& b, const Rest&... rest) -> ::std::common_type_t<A, B, Rest...> {
    return py_min(py_min(a, b), rest...);
}

template <class A, class B>
static inline auto py_max(const A& a, const B& b) -> ::std::common_type_t<A, B> {
    using R = ::std::common_type_t<A, B>;
    return ::std::max<R>(static_cast<R>(a), static_cast<R>(b));
}

template <class A, class B, class... Rest>
static inline auto py_max(const A& a, const B& b, const Rest&... rest) -> ::std::common_type_t<A, B, Rest...> {
    return py_max(py_max(a, b), rest...);
}

// Python の range / シーケンス repeat 互換。
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
    out.reserve(v.size() * static_cast<::std::size_t>(n));
    for (int64 i = 0; i < n; ++i) {
        out.insert(out.end(), v.begin(), v.end());
    }
    return out;
}

static inline str py_repeat(const str& v, int64 n) {
    if (n <= 0) return "";
    str out;
    out.reserve(v.size() * static_cast<::std::size_t>(n));
    for (int64 i = 0; i < n; ++i) {
        out += v;
    }
    return out;
}

#endif  // PYTRA_BUILT_IN_PY_RUNTIME_H
