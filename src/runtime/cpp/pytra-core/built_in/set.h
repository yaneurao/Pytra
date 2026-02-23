#ifndef PYTRA_BUILT_IN_SET_H
#define PYTRA_BUILT_IN_SET_H

#include "container_common.h"

template <class T>
class set {
public:
    using base_type = ::std::unordered_set<T>;
    using iterator = typename base_type::iterator;
    using const_iterator = typename base_type::const_iterator;
    using value_type = typename base_type::value_type;

    set() = default;
    set(::std::initializer_list<value_type> init) : data_(init) {}

    template <class It>
    set(It first, It last) : data_(first, last) {}

    operator const base_type&() const { return data_; }  // NOLINT(google-explicit-constructor)
    operator base_type&() { return data_; }              // NOLINT(google-explicit-constructor)

    iterator begin() { return data_.begin(); }
    iterator end() { return data_.end(); }
    const_iterator begin() const { return data_.begin(); }
    const_iterator end() const { return data_.end(); }
    const_iterator cbegin() const { return data_.cbegin(); }
    const_iterator cend() const { return data_.cend(); }

    ::std::size_t size() const { return data_.size(); }
    bool empty() const { return data_.empty(); }
    void clear() { data_.clear(); }

    ::std::size_t count(const T& value) const { return data_.count(value); }
    ::std::pair<iterator, bool> insert(const T& value) { return data_.insert(value); }
    ::std::pair<iterator, bool> insert(T&& value) { return data_.insert(::std::move(value)); }
    ::std::size_t erase(const T& value) { return data_.erase(value); }
    iterator find(const T& value) { return data_.find(value); }
    const_iterator find(const T& value) const { return data_.find(value); }

    void add(const T& value) { data_.insert(value); }

    void discard(const T& value) { data_.erase(value); }

    void remove(const T& value) {
        if (data_.erase(value) == 0) {
            throw ::std::out_of_range("set.remove missing value");
        }
    }

private:
    base_type data_;
};

#endif  // PYTRA_BUILT_IN_SET_H
