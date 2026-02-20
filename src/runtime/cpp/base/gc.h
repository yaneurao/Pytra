// このファイルは `src/gc.h` のテスト/実装コードです。
// 読み手が責務を把握しやすいように、日本語コメントを追記しています。
// 変更時は、スレッド安全性と参照カウント整合性を必ず確認してください。

#ifndef PYTRA_GC_H
#define PYTRA_GC_H

#include <atomic>
#include <cassert>
#include <cstdint>
#include <type_traits>
#include <utility>

namespace pytra::gc {

/**
 * @brief RC（参照カウント）管理対象の基底クラスです。
 *
 * すべての参照型オブジェクトはこの型を継承し、ref_count を通じて
 * 生存期間を管理します。
 */
class PyObj {
public:
    explicit PyObj(uint32_t type_id = 0) : ref_count_(1), type_id_(type_id) {}
    PyObj(const PyObj&) = delete;
    PyObj& operator=(const PyObj&) = delete;

    virtual ~PyObj() = default;

    uint32_t ref_count() const noexcept {
        return ref_count_.load(::std::memory_order_acquire);
    }

    uint32_t type_id() const noexcept {
        return type_id_;
    }

    /**
     * @brief 破棄直前に子参照を解放するためのフックです。
     *
     * 参照型メンバーを持つ派生クラスは、この関数で decref を実行します。
     */
    virtual void rc_release_refs();

private:
    friend void incref(PyObj* obj) noexcept;
    friend void decref(PyObj* obj) noexcept;

    ::std::atomic<uint32_t> ref_count_;
    uint32_t type_id_;
};

void incref(PyObj* obj) noexcept;
void decref(PyObj* obj) noexcept;

/**
 * @brief RC管理オブジェクトを生成します。
 *
 * @tparam T 生成するクラス（PyObj 継承必須）
 * @tparam Args コンストラクタ引数型
 * @param args T のコンストラクタへ渡す引数
 * @return T* 生成したオブジェクト（初期 ref_count=1）
 */
template <class T, class... Args>
T* rc_new(Args&&... args) {
    static_assert(::std::is_base_of_v<PyObj, T>, "T must derive from PyObj");
    return new T(::std::forward<Args>(args)...);
}

template <class T>
class RcHandle {
public:
    RcHandle() = default;

    explicit RcHandle(T* ptr, bool add_ref = true) : ptr_(ptr) {
        static_assert(::std::is_base_of_v<PyObj, T>, "T must derive from PyObj");
        if (ptr_ != nullptr && add_ref) {
            incref(ptr_);
        }
    }

    /**
     * @brief rc_new 直後の裸ポインタをそのまま所有するファクトリです。
     * @param ptr 所有開始するポインタ（追加 incref しない）
     */
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

    /**
     * @brief 保持対象を差し替えます。
     *
     * @param ptr 新たに保持するポインタ
     * @param add_ref true の場合、差し替え前に incref します
     */
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

}  // namespace pytra::gc

#endif  // PYTRA_GC_H
