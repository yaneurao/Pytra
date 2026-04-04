// Pytra Zig runtime – minimal built-in helpers.
// This file is loaded by generated Zig programs via @import("py_runtime.zig").

const std = @import("std");

/// Fallback type for unresolved Python types (Any/object/unknown).
pub const PyObject = i64;

/// Print a single value followed by newline, Python-style.
pub fn print(value: anytype) void {
    const writer = std.io.getStdOut().writer();
    printValue(writer, value);
    writer.writeAll("\n") catch {};
}

pub fn print_list(comptime T: type, obj: Obj) void {
    const writer = std.io.getStdOut().writer();
    writer.writeAll("[") catch {};
    const items = list_items(obj, T);
    for (items, 0..) |item, i| {
        if (i != 0) writer.writeAll(", ") catch {};
        printValue(writer, item);
    }
    writer.writeAll("]\n") catch {};
}

pub fn format_int_width(value: anytype, width: i64) []const u8 {
    const alloc = std.heap.page_allocator;
    const w: usize = @intCast(if (width < 0) 0 else width);
    const raw = std.fmt.allocPrint(alloc, "{d}", .{value}) catch return "?";
    if (raw.len >= w) return raw;
    const out = alloc.alloc(u8, w) catch return raw;
    @memset(out, ' ');
    @memcpy(out[w - raw.len ..], raw);
    return out;
}

pub fn format_int_zero_width(value: anytype, width: i64) []const u8 {
    const alloc = std.heap.page_allocator;
    const w: usize = @intCast(if (width < 0) 0 else width);
    const raw = std.fmt.allocPrint(alloc, "{d}", .{value}) catch return "?";
    const sign_len: usize = if (raw.len > 0 and raw[0] == '-') 1 else 0;
    if (raw.len >= w) return raw;
    const out = alloc.alloc(u8, w) catch return raw;
    if (sign_len == 1) out[0] = '-';
    const zero_start = sign_len;
    const body = raw[sign_len..];
    const zero_count = w - sign_len - body.len;
    @memset(out[zero_start .. zero_start + zero_count], '0');
    @memcpy(out[zero_start + zero_count ..], body);
    return out;
}

pub fn format_int_sign(value: anytype) []const u8 {
    const alloc = std.heap.page_allocator;
    const v: i64 = @intCast(value);
    if (v >= 0) return std.fmt.allocPrint(alloc, "+{d}", .{v}) catch "?";
    return std.fmt.allocPrint(alloc, "{d}", .{v}) catch "?";
}

pub fn format_int_hex_width(value: anytype, width: i64, uppercase: bool) []const u8 {
    const alloc = std.heap.page_allocator;
    const w: usize = @intCast(if (width < 0) 0 else width);
    const raw = if (uppercase)
        std.fmt.allocPrint(alloc, "{X}", .{value}) catch return "?"
    else
        std.fmt.allocPrint(alloc, "{x}", .{value}) catch return "?";
    if (raw.len >= w) return raw;
    const out = alloc.alloc(u8, w) catch return raw;
    @memset(out, '0');
    @memcpy(out[w - raw.len ..], raw);
    return out;
}

pub fn format_int_grouped(value: anytype) []const u8 {
    const alloc = std.heap.page_allocator;
    const raw = std.fmt.allocPrint(alloc, "{d}", .{value}) catch return "?";
    const sign_len: usize = if (raw.len > 0 and raw[0] == '-') 1 else 0;
    const body = raw[sign_len..];
    if (body.len <= 3) return raw;
    const commas = (body.len - 1) / 3;
    const out = alloc.alloc(u8, raw.len + commas) catch return raw;
    if (sign_len == 1) out[0] = '-';
    var src_i: usize = body.len;
    var dst_i: usize = out.len;
    var group_count: usize = 0;
    while (src_i > 0) {
        src_i -= 1;
        dst_i -= 1;
        out[dst_i] = body[src_i];
        group_count += 1;
        if (src_i > 0 and group_count == 3) {
            dst_i -= 1;
            out[dst_i] = ',';
            group_count = 0;
        }
    }
    return out;
}

pub fn format_float_precision(value: anytype, precision: i64) []const u8 {
    const alloc = std.heap.page_allocator;
    const p: usize = @intCast(if (precision < 0) 0 else precision);
    const v: f64 = @floatCast(value);
    return std.fmt.allocPrint(alloc, "{d:.[1]}", .{ v, p }) catch "?";
}

pub fn format_float_width_precision(value: anytype, width: i64, precision: i64) []const u8 {
    const alloc = std.heap.page_allocator;
    const raw = format_float_precision(value, precision);
    const w: usize = @intCast(if (width < 0) 0 else width);
    if (raw.len >= w) return raw;
    const out = alloc.alloc(u8, w) catch return raw;
    @memset(out, ' ');
    @memcpy(out[w - raw.len ..], raw);
    return out;
}

pub fn format_percent_precision(value: anytype, precision: i64) []const u8 {
    const alloc = std.heap.page_allocator;
    const scaled: f64 = @as(f64, @floatCast(value)) * 100.0;
    const raw = format_float_precision(scaled, precision);
    return std.fmt.allocPrint(alloc, "{s}%", .{raw}) catch raw;
}

pub fn format_str_left_width(value: []const u8, width: i64) []const u8 {
    const alloc = std.heap.page_allocator;
    const w: usize = @intCast(if (width < 0) 0 else width);
    if (value.len >= w) return value;
    const out = alloc.alloc(u8, w) catch return value;
    @memcpy(out[0..value.len], value);
    @memset(out[value.len..], ' ');
    return out;
}

/// Print two values separated by a space.
pub fn print2(a: anytype, b: anytype) void {
    const writer = std.io.getStdOut().writer();
    printValue(writer, a);
    writer.writeAll(" ") catch {};
    printValue(writer, b);
    writer.writeAll("\n") catch {};
}

/// Print three values separated by spaces.
pub fn print3(a: anytype, b: anytype, c: anytype) void {
    const writer = std.io.getStdOut().writer();
    printValue(writer, a);
    writer.writeAll(" ") catch {};
    printValue(writer, b);
    writer.writeAll(" ") catch {};
    printValue(writer, c);
    writer.writeAll("\n") catch {};
}

fn printValue(writer: anytype, value: anytype) void {
    const T = @TypeOf(value);
    switch (@typeInfo(T)) {
        .int, .comptime_int => {
            writer.print("{d}", .{value}) catch {};
        },
        .float, .comptime_float => {
            printFloat(writer, value);
        },
        .bool => {
            writer.writeAll(if (value) "True" else "False") catch {};
        },
        .pointer => |ptr_info| {
            if (ptr_info.size == .slice and ptr_info.child == u8) {
                writer.writeAll(value) catch {};
            } else if (ptr_info.size == .one) {
                // *const [N:0]u8 (string literal) → coerce to slice
                const child_info = @typeInfo(ptr_info.child);
                if (child_info == .array and child_info.array.child == u8) {
                    writer.writeAll(value) catch {};
                } else {
                    writer.print("{any}", .{value}) catch {};
                }
            } else {
                writer.print("{any}", .{value}) catch {};
            }
        },
        .optional => {
            if (value) |v| {
                printValue(writer, v);
            } else {
                writer.writeAll("None") catch {};
            }
        },
        .null => {
            writer.writeAll("None") catch {};
        },
        .void => {
            writer.writeAll("None") catch {};
        },
        else => {
            writer.print("{any}", .{value}) catch {};
        },
    }
}

fn printFloat(writer: anytype, value: anytype) void {
    // Python-style float printing: no trailing zeros, but at least one decimal
    const v: f64 = @floatCast(value);
    // Check if it's an integer value
    const truncated = @trunc(v);
    if (v == truncated and !std.math.isNan(v) and !std.math.isInf(v)) {
        writer.print("{d}.0", .{@as(i64, @intFromFloat(truncated))}) catch {};
    } else {
        writer.print("{d}", .{v}) catch {};
    }
}

/// Python-style truthiness check.
pub fn truthy(value: anytype) bool {
    const T = @TypeOf(value);
    if (T == *UnionVal) {
        return json_to_bool(value);
    }
    switch (@typeInfo(T)) {
        .bool => return value,
        .int, .comptime_int => return value != 0,
        .float, .comptime_float => return value != 0.0,
        .optional => return value != null,
        .null => return false,
        .pointer => |ptr_info| {
            if (ptr_info.size == .slice) {
                return value.len > 0;
            }
            return true;
        },
        else => return true,
    }
}

/// Convert a value to string representation.
pub fn to_str(value: anytype) []const u8 {
    const T = @TypeOf(value);
    const alloc = std.heap.page_allocator;
    if (T == *UnionVal) {
        return switch (value.*) {
            .none => "None",
            .bool_ => |v| if (v) "True" else "False",
            .int_ => |v| to_str(v),
            .float_ => |v| to_str(v),
            .str_ => |v| v,
            .list_ => |v| to_str(v),
            .dict_ => |v| dict_repr(*UnionVal, v.*),
        };
    }
    if (@typeInfo(T) == .@"struct" and @hasDecl(T, "get") and @hasDecl(T, "contains") and @hasDecl(T, "iterator") and @hasDecl(T, "count")) {
        if (value.count() == 0) return "{}";
    }
    switch (@typeInfo(T)) {
        .int, .comptime_int => {
            // Format integer to string
            var v: i64 = @intCast(value);
            var neg = false;
            if (v < 0) {
                neg = true;
                v = -v;
            }
            var buf: [20]u8 = undefined;
            var pos: usize = buf.len;
            if (v == 0) {
                pos -= 1;
                buf[pos] = '0';
            } else {
                while (v > 0) {
                    pos -= 1;
                    buf[pos] = @intCast(@as(u8, @intCast(@mod(v, 10))) + '0');
                    v = @divFloor(v, 10);
                }
            }
            if (neg) {
                pos -= 1;
                buf[pos] = '-';
            }
            const len = buf.len - pos;
            const result = alloc.alloc(u8, len) catch return "?";
            @memcpy(result, buf[pos..]);
            return result;
        },
        .float, .comptime_float => {
            // Simple float formatting
            const fv: f64 = @floatCast(value);
            const iv: i64 = @intFromFloat(fv);
            return to_str(iv);
        },
        .bool => {
            return if (value) "True" else "False";
        },
        .optional => {
            if (value) |inner| {
                return to_str(inner);
            }
            return "None";
        },
        .null => {
            return "None";
        },
        .void => {
            return "None";
        },
        .pointer => |ptr_info| {
            if (ptr_info.size == .slice and ptr_info.child == u8) {
                return value;
            }
            if (ptr_info.size == .one) {
                const child_info = @typeInfo(ptr_info.child);
                if (child_info == .array and child_info.array.child == u8) {
                    return value;
                }
            }
            return "<object>";
        },
        else => return "<object>",
    }
}

/// Concatenate two strings.
pub fn str_concat(a: []const u8, b: []const u8) []const u8 {
    const alloc = std.heap.page_allocator;
    const buf = alloc.alloc(u8, a.len + b.len) catch return "";
    @memcpy(buf[0..a.len], a);
    @memcpy(buf[a.len..], b);
    return buf;
}

pub fn str_upper(s: []const u8) []const u8 {
    const alloc = std.heap.page_allocator;
    const buf = alloc.alloc(u8, s.len) catch return "";
    for (s, 0..) |ch, i| {
        buf[i] = if (ch >= 'a' and ch <= 'z') ch - 32 else ch;
    }
    return buf;
}

pub fn str_lower(s: []const u8) []const u8 {
    const alloc = std.heap.page_allocator;
    const buf = alloc.alloc(u8, s.len) catch return "";
    for (s, 0..) |ch, i| {
        buf[i] = if (ch >= 'A' and ch <= 'Z') ch + 32 else ch;
    }
    return buf;
}

pub fn str_strip(s: []const u8) []const u8 {
    return std.mem.trim(u8, s, " \t\r\n");
}

pub fn str_strip_chars(s: []const u8, chars: []const u8) []const u8 {
    return std.mem.trim(u8, s, chars);
}

pub fn str_lstrip(s: []const u8) []const u8 {
    return std.mem.trimLeft(u8, s, " \t\r\n");
}

pub fn str_lstrip_chars(s: []const u8, chars: []const u8) []const u8 {
    return std.mem.trimLeft(u8, s, chars);
}

pub fn str_rstrip(s: []const u8) []const u8 {
    return std.mem.trimRight(u8, s, " \t\r\n");
}

pub fn str_rstrip_chars(s: []const u8, chars: []const u8) []const u8 {
    return std.mem.trimRight(u8, s, chars);
}

pub fn str_startswith(s: []const u8, prefix: []const u8) bool {
    return std.mem.startsWith(u8, s, prefix);
}

pub fn str_endswith(s: []const u8, suffix: []const u8) bool {
    return std.mem.endsWith(u8, s, suffix);
}

pub fn str_find(s: []const u8, needle: []const u8) i64 {
    const idx = std.mem.indexOf(u8, s, needle);
    return if (idx) |pos| @as(i64, @intCast(pos)) else -1;
}

pub fn str_index_of(s: []const u8, needle: []const u8) i64 {
    return str_find(s, needle);
}

pub fn chr(code: i64) []const u8 {
    const alloc = std.heap.page_allocator;
    const cp: u21 = @intCast(@max(@as(i64, 0), code));
    var buf = alloc.alloc(u8, 4) catch return "";
    const len = std.unicode.utf8Encode(cp, buf) catch return "";
    return buf[0..len];
}

pub fn ord(ch: []const u8) i64 {
    if (ch.len == 0) return 0;
    const cp = std.unicode.utf8Decode(ch) catch return @as(i64, ch[0]);
    return @intCast(cp);
}

pub fn list_index(obj: Obj, comptime T: type, needle: T) i64 {
    const items = list_items(obj, T);
    var i: usize = 0;
    while (i < items.len) : (i += 1) {
        if (T == []const u8) {
            if (std.mem.eql(u8, items[i], needle)) return @as(i64, @intCast(i));
        } else if (std.meta.eql(items[i], needle)) {
            return @as(i64, @intCast(i));
        }
    }
    return -1;
}

pub fn str_replace(s: []const u8, old: []const u8, new: []const u8) []const u8 {
    const idx_opt = std.mem.indexOf(u8, s, old);
    if (idx_opt == null) return s;
    const idx = idx_opt.?;
    const alloc = std.heap.page_allocator;
    const total = idx + new.len + (s.len - idx - old.len);
    const buf = alloc.alloc(u8, total) catch return s;
    @memcpy(buf[0..idx], s[0..idx]);
    @memcpy(buf[idx .. idx + new.len], new);
    @memcpy(buf[idx + new.len ..], s[idx + old.len ..]);
    return buf;
}

pub fn str_isalnum(s: []const u8) bool {
    if (s.len == 0) return false;
    for (s) |ch| {
        const is_alpha = (ch >= 'a' and ch <= 'z') or (ch >= 'A' and ch <= 'Z');
        const is_digit = ch >= '0' and ch <= '9';
        if (!is_alpha and !is_digit) return false;
    }
    return true;
}

pub fn str_split(s: []const u8, sep: []const u8) Obj {
    const out = make_list([]const u8);
    if (sep.len == 0) {
        list_append(out, []const u8, s);
        return out;
    }
    var start: usize = 0;
    while (true) {
        const rel = std.mem.indexOfPos(u8, s, start, sep);
        if (rel == null) break;
        const idx = rel.?;
        list_append(out, []const u8, s[start..idx]);
        start = idx + sep.len;
    }
    list_append(out, []const u8, s[start..]);
    return out;
}

pub fn str_chars(s: []const u8) Obj {
    const out = make_list([]const u8);
    var i: usize = 0;
    while (i < s.len) : (i += 1) {
        list_append(out, []const u8, s[i .. i + 1]);
    }
    return out;
}

/// Join multiple string slices.
pub fn str_join(parts: anytype) []const u8 {
    const alloc = std.heap.page_allocator;
    var total: usize = 0;
    inline for (parts) |p| {
        total += p.len;
    }
    const buf = alloc.alloc(u8, total) catch return "";
    var pos: usize = 0;
    inline for (parts) |p| {
        @memcpy(buf[pos..][0..p.len], p);
        pos += p.len;
    }
    return buf;
}

/// Join string slices with a separator (Python str.join equivalent).
pub fn str_join_sep(sep: []const u8, parts: []const []const u8) []const u8 {
    if (parts.len == 0) return "";
    const alloc = std.heap.page_allocator;
    var total: usize = 0;
    for (parts) |p| {
        total += p.len;
    }
    total += sep.len * (parts.len - 1);
    const buf = alloc.alloc(u8, total) catch return "";
    var pos: usize = 0;
    for (parts, 0..) |p, i| {
        if (i > 0) {
            @memcpy(buf[pos..][0..sep.len], sep);
            pos += sep.len;
        }
        @memcpy(buf[pos..][0..p.len], p);
        pos += p.len;
    }
    return buf;
}

fn str_quote(s: []const u8) []const u8 {
    return str_join(&.{ "'", s, "'" });
}

fn repr_value(value: anytype) []const u8 {
    const T = @TypeOf(value);
    if (T == []const u8) return str_quote(value);
    if (@typeInfo(T) == .pointer) {
        const ptr_info = @typeInfo(T).pointer;
        if (ptr_info.size == .one and @typeInfo(ptr_info.child) == .array and @typeInfo(ptr_info.child).array.child == u8) {
            const s: []const u8 = value;
            return str_quote(s);
        }
    }
    return to_str(value);
}

pub fn list_repr(comptime T: type, obj: Obj) []const u8 {
    const items = list_items(obj, T);
    if (items.len == 0) return "[]";
    var parts = std.ArrayList([]const u8).init(std.heap.page_allocator);
    defer parts.deinit();
    for (items, 0..) |item, i| {
        if (i != 0) parts.append(", ") catch {};
        parts.append(repr_value(item)) catch {};
    }
    return str_join_many("[", parts.items, "]");
}

pub fn list_repr_nested(comptime InnerT: type, obj: Obj) []const u8 {
    const items = list_items(obj, Obj);
    if (items.len == 0) return "[]";
    var parts = std.ArrayList([]const u8).init(std.heap.page_allocator);
    defer parts.deinit();
    for (items, 0..) |item, i| {
        if (i != 0) parts.append(", ") catch {};
        parts.append(list_repr(InnerT, item)) catch {};
    }
    return str_join_many("[", parts.items, "]");
}

pub fn dict_repr(comptime V: type, map: std.StringHashMap(V)) []const u8 {
    if (map.count() == 0) return "{}";
    var parts = std.ArrayList([]const u8).init(std.heap.page_allocator);
    defer parts.deinit();
    var keys = std.ArrayList([]const u8).init(std.heap.page_allocator);
    defer keys.deinit();
    var it = map.iterator();
    while (it.next()) |entry| {
        keys.append(entry.key_ptr.*) catch {};
    }
    var i: usize = 1;
    while (i < keys.items.len) : (i += 1) {
        const key = keys.items[i];
        var j = i;
        while (j > 0 and std.mem.order(u8, keys.items[j - 1], key) == .gt) : (j -= 1) {
            keys.items[j] = keys.items[j - 1];
        }
        keys.items[j] = key;
    }
    for (keys.items, 0..) |key, idx| {
        if (idx != 0) parts.append(", ") catch {};
        parts.append(str_quote(key)) catch {};
        parts.append(": ") catch {};
        parts.append(repr_value(map.get(key).?)) catch {};
    }
    return str_join_many("{", parts.items, "}");
}

pub fn tuple_repr(value: anytype) []const u8 {
    const T = @TypeOf(value);
    const info = @typeInfo(T);
    if (info != .@"struct") return to_str(value);
    var parts = std.ArrayList([]const u8).init(std.heap.page_allocator);
    defer parts.deinit();
    comptime var tuple_i: usize = 0;
    inline for (info.@"struct".fields) |field| {
        if (comptime std.mem.startsWith(u8, field.name, "_")) {
            if (tuple_i != 0) parts.append(", ") catch {};
            parts.append(repr_value(@field(value, field.name))) catch {};
            tuple_i += 1;
        }
    }
    const suffix = if (tuple_i == 1) ",)" else ")";
    return str_join_many("(", parts.items, suffix);
}

fn str_join_many(prefix: []const u8, parts: []const []const u8, suffix: []const u8) []const u8 {
    const alloc = std.heap.page_allocator;
    var total: usize = prefix.len + suffix.len;
    for (parts) |p| total += p.len;
    const buf = alloc.alloc(u8, total) catch return "";
    var pos: usize = 0;
    @memcpy(buf[pos .. pos + prefix.len], prefix);
    pos += prefix.len;
    for (parts) |p| {
        @memcpy(buf[pos .. pos + p.len], p);
        pos += p.len;
    }
    @memcpy(buf[pos .. pos + suffix.len], suffix);
    return buf;
}

/// Create a new empty StringHashMap.
pub fn make_str_dict(comptime V: type) std.StringHashMap(V) {
    return std.StringHashMap(V).init(std.heap.page_allocator);
}

/// Create a StringHashMap from key/value arrays.
pub fn make_str_dict_from(comptime V: type, keys: []const []const u8, values: []const V) std.StringHashMap(V) {
    var m = std.StringHashMap(V).init(std.heap.page_allocator);
    var i: usize = 0;
    while (i < keys.len and i < values.len) : (i += 1) {
        m.put(keys[i], values[i]) catch {};
    }
    return m;
}

fn typeNameEquals(typ: anytype, expected: []const u8) bool {
    const TT = @TypeOf(typ);
    if (TT == []const u8) return std.mem.eql(u8, typ, expected);
    if (@typeInfo(TT) == .pointer) {
        const ptr_info = @typeInfo(TT).pointer;
        if (ptr_info.size == .one and @typeInfo(ptr_info.child) == .array and @typeInfo(ptr_info.child).array.child == u8) {
            const typ_slice: []const u8 = typ;
            return std.mem.eql(u8, typ_slice, expected);
        }
    }
    return false;
}

fn isStringLike(comptime T: type) bool {
    if (T == []const u8) return true;
    if (@typeInfo(T) != .pointer) return false;
    const ptr_info = @typeInfo(T).pointer;
    return ptr_info.size == .one and @typeInfo(ptr_info.child) == .array and @typeInfo(ptr_info.child).array.child == u8;
}

/// isinstance check for builtin/container cases used by narrowing.
pub fn isinstance_check(obj: anytype, typ: anytype) bool {
    const T = @TypeOf(obj);
    if (T == *UnionVal) {
        if (typeNameEquals(typ, "dict")) return obj.* == .dict_;
        if (typeNameEquals(typ, "list")) return obj.* == .list_;
        if (typeNameEquals(typ, "str")) return obj.* == .str_;
        if (typeNameEquals(typ, "bool")) return obj.* == .bool_;
        if (typeNameEquals(typ, "int") or typeNameEquals(typ, "int8") or typeNameEquals(typ, "int16") or typeNameEquals(typ, "int32") or typeNameEquals(typ, "int64")) return obj.* == .int_;
        if (typeNameEquals(typ, "float") or typeNameEquals(typ, "float32") or typeNameEquals(typ, "float64")) return obj.* == .float_;
        if (typeNameEquals(typ, "None")) return obj.* == .none;
        return false;
    }
    if (typeNameEquals(typ, "dict")) {
        return @typeInfo(T) == .@"struct" and @hasDecl(T, "get") and @hasDecl(T, "contains");
    }
    if (typeNameEquals(typ, "list") or typeNameEquals(typ, "set") or typeNameEquals(typ, "tuple")) {
        return T == Obj;
    }
    if (typeNameEquals(typ, "str")) {
        return isStringLike(T);
    }
    if (typeNameEquals(typ, "bool")) {
        return T == bool;
    }
    if (typeNameEquals(typ, "int") or typeNameEquals(typ, "int8") or typeNameEquals(typ, "int16") or typeNameEquals(typ, "int32") or typeNameEquals(typ, "int64")) {
        return T == i64 or T == i32 or T == i16 or T == i8 or T == comptime_int;
    }
    if (typeNameEquals(typ, "uint8") or typeNameEquals(typ, "uint16") or typeNameEquals(typ, "uint32") or typeNameEquals(typ, "uint64")) {
        return T == u8 or T == u16 or T == u32 or T == u64;
    }
    if (typeNameEquals(typ, "float") or typeNameEquals(typ, "float32") or typeNameEquals(typ, "float64")) {
        return T == f32 or T == f64 or T == comptime_float;
    }
    if (typeNameEquals(typ, "None")) {
        return T == void;
    }
    return false;
}

/// Contains check for `in` operator.
pub fn contains(haystack: anytype, needle: anytype) bool {
    const HT = @TypeOf(haystack);
    // StringHashMap: check if key exists
    if (@typeInfo(HT) == .@"struct" and @hasDecl(HT, "contains")) {
        return haystack.contains(needle);
    }
    if (HT == []const u8) {
        const NT = @TypeOf(needle);
        if (NT == []const u8) {
            return std.mem.indexOf(u8, haystack, needle) != null;
        }
        if (@typeInfo(NT) == .pointer) {
            const ptr_info = @typeInfo(NT).pointer;
            if (ptr_info.size == .one and @typeInfo(ptr_info.child) == .array and @typeInfo(ptr_info.child).array.child == u8) {
                const needle_slice: []const u8 = needle;
                return std.mem.indexOf(u8, haystack, needle_slice) != null;
            }
        }
    }
    if (@typeInfo(HT) == .pointer) {
        const ptr_info = @typeInfo(HT).pointer;
        if (ptr_info.size == .one and @typeInfo(ptr_info.child) == .array and @typeInfo(ptr_info.child).array.child == u8) {
            const haystack_slice: []const u8 = haystack;
            const NT = @TypeOf(needle);
            if (NT == []const u8) {
                return std.mem.indexOf(u8, haystack_slice, needle) != null;
            }
            if (@typeInfo(NT) == .pointer) {
                const needle_ptr_info = @typeInfo(NT).pointer;
                if (needle_ptr_info.size == .one and @typeInfo(needle_ptr_info.child) == .array and @typeInfo(needle_ptr_info.child).array.child == u8) {
                    const needle_slice: []const u8 = needle;
                    return std.mem.indexOf(u8, haystack_slice, needle_slice) != null;
                }
            }
        }
    }
    if (HT == Obj) {
        const NT = @TypeOf(needle);
        if (NT == i64 or NT == comptime_int) {
            for (list_items(haystack, i64)) |v| {
                if (v == needle) return true;
            }
            return false;
        }
        if (NT == bool) {
            for (list_items(haystack, bool)) |v| {
                if (v == needle) return true;
            }
            return false;
        }
        if (NT == []const u8) {
            for (list_items(haystack, []const u8)) |v| {
                if (std.mem.eql(u8, v, needle)) return true;
            }
            return false;
        }
        if (@typeInfo(NT) == .pointer) {
            const ptr_info = @typeInfo(NT).pointer;
            if (ptr_info.size == .one and @typeInfo(ptr_info.child) == .array and @typeInfo(ptr_info.child).array.child == u8) {
                const needle_slice: []const u8 = needle;
                for (list_items(haystack, []const u8)) |v| {
                    if (std.mem.eql(u8, v, needle_slice)) return true;
                }
                return false;
            }
        }
        if (@typeInfo(NT) == .@"struct") {
            for (list_items(haystack, NT)) |v| {
                if (std.meta.eql(v, needle)) return true;
            }
            return false;
        }
    }
    if (@typeInfo(HT) == .@"struct") {
        inline for (@typeInfo(HT).@"struct".fields) |field| {
            if (std.mem.startsWith(u8, field.name, "_")) {
                if (std.meta.eql(@field(haystack, field.name), needle)) return true;
            }
        }
    }
    return false;
}

pub const UnionDict = std.StringHashMap(*UnionVal);

pub const UnionVal = union(enum) {
    none,
    bool_: bool,
    int_: i64,
    float_: f64,
    str_: []const u8,
    list_: Obj,
    dict_: *UnionDict,
};

pub const JsonDict = UnionDict;
pub const JsonVal = UnionVal;

fn unionAlloc(value: UnionVal) *UnionVal {
    const alloc = std.heap.page_allocator;
    const ptr = alloc.create(UnionVal) catch @panic("alloc failed");
    ptr.* = value;
    return ptr;
}

pub fn union_new_none() *UnionVal {
    return unionAlloc(.none);
}

pub fn union_wrap(value: anytype) *UnionVal {
    const T = @TypeOf(value);
    if (T == *UnionVal) return value;
    if (T == bool) return unionAlloc(.{ .bool_ = value });
    if (T == i64 or T == i32 or T == i16 or T == i8 or T == comptime_int) {
        return unionAlloc(.{ .int_ = @as(i64, @intCast(value)) });
    }
    if (T == u8 or T == u16 or T == u32 or T == u64) {
        return unionAlloc(.{ .int_ = @as(i64, @intCast(value)) });
    }
    if (T == f32 or T == f64 or T == comptime_float) {
        return unionAlloc(.{ .float_ = @as(f64, value) });
    }
    if (comptime isStringLike(T)) {
        const text: []const u8 = value;
        return unionAlloc(.{ .str_ = text });
    }
    if (T == Obj) {
        return unionAlloc(.{ .list_ = value });
    }
    if (@typeInfo(T) == .@"struct" and @hasDecl(T, "get") and @hasDecl(T, "contains")) {
        var out = UnionDict.init(std.heap.page_allocator);
        var it = value.iterator();
        while (it.next()) |entry| {
            out.put(entry.key_ptr.*, union_wrap(entry.value_ptr.*)) catch {};
        }
        const alloc = std.heap.page_allocator;
        const map_ptr = alloc.create(UnionDict) catch @panic("alloc failed");
        map_ptr.* = out;
        return unionAlloc(.{ .dict_ = map_ptr });
    }
    return union_new_none();
}

pub fn union_is_dict(value: *UnionVal) bool {
    return value.* == .dict_;
}

pub fn union_is_none(value: *UnionVal) bool {
    return value.* == .none;
}

pub fn is_none_any(value: anytype) bool {
    const T = @TypeOf(value);
    if (T == *UnionVal) {
        return union_is_none(value);
    }
    if (T == ?*UnionVal) {
        return if (value) |v| union_is_none(v) else true;
    }
    return switch (@typeInfo(T)) {
        .optional => value == null,
        else => false,
    };
}

pub fn as_list_any(value: anytype) Obj {
    const T = @TypeOf(value);
    if (T == *UnionVal) {
        return union_as_list(value);
    }
    if (T == Obj) {
        return value;
    }
    unreachable;
}

pub fn as_dict_any(value: anytype) UnionDict {
    const T = @TypeOf(value);
    if (T == *UnionVal) {
        return union_as_dict(value);
    }
    if (T == UnionDict) {
        return value;
    }
    unreachable;
}

pub fn union_is_list(value: *UnionVal) bool {
    return value.* == .list_;
}

pub fn union_is_str(value: *UnionVal) bool {
    return value.* == .str_;
}

pub fn union_as_dict(value: *UnionVal) UnionDict {
    return value.dict_.*;
}

pub fn union_as_list(value: *UnionVal) Obj {
    return value.list_;
}

pub fn union_as_str(value: *UnionVal) []const u8 {
    return value.str_;
}

pub fn union_to_int(value: *UnionVal) i64 {
    return switch (value.*) {
        .int_ => |v| v,
        .float_ => |v| @as(i64, @intFromFloat(v)),
        .bool_ => |v| if (v) 1 else 0,
        .str_ => |v| str_to_int(v),
        else => 0,
    };
}

pub fn union_to_float(value: *UnionVal) f64 {
    return switch (value.*) {
        .int_ => |v| @as(f64, @floatFromInt(v)),
        .float_ => |v| v,
        .bool_ => |v| if (v) 1.0 else 0.0,
        .str_ => |_| 0.0,
        else => 0.0,
    };
}

pub fn union_to_bool(value: *UnionVal) bool {
    return switch (value.*) {
        .none => false,
        .bool_ => |v| v,
        .int_ => |v| v != 0,
        .float_ => |v| v != 0.0,
        .str_ => |v| v.len > 0,
        .list_ => |v| list_len(v, *UnionVal) != 0,
        .dict_ => |v| v.count() != 0,
    };
}

pub const json_new_none = union_new_none;
pub const json_wrap = union_wrap;
pub const json_is_dict = union_is_dict;
pub const json_is_list = union_is_list;
pub const json_is_str = union_is_str;
pub const json_as_dict = union_as_dict;
pub const json_as_list = union_as_list;
pub const json_as_str = union_as_str;
pub const json_to_int = union_to_int;
pub const json_to_float = union_to_float;
pub const json_to_bool = union_to_bool;

/// Reference-counted object wrapper (Pytra Object<T> equivalent).
pub fn Object(comptime T: type) type {
    return struct {
        const Self = @This();
        ptr: *T,
        rc: *usize,

        pub fn init(value: T) Self {
            const alloc = std.heap.page_allocator;
            const p = alloc.create(T) catch @panic("alloc failed");
            p.* = value;
            const rc = alloc.create(usize) catch @panic("alloc failed");
            rc.* = 1;
            return Self{ .ptr = p, .rc = rc };
        }

        pub fn clone(self: Self) Self {
            self.rc.* += 1;
            return Self{ .ptr = self.ptr, .rc = self.rc };
        }

        pub fn release(self: Self) void {
            self.rc.* -= 1;
            if (self.rc.* == 0) {
                const alloc = std.heap.page_allocator;
                alloc.destroy(self.ptr);
                alloc.destroy(self.rc);
            }
        }
    };
}

/// Create a heap-allocated object and return a pointer.
pub fn make_object(comptime T: type, value: T) *T {
    const alloc = std.heap.page_allocator;
    const p = alloc.create(T) catch @panic("alloc failed");
    p.* = value;
    return p;
}

/// Type-erased object with vtable and reference count (spec-object.md §14).
pub const Obj = struct {
    data: *anyopaque,
    vtable: *const anyopaque,
    rc: *usize,
    drop_fn: ?*const fn (*anyopaque) void,

    pub fn retain(self: Obj) Obj {
        self.rc.* += 1;
        return self;
    }

    pub fn release(self: Obj) void {
        if (self.rc.* > 0) {
            self.rc.* -= 1;
            if (self.rc.* == 0) {
                if (self.drop_fn) |drop| {
                    drop(self.data);
                }
            }
        }
    }

    /// Get the vtable cast to a specific VTable type.
    pub fn vt(self: Obj, comptime VT: type) *const VT {
        return @ptrCast(@alignCast(self.vtable));
    }

    /// Get the data pointer cast to a specific type.
    pub fn as(self: Obj, comptime T: type) *T {
        return @ptrCast(@alignCast(self.data));
    }
};

/// Create a type-erased Obj with vtable.
pub fn make_obj(comptime T: type, value: T, vtable: *const anyopaque) Obj {
    return make_obj_drop(T, value, vtable, null);
}

pub fn make_obj_drop(comptime T: type, value: T, vtable: *const anyopaque, drop_fn: ?*const fn (*anyopaque) void) Obj {
    const alloc = std.heap.page_allocator;
    const p = alloc.create(T) catch @panic("alloc failed");
    p.* = value;
    const rc = alloc.create(usize) catch @panic("alloc failed");
    rc.* = 1;
    return Obj{
        .data = @ptrCast(p),
        .vtable = vtable,
        .rc = rc,
        .drop_fn = drop_fn,
    };
}

// ─── List (Obj-managed ArrayList) ───

/// Create an empty list as Obj.
pub fn make_list(comptime T: type) Obj {
    const alloc = std.heap.page_allocator;
    const p = alloc.create(std.ArrayList(T)) catch @panic("alloc failed");
    p.* = std.ArrayList(T).init(alloc);
    const rc = alloc.create(usize) catch @panic("alloc failed");
    rc.* = 1;
    return Obj{ .data = @ptrCast(p), .vtable = @ptrCast(&EMPTY_VT), .rc = rc, .drop_fn = null };
}

/// Create a list from a slice as Obj.
pub fn make_list_from(comptime T: type, items: []const T) Obj {
    const alloc = std.heap.page_allocator;
    const p = alloc.create(std.ArrayList(T)) catch @panic("alloc failed");
    p.* = std.ArrayList(T).init(alloc);
    p.appendSlice(items) catch {};
    const rc = alloc.create(usize) catch @panic("alloc failed");
    rc.* = 1;
    return Obj{ .data = @ptrCast(p), .vtable = @ptrCast(&EMPTY_VT), .rc = rc, .drop_fn = null };
}

/// Empty list (Obj).
pub fn empty_list() Obj {
    return make_list(i64);
}

/// bytearray(size) — Obj wrapping ArrayList(u8) with zero-fill.
pub fn bytearray(size: anytype) Obj {
    const alloc = std.heap.page_allocator;
    const n: usize = if (@TypeOf(size) == usize) size else @intCast(size);
    const p = alloc.create(std.ArrayList(u8)) catch @panic("alloc failed");
    p.* = std.ArrayList(u8).initCapacity(alloc, n) catch std.ArrayList(u8).init(alloc);
    p.appendNTimes(0, n) catch {};
    const rc = alloc.create(usize) catch @panic("alloc failed");
    rc.* = 1;
    return Obj{ .data = @ptrCast(p), .vtable = @ptrCast(&EMPTY_VT), .rc = rc, .drop_fn = null };
}

/// Copy bytes/bytearray Obj as an independent ArrayList(u8).
pub fn bytes_copy(src: Obj) Obj {
    const alloc = std.heap.page_allocator;
    const src_list: *std.ArrayList(u8) = @ptrCast(@alignCast(src.data));
    const p = alloc.create(std.ArrayList(u8)) catch @panic("alloc failed");
    p.* = std.ArrayList(u8).init(alloc);
    p.ensureTotalCapacity(src_list.items.len) catch {};
    p.appendSlice(src_list.items) catch {};
    const rc = alloc.create(usize) catch @panic("alloc failed");
    rc.* = 1;
    return Obj{ .data = @ptrCast(p), .vtable = @ptrCast(&EMPTY_VT), .rc = rc, .drop_fn = null };
}

/// Convert list[i64] to list[u8] (Python bytes(list) semantics).
pub fn list_to_bytes(src: Obj) Obj {
    const alloc = std.heap.page_allocator;
    const int_list: *std.ArrayList(i64) = @ptrCast(@alignCast(src.data));
    const p = alloc.create(std.ArrayList(u8)) catch @panic("alloc failed");
    p.* = std.ArrayList(u8).init(alloc);
    p.ensureTotalCapacity(int_list.items.len) catch {};
    for (int_list.items) |v| {
        p.append(@intCast(v & 0xFF)) catch {};
    }
    const rc = alloc.create(usize) catch @panic("alloc failed");
    rc.* = 1;
    return Obj{ .data = @ptrCast(p), .vtable = @ptrCast(&EMPTY_VT), .rc = rc, .drop_fn = null };
}

/// Append a value to an Obj-managed list.
pub fn list_append(obj: Obj, comptime T: type, value: T) void {
    const p: *std.ArrayList(T) = @ptrCast(@alignCast(obj.data));
    p.append(value) catch {};
}

/// Get an element from an Obj-managed list (supports negative indices).
pub fn list_get(obj: Obj, comptime T: type, idx: i64) T {
    const p: *std.ArrayList(T) = @ptrCast(@alignCast(obj.data));
    const len: i64 = @intCast(p.items.len);
    const real_idx: usize = @intCast(if (idx < 0) idx + len else idx);
    return p.items[real_idx];
}

/// Set an element in an Obj-managed list (supports negative indices).
pub fn list_set(obj: Obj, comptime T: type, idx: i64, value: T) void {
    const p: *std.ArrayList(T) = @ptrCast(@alignCast(obj.data));
    const len: i64 = @intCast(p.items.len);
    const real_idx: usize = @intCast(if (idx < 0) idx + len else idx);
    p.items[real_idx] = value;
}

/// Get the length of an Obj-managed list.
pub fn list_len(obj: Obj, comptime T: type) i64 {
    const p: *std.ArrayList(T) = @ptrCast(@alignCast(obj.data));
    return @as(i64, @intCast(p.items.len));
}

pub fn list_clear(obj: Obj, comptime T: type) void {
    const p: *std.ArrayList(T) = @ptrCast(@alignCast(obj.data));
    p.clearRetainingCapacity();
}

/// Get the items slice of an Obj-managed list (for iteration).
pub fn list_items(obj: Obj, comptime T: type) []T {
    const p: *std.ArrayList(T) = @ptrCast(@alignCast(obj.data));
    return p.items;
}

pub fn list_slice(obj: Obj, comptime T: type, start: i64, end: i64) Obj {
    const p: *std.ArrayList(T) = @ptrCast(@alignCast(obj.data));
    const len: i64 = @intCast(p.items.len);
    var s = start;
    var e = end;
    if (s < 0) s += len;
    if (e < 0) e += len;
    if (s < 0) s = 0;
    if (e < s) e = s;
    if (e > len) e = len;
    const out = make_list(T);
    var i = s;
    while (i < e) : (i += 1) {
        list_append(out, T, p.items[@intCast(i)]);
    }
    return out;
}

/// Pop the last element from an Obj-managed list (Python list.pop()).
pub fn list_pop(obj: Obj, comptime T: type) T {
    const p: *std.ArrayList(T) = @ptrCast(@alignCast(obj.data));
    return p.pop().?;
}

/// Remove the last element from an Obj-managed list (void variant for pop without return).
pub fn list_pop_void(obj: Obj, comptime T: type) void {
    const p: *std.ArrayList(T) = @ptrCast(@alignCast(obj.data));
    _ = p.pop();
}

/// Append a slice to an Obj-managed list.
pub fn list_extend(obj: Obj, comptime T: type, src: Obj) void {
    const dst: *std.ArrayList(T) = @ptrCast(@alignCast(obj.data));
    const s: *std.ArrayList(T) = @ptrCast(@alignCast(src.data));
    dst.appendSlice(s.items) catch {};
}

pub fn list_reverse(obj: Obj, comptime T: type) void {
    const p: *std.ArrayList(T) = @ptrCast(@alignCast(obj.data));
    var i: usize = 0;
    var j: usize = p.items.len;
    while (i < j) {
        j -= 1;
        if (i >= j) break;
        const tmp = p.items[i];
        p.items[i] = p.items[j];
        p.items[j] = tmp;
        i += 1;
    }
}

pub fn list_sort_i64(obj: Obj) void {
    const p: *std.ArrayList(i64) = @ptrCast(@alignCast(obj.data));
    std.sort.heap(i64, p.items, {}, comptime std.sort.asc(i64));
}

pub fn set_add(obj: Obj, comptime T: type, value: T) void {
    if (!contains(obj, value)) {
        list_append(obj, T, value);
    }
}

pub fn set_discard(obj: Obj, comptime T: type, value: T) void {
    const p: *std.ArrayList(T) = @ptrCast(@alignCast(obj.data));
    var i: usize = 0;
    while (i < p.items.len) : (i += 1) {
        if (p.items[i] == value) {
            _ = p.orderedRemove(i);
            return;
        }
    }
}

pub fn set_remove(obj: Obj, comptime T: type, value: T) void {
    set_discard(obj, T, value);
}

/// Empty vtable placeholder for containers.
const EMPTY_VT = struct {};

// ─── String operations ───

/// String index: str[i] → single-char slice (Python semantics).
pub fn str_index(s: []const u8, idx: i64) []const u8 {
    const len: i64 = @intCast(s.len);
    const real: usize = @intCast(if (idx < 0) idx + len else idx);
    return s[real .. real + 1];
}

/// String slice: str[start:end] → sub-slice (Python semantics).
pub fn str_slice(s: []const u8, start: i64, end: i64) []const u8 {
    const len: i64 = @intCast(s.len);
    var s0 = if (start < 0) start + len else start;
    var e0 = if (end < 0) end + len else end;
    if (s0 < 0) s0 = 0;
    if (e0 > len) e0 = len;
    if (s0 >= e0) return "";
    return s[@intCast(s0)..@intCast(e0)];
}

/// Python str.isdigit() — check if single char is a digit.
pub fn char_isdigit(s: []const u8) bool {
    if (s.len == 0) return false;
    return s[0] >= '0' and s[0] <= '9';
}

/// Python str.isalpha() — check if single char is alphabetic.
pub fn char_isalpha(s: []const u8) bool {
    if (s.len == 0) return false;
    const c = s[0];
    return (c >= 'A' and c <= 'Z') or (c >= 'a' and c <= 'z');
}

/// Parse integer from string (Python int(s)).
pub fn str_to_int(s: []const u8) i64 {
    var result: i64 = 0;
    var neg = false;
    var i: usize = 0;
    if (i < s.len and (s[i] == '-' or s[i] == '+')) {
        neg = s[i] == '-';
        i += 1;
    }
    while (i < s.len) : (i += 1) {
        const c = s[i];
        if (c < '0' or c > '9') break;
        result = result * 10 + @as(i64, c - '0');
    }
    return if (neg) -result else result;
}

/// HashMap get with default value.
pub fn dict_get_default(comptime V: type, map: std.StringHashMap(V), key: []const u8, default: V) V {
    return map.get(key) orelse default;
}

pub fn dict_get_optional(comptime V: type, map: std.StringHashMap(V), key: []const u8) ?V {
    return map.get(key);
}

pub fn dict_pop(comptime V: type, map: *std.StringHashMap(V), key: []const u8, default: V) V {
    _ = default;
    return map.fetchRemove(key).?.value;
}

pub fn dict_setdefault(comptime V: type, map: *std.StringHashMap(V), key: []const u8, default: V) V {
    if (map.get(key)) |value| {
        return value;
    }
    map.put(key, default) catch {};
    return default;
}

pub fn dict_keys(comptime V: type, map: std.StringHashMap(V)) Obj {
    const out = make_list([]const u8);
    var it = map.iterator();
    while (it.next()) |entry| {
        list_append(out, []const u8, entry.key_ptr.*);
    }
    return out;
}

pub fn dict_values(comptime V: type, map: std.StringHashMap(V)) Obj {
    const out = make_list(V);
    var it = map.iterator();
    while (it.next()) |entry| {
        list_append(out, V, entry.value_ptr.*);
    }
    return out;
}

/// Slice (stub — kept for backward compat, prefer str_slice).
pub fn slice(lower: anytype, upper: anytype) void {
    _ = lower;
    _ = upper;
    return;
}

/// Legacy list_from (backward compat — returns Obj now).
pub fn list_from(comptime T: type, items: []const T) Obj {
    return make_list_from(T, items);
}

/// list_from_any is no longer used; tuple-element lists are expanded to
/// make_list + list_append sequences by the emitter.

/// time.perf_counter() — seconds since arbitrary epoch.
pub fn perf_counter() f64 {
    const ns = std.time.nanoTimestamp();
    return @as(f64, @floatFromInt(ns)) / 1_000_000_000.0;
}

/// File handle (wraps std.fs.File as integer handle).
pub fn file_open(path: []const u8) PyObject {
    const alloc = std.heap.page_allocator;
    // Ensure parent directories exist (Python open() creates files but expects dirs)
    if (std.mem.lastIndexOfScalar(u8, path, '/')) |sep| {
        const dir_path = path[0..sep];
        if (dir_path.len > 0) {
            std.fs.cwd().makePath(dir_path) catch {};
        }
    }
    const p = alloc.create(std.fs.File) catch @panic("alloc failed");
    p.* = std.fs.cwd().createFile(path, .{}) catch @panic("file open failed");
    return @as(PyObject, @intCast(@intFromPtr(p)));
}

pub fn file_write(handle: PyObject, data: anytype) void {
    const p: *std.fs.File = @ptrFromInt(@as(usize, @intCast(handle)));
    const T = @TypeOf(data);
    if (T == Obj) {
        // Obj wrapping ArrayList — write as bytes
        file_write_obj(p, data);
    } else if (@typeInfo(T) == .pointer) {
        p.writeAll(data) catch {};
    }
}

fn file_write_obj(p: *std.fs.File, obj: Obj) void {
    // Obj is always ArrayList(u8) from list_to_bytes / bytearray
    const al: *std.ArrayList(u8) = @ptrCast(@alignCast(obj.data));
    if (al.items.len > 0) {
        p.writeAll(al.items) catch {};
    }
}

pub fn file_close(handle: PyObject) void {
    const p: *std.fs.File = @ptrFromInt(@as(usize, @intCast(handle)));
    p.close();
}
