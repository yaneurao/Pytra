// Python の py_module.gif_helper に対応する GIF 書き出し実装です。

#include "cpp_module/gif.h"

#include <cstdint>
#include <fstream>
#include <stdexcept>
#include <string>
#include <unordered_map>
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

    std::unordered_map<std::string, int> dict;
    dict.reserve(5000);
    for (int i = 0; i < clear_code; ++i) {
        dict[std::string(1, static_cast<char>(i))] = i;
    }

    int next_code = end_code + 1;
    int code_size = min_code_size + 1;

    std::string out;
    out.reserve(data.size());

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

    emit(clear_code);

    std::string s(1, data[0]);
    for (std::size_t i = 1; i < data.size(); ++i) {
        const char c = data[i];
        std::string sc = s;
        sc.push_back(c);

        auto it = dict.find(sc);
        if (it != dict.end()) {
            s = sc;
            continue;
        }

        emit(dict[s]);

        if (next_code < 4096) {
            dict.emplace(sc, next_code);
            ++next_code;
            if (next_code == (1 << code_size) && code_size < 12) {
                ++code_size;
            }
        } else {
            emit(clear_code);
            dict.clear();
            for (int j = 0; j < clear_code; ++j) {
                dict[std::string(1, static_cast<char>(j))] = j;
            }
            next_code = end_code + 1;
            code_size = min_code_size + 1;
        }

        s = std::string(1, c);
    }

    emit(dict[s]);
    emit(end_code);

    if (bit_count > 0) {
        out.push_back(static_cast<char>(bit_buffer & 0xFF));
    }

    return out;
}

}  // namespace

std::string grayscale_palette() {
    std::string p;
    p.reserve(256 * 3);
    for (int i = 0; i < 256; ++i) {
        const char v = static_cast<char>(i);
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
    const std::vector<std::string>& frames,
    const std::string& palette,
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
    out.append(palette);

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
