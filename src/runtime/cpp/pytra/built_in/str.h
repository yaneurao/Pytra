#ifndef PYTRA_BUILT_IN_STR_H
#define PYTRA_BUILT_IN_STR_H

#include "container_common.h"

template <class T>
class list;
template <class T>
::std::string py_to_string(const T& v);

class str {
public:
    using iterator = ::std::string::iterator;
    using const_iterator = ::std::string::const_iterator;
    static constexpr ::std::size_t npos = ::std::string::npos;

    str() = default;
    str(const char* s) : data_(s == nullptr ? "" : s) {}
    str(const ::std::string& s) : data_(s) {}
    str(::std::string&& s) : data_(::std::move(s)) {}
    str(::std::size_t count, char ch) : data_(count, ch) {}
    str(char c) : data_(1, c) {}
    str(const object& v) : data_(obj_to_str(v).std()) {}
    str(const ::std::any& v) {
        if (const auto* p = ::std::any_cast<str>(&v)) {
            data_ = p->std();
        } else if (const auto* p = ::std::any_cast<::std::string>(&v)) {
            data_ = *p;
        } else if (const auto* p = ::std::any_cast<const char*>(&v)) {
            data_ = (*p == nullptr ? "" : *p);
        } else if (const auto* p = ::std::any_cast<char>(&v)) {
            data_ = ::std::string(1, *p);
        } else if (const auto* p = ::std::any_cast<bool>(&v)) {
            data_ = *p ? "True" : "False";
        } else if (const auto* p = ::std::any_cast<int64>(&v)) {
            data_ = ::std::to_string(*p);
        } else if (const auto* p = ::std::any_cast<int32>(&v)) {
            data_ = ::std::to_string(*p);
        } else if (const auto* p = ::std::any_cast<uint64>(&v)) {
            data_ = ::std::to_string(*p);
        } else if (const auto* p = ::std::any_cast<uint32>(&v)) {
            data_ = ::std::to_string(*p);
        } else if (const auto* p = ::std::any_cast<float64>(&v)) {
            data_ = ::std::to_string(*p);
        } else if (const auto* p = ::std::any_cast<float32>(&v)) {
            data_ = ::std::to_string(*p);
        } else {
            data_.clear();
        }
    }

    str& operator=(const char* s) {
        data_ = (s == nullptr ? "" : s);
        return *this;
    }
    str& operator=(const object& v) {
        data_ = obj_to_str(v).std();
        return *this;
    }

    operator const ::std::string&() const { return data_; }  // NOLINT(google-explicit-constructor)
    operator ::std::string&() { return data_; }              // NOLINT(google-explicit-constructor)

    const ::std::string& std() const { return data_; }
    ::std::string& std() { return data_; }

    iterator begin() { return data_.begin(); }
    iterator end() { return data_.end(); }
    const_iterator begin() const { return data_.begin(); }
    const_iterator end() const { return data_.end(); }
    const_iterator cbegin() const { return data_.cbegin(); }
    const_iterator cend() const { return data_.cend(); }

    ::std::size_t size() const { return data_.size(); }
    bool empty() const { return data_.empty(); }
    void clear() { data_.clear(); }
    void reserve(::std::size_t n) { data_.reserve(n); }
    const char* c_str() const { return data_.c_str(); }

    str& operator+=(const str& rhs) {
        data_ += rhs.data_;
        return *this;
    }

    str& operator+=(const ::std::string& rhs) {
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
            throw ::std::out_of_range("string index out of range");
        }
        return str(1, data_[static_cast<::std::size_t>(idx)]);
    }

    char at(int64 idx) const {
        int64 n = static_cast<int64>(data_.size());
        if (idx < 0) idx += n;
        if (idx < 0 || idx >= n) {
            throw ::std::out_of_range("string index out of range");
        }
        return data_.at(static_cast<::std::size_t>(idx));
    }

    str substr(::std::size_t pos, ::std::size_t count = ::std::string::npos) const {
        return str(data_.substr(pos, count));
    }

    ::std::size_t find(const str& needle, ::std::size_t pos = 0) const {
        return data_.find(needle.data_, pos);
    }

    ::std::size_t find(const char* needle, ::std::size_t pos = 0) const {
        return data_.find(needle, pos);
    }

    ::std::size_t find(char needle, ::std::size_t pos = 0) const {
        return data_.find(needle, pos);
    }

    ::std::size_t rfind(const str& needle, ::std::size_t pos = ::std::string::npos) const {
        return data_.rfind(needle.data_, pos);
    }

    ::std::size_t rfind(const char* needle, ::std::size_t pos = ::std::string::npos) const {
        return data_.rfind(needle, pos);
    }

    int compare(const str& other) const { return data_.compare(other.data_); }

    int compare(::std::size_t pos, ::std::size_t count, const str& other) const {
        return data_.compare(pos, count, other.data_);
    }

    str& replace(::std::size_t pos, ::std::size_t count, const str& replacement) {
        data_.replace(pos, count, replacement.data_);
        return *this;
    }

    str replace(const str& old_text, const str& new_text) const {
        if (old_text.empty()) return *this;
        ::std::string out = data_;
        const ::std::string old_s = old_text.std();
        const ::std::string new_s = new_text.std();
        ::std::size_t pos = 0;
        while (true) {
            pos = out.find(old_s, pos);
            if (pos == ::std::string::npos) break;
            out.replace(pos, old_s.size(), new_s);
            pos += new_s.size();
        }
        return str(::std::move(out));
    }

    ::std::size_t find_last_of(char ch, ::std::size_t pos = ::std::string::npos) const {
        return data_.find_last_of(ch, pos);
    }

    ::std::size_t find_last_of(const str& chars, ::std::size_t pos = ::std::string::npos) const {
        return data_.find_last_of(chars.data_, pos);
    }

    ::std::size_t find_last_of(const char* chars, ::std::size_t pos = ::std::string::npos) const {
        return data_.find_last_of(chars, pos);
    }

    template <class T>
    str join(const list<T>& values) const {
        if (values.empty()) return "";
        str out = py_to_string(values[0]);
        for (::std::size_t i = 1; i < values.size(); i++) {
            out += *this;
            out += py_to_string(values[i]);
        }
        return out;
    }

    bool isdigit() const {
        if (data_.empty()) return false;
        for (char ch : data_) {
            if (!::std::isdigit(static_cast<unsigned char>(ch))) return false;
        }
        return true;
    }

    bool isalpha() const {
        if (data_.empty()) return false;
        for (char ch : data_) {
            if (!::std::isalpha(static_cast<unsigned char>(ch))) return false;
        }
        return true;
    }

    bool isalnum() const {
        if (data_.empty()) return false;
        for (char ch : data_) {
            if (!::std::isalnum(static_cast<unsigned char>(ch))) return false;
        }
        return true;
    }

    friend ::std::ostream& operator<<(::std::ostream& os, const str& s) {
        os << s.data_;
        return os;
    }

    friend str operator+(const str& lhs, const str& rhs) { return str(lhs.data_ + rhs.data_); }
    friend str operator+(const str& lhs, const ::std::string& rhs) { return str(lhs.data_ + rhs); }
    friend str operator+(const ::std::string& lhs, const str& rhs) { return str(lhs + rhs.data_); }
    friend str operator+(const str& lhs, const char* rhs) { return str(lhs.data_ + ::std::string(rhs)); }
    friend str operator+(const char* lhs, const str& rhs) { return str(::std::string(lhs) + rhs.data_); }
    friend str operator+(const str& lhs, char rhs) { return str(lhs.data_ + rhs); }
    friend str operator+(char lhs, const str& rhs) { return str(::std::string(1, lhs) + rhs.data_); }

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
    ::std::string data_;
};

static inline pytra::runtime::cpp::base::PyFile open(const str& path, const str& mode) {
    return pytra::runtime::cpp::base::open(static_cast<::std::string>(path), static_cast<::std::string>(mode));
}

namespace std {
template <>
struct hash<str> {
    ::std::size_t operator()(const str& s) const noexcept {
        return ::std::hash<::std::string>{}(s.std());
    }
};
}  // namespace std

static inline bool py_isdigit(const str& ch) {
    return ch.size() == 1 && ::std::isdigit(static_cast<unsigned char>(static_cast<const ::std::string&>(ch)[0])) != 0;
}

static inline bool py_isalpha(const str& ch) {
    return ch.size() == 1 && ::std::isalpha(static_cast<unsigned char>(static_cast<const ::std::string&>(ch)[0])) != 0;
}

#endif  // PYTRA_BUILT_IN_STR_H
