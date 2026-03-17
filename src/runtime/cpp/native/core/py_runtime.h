#ifndef PYTRA_BUILT_IN_PY_RUNTIME_H
#define PYTRA_BUILT_IN_PY_RUNTIME_H

#include <algorithm>
#include <cmath>
#include <cstdint>
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

#include "py_types.h"
#include "exceptions.h"
#include "io.h"
// `str` method delegates still live here, so string helper declarations remain a direct dependency.
#include "runtime/cpp/generated/built_in/string_ops.h"

template <class T>
static inline rc<list<T>> obj_to_rc_list(const object& v, const char* ctx = "obj_to_rc_list");

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
    return py_split(*this, sep, maxsplit);
}

inline list<str> str::split(const str& sep) const {
    return split(sep, -1);
}

inline list<str> str::splitlines() const {
    return py_splitlines(*this);
}

inline int64 str::count(const str& needle) const {
    return py_count(*this, needle);
}

inline str str::join(const list<str>& parts) const {
    return py_join(*this, parts);
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

template <class T>
static inline list<rc<T>> py_to_rc_list_from_object(const object& v, const char* ctx = "py_to_rc_list_from_object") {
    list<rc<T>> out{};
    const list<object>* src = obj_to_list_ptr(v);
    if (src == nullptr) return out;
    out.reserve(src->size());
    for (const object& item : *src) out.append(obj_to_rc_or_raise<T>(item, ctx));
    return out;
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
static inline object py_make_list_object_from_values(const list<T>& values) {
    list<object> out;
    out.reserve(values.size());
    for (const auto& value : values) out.append(make_object(value));
    return object_new<PyListObj>(::std::move(out));
}

template <class T>
static inline object make_object(const list<T>& values) {
    return py_make_list_object_from_values(values);
}

static inline object make_object(const list<object>& values) {
    return object_new<PyListObj>(values);
}

static inline object make_object(list<object>&& values) {
    return object_new<PyListObj>(::std::move(values));
}

template <class T>
static inline object make_object(const rc<list<T>>& values) {
    if (!values) {
        return object();
    }
    return py_make_list_object_from_values(rc_list_ref(values));
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
    } else if constexpr (!::std::is_integral_v<T> && !::std::is_floating_point_v<T> && !::std::is_convertible_v<T, str> && ::std::is_convertible_v<T, bool>) {
        return object_new<PyBoolObj>(static_cast<bool>(v));
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

inline str obj_to_str(const object& v) {
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

inline const dict<str, object>* obj_to_dict_ptr(const object& v) {
    if (const auto* p = py_obj_cast<PyDictObj>(v)) return &(p->value);
    return nullptr;
}

inline const list<object>* obj_to_list_ptr(const object& v) {
    const auto p = obj_to_rc<PyListObj>(v);
    if (p) return &(p->value);
    return nullptr;
}

static inline rc<PyListObj> obj_to_list_obj(const object& v) {
    return obj_to_rc<PyListObj>(v);
}

static inline list<object>& obj_to_list_ref_or_raise(object& v, const char* ctx = "obj_to_list_ref_or_raise") {
    auto p = obj_to_list_obj(v);
    if (p) return p->value;
    const char* label = ctx != nullptr ? ctx : "obj_to_list_ref_or_raise";
    throw ::std::runtime_error(::std::string(label) + ": object is not list");
}

static inline const list<object>& obj_to_list_ref_or_raise(const object& v, const char* ctx = "obj_to_list_ref_or_raise") {
    const auto* p = obj_to_list_ptr(v);
    if (p) return *p;
    const char* label = ctx != nullptr ? ctx : "obj_to_list_ref_or_raise";
    throw ::std::runtime_error(::std::string(label) + ": object is not list");
}

inline const list<object>* obj_to_set_ptr(const object& v) {
    if (const auto* p = py_obj_cast<PySetObj>(v)) return &(p->value);
    return nullptr;
}

inline dict<str, object> obj_to_dict(const object& v) {
    if (const auto* p = obj_to_dict_ptr(v)) return *p;
    return {};
}

static inline int64 py_len(const object& v) {
    if (!v) return 0;
    const auto len = v->py_try_len();
    if (len.has_value()) return *len;
    return 0;
}

template <class T>
static inline int64 py_len(const rc<list<T>>& v) {
    if (!v) return 0;
    return static_cast<int64>(v->size());
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

// selfhost 段階で一時的に残る `len(x)` を受ける互換エイリアス。
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

static inline ::std::string py_to_string(const object& v) {
    return obj_to_str(v);
}

// `object` / `any` に入った値を型付きで取り出す補助キャスト群。
template <class D>
static inline ::std::optional<D> py_object_try_cast(const object& v) {
    if constexpr (::std::is_same_v<D, object>) {
        return v;
    } else if constexpr (py_is_rc_list_handle<D>::value) {
        using item_type = typename py_is_rc_list_handle<D>::item_type;
        auto out = obj_to_rc_list<item_type>(v);
        if (out) return out;
        return ::std::nullopt;
    } else if constexpr (::std::is_same_v<D, str>) {
        return obj_to_str(v);
    } else if constexpr (::std::is_same_v<D, bool>) {
        return obj_to_bool(v);
    } else if constexpr (::std::is_integral_v<D> && !::std::is_same_v<D, bool>) {
        int64 i = 0;
        if (obj_try_to_int64(v, i)) return static_cast<D>(i);
        float64 f = 0.0;
        if (obj_try_to_float64(v, f)) return static_cast<D>(f);
        return ::std::nullopt;
    } else if constexpr (::std::is_floating_point_v<D>) {
        float64 f = 0.0;
        if (obj_try_to_float64(v, f)) return static_cast<D>(f);
        int64 i = 0;
        if (obj_try_to_int64(v, i)) return static_cast<D>(i);
        return ::std::nullopt;
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

template <class T>
static inline T py_to(const object& v);

template <class T, ::std::enable_if_t<!::std::is_same_v<T, object>, int> = 0>
static inline T py_to(const T& v);

static inline int64 py_to_int64(const str& v) {
    return static_cast<int64>(::std::stoll(v));
}

template <class T, ::std::enable_if_t<::std::is_arithmetic_v<T>, int> = 0>
static inline int64 py_to_int64(T v) {
    return py_to<int64>(v);
}

static inline int64 py_to_int64(const object& v) {
    return py_to<int64>(v);
}

static inline float64 py_to_float64(const object& v) {
    return py_to<float64>(v);
}

static inline float64 py_to_float64(const str& v) {
    return static_cast<float64>(::std::stod(v.std()));
}

template <class T, ::std::enable_if_t<::std::is_arithmetic_v<T>, int> = 0>
static inline float64 py_to_float64(T v) {
    return py_to<float64>(v);
}

static inline bool py_to_bool(const object& v) {
    return py_to<bool>(v);
}

template <class T>
static inline bool py_to_bool(const rc<list<T>>& v) {
    return v && !v->empty();
}

static inline bool py_to_bool(bool v) {
    return py_to<bool>(v);
}

template <class T, ::std::enable_if_t<!::std::is_same_v<T, object>, int>>
static inline T py_to(const T& v) {
    return v;
}

template <class T>
struct py_is_list_type : ::std::false_type {};

template <class T>
struct py_is_list_type<list<T>> : ::std::true_type {
    using item_type = T;
};

template <class T>
struct py_is_list_type<rc<list<T>>> : ::std::true_type {
    using item_type = T;
};

template <class T>
static inline list<T> py_copy_typed_list_from_object(const object& value, const char* ctx);

template <class T>
static inline T py_to(const object& v) {
    if constexpr (::std::is_same_v<T, object>) {
        return v;
    } else if constexpr (py_is_list_type<T>::value && (!py_is_rc_list_handle<T>::value)) {
        using item_type = typename py_is_list_type<T>::item_type;
        return py_copy_typed_list_from_object<item_type>(v, "py_to<object-list>");
    } else if constexpr (py_is_rc_list_handle<T>::value) {
        using item_type = typename py_is_rc_list_handle<T>::item_type;
        return obj_to_rc_list<item_type>(v);
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
static inline list<T> py_list_slice_copy(const list<T>& values, int64 lo, int64 up) {
    const int64 n = static_cast<int64>(values.size());
    if (lo < 0) lo += n;
    if (up < 0) up += n;
    lo = ::std::max<int64>(0, ::std::min<int64>(lo, n));
    up = ::std::max<int64>(0, ::std::min<int64>(up, n));
    if (up < lo) up = lo;
    return list<T>(values.begin() + lo, values.begin() + up);
}

template <class T>
static inline int64 py_list_normalize_index_or_raise(const list<T>& values, int64 idx, const char* label) {
    int64 pos = idx;
    const int64 n = static_cast<int64>(values.size());
    if (pos < 0) pos += n;
    if (pos < 0 || pos >= n) {
        throw ::std::out_of_range(label);
    }
    return pos;
}

template <class T>
static inline typename list<T>::reference py_list_at_ref(list<T>& values, int64 idx) {
    const int64 pos = py_list_normalize_index_or_raise(values, idx, "list index out of range");
    return values[static_cast<::std::size_t>(pos)];
}

template <class T>
static inline typename list<T>::const_reference py_list_at_ref(const list<T>& values, int64 idx) {
    const int64 pos = py_list_normalize_index_or_raise(values, idx, "list index out of range");
    return values[static_cast<::std::size_t>(pos)];
}

template <class T>
struct py_is_cstr_like : ::std::bool_constant<
    ::std::is_pointer_v<::std::decay_t<T>>
    && ::std::is_same_v<
        ::std::remove_cv_t<::std::remove_pointer_t<::std::decay_t<T>>>,
        char>> {};

template <class T>
static inline T py_coerce_cstr_typed_value(const char* value) {
    if constexpr (::std::is_same_v<T, str>) {
        return str(value);
    } else if constexpr (::std::is_same_v<T, object>) {
        return make_object(str(value));
    } else if constexpr (::std::is_same_v<T, bool>) {
        return str(value).size() != 0;
    } else if constexpr (::std::is_integral_v<T> && !::std::is_same_v<T, bool>) {
        return static_cast<T>(py_to_int64(str(value)));
    } else if constexpr (::std::is_floating_point_v<T>) {
        return static_cast<T>(py_to_float64(str(value)));
    } else if constexpr (::std::is_convertible_v<const char*, T>) {
        return static_cast<T>(value);
    } else if constexpr (::std::is_constructible_v<T, const char*>) {
        return T(value);
    } else if constexpr (::std::is_convertible_v<str, T>) {
        return static_cast<T>(str(value));
    } else if constexpr (::std::is_constructible_v<T, str>) {
        return T(str(value));
    } else {
        static_assert(!::std::is_same_v<T, T>, "py_coerce_cstr_typed_value<T>: unsupported target type");
    }
}

template <class T, class U>
static inline void py_list_append_mut(list<T>& values, const U& item) {
    if constexpr (::std::is_same_v<U, object>) {
        values.append(py_to<T>(item));
    } else if constexpr (py_is_cstr_like<U>::value) {
        values.append(py_coerce_cstr_typed_value<T>(item));
    } else if constexpr (::std::is_same_v<T, U>) {
        values.append(item);
    } else if constexpr (::std::is_convertible_v<U, T>) {
        values.append(static_cast<T>(item));
    } else {
        values.append(T(item));
    }
}

template <class T, class I, class U>
static inline void py_list_set_at_mut(list<T>& values, I idx, const U& item) {
    int64 pos = py_to<int64>(idx);
    pos = py_list_normalize_index_or_raise(values, pos, "list index out of range");
    if constexpr (::std::is_same_v<U, object>) {
        values[static_cast<::std::size_t>(pos)] = py_to<T>(item);
    } else if constexpr (py_is_cstr_like<U>::value) {
        values[static_cast<::std::size_t>(pos)] = py_coerce_cstr_typed_value<T>(item);
    } else if constexpr (::std::is_same_v<T, U>) {
        values[static_cast<::std::size_t>(pos)] = item;
    } else if constexpr (::std::is_convertible_v<U, T>) {
        values[static_cast<::std::size_t>(pos)] = static_cast<T>(item);
    } else {
        values[static_cast<::std::size_t>(pos)] = T(item);
    }
}

template <class T, class U>
static inline void py_list_extend_mut(list<T>& values, const U& items) {
    values.extend(items);
}

template <class T>
static inline T py_list_pop_mut(list<T>& values) {
    return values.pop();
}

template <class T>
static inline T py_list_pop_mut(list<T>& values, int64 idx) {
    return values.pop(idx);
}

template <class T>
static inline void py_list_clear_mut(list<T>& values) {
    values.clear();
}

template <class T>
static inline void py_list_reverse_mut(list<T>& values) {
    ::std::reverse(values.begin(), values.end());
}

template <class T>
static inline void py_list_sort_mut(list<T>& values) {
    ::std::sort(values.begin(), values.end());
}

static inline void py_list_sort_mut(list<object>& values) {
    ::std::sort(
        values.begin(),
        values.end(),
        [](const object& lhs, const object& rhs) {
            return py_to_string(lhs) < py_to_string(rhs);
        });
}

template <class T>
static inline list<T> py_slice(const list<T>& v, int64 lo, int64 up) {
    return py_list_slice_copy(v, lo, up);
}

template <class T>
static inline list<T> py_slice(const rc<list<T>>& v, int64 lo, int64 up) {
    return py_list_slice_copy(rc_list_ref(v), lo, up);
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

template <class T>
static inline typename list<T>::const_reference py_at(const list<T>& v, int64 idx) {
    return py_list_at_ref(v, idx);
}

template <class T>
static inline typename list<T>::reference py_at(rc<list<T>>& v, int64 idx) {
    return py_list_at_ref(rc_list_ref(v), idx);
}

template <class T>
static inline typename list<T>::const_reference py_at(const rc<list<T>>& v, int64 idx) {
    return py_list_at_ref(rc_list_ref(v), idx);
}

static inline object py_at(const object& v, int64 idx) {
    return py_list_at_ref(obj_to_list_ref_or_raise(v, "py_at"), idx);
}

// P0-contract-shrink label: object_bridge_compat surface only.
// Compatibility seam for object-bridge mutation only.
// Typed lanes must use direct list mutation or py_list_*_mut directly.
template <class U>
static inline void py_append(object& v, const U& item) {
    py_list_append_mut(obj_to_list_ref_or_raise(v, "py_append"), item);
}

template <class T>
static inline list<T> py_copy_typed_list_from_object(const object& value, const char* ctx) {
    const list<object>* src = obj_to_list_ptr(value);
    if (src == nullptr) {
        if (ctx == nullptr) {
            throw ::std::runtime_error("py_copy_typed_list_from_object: object is not list");
        }
        throw ::std::runtime_error(::std::string(ctx) + ": object is not list");
    }
    list<T> out{};
    out.reserve(src->size());
    for (const object& item : *src) {
        out.append(py_to<T>(item));
    }
    return out;
}

template <class T>
static inline rc<list<T>> obj_to_rc_list(const object& value, const char* ctx) {
    const list<object>* src = obj_to_list_ptr(value);
    if (src == nullptr) {
        return rc<list<T>>{};
    }
    return rc_list_from_value(py_copy_typed_list_from_object<T>(value, ctx));
}

template <class K, class V, class Q>
static inline V& py_at(dict<K, V>& d, const Q& key) {
    const K k = [&]() -> K {
        if constexpr (::std::is_same_v<Q, object>) {
            if constexpr (::std::is_same_v<K, object>) {
                return key;
            } else if constexpr (
                ::std::is_arithmetic_v<K>
                || ::std::is_same_v<K, bool>
                || ::std::is_same_v<K, str>) {
                return py_to<K>(key);
            } else {
                return K(key);
            }
        } else if constexpr (py_is_cstr_like<Q>::value) {
            return py_coerce_cstr_typed_value<K>(key);
        } else if constexpr (::std::is_same_v<K, Q>) {
            return key;
        } else if constexpr (::std::is_convertible_v<Q, K>) {
            return static_cast<K>(key);
        } else {
            return K(key);
        }
    }();
    auto it = d.find(k);
    if (it == d.end()) {
        throw ::std::out_of_range("dict key not found");
    }
    return it->second;
}

template <class K, class V, class Q>
static inline const V& py_at(const dict<K, V>& d, const Q& key) {
    const K k = [&]() -> K {
        if constexpr (::std::is_same_v<Q, object>) {
            if constexpr (::std::is_same_v<K, object>) {
                return key;
            } else if constexpr (
                ::std::is_arithmetic_v<K>
                || ::std::is_same_v<K, bool>
                || ::std::is_same_v<K, str>) {
                return py_to<K>(key);
            } else {
                return K(key);
            }
        } else if constexpr (py_is_cstr_like<Q>::value) {
            return py_coerce_cstr_typed_value<K>(key);
        } else if constexpr (::std::is_same_v<K, Q>) {
            return key;
        } else if constexpr (::std::is_convertible_v<Q, K>) {
            return static_cast<K>(key);
        } else {
            return K(key);
        }
    }();
    auto it = d.find(k);
    if (it == d.end()) {
        throw ::std::out_of_range("dict key not found");
    }
    return it->second;
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

template <class T> static inline bool py_is_dict(const T&) { return false; }
template <class T> static inline bool py_is_list(const T&) { return false; }
template <class T> static inline bool py_is_set(const T&) { return false; }
template <class T> static inline bool py_is_str(const T&) { return false; }
template <class T> static inline bool py_is_bool(const T&) { return false; }

template <class K, class V> static inline bool py_is_dict(const dict<K, V>&) { return true; }
template <class U> static inline bool py_is_list(const list<U>&) { return true; }
template <class U> static inline bool py_is_list(const rc<list<U>>&) { return true; }
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

// P0-contract-shrink label: shared_type_id_contract seam.
// type_id 判定ロジックは generated built_in 層（py_tid_*）を正本とする。
#include "runtime/cpp/generated/built_in/type_id.h"

static inline dict<uint32, uint32>& py_runtime_user_type_base_registry() {
    static dict<uint32, uint32> user_type_base{};
    return user_type_base;
}

static inline uint32& py_runtime_next_user_type_id() {
    static uint32 next_user_type_id = 1000;
    return next_user_type_id;
}

static inline uint32& py_runtime_synced_user_type_count() {
    static uint32 synced_user_type_count = 0;
    return synced_user_type_count;
}

static inline void py_sync_generated_user_type_registry() {
    auto& user_type_base = py_runtime_user_type_base_registry();
    if (user_type_base.empty()) {
        return;
    }
    auto& synced_user_type_count = py_runtime_synced_user_type_count();
    uint32 next_user_type_id = py_runtime_next_user_type_id();
    uint32 last_registered_tid = next_user_type_id - 1;
    bool needs_sync = synced_user_type_count != user_type_base.size();
    if (!needs_sync) {
        auto last_it = user_type_base.find(last_registered_tid);
        if (last_it != user_type_base.end()) {
            needs_sync = _TYPE_BASE.find(static_cast<int64>(last_registered_tid)) == _TYPE_BASE.end();
        }
    }
    if (!needs_sync) {
        return;
    }
    for (uint32 tid = 1000; tid < next_user_type_id; ++tid) {
        auto it = user_type_base.find(tid);
        if (it == user_type_base.end()) {
            continue;
        }
        py_tid_register_known_class_type(static_cast<int64>(tid), static_cast<int64>(it->second));
    }
    synced_user_type_count = static_cast<uint32>(user_type_base.size());
}

static inline uint32 py_register_class_type(uint32 base_type_id = PYTRA_TID_OBJECT) {
    // NOTE:
    // Avoid cross-TU static initialization order issues by keeping user type
    // registry in function-local statics (initialized on first use).
    auto& user_type_base = py_runtime_user_type_base_registry();
    uint32 tid = py_runtime_next_user_type_id();
    while (user_type_base.find(tid) != user_type_base.end()) {
        ++tid;
    }
    py_runtime_next_user_type_id() = tid + 1;
    user_type_base[tid] = base_type_id;
    return tid;
}

// Generated user classes share this exact type-id boilerplate.
// Keep it in runtime so backend output stays compact and consistent.
#define PYTRA_DECLARE_CLASS_TYPE(BASE_TYPE_ID_EXPR)                                                     \
    inline static uint32 PYTRA_TYPE_ID = py_register_class_type((BASE_TYPE_ID_EXPR));                   \
    uint32 py_type_id() const noexcept override {                                                        \
        return PYTRA_TYPE_ID;                                                                            \
}

static inline bool py_runtime_type_id_is_subtype(uint32 actual_type_id, uint32 expected_type_id) {
    py_sync_generated_user_type_registry();
    return py_tid_is_subtype(static_cast<int64>(actual_type_id), static_cast<int64>(expected_type_id));
}

static inline bool py_runtime_type_id_issubclass(uint32 actual_type_id, uint32 expected_type_id) {
    py_sync_generated_user_type_registry();
    return py_tid_issubclass(static_cast<int64>(actual_type_id), static_cast<int64>(expected_type_id));
}

static inline uint32 py_runtime_object_type_id(const object& v) {
    if (!v) {
        return PYTRA_TID_NONE;
    }
    uint32 out = v->type_id();
    if (out == 0) {
        return PYTRA_TID_OBJECT;
    }
    return out;
}

static inline bool py_runtime_object_isinstance(const object& value, uint32 expected_type_id) {
    if (!value) {
        return expected_type_id == PYTRA_TID_NONE;
    }
    py_sync_generated_user_type_registry();
    return py_tid_isinstance(value, static_cast<int64>(expected_type_id));
}

template <class T>
static inline uint32 py_runtime_value_type_id(const T& value) {
    return py_runtime_object_type_id(make_object(value));
}

template <class T>
static inline bool py_runtime_value_isinstance(const T& value, uint32 expected_type_id) {
    return py_runtime_object_isinstance(make_object(value), expected_type_id);
}

template <class T, ::std::enable_if_t<::std::is_arithmetic_v<T>, int> = 0>
static inline auto operator-(const rc<T>& v) -> decltype(v->__neg__()) {
    return v->__neg__();
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

#endif  // PYTRA_BUILT_IN_PY_RUNTIME_H
