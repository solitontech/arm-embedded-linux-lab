#pragma once
#include <cstdint>
#include <string>
#include <utility>

namespace visiond {

enum class ErrorCode : uint16_t {
    OK = 0,
    INVALID_ARG,
    IO_ERROR,
    DEVICE_NOT_FOUND,
    PERMISSION_DENIED,
    ALREADY_RUNNING,
    NOT_INITIALIZED,
    TIMEOUT,
};

struct Error {
    ErrorCode   code;
    std::string context;
};

// --- expected<T, E> polyfill ---
#if __cpp_lib_expected >= 202211L
    #include <expected>
    template <typename T, typename E = Error>
    using expected = std::expected<T, E>;
    using std::unexpected;
#else

template <typename E>
class unexpected {
public:
    explicit unexpected(const E& e) : val_(e) {}
    explicit unexpected(E&& e) : val_(std::move(e)) {}
    const E& value() const& { return val_; }
    E& value() & { return val_; }
    E&& value() && { return std::move(val_); }
private:
    E val_;
};

template <typename T, typename E = Error>
class expected {
public:
    expected(const T& v) : has_val_(true) { new (&storage_.val) T(v); }
    expected(T&& v) : has_val_(true) { new (&storage_.val) T(std::move(v)); }
    expected(const unexpected<E>& u) : has_val_(false) { new (&storage_.err) E(u.value()); }
    expected(unexpected<E>&& u) : has_val_(false) { new (&storage_.err) E(std::move(u).value()); }

    expected(const expected& o) : has_val_(o.has_val_) {
        if (has_val_) new (&storage_.val) T(o.storage_.val);
        else new (&storage_.err) E(o.storage_.err);
    }

    expected(expected&& o) noexcept : has_val_(o.has_val_) {
        if (has_val_) new (&storage_.val) T(std::move(o.storage_.val));
        else new (&storage_.err) E(std::move(o.storage_.err));
    }

    expected& operator=(const expected& o) {
        if (this != &o) { destroy(); has_val_ = o.has_val_;
            if (has_val_) new (&storage_.val) T(o.storage_.val);
            else new (&storage_.err) E(o.storage_.err); }
        return *this;
    }

    expected& operator=(expected&& o) noexcept {
        if (this != &o) { destroy(); has_val_ = o.has_val_;
            if (has_val_) new (&storage_.val) T(std::move(o.storage_.val));
            else new (&storage_.err) E(std::move(o.storage_.err)); }
        return *this;
    }

    ~expected() { destroy(); }

    bool has_value() const { return has_val_; }
    explicit operator bool() const { return has_val_; }
    T& value() & { return storage_.val; }
    const T& value() const& { return storage_.val; }
    T&& value() && { return std::move(storage_.val); }
    E& error() & { return storage_.err; }
    const E& error() const& { return storage_.err; }

private:
    void destroy() {
        if (has_val_) storage_.val.~T();
        else storage_.err.~E();
    }
    union Storage {
        T val;
        E err;
        Storage() {}
        ~Storage() {}
    } storage_;
    bool has_val_;
};

// Void specialization
template <typename E>
class expected<void, E> {
public:
    expected() : has_val_(true) {}
    expected(const unexpected<E>& u) : has_val_(false), err_(u.value()) {}
    expected(unexpected<E>&& u) : has_val_(false), err_(std::move(u).value()) {}

    bool has_value() const { return has_val_; }
    explicit operator bool() const { return has_val_; }
    E& error() & { return err_; }
    const E& error() const& { return err_; }

private:
    bool has_val_;
    E err_{};
};

#endif

} // namespace visiond
