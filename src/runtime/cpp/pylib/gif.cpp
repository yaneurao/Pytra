// このファイルは src/pylib/gif.py を正本として C++ 実装化したものです。

#include "runtime/cpp/pylib/gif.h"

#include "runtime/cpp/py_runtime.h"

namespace pytra::pylib::gif {
namespace {

bytes _lzw_encode(const bytes& data, int64 min_code_size) {
    if (py_len(data) == 0) {
        return py_bytes_lit("");
    }

    int64 clear_code = 1 << min_code_size;
    int64 end_code = clear_code + 1;

    int64 code_size = min_code_size + 1;

    bytearray out = bytearray{};
    int64 bit_buffer = 0;
    int64 bit_count = 0;

    bit_buffer |= (clear_code << bit_count);
    bit_count += code_size;
    while (bit_count >= 8) {
        out.append(bit_buffer & 255);
        bit_buffer >>= 8;
        bit_count -= 8;
    }
    code_size = min_code_size + 1;

    for (uint8 v : data) {
        bit_buffer |= (int64(v) << bit_count);
        bit_count += code_size;
        while (bit_count >= 8) {
            out.append(bit_buffer & 255);
            bit_buffer >>= 8;
            bit_count -= 8;
        }

        bit_buffer |= (clear_code << bit_count);
        bit_count += code_size;
        while (bit_count >= 8) {
            out.append(bit_buffer & 255);
            bit_buffer >>= 8;
            bit_count -= 8;
        }

        code_size = min_code_size + 1;
    }

    bit_buffer |= (end_code << bit_count);
    bit_count += code_size;
    while (bit_count >= 8) {
        out.append(bit_buffer & 255);
        bit_buffer >>= 8;
        bit_count -= 8;
    }

    if (bit_count > 0) {
        out.append(bit_buffer & 255);
    }

    return bytes(out);
}

bytes grayscale_palette_impl() {
    bytearray p = bytearray{};
    int64 i = 0;
    while (i < 256) {
        p.append(i);
        p.append(i);
        p.append(i);
        i++;
    }
    return bytes(p);
}

void save_gif_impl(
    const str& path,
    int64 width,
    int64 height,
    const list<bytes>& frames,
    const bytes& palette,
    int64 delay_cs,
    int64 loop
) {
    if (py_len(palette) != 256 * 3) {
        throw ValueError("palette must be 256*3 bytes");
    }

    for (bytes fr : frames) {
        if (py_len(fr) != width * height) {
            throw ValueError("frame size mismatch");
        }
    }

    bytearray out = bytearray{};
    out.extend(py_bytes_lit("GIF89a"));
    out.extend(py_int_to_bytes(width, 2, "little"));
    out.extend(py_int_to_bytes(height, 2, "little"));
    out.append(247);
    out.append(0);
    out.append(0);
    out.extend(palette);

    out.extend(py_bytes_lit("\x21\xFF\x0BNETSCAPE2.0\x03\x01"));
    out.extend(py_int_to_bytes(loop, 2, "little"));
    out.append(0);

    for (bytes fr : frames) {
        out.extend(py_bytes_lit("\x21\xF9\x04\x00"));
        out.extend(py_int_to_bytes(delay_cs, 2, "little"));
        out.extend(py_bytes_lit("\x00\x00"));

        out.append(44);
        out.extend(py_int_to_bytes(0, 2, "little"));
        out.extend(py_int_to_bytes(0, 2, "little"));
        out.extend(py_int_to_bytes(width, 2, "little"));
        out.extend(py_int_to_bytes(height, 2, "little"));
        out.append(0);

        out.append(8);
        bytes compressed = _lzw_encode(fr, 8);
        int64 pos = 0;
        while (pos < py_len(compressed)) {
            bytes chunk = py_slice(compressed, pos, pos + 255);
            out.append(py_len(chunk));
            out.extend(chunk);
            pos += py_len(chunk);
        }
        out.append(0);
    }

    out.append(59);

    pytra::runtime::cpp::base::PyFile f = open(path, "wb");
    {
        auto __finally_1 = py_make_scope_exit([&]() { f.close(); });
        f.write(out);
    }
}

}  // namespace

std::vector<std::uint8_t> grayscale_palette() {
    const bytes b = grayscale_palette_impl();
    return std::vector<std::uint8_t>(b.begin(), b.end());
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
    list<bytes> frame_list{};
    frame_list.reserve(frames.size());
    for (const auto& fr : frames) {
        frame_list.append(bytes(fr.begin(), fr.end()));
    }
    const bytes pal_bytes(palette.begin(), palette.end());
    save_gif_impl(str(path), int64(width), int64(height), frame_list, pal_bytes, int64(delay_cs), int64(loop));
}

}  // namespace pytra::pylib::gif
