#ifndef PYTRA_BUILT_IN_DICT_H
#define PYTRA_BUILT_IN_DICT_H

#include "container_common.h"

template <class K, class V>
class dict {
public:
    using base_type = ::std::unordered_map<K, V>;
    using iterator = typename base_type::iterator;
    using const_iterator = typename base_type::const_iterator;
    using value_type = typename base_type::value_type;

    dict() = default;
    dict(::std::initializer_list<value_type> init) : data_(init) {}
    template <class KK = K, class VV = V, ::std::enable_if_t<::std::is_same_v<KK, str> && ::std::is_same_v<VV, object>, int> = 0>
    dict(const object& v) : data_(obj_to_dict(v)) {}

    template <class It>
    dict(It first, It last) : data_(first, last) {}

    operator const base_type&() const { return data_; }  // NOLINT(google-explicit-constructor)
    operator base_type&() { return data_; }              // NOLINT(google-explicit-constructor)
    template <class KK = K, class VV = V, ::std::enable_if_t<::std::is_same_v<KK, str> && ::std::is_same_v<VV, object>, int> = 0>
    dict& operator=(const object& v) {
        data_ = obj_to_dict(v);
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
    void clear() { data_.clear(); }
    void update(const dict<K, V>& other) {
        for (const auto& kv : other) data_[kv.first] = kv.second;
    }
    void update(const base_type& other) {
        for (const auto& kv : other) data_[kv.first] = kv.second;
    }

    iterator find(const K& key) { return data_.find(key); }
    const_iterator find(const K& key) const { return data_.find(key); }
    ::std::size_t count(const K& key) const { return data_.count(key); }
    bool contains(const K& key) const { return data_.find(key) != data_.end(); }

    V& operator[](const K& key) { return data_[key]; }
    V& at(const K& key) { return data_.at(key); }
    const V& at(const K& key) const { return data_.at(key); }

    ::std::pair<iterator, bool> insert(const value_type& value) { return data_.insert(value); }
    ::std::pair<iterator, bool> insert(value_type&& value) { return data_.insert(::std::move(value)); }

    template <class P>
    ::std::pair<iterator, bool> insert(P&& value) {
        return data_.insert(::std::forward<P>(value));
    }

    template <class... Args>
    ::std::pair<iterator, bool> emplace(Args&&... args) {
        return data_.emplace(::std::forward<Args>(args)...);
    }

    ::std::size_t erase(const K& key) { return data_.erase(key); }
    iterator erase(iterator pos) { return data_.erase(pos); }
    iterator erase(iterator first, iterator last) { return data_.erase(first, last); }

    V get(const K& key) const {
        auto it = data_.find(key);
        if (it == data_.end()) {
            throw ::std::out_of_range("dict.get missing key");
        }
        return it->second;
    }

    V get(const K& key, const V& default_value) const {
        auto it = data_.find(key);
        if (it == data_.end()) {
            return default_value;
        }
        return it->second;
    }

    list<K> keys() const {
        list<K> out{};
        out.reserve(data_.size());
        for (const auto& kv : data_) out.push_back(kv.first);
        return out;
    }

    list<V> values() const {
        list<V> out{};
        out.reserve(data_.size());
        for (const auto& kv : data_) out.push_back(kv.second);
        return out;
    }

    list<::std::tuple<K, V>> items() const {
        list<::std::tuple<K, V>> out{};
        out.reserve(data_.size());
        for (const auto& kv : data_) out.push_back(::std::make_tuple(kv.first, kv.second));
        return out;
    }

private:
    base_type data_;
};


#endif  // PYTRA_BUILT_IN_DICT_H
