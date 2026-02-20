#ifndef PYTRA_BUILT_IN_LIST_H
#define PYTRA_BUILT_IN_LIST_H

#include "container_common.h"

template <class T>
class list {
public:
    using value_type = T;
    using iterator = typename ::std::vector<T>::iterator;
    using const_iterator = typename ::std::vector<T>::const_iterator;

    list() = default;
    list(::std::initializer_list<T> init) : data_(init) {}
    explicit list(::std::size_t count) : data_(count) {}
    list(::std::size_t count, const T& value) : data_(count, value) {}
    template <class U = T, ::std::enable_if_t<::std::is_same_v<U, uint8>, int> = 0>
    list(const char* s) {
        if (s == nullptr) return;
        const unsigned char* p = reinterpret_cast<const unsigned char*>(s);
        while (*p != 0) {
            data_.push_back(static_cast<uint8>(*p));
            ++p;
        }
    }
    template <class U = T, ::std::enable_if_t<::std::is_same_v<U, uint8>, int> = 0>
    list(const str& s) {
        for (char ch : s) {
            data_.push_back(static_cast<uint8>(static_cast<unsigned char>(ch)));
        }
    }
    template <class U = T, ::std::enable_if_t<::std::is_same_v<U, object>, int> = 0>
    list(const object& v) {
        if (const auto* p = obj_to_list_ptr(v)) data_ = *p;
    }
    template <class U = T, ::std::enable_if_t<!::std::is_same_v<U, object>, int> = 0>
    list(const object& v) {
        if (const auto* p = obj_to_list_ptr(v)) {
            reserve(p->size());
            for (const object& elem : *p) {
                if constexpr (::std::is_constructible_v<T, object>) {
                    data_.push_back(T(elem));
                } else {
                    auto casted = py_object_try_cast<T>(elem);
                    if (casted.has_value()) data_.push_back(*casted);
                }
            }
        }
    }

    template <class It>
    list(It first, It last) : data_(first, last) {}

    template <class U, ::std::enable_if_t<!::std::is_same_v<U, T>, int> = 0>
    list(const list<U>& other) {
        reserve(other.size());
        for (const auto& v : other) {
            if constexpr (::std::is_same_v<U, object>) {
                if constexpr (::std::is_constructible_v<T, object>) {
                    data_.push_back(T(v));
                } else {
                    auto casted = py_object_try_cast<T>(v);
                    if (casted.has_value()) data_.push_back(*casted);
                }
            } else {
                data_.push_back(static_cast<T>(v));
            }
        }
    }

    operator const ::std::vector<T>&() const { return data_; }  // NOLINT(google-explicit-constructor)
    operator ::std::vector<T>&() { return data_; }              // NOLINT(google-explicit-constructor)
    template <class U = T, ::std::enable_if_t<::std::is_same_v<U, object>, int> = 0>
    list& operator=(const object& v) {
        if (const auto* p = obj_to_list_ptr(v)) data_ = *p;
        else data_.clear();
        return *this;
    }

    iterator begin() { return data_.begin(); }
    iterator end() { return data_.end(); }
    const_iterator begin() const { return data_.begin(); }
    const_iterator end() const { return data_.end(); }
    const_iterator cbegin() const { return data_.cbegin(); }
    const_iterator cend() const { return data_.cend(); }

    ::std::size_t size() const { return data_.size(); }
    bool empty() const { return data_.empty(); }
    void reserve(::std::size_t n) { data_.reserve(n); }
    void clear() { data_.clear(); }
    void resize(::std::size_t n) { data_.resize(n); }
    void resize(::std::size_t n, const T& value) { data_.resize(n, value); }

    T& operator[](::std::size_t i) { return data_[i]; }
    const T& operator[](::std::size_t i) const { return data_[i]; }
    T& at(::std::size_t i) { return data_.at(i); }
    const T& at(::std::size_t i) const { return data_.at(i); }
    T& front() { return data_.front(); }
    const T& front() const { return data_.front(); }
    T& back() { return data_.back(); }
    const T& back() const { return data_.back(); }

    void push_back(const T& value) { data_.push_back(value); }
    void push_back(T&& value) { data_.push_back(::std::move(value)); }

    template <class... Args>
    T& emplace_back(Args&&... args) {
        return data_.emplace_back(::std::forward<Args>(args)...);
    }

    iterator insert(iterator pos, const T& value) { return data_.insert(pos, value); }
    iterator insert(iterator pos, T&& value) { return data_.insert(pos, ::std::move(value)); }

    template <class It>
    iterator insert(iterator pos, It first, It last) {
        return data_.insert(pos, first, last);
    }

    iterator erase(iterator pos) { return data_.erase(pos); }
    iterator erase(iterator first, iterator last) { return data_.erase(first, last); }
    void pop_back() { data_.pop_back(); }

    void append(const T& value) { data_.push_back(value); }
    void append(T&& value) { data_.push_back(::std::move(value)); }
    template <
        class A,
        class U = T,
        ::std::enable_if_t<!::std::is_same_v<U, ::std::any> && ::std::is_same_v<::std::decay_t<A>, ::std::any>, int> = 0>
    void append(A&& value) {
        const ::std::any& any_value = value;
        if (const auto* p = ::std::any_cast<U>(&any_value)) {
            data_.push_back(*p);
        }
    }

    template <class U>
    void extend(const U& values) {
        for (const auto& value : values) {
            data_.push_back(static_cast<T>(value));
        }
    }

    T pop() {
        if (data_.empty()) {
            throw ::std::out_of_range("pop from empty list");
        }
        T out = data_.back();
        data_.pop_back();
        return out;
    }

    T pop(int64 idx) {
        if (data_.empty()) {
            throw ::std::out_of_range("pop from empty list");
        }
        if (idx < 0) idx += static_cast<int64>(data_.size());
        if (idx < 0 || idx >= static_cast<int64>(data_.size())) {
            throw ::std::out_of_range("pop index out of range");
        }
        T out = data_[static_cast<::std::size_t>(idx)];
        data_.erase(data_.begin() + idx);
        return out;
    }

private:
    ::std::vector<T> data_;
};

using bytearray = list<uint8>;
using bytes = bytearray;

static inline bytes operator+(const bytes& lhs, const bytes& rhs) {
    bytes out = lhs;
    out.extend(rhs);
    return out;
}

static inline bytes operator+(const bytes& lhs, const char* rhs) {
    bytes out = lhs;
    out.extend(bytes(rhs));
    return out;
}

static inline bytes operator+(const char* lhs, const bytes& rhs) {
    bytes out = bytes(lhs);
    out.extend(rhs);
    return out;
}

template <::std::size_t N>
static inline bytes py_bytes_lit(const char (&s)[N]) {
    bytes out{};
    out.reserve(N - 1);
    ::std::size_t i = 0;
    while (i + 1 <= N - 1) {
        out.append(static_cast<uint8>(static_cast<unsigned char>(s[i])));
        i++;
    }
    return out;
}

static inline bytes py_int_to_bytes(int64 value, int64 length, const str& byteorder) {
    auto raw = pytra::runtime::cpp::base::int_to_bytes(value, length, static_cast<::std::string>(byteorder));
    return bytes(raw.begin(), raw.end());
}


#endif  // PYTRA_BUILT_IN_LIST_H
