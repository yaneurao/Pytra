// Pytra Zig runtime – minimal built-in helpers.
// This file is loaded by generated Zig programs via @import("py_runtime.zig").

const std = @import("std");

/// Print a single value followed by newline, Python-style.
pub fn print(value: anytype) void {
    const writer = std.io.getStdOut().writer();
    printValue(writer, value);
    writer.writeAll("\n") catch {};
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
        .Int, .ComptimeInt => {
            writer.print("{d}", .{value}) catch {};
        },
        .Float, .ComptimeFloat => {
            printFloat(writer, value);
        },
        .Bool => {
            writer.writeAll(if (value) "True" else "False") catch {};
        },
        .Pointer => |ptr_info| {
            if (ptr_info.size == .Slice and ptr_info.child == u8) {
                writer.writeAll(value) catch {};
            } else if (ptr_info.size == .One) {
                // *const [N:0]u8 (string literal) → coerce to slice
                const child_info = @typeInfo(ptr_info.child);
                if (child_info == .Array and child_info.Array.child == u8) {
                    writer.writeAll(value) catch {};
                } else {
                    writer.print("{any}", .{value}) catch {};
                }
            } else {
                writer.print("{any}", .{value}) catch {};
            }
        },
        .Optional => {
            if (value) |v| {
                printValue(writer, v);
            } else {
                writer.writeAll("None") catch {};
            }
        },
        .Null => {
            writer.writeAll("None") catch {};
        },
        .Void => {
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
    switch (@typeInfo(T)) {
        .Bool => return value,
        .Int, .ComptimeInt => return value != 0,
        .Float, .ComptimeFloat => return value != 0.0,
        .Optional => return value != null,
        .Null => return false,
        .Pointer => |ptr_info| {
            if (ptr_info.size == .Slice) {
                return value.len > 0;
            }
            return true;
        },
        else => return true,
    }
}

/// Convert a value to string representation (stub).
pub fn to_str(value: anytype) []const u8 {
    _ = value;
    return "<value>";
}

/// Concatenate two strings.
pub fn str_concat(a: []const u8, b: []const u8) []const u8 {
    const alloc = std.heap.page_allocator;
    const buf = alloc.alloc(u8, a.len + b.len) catch return "";
    @memcpy(buf[0..a.len], a);
    @memcpy(buf[a.len..], b);
    return buf;
}

/// Join multiple string slices.
pub fn str_join(parts: anytype) []const u8 {
    const alloc = std.heap.page_allocator;
    var total: usize = 0;
    for (parts) |p| {
        total += p.len;
    }
    const buf = alloc.alloc(u8, total) catch return "";
    var pos: usize = 0;
    for (parts) |p| {
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

/// isinstance check (stub).
pub fn isinstance_check(obj: anytype, typ: anytype) bool {
    _ = obj;
    _ = typ;
    return false;
}

/// Contains check (stub for `in` operator).
pub fn contains(haystack: anytype, needle: anytype) bool {
    _ = haystack;
    _ = needle;
    return false;
}

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

/// Empty list (stub for comprehensions).
pub fn empty_list() void {
    return;
}

/// Slice (stub).
pub fn slice(lower: anytype, upper: anytype) void {
    _ = lower;
    _ = upper;
    return;
}
