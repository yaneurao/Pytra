#ifndef PYTRA_CORE_OBJECT_H
#define PYTRA_CORE_OBJECT_H

// Object<T> — ControlBlock + templated view.
// See docs/ja/spec/spec-object.md for design rationale.

#include <cstdint>
#include <cassert>
#include <iostream>
#include <optional>
#include <type_traits>
#include <utility>
#include "core/py_scalar_types.h"

// Forward declarations for POD boxing constructors.
class str;

// =============================
// TypeInfo (interval subtype)
// =============================

struct TypeInfo {
    uint32_t id;
    uint32_t entry;
    uint32_t exit;
    void (*deleter)(void*);
};

template<typename T>
void deleter_impl(void* p);

// =============================
// ControlBlock
// =============================

struct ControlBlock {
    int rc;
    uint32_t type_id;  // 実体型 — cast しても変わらない
    void* base_ptr;    // 常に最も派生型のポインタ
    void (*deleter)(void*);
};

// =============================
// Object<T>
// =============================

template<typename T>
struct Object {
    ControlBlock* cb;
    T* ptr;

    Object() : cb(nullptr), ptr(nullptr) {}

    Object(ControlBlock* cb_, T* ptr_)
        : cb(cb_), ptr(ptr_) {
        retain();
    }

    Object(const Object& other)
        : cb(other.cb), ptr(other.ptr) {
        retain();
    }

    Object(Object&& other) noexcept
        : cb(other.cb), ptr(other.ptr) {
        other.cb = nullptr;
        other.ptr = nullptr;
    }

    // Upcast: Object<Derived> → Object<Base>
    template<typename U, typename = ::std::enable_if_t<::std::is_base_of_v<T, U>>>
    Object(const Object<U>& other)
        : cb(other.cb), ptr(static_cast<T*>(other.ptr)) {
        retain();
    }

    ~Object() {
        release();
    }

    Object& operator=(const Object& other) {
        if (this != &other) {
            release();
            cb = other.cb;
            ptr = other.ptr;
            retain();
        }
        return *this;
    }

    Object& operator=(Object&& other) noexcept {
        if (this != &other) {
            release();
            cb = other.cb;
            ptr = other.ptr;
            other.cb = nullptr;
            other.ptr = nullptr;
        }
        return *this;
    }

    // Access
    T& operator*() const { return *ptr; }
    T* operator->() const { return ptr; }
    operator T&() const { return *ptr; }  // implicit conversion to T&
    explicit operator bool() const { return cb != nullptr && ptr != nullptr; }

    template<typename U>
    Object<U> as() const {
        if (!cb) return Object<U>();
        return Object<U>(cb, static_cast<U*>(cb->base_ptr));
    }

    template<typename K, typename P = T>
    auto get(const K& key) const -> decltype(std::declval<const P&>().get(key)) { return ptr->get(key); }

    template<typename K, typename D, typename P = T>
    auto get(const K& key, const D& fallback) const -> decltype(std::declval<const P&>().get(key, fallback)) { return ptr->get(key, fallback); }

    template<typename K, typename P = T>
    auto operator[](const K& key) -> decltype(std::declval<P&>()[key]) { return (*ptr)[key]; }

    template<typename K, typename P = T>
    auto operator[](const K& key) const -> decltype(std::declval<const P&>().at(key)) { return (*ptr).at(key); }

    template<typename V, typename P = T>
    auto append(V&& value) -> decltype(std::declval<P&>().append(std::forward<V>(value))) { return ptr->append(std::forward<V>(value)); }

    template<typename P = T>
    auto keys() const -> decltype(std::declval<const P&>().keys()) { return ptr->keys(); }
    template<typename P = T>
    auto values() const -> decltype(std::declval<const P&>().values()) { return ptr->values(); }
    template<typename P = T>
    auto items() const -> decltype(std::declval<const P&>().items()) { return ptr->items(); }

    // Type queries
    uint32_t type_id() const { return cb ? cb->type_id : 0; }

    bool is(uint32_t expected) const { return cb && cb->type_id == expected; }
    bool isinstance(const TypeInfo* base) const {
        return cb && base->entry <= cb->type_id && cb->type_id < base->exit;
    }

    // Downcast: Object<Base> → Object<Derived>*
    // Returns nullptr if type mismatch.
    template<typename U>
    Object<U> downcast(const TypeInfo* target) const {
        if (!cb || !isinstance(target)) return Object<U>();
        return Object<U>(cb, static_cast<U*>(cb->base_ptr));
    }

private:
    void retain() {
        if (cb) ++cb->rc;
    }

    void release() {
        if (!cb) return;
        if (--cb->rc == 0) {
            if (cb->deleter) {
                cb->deleter(cb->base_ptr);
            }
            delete cb;
        }
        cb = nullptr;
        ptr = nullptr;
    }
};

// =============================
// Object<void> — type-erased view (replaces old `object`)
// =============================

template<>
struct Object<void> {
    ControlBlock* cb;

    Object() : cb(nullptr) {}
    Object(::std::nullopt_t) : cb(nullptr) {}  // None

    Object(ControlBlock* cb_) : cb(cb_) { retain(); }

    // From any Object<T>
    template<typename T>
    Object(const Object<T>& other) : cb(other.cb) { retain(); }

    Object(const Object& other) : cb(other.cb) { retain(); }
    Object(Object&& other) noexcept : cb(other.cb) { other.cb = nullptr; }

    // POD boxing constructors (defined after str/list/dict are complete)
    Object(int64 v);
    Object(int v);
    Object(const char* v);
    Object(float64 v);
    Object(bool v);
    Object(const str& v);
    Object(::std::size_t v);  // avoid ambiguity with int64/bool
    // vector<bool>::reference is a proxy type, not bool
    template<typename T, typename = ::std::enable_if_t<::std::is_convertible_v<T, bool> && !::std::is_same_v<::std::decay_t<T>, bool> && !::std::is_integral_v<::std::decay_t<T>>>>
    Object(T v) : Object(static_cast<bool>(v)) {}

    ~Object() { release(); }

    Object& operator=(const Object& other) {
        if (this != &other) { release(); cb = other.cb; retain(); }
        return *this;
    }
    Object& operator=(Object&& other) noexcept {
        if (this != &other) { release(); cb = other.cb; other.cb = nullptr; }
        return *this;
    }

    explicit operator bool() const { return cb != nullptr; }
    uint32_t type_id() const { return cb ? cb->type_id : 0; }
    bool is(uint32_t expected) const { return cb && cb->type_id == expected; }
    bool isinstance(const TypeInfo* base) const {
        return cb && base->entry <= cb->type_id && cb->type_id < base->exit;
    }

    // Downcast to typed Object
    template<typename T>
    Object<T> as() const {
        if (!cb) return Object<T>();
        return Object<T>(cb, static_cast<T*>(cb->base_ptr));
    }

    // Access base_ptr
    void* get() const { return cb ? cb->base_ptr : nullptr; }

    // Unbox a POD value from Object<void> — defined after PyBoxedValue in py_types.h
    template<typename T>
    const T& unbox() const;

private:
    void retain() { if (cb) ++cb->rc; }
    void release() {
        if (!cb) return;
        if (--cb->rc == 0) {
            if (cb->deleter) cb->deleter(cb->base_ptr);
            delete cb;
        }
        cb = nullptr;
    }
};

// Comparison operators for Object<void>
inline bool operator==(const Object<void>& a, const Object<void>& b) {
    if (!a && !b) return true;
    if (!a || !b) return false;
    // Same ControlBlock = same object
    return a.cb == b.cb;
}

inline bool operator!=(const Object<void>& a, const Object<void>& b) {
    return !(a == b);
}

// `object` is now an alias for Object<void>
using object = Object<void>;

// =============================
// make_object
// =============================

template<typename T, typename... Args>
Object<T> make_object(uint32_t tid, Args&&... args) {
    T* obj = new T(::std::forward<Args>(args)...);
    ControlBlock* cb = new ControlBlock{0, tid, obj, &deleter_impl<T>};  // retain() in Object ctor will set to 1
    return Object<T>(cb, obj);
}

// =============================
// upcast (explicit)
// =============================

template<typename To, typename From>
Object<To> upcast(const Object<From>& from) {
    To* new_ptr = static_cast<To*>(from.ptr);
    return Object<To>(from.cb, new_ptr);
}

template<typename T>
auto begin(Object<T>& value) -> decltype((*value).begin()) {
    return (*value).begin();
}

template<typename T>
auto begin(const Object<T>& value) -> decltype((*value).begin()) {
    return (*value).begin();
}

template<typename T>
auto end(Object<T>& value) -> decltype((*value).end()) {
    return (*value).end();
}

template<typename T>
auto end(const Object<T>& value) -> decltype((*value).end()) {
    return (*value).end();
}

// =============================
// is_subtype
// =============================

inline bool is_subtype(uint32_t t, const TypeInfo* base) {
    return base->entry <= t && t < base->exit;
}

// =============================
// deleter template
// =============================

template<typename T>
void deleter_impl(void* p) {
    delete static_cast<T*>(p);
}

#endif  // PYTRA_CORE_OBJECT_H
