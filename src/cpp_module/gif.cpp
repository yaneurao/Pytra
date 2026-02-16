// Python の py_module.gif_helper に対応する GIF 書き出し実装です。

#include "cpp_module/gif.h"

#include <cstdint>
#include <fstream>
#include <stdexcept>
#include <string>
#include <vector>

namespace pycs::cpp_module::gif {
namespace {

void append_u16_le(std::string& out, std::uint16_t v) {
    out.push_back(static_cast<char>(v & 0xFF));
    out.push_back(static_cast<char>((v >> 8) & 0xFF));
}

std::string lzw_encode(const std::string& data, int min_code_size) {
    if (data.empty()) {
        return std::string();
    }

    const int clear_code = 1 << min_code_size;
    const int end_code = clear_code + 1;
    int code_size = min_code_size + 1;

    std::string out;
    out.reserve(data.size() + data.size() / 2);

    std::uint32_t bit_buffer = 0;
    int bit_count = 0;

    auto emit = [&](int code) {
        bit_buffer |= (static_cast<std::uint32_t>(code) << bit_count);
        bit_count += code_size;
        while (bit_count >= 8) {
            out.push_back(static_cast<char>(bit_buffer & 0xFF));
            bit_buffer >>= 8;
            bit_count -= 8;
        }
    };

    auto reset_table = [&]() { code_size = min_code_size + 1; };

    emit(clear_code);
    reset_table();

    for (unsigned char c : data) {
        emit(static_cast<int>(c));
        emit(clear_code);
        reset_table();
    }
    emit(end_code);

    if (bit_count > 0) {
        out.push_back(static_cast<char>(bit_buffer & 0xFF));
    }

    return out;
}

std::string lzw_encode(const std::vector<std::uint8_t>& data, int min_code_size) {
    if (data.empty()) {
        return std::string();
    }

    const int clear_code = 1 << min_code_size;
    const int end_code = clear_code + 1;
    int code_size = min_code_size + 1;

    std::string out;
    out.reserve(data.size() + data.size() / 2);

    std::uint32_t bit_buffer = 0;
    int bit_count = 0;

    auto emit = [&](int code) {
        bit_buffer |= (static_cast<std::uint32_t>(code) << bit_count);
        bit_count += code_size;
        while (bit_count >= 8) {
            out.push_back(static_cast<char>(bit_buffer & 0xFF));
            bit_buffer >>= 8;
            bit_count -= 8;
        }
    };

    auto reset_table = [&]() { code_size = min_code_size + 1; };

    emit(clear_code);
    reset_table();

    for (std::uint8_t c : data) {
        emit(static_cast<int>(c));
        emit(clear_code);
        reset_table();
    }
    emit(end_code);

    if (bit_count > 0) {
        out.push_back(static_cast<char>(bit_buffer & 0xFF));
    }

    return out;
}

}  // namespace

std::vector<std::uint8_t> grayscale_palette() {
    std::vector<std::uint8_t> p;
    p.reserve(256 * 3);
    for (int i = 0; i < 256; ++i) {
        const auto v = static_cast<std::uint8_t>(i);
        p.push_back(v);
        p.push_back(v);
        p.push_back(v);
    }
    return p;
}

void save_gif(
    const std::string& path,
    int width,
    int height,
    const std::vector<std::vector<std::uint8_t>>& frames,
    const std::vector<std::uint8_t>& palette,
    int delay_cs,
    int loop
) {
    if (width <= 0 || height <= 0) {
        throw std::runtime_error("gif: width/height must be positive");
    }
    if (palette.size() != 256 * 3) {
        throw std::runtime_error("gif: palette must be 768 bytes");
    }

    const std::size_t frame_bytes = static_cast<std::size_t>(width) * static_cast<std::size_t>(height);
    for (const auto& fr : frames) {
        if (fr.size() != frame_bytes) {
            throw std::runtime_error("gif: frame size mismatch");
        }
    }

    std::string out;
    out.reserve(static_cast<std::size_t>(1024) + frames.size() * frame_bytes / 2);

    out.append("GIF89a", 6);
    append_u16_le(out, static_cast<std::uint16_t>(width));
    append_u16_le(out, static_cast<std::uint16_t>(height));
    out.push_back(static_cast<char>(0xF7));
    out.push_back(static_cast<char>(0));
    out.push_back(static_cast<char>(0));
    out.append(reinterpret_cast<const char*>(palette.data()), static_cast<std::size_t>(palette.size()));

    out.push_back(static_cast<char>(0x21));
    out.push_back(static_cast<char>(0xFF));
    out.push_back(static_cast<char>(0x0B));
    out.append("NETSCAPE2.0", 11);
    out.push_back(static_cast<char>(0x03));
    out.push_back(static_cast<char>(0x01));
    append_u16_le(out, static_cast<std::uint16_t>(loop));
    out.push_back(static_cast<char>(0x00));

    for (const auto& fr : frames) {
        out.push_back(static_cast<char>(0x21));
        out.push_back(static_cast<char>(0xF9));
        out.push_back(static_cast<char>(0x04));
        out.push_back(static_cast<char>(0x00));
        append_u16_le(out, static_cast<std::uint16_t>(delay_cs));
        out.push_back(static_cast<char>(0x00));
        out.push_back(static_cast<char>(0x00));

        out.push_back(static_cast<char>(0x2C));
        append_u16_le(out, static_cast<std::uint16_t>(0));
        append_u16_le(out, static_cast<std::uint16_t>(0));
        append_u16_le(out, static_cast<std::uint16_t>(width));
        append_u16_le(out, static_cast<std::uint16_t>(height));
        out.push_back(static_cast<char>(0x00));

        out.push_back(static_cast<char>(0x08));
        const std::string compressed = lzw_encode(fr, 8);
        std::size_t pos = 0;
        while (pos < compressed.size()) {
            const std::size_t len = (compressed.size() - pos > 255) ? 255 : (compressed.size() - pos);
            out.push_back(static_cast<char>(len));
            out.append(compressed, pos, len);
            pos += len;
        }
        out.push_back(static_cast<char>(0x00));
    }

    out.push_back(static_cast<char>(0x3B));

    std::ofstream ofs(path, std::ios::binary);
    if (!ofs) {
        throw std::runtime_error("gif: failed to open output file");
    }
    ofs.write(out.data(), static_cast<std::streamsize>(out.size()));
}

}  // namespace pycs::cpp_module::gif
