#ifndef PYCS_GC_H
#define PYCS_GC_H

#include <atomic>
#include <cassert>
#include <cstdint>
#include <type_traits>
#include <utility>

namespace pycs::gc {

class PyObj {
public:
    explicit PyObj(uint32_t type_id = 0) : ref_count_(1), type_id_(type_id) {}
    PyObj(const PyObj&) = delete;
    PyObj& operator=(const PyObj&) = delete;

    virtual ~PyObj() = default;

    uint32_t ref_count() const noexcept {
        return ref_count_.load(std::memory_order_acquire);
    }

    uint32_t type_id() const noexcept {
        return type_id_;
    }

    virtual void rc_release_refs();

private:
    friend void incref(PyObj* obj) noexcept;
    friend void decref(PyObj* obj) noexcept;

    std::atomic<uint32_t> ref_count_;
    uint32_t type_id_;
};

void incref(PyObj* obj) noexcept;
void decref(PyObj* obj) noexcept;

template <class T, class... Args>
T* rc_new(Args&&... args) {
    static_assert(std::is_base_of_v<PyObj, T>, "T must derive from PyObj");
    return new T(std::forward<Args>(args)...);
}

template <class T>
class RcHandle {
public:
    RcHandle() = default;

    explicit RcHandle(T* ptr, bool add_ref = true) : ptr_(ptr) {
        static_assert(std::is_base_of_v<PyObj, T>, "T must derive from PyObj");
        if (ptr_ != nullptr && add_ref) {
            incref(ptr_);
        }
    }

    static RcHandle<T> adopt(T* ptr) {
        RcHandle<T> h;
        h.ptr_ = ptr;
        return h;
    }

    RcHandle(const RcHandle& other) : ptr_(other.ptr_) {
        if (ptr_ != nullptr) {
            incref(ptr_);
        }
    }

    RcHandle(RcHandle&& other) noexcept : ptr_(other.ptr_) {
        other.ptr_ = nullptr;
    }

    RcHandle& operator=(const RcHandle& other) {
        if (this == &other) {
            return *this;
        }
        reset(other.ptr_);
        return *this;
    }

    RcHandle& operator=(RcHandle&& other) noexcept {
        if (this == &other) {
            return *this;
        }
        if (ptr_ != nullptr) {
            decref(ptr_);
        }
        ptr_ = other.ptr_;
        other.ptr_ = nullptr;
        return *this;
    }

    ~RcHandle() {
        if (ptr_ != nullptr) {
            decref(ptr_);
            ptr_ = nullptr;
        }
    }

    void reset(T* ptr = nullptr, bool add_ref = true) {
        if (ptr != nullptr && add_ref) {
            incref(ptr);
        }
        if (ptr_ != nullptr) {
            decref(ptr_);
        }
        ptr_ = ptr;
    }

    T* release() noexcept {
        T* out = ptr_;
        ptr_ = nullptr;
        return out;
    }

    T* get() const noexcept { return ptr_; }
    T& operator*() const noexcept { return *ptr_; }
    T* operator->() const noexcept { return ptr_; }
    explicit operator bool() const noexcept { return ptr_ != nullptr; }

private:
    T* ptr_ = nullptr;
};

}  // namespace pycs::gc

#endif  // PYCS_GC_H
