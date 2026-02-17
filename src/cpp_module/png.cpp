// このファイルは PNG 出力の最小実装本体です。
// 依存ライブラリなしで、無圧縮DEFLATE（zlibラッパ）を使って PNG を生成します。

#include "cpp_module/png.h"

#include <cstdint>
#include <fstream>
#include <stdexcept>
#include <string>
#include <vector>

namespace pycs::cpp_module::png {
namespace {

void append_u32_be(std::string& out, std::uint32_t v) {
    out.push_back(static_cast<char>((v >> 24) & 0xFF));
    out.push_back(static_cast<char>((v >> 16) & 0xFF));
    out.push_back(static_cast<char>((v >> 8) & 0xFF));
    out.push_back(static_cast<char>(v & 0xFF));
}

std::uint32_t crc32_bytes(const std::string& data) {
    std::uint32_t crc = 0xFFFFFFFFu;
    for (unsigned char b : data) {
        crc ^= b;
        for (int i = 0; i < 8; ++i) {
            if (crc & 1u) {
                crc = (crc >> 1) ^ 0xEDB88320u;
            } else {
                crc >>= 1;
            }
        }
    }
    return ~crc;
}

std::uint32_t adler32_bytes(const std::string& data) {
    constexpr std::uint32_t MOD = 65521u;
    std::uint32_t a = 1u;
    std::uint32_t b = 0u;
    for (unsigned char ch : data) {
        a = (a + static_cast<std::uint32_t>(ch)) % MOD;
        b = (b + a) % MOD;
    }
    return (b << 16) | a;
}

void append_chunk(std::string& out, const char type[4], const std::string& payload) {
    append_u32_be(out, static_cast<std::uint32_t>(payload.size()));
    const std::size_t type_pos = out.size();
    out.append(type, 4);
    out.append(payload);
    const std::string crc_input = out.substr(type_pos, 4 + payload.size());
    append_u32_be(out, crc32_bytes(crc_input));
}

std::string zlib_store(const std::string& raw) {
    std::string out;
    // zlib header: CMF/FLG (deflate, 32K window, fastest strategy)
    out.push_back(static_cast<char>(0x78));
    out.push_back(static_cast<char>(0x01));

    std::size_t pos = 0;
    while (pos < raw.size()) {
        const std::size_t remain = raw.size() - pos;
        const std::uint16_t len = static_cast<std::uint16_t>(remain > 65535 ? 65535 : remain);
        const bool final_block = (pos + len == raw.size());

        out.push_back(static_cast<char>(final_block ? 0x01 : 0x00));  // BFINAL + BTYPE=00
        out.push_back(static_cast<char>(len & 0xFF));
        out.push_back(static_cast<char>((len >> 8) & 0xFF));
        const std::uint16_t nlen = static_cast<std::uint16_t>(~len);
        out.push_back(static_cast<char>(nlen & 0xFF));
        out.push_back(static_cast<char>((nlen >> 8) & 0xFF));
        out.append(raw, pos, len);
        pos += len;
    }

    append_u32_be(out, adler32_bytes(raw));
    return out;
}

}  // namespace

void write_rgb_png(const std::string& path, int width, int height, const std::vector<std::uint8_t>& pixels) {
    if (width <= 0 || height <= 0) {
        throw std::runtime_error("png: width/height must be positive");
    }
    const std::size_t expected = static_cast<std::size_t>(width) * static_cast<std::size_t>(height) * 3u;
    if (pixels.size() != expected) {
        throw std::runtime_error("png: pixels length mismatch");
    }

    const int row_bytes = width * 3;
    std::string raw;
    raw.reserve(static_cast<std::size_t>(height) * static_cast<std::size_t>(row_bytes + 1));
    for (int y = 0; y < height; ++y) {
        raw.push_back(static_cast<char>(0));  // filter type 0
        const std::size_t row_start = static_cast<std::size_t>(y) * static_cast<std::size_t>(row_bytes);
        for (int i = 0; i < row_bytes; ++i) {
            raw.push_back(static_cast<char>(pixels[row_start + static_cast<std::size_t>(i)]));
        }
    }

    std::string ihdr;
    ihdr.reserve(13);
    append_u32_be(ihdr, static_cast<std::uint32_t>(width));
    append_u32_be(ihdr, static_cast<std::uint32_t>(height));
    ihdr.push_back(static_cast<char>(8));   // bit depth
    ihdr.push_back(static_cast<char>(2));   // color type RGB
    ihdr.push_back(static_cast<char>(0));   // compression
    ihdr.push_back(static_cast<char>(0));   // filter
    ihdr.push_back(static_cast<char>(0));   // interlace

    const std::string idat = zlib_store(raw);

    std::string png;
    png.reserve(8 + 12 + ihdr.size() + 12 + idat.size() + 12);
    png.append("\x89PNG\r\n\x1a\n", 8);
    append_chunk(png, "IHDR", ihdr);
    append_chunk(png, "IDAT", idat);
    append_chunk(png, "IEND", "");

    std::ofstream ofs(path, std::ios::binary);
    if (!ofs) {
        throw std::runtime_error("png: failed to open output file");
    }
    ofs.write(png.data(), static_cast<std::streamsize>(png.size()));
}

void write_rgb_ppm(const std::string& path, int width, int height, const std::vector<std::uint8_t>& pixels) {
    if (width <= 0 || height <= 0) {
        throw std::runtime_error("ppm: width/height must be positive");
    }
    const std::size_t expected = static_cast<std::size_t>(width) * static_cast<std::size_t>(height) * 3u;
    if (pixels.size() != expected) {
        throw std::runtime_error("ppm: pixels length mismatch");
    }

    std::ofstream ofs(path, std::ios::binary);
    if (!ofs) {
        throw std::runtime_error("ppm: failed to open output file");
    }
    ofs << "P6\n" << width << " " << height << "\n255\n";
    ofs.write(reinterpret_cast<const char*>(pixels.data()), static_cast<std::streamsize>(pixels.size()));
}

}  // namespace pycs::cpp_module::png
