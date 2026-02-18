#ifndef PYTRA_RUNTIME_CPP_BASE_CONTAINERS_H
#define PYTRA_RUNTIME_CPP_BASE_CONTAINERS_H

// py_runtime.h から分離した Python 互換コンテナ/文字列ラッパ。
// このヘッダは py_runtime.h 側で定義される型エイリアス・前方宣言を利用します。

class str {
public:
    using iterator = std::string::iterator;
    using const_iterator = std::string::const_iterator;
    static constexpr std::size_t npos = std::string::npos;

    str() = default;
    str(const char* s) : data_(s == nullptr ? "" : s) {}
    str(const std::string& s) : data_(s) {}
    str(std::string&& s) : data_(std::move(s)) {}
    str(std::size_t count, char ch) : data_(count, ch) {}
    str(char c) : data_(1, c) {}
    str(const object& v) : data_(obj_to_str(v).std()) {}

    str& operator=(const char* s) {
        data_ = (s == nullptr ? "" : s);
        return *this;
    }
    str& operator=(const object& v) {
        data_ = obj_to_str(v).std();
        return *this;
    }

    operator const std::string&() const { return data_; }  // NOLINT(google-explicit-constructor)
    operator std::string&() { return data_; }              // NOLINT(google-explicit-constructor)

    const std::string& std() const { return data_; }
    std::string& std() { return data_; }

    iterator begin() { return data_.begin(); }
    iterator end() { return data_.end(); }
    const_iterator begin() const { return data_.begin(); }
    const_iterator end() const { return data_.end(); }
    const_iterator cbegin() const { return data_.cbegin(); }
    const_iterator cend() const { return data_.cend(); }

    std::size_t size() const { return data_.size(); }
    bool empty() const { return data_.empty(); }
    void clear() { data_.clear(); }
    void reserve(std::size_t n) { data_.reserve(n); }
    const char* c_str() const { return data_.c_str(); }

    str& operator+=(const str& rhs) {
        data_ += rhs.data_;
        return *this;
    }

    str& operator+=(const std::string& rhs) {
        data_ += rhs;
        return *this;
    }

    str& operator+=(const char* rhs) {
        data_ += rhs;
        return *this;
    }

    str& operator+=(char ch) {
        data_ += ch;
        return *this;
    }

    str operator[](int64 idx) const {
        int64 n = static_cast<int64>(data_.size());
        if (idx < 0) idx += n;
        if (idx < 0 || idx >= n) {
            throw std::out_of_range("string index out of range");
        }
        return str(1, data_[static_cast<std::size_t>(idx)]);
    }

    char at(int64 idx) const {
        int64 n = static_cast<int64>(data_.size());
        if (idx < 0) idx += n;
        if (idx < 0 || idx >= n) {
            throw std::out_of_range("string index out of range");
        }
        return data_.at(static_cast<std::size_t>(idx));
    }

    str substr(std::size_t pos, std::size_t count = std::string::npos) const {
        return str(data_.substr(pos, count));
    }

    std::size_t find(const str& needle, std::size_t pos = 0) const {
        return data_.find(needle.data_, pos);
    }

    std::size_t find(const char* needle, std::size_t pos = 0) const {
        return data_.find(needle, pos);
    }

    std::size_t find(char needle, std::size_t pos = 0) const {
        return data_.find(needle, pos);
    }

    std::size_t rfind(const str& needle, std::size_t pos = std::string::npos) const {
        return data_.rfind(needle.data_, pos);
    }

    std::size_t rfind(const char* needle, std::size_t pos = std::string::npos) const {
        return data_.rfind(needle, pos);
    }

    int compare(const str& other) const { return data_.compare(other.data_); }

    int compare(std::size_t pos, std::size_t count, const str& other) const {
        return data_.compare(pos, count, other.data_);
    }

    str& replace(std::size_t pos, std::size_t count, const str& replacement) {
        data_.replace(pos, count, replacement.data_);
        return *this;
    }

    std::size_t find_last_of(char ch, std::size_t pos = std::string::npos) const {
        return data_.find_last_of(ch, pos);
    }

    std::size_t find_last_of(const str& chars, std::size_t pos = std::string::npos) const {
        return data_.find_last_of(chars.data_, pos);
    }

    std::size_t find_last_of(const char* chars, std::size_t pos = std::string::npos) const {
        return data_.find_last_of(chars, pos);
    }

    friend std::ostream& operator<<(std::ostream& os, const str& s) {
        os << s.data_;
        return os;
    }

    friend str operator+(const str& lhs, const str& rhs) { return str(lhs.data_ + rhs.data_); }
    friend str operator+(const str& lhs, const std::string& rhs) { return str(lhs.data_ + rhs); }
    friend str operator+(const std::string& lhs, const str& rhs) { return str(lhs + rhs.data_); }
    friend str operator+(const str& lhs, const char* rhs) { return str(lhs.data_ + std::string(rhs)); }
    friend str operator+(const char* lhs, const str& rhs) { return str(std::string(lhs) + rhs.data_); }
    friend str operator+(const str& lhs, char rhs) { return str(lhs.data_ + rhs); }
    friend str operator+(char lhs, const str& rhs) { return str(std::string(1, lhs) + rhs.data_); }

    friend bool operator==(const str& lhs, const str& rhs) { return lhs.data_ == rhs.data_; }
    friend bool operator==(const str& lhs, const char* rhs) { return lhs.data_ == rhs; }
    friend bool operator==(const char* lhs, const str& rhs) { return lhs == rhs.data_; }
    friend bool operator!=(const str& lhs, const str& rhs) { return !(lhs == rhs); }
    friend bool operator!=(const str& lhs, const char* rhs) { return !(lhs == rhs); }
    friend bool operator!=(const char* lhs, const str& rhs) { return !(lhs == rhs); }
    friend bool operator<(const str& lhs, const str& rhs) { return lhs.data_ < rhs.data_; }
    friend bool operator<=(const str& lhs, const str& rhs) { return lhs.data_ <= rhs.data_; }
    friend bool operator>(const str& lhs, const str& rhs) { return lhs.data_ > rhs.data_; }
    friend bool operator>=(const str& lhs, const str& rhs) { return lhs.data_ >= rhs.data_; }

private:
    std::string data_;
};

static inline pytra::runtime::cpp::base::PyFile open(const str& path, const str& mode) {
    return pytra::runtime::cpp::base::open(static_cast<std::string>(path), static_cast<std::string>(mode));
}

namespace std {
template <>
struct hash<str> {
    std::size_t operator()(const str& s) const noexcept {
        return std::hash<std::string>{}(s.std());
    }
};
}  // namespace std

class Path {
public:
    Path() = default;
    Path(const char* s) : p_(s) {}
    Path(const str& s) : p_(std::string(s)) {}
    Path(const std::filesystem::path& p) : p_(p) {}

    Path operator/(const char* rhs) const { return Path(p_ / rhs); }
    Path operator/(const str& rhs) const { return Path(p_ / std::filesystem::path(std::string(rhs))); }
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
class list {
public:
    using value_type = T;
    using iterator = typename std::vector<T>::iterator;
    using const_iterator = typename std::vector<T>::const_iterator;

    list() = default;
    list(std::initializer_list<T> init) : data_(init) {}
    explicit list(std::size_t count) : data_(count) {}
    list(std::size_t count, const T& value) : data_(count, value) {}
    template <class U = T, std::enable_if_t<std::is_same_v<U, object>, int> = 0>
    list(const object& v) {
        if (const auto* p = obj_to_list_ptr(v)) data_ = *p;
    }

    template <class It>
    list(It first, It last) : data_(first, last) {}

    template <class U, std::enable_if_t<!std::is_same_v<U, T>, int> = 0>
    explicit list(const list<U>& other) {
        reserve(other.size());
        for (const auto& v : other) {
            data_.push_back(static_cast<T>(v));
        }
    }

    operator const std::vector<T>&() const { return data_; }  // NOLINT(google-explicit-constructor)
    operator std::vector<T>&() { return data_; }              // NOLINT(google-explicit-constructor)
    template <class U = T, std::enable_if_t<std::is_same_v<U, object>, int> = 0>
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

    std::size_t size() const { return data_.size(); }
    bool empty() const { return data_.empty(); }
    void reserve(std::size_t n) { data_.reserve(n); }
    void clear() { data_.clear(); }
    void resize(std::size_t n) { data_.resize(n); }
    void resize(std::size_t n, const T& value) { data_.resize(n, value); }

    T& operator[](std::size_t i) { return data_[i]; }
    const T& operator[](std::size_t i) const { return data_[i]; }
    T& at(std::size_t i) { return data_.at(i); }
    const T& at(std::size_t i) const { return data_.at(i); }
    T& front() { return data_.front(); }
    const T& front() const { return data_.front(); }
    T& back() { return data_.back(); }
    const T& back() const { return data_.back(); }

    void push_back(const T& value) { data_.push_back(value); }
    void push_back(T&& value) { data_.push_back(std::move(value)); }

    template <class... Args>
    T& emplace_back(Args&&... args) {
        return data_.emplace_back(std::forward<Args>(args)...);
    }

    iterator insert(iterator pos, const T& value) { return data_.insert(pos, value); }
    iterator insert(iterator pos, T&& value) { return data_.insert(pos, std::move(value)); }

    template <class It>
    iterator insert(iterator pos, It first, It last) {
        return data_.insert(pos, first, last);
    }

    iterator erase(iterator pos) { return data_.erase(pos); }
    iterator erase(iterator first, iterator last) { return data_.erase(first, last); }
    void pop_back() { data_.pop_back(); }

    void append(const T& value) { data_.push_back(value); }
    void append(T&& value) { data_.push_back(std::move(value)); }
    template <class U = T, std::enable_if_t<!std::is_same_v<U, std::any>, int> = 0>
    void append(const std::any& value) {
        if (const auto* p = std::any_cast<U>(&value)) {
            data_.push_back(*p);
        }
    }

    template <class U>
    void extend(const U& values) {
        data_.insert(data_.end(), values.begin(), values.end());
    }

    T pop() {
        if (data_.empty()) {
            throw std::out_of_range("pop from empty list");
        }
        T out = data_.back();
        data_.pop_back();
        return out;
    }

    T pop(int64 idx) {
        if (data_.empty()) {
            throw std::out_of_range("pop from empty list");
        }
        if (idx < 0) idx += static_cast<int64>(data_.size());
        if (idx < 0 || idx >= static_cast<int64>(data_.size())) {
            throw std::out_of_range("pop index out of range");
        }
        T out = data_[static_cast<std::size_t>(idx)];
        data_.erase(data_.begin() + idx);
        return out;
    }

private:
    std::vector<T> data_;
};

using bytearray = list<uint8>;
using bytes = bytearray;

static inline bytes py_int_to_bytes(int64 value, int64 length, const str& byteorder) {
    auto raw = pytra::runtime::cpp::base::int_to_bytes(value, length, static_cast<std::string>(byteorder));
    return bytes(raw.begin(), raw.end());
}

template <class K, class V>
class dict {
public:
    using base_type = std::unordered_map<K, V>;
    using iterator = typename base_type::iterator;
    using const_iterator = typename base_type::const_iterator;
    using value_type = typename base_type::value_type;

    dict() = default;
    dict(std::initializer_list<value_type> init) : data_(init) {}
    template <class KK = K, class VV = V, std::enable_if_t<std::is_same_v<KK, str> && std::is_same_v<VV, object>, int> = 0>
    dict(const object& v) : data_(obj_to_dict(v)) {}

    template <class It>
    dict(It first, It last) : data_(first, last) {}

    operator const base_type&() const { return data_; }  // NOLINT(google-explicit-constructor)
    operator base_type&() { return data_; }              // NOLINT(google-explicit-constructor)
    template <class KK = K, class VV = V, std::enable_if_t<std::is_same_v<KK, str> && std::is_same_v<VV, object>, int> = 0>
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

    std::size_t size() const { return data_.size(); }
    bool empty() const { return data_.empty(); }
    void clear() { data_.clear(); }

    iterator find(const K& key) { return data_.find(key); }
    const_iterator find(const K& key) const { return data_.find(key); }
    std::size_t count(const K& key) const { return data_.count(key); }
    bool contains(const K& key) const { return data_.find(key) != data_.end(); }

    V& operator[](const K& key) { return data_[key]; }
    V& at(const K& key) { return data_.at(key); }
    const V& at(const K& key) const { return data_.at(key); }

    std::pair<iterator, bool> insert(const value_type& value) { return data_.insert(value); }
    std::pair<iterator, bool> insert(value_type&& value) { return data_.insert(std::move(value)); }

    template <class P>
    std::pair<iterator, bool> insert(P&& value) {
        return data_.insert(std::forward<P>(value));
    }

    template <class... Args>
    std::pair<iterator, bool> emplace(Args&&... args) {
        return data_.emplace(std::forward<Args>(args)...);
    }

    std::size_t erase(const K& key) { return data_.erase(key); }
    iterator erase(iterator pos) { return data_.erase(pos); }
    iterator erase(iterator first, iterator last) { return data_.erase(first, last); }

    V get(const K& key) const {
        auto it = data_.find(key);
        if (it == data_.end()) {
            throw std::out_of_range("dict.get missing key");
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

    list<std::tuple<K, V>> items() const {
        list<std::tuple<K, V>> out{};
        out.reserve(data_.size());
        for (const auto& kv : data_) out.push_back(std::make_tuple(kv.first, kv.second));
        return out;
    }

private:
    base_type data_;
};

template <class T>
class set {
public:
    using base_type = std::unordered_set<T>;
    using iterator = typename base_type::iterator;
    using const_iterator = typename base_type::const_iterator;
    using value_type = typename base_type::value_type;

    set() = default;
    set(std::initializer_list<value_type> init) : data_(init) {}

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

    std::size_t size() const { return data_.size(); }
    bool empty() const { return data_.empty(); }
    void clear() { data_.clear(); }

    std::size_t count(const T& value) const { return data_.count(value); }
    std::pair<iterator, bool> insert(const T& value) { return data_.insert(value); }
    std::pair<iterator, bool> insert(T&& value) { return data_.insert(std::move(value)); }
    std::size_t erase(const T& value) { return data_.erase(value); }
    iterator find(const T& value) { return data_.find(value); }
    const_iterator find(const T& value) const { return data_.find(value); }

    void add(const T& value) { data_.insert(value); }

    void discard(const T& value) { data_.erase(value); }

    void remove(const T& value) {
        if (data_.erase(value) == 0) {
            throw std::out_of_range("set.remove missing value");
        }
    }

private:
    base_type data_;
};

#endif  // PYTRA_RUNTIME_CPP_BASE_CONTAINERS_H
