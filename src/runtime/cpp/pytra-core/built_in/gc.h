// このファイルは `src/gc.h` のテスト/実装コードです。
// 読み手が責務を把握しやすいように、日本語コメントを追記しています。
// 変更時は、スレッド安全性と参照カウント整合性を必ず確認してください。

#ifndef PYTRA_BUILT_IN_GC_H
#define PYTRA_BUILT_IN_GC_H

#include <atomic>
#include <cassert>
#include <cstdint>
#include <optional>
#include <stdexcept>
#include <string>
#include <type_traits>
#include <utility>

namespace pytra::gc {

template <class T>
class RcHandle;
class PyObj;
using object = RcHandle<PyObj>;

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

    virtual uint32_t py_type_id() const noexcept {
        return type_id_;
    }

    uint32_t type_id() const noexcept {
        return py_type_id();
    }

    /**
     * @brief 破棄直前に子参照を解放するためのフックです。
     *
     * 参照型メンバーを持つ派生クラスは、この関数で decref を実行します。
     */
    virtual void rc_release_refs();

    /**
     * @brief truthiness 判定フック。
     *
     * 既定値は Python object と同様に truthy（true）とする。
     */
    virtual bool py_truthy() const {
        return true;
    }

    /**
     * @brief `len(...)` 相当の長さ問い合わせフック。
     *
     * 長さを持たない型は `std::nullopt` を返す。
     */
    virtual ::std::optional<::std::int64_t> py_try_len() const {
        return ::std::nullopt;
    }

    /**
     * @brief `iter(obj)` 相当のフック。
     *
     * 既定実装は non-iterable として `std::runtime_error` を送出する。
     */
    virtual object py_iter_or_raise() const;

    /**
     * @brief `next(it)` 相当のフック。
     *
     * 次要素がある場合は `object`、終端時は `std::nullopt` を返す。
     * 既定実装は non-iterator として `std::runtime_error` を送出する。
     */
    virtual ::std::optional<object> py_next_or_stop();

    /**
     * @brief 文字列表現フック。
     *
     * 既定値は汎用 object 表現を返す。
     */
    virtual ::std::string py_str() const {
        return "<object>";
    }

    /**
     * @brief C++ 側の virtual 型判定フック。
     *
     * 既定では自身の type_id と一致する場合のみ true。
     */
    virtual bool py_isinstance_of(uint32_t expected_type_id) const {
        return py_type_id() == expected_type_id;
    }

protected:
    void set_type_id(uint32_t type_id) noexcept {
        type_id_ = type_id;
    }

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
    template <class U>
    using EnableUpcast = ::std::enable_if_t<
        ::std::is_base_of_v<PyObj, U> &&
        ::std::is_convertible_v<U*, T*> &&
        !::std::is_same_v<U, T>,
        int>;

    RcHandle() = default;

    explicit RcHandle(T* ptr, bool add_ref = true) : ptr_(ptr) {
        static_assert(::std::is_base_of_v<PyObj, T>, "T must derive from PyObj");
        if (ptr_ != nullptr && add_ref) {
            incref(reinterpret_cast<PyObj*>(ptr_));
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
            incref(reinterpret_cast<PyObj*>(ptr_));
        }
    }

    RcHandle(RcHandle&& other) noexcept : ptr_(other.ptr_) {
        other.ptr_ = nullptr;
    }

    template <class U, EnableUpcast<U> = 0>
    RcHandle(const RcHandle<U>& other) : ptr_(static_cast<T*>(other.get())) {
        if (ptr_ != nullptr) {
            incref(reinterpret_cast<PyObj*>(ptr_));
        }
    }

    template <class U, EnableUpcast<U> = 0>
    RcHandle(RcHandle<U>&& other) noexcept : ptr_(static_cast<T*>(other.release())) {}

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
            decref(reinterpret_cast<PyObj*>(ptr_));
        }
        ptr_ = other.ptr_;
        other.ptr_ = nullptr;
        return *this;
    }

    template <class U, EnableUpcast<U> = 0>
    RcHandle& operator=(const RcHandle<U>& other) {
        reset(static_cast<T*>(other.get()));
        return *this;
    }

    template <class U, EnableUpcast<U> = 0>
    RcHandle& operator=(RcHandle<U>&& other) noexcept {
        if (ptr_ != nullptr) {
            decref(reinterpret_cast<PyObj*>(ptr_));
        }
        ptr_ = static_cast<T*>(other.release());
        return *this;
    }

    ~RcHandle() {
        if (ptr_ != nullptr) {
            decref(reinterpret_cast<PyObj*>(ptr_));
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
            incref(reinterpret_cast<PyObj*>(ptr));
        }
        if (ptr_ != nullptr) {
            decref(reinterpret_cast<PyObj*>(ptr_));
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
    bool operator==(const RcHandle& other) const noexcept { return ptr_ == other.ptr_; }
    bool operator!=(const RcHandle& other) const noexcept { return ptr_ != other.ptr_; }

private:
    T* ptr_ = nullptr;
};

inline object PyObj::py_iter_or_raise() const {
    throw ::std::runtime_error("object is not iterable");
}

inline ::std::optional<object> PyObj::py_next_or_stop() {
    throw ::std::runtime_error("object is not an iterator");
}

}  // namespace pytra::gc

#endif  // PYTRA_BUILT_IN_GC_H
