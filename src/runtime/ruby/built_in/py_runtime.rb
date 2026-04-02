# Ruby native backend runtime helpers.
# Provides Python built-in functions only (print, len, range, int, float, str, etc.).
# pytra.std.* / pytra.utils.* functions are provided by generated modules
# and their _native seam files.

def __pytra_noop(*args)
  _ = args
  nil
end

def __pytra_assert(*args)
  _ = args
  "True"
end

def __pytra_truthy(v)
  return false if v.nil?
  return v if v == true || v == false
  return v != 0 if v.is_a?(Integer)
  return v != 0.0 if v.is_a?(Float)
  return !v.empty? if v.respond_to?(:empty?)
  true
end

def __pytra_int(v)
  return 0 if v.nil?
  v.to_i
end

def __pytra_float(v)
  return 0.0 if v.nil?
  v.to_f
end

def __pytra_cast(_type_hint, value)
  value
end

def __pytra_div(a, b)
  lhs = __pytra_float(a)
  rhs = __pytra_float(b)
  raise ZeroDivisionError, "division by zero" if rhs == 0.0
  lhs / rhs
end

def __pytra_str(v)
  return "" if v.nil?
  return "True" if v == true
  return "False" if v == false
  return v if v.is_a?(String)
  if v.is_a?(PytraTuple) || v.is_a?(Array) || v.is_a?(Hash) || v.is_a?(Set)
    return __pytra_repr(v)
  end
  v.to_s
end

def __pytra_repr(v)
  return "None" if v.nil?
  return "True" if v == true
  return "False" if v == false
  if v.is_a?(String)
    return "'" + v.gsub("\\", "\\\\").gsub("'", "\\'") + "'"
  end
  if v.is_a?(PytraTuple)
    items = v.map { |item| __pytra_repr(item) }
    return "(" + items[0] + ",)" if items.length == 1
    return "(" + items.join(", ") + ")"
  end
  if v.is_a?(Array)
    return "[" + v.map { |item| __pytra_repr(item) }.join(", ") + "]"
  end
  if v.is_a?(Hash)
    return "{" + v.map { |k, val| __pytra_repr(k) + ": " + __pytra_repr(val) }.join(", ") + "}"
  end
  if v.is_a?(Set)
    return "{" + v.to_a.map { |item| __pytra_repr(item) }.join(", ") + "}"
  end
  v.to_s
end

class PytraTuple < Array
end

def __pytra_tuple(items)
  tuple = PytraTuple.new
  items.each { |item| tuple << item }
  tuple
end

def __pytra_len(v)
  return 0 if v.nil?
  return v.length if v.respond_to?(:length)
  0
end

def __pytra_as_list(v)
  return v if v.is_a?(Array)
  return v.chars if v.is_a?(String)
  return v.to_a if v.respond_to?(:to_a)
  []
end

def __pytra_as_dict(v)
  return v if v.is_a?(Hash)
  {}
end

def __pytra_bytearray(v = nil)
  return [] if v.nil?
  if v.is_a?(Integer)
    n = v
    n = 0 if n < 0
    return Array.new(n, 0)
  end
  if v.is_a?(String)
    return v.bytes
  end
  src = __pytra_as_list(v)
  out = []
  i = 0
  while i < src.length
    out << (__pytra_int(src[i]) & 255)
    i += 1
  end
  out
end

def __pytra_bytes(v = nil)
  return [] if v.nil?
  return v.bytes if v.is_a?(String)
  src = __pytra_as_list(v)
  out = []
  i = 0
  while i < src.length
    out << (__pytra_int(src[i]) & 255)
    i += 1
  end
  out
end

def __pytra_range(*args)
  if args.length == 1
    start_v = 0
    stop_v = args[0]
    step_v = 1
  elsif args.length == 2
    start_v = args[0]
    stop_v = args[1]
    step_v = 1
  else
    start_v = args[0]
    stop_v = args[1]
    step_v = args[2]
  end
  out = []
  step = __pytra_int(step_v)
  return out if step == 0
  i = __pytra_int(start_v)
  stop = __pytra_int(stop_v)
  while ((step >= 0 && i < stop) || (step < 0 && i > stop))
    out << i
    i += step
  end
  out
end

def __pytra_list_comp_range(start_v, stop_v, step_v)
  out = []
  step = __pytra_int(step_v)
  return out if step == 0
  i = __pytra_int(start_v)
  stop = __pytra_int(stop_v)
  while ((step >= 0 && i < stop) || (step < 0 && i > stop))
    out << yield(i)
    i += step
  end
  out
end

def __pytra_enumerate(v, start = 0)
  src = __pytra_as_list(v)
  out = []
  i = 0
  base = __pytra_int(start)
  while i < src.length
    out << [base + i, src[i]]
    i += 1
  end
  out
end

def __pytra_abs(v)
  x = __pytra_float(v)
  x < 0 ? -x : x
end

def __pytra_get_index(container, index)
  if container.is_a?(Array)
    i = __pytra_int(index)
    i += container.length if i < 0
    return nil if i < 0 || i >= container.length
    return container[i]
  end
  if container.is_a?(Hash)
    return container[index]
  end
  if container.is_a?(String)
    i = __pytra_int(index)
    i += container.length if i < 0
    return "" if i < 0 || i >= container.length
    return container[i] || ""
  end
  nil
end

def __pytra_set_index(container, index, value)
  if container.is_a?(Array)
    i = __pytra_int(index)
    i += container.length if i < 0
    return if i < 0 || i >= container.length
    container[i] = value
    return
  end
  if container.is_a?(Hash)
    container[index] = value
  end
end

def __pytra_slice(container, lower, upper)
  return nil if container.nil?
  lo = __pytra_int(lower)
  hi = __pytra_int(upper)
  container[lo...hi]
end

def __pytra_min(a, b)
  __pytra_float(a) < __pytra_float(b) ? a : b
end

def __pytra_max(a, b)
  __pytra_float(a) > __pytra_float(b) ? a : b
end

def __pytra_isdigit(v)
  s = __pytra_str(v)
  return false if s.empty?
  !!(s =~ /\A[0-9]+\z/)
end

def __pytra_isalpha(v)
  s = __pytra_str(v)
  return false if s.empty?
  !!(s =~ /\A[A-Za-z]+\z/)
end

def __pytra_lstrip(s, chars = nil)
  txt = __pytra_str(s)
  return txt.lstrip if chars.nil?
  cut = __pytra_str(chars)
  i = 0
  while i < txt.length && cut.include?(txt[i])
    i += 1
  end
  txt[i..] || ""
end

def __pytra_rstrip(s, chars = nil)
  txt = __pytra_str(s)
  return txt.rstrip if chars.nil?
  cut = __pytra_str(chars)
  i = txt.length - 1
  while i >= 0 && cut.include?(txt[i])
    i -= 1
  end
  return "" if i < 0
  txt[0..i]
end

def __pytra_strip(s, chars = nil)
  __pytra_rstrip(__pytra_lstrip(s, chars), chars)
end

def __pytra_contains(container, item)
  return false if container.nil?
  return container.key?(item) if container.is_a?(Hash)
  return container.include?(item) if container.is_a?(Set)
  return container.include?(item) if container.is_a?(Array)
  return container.include?(__pytra_str(item)) if container.is_a?(String)
  false
end

def __pytra_print(*args)
  if args.empty?
    puts
    return
  end
  puts(args.map { |x| __pytra_str(x) }.join(" "))
end

def write_stderr(text)
  $stderr.write(__pytra_str(text))
end

def write_stdout(text)
  $stdout.write(__pytra_str(text))
end

# Python built-in `open(path, mode)` shim.
class PyFile
  def initialize(path, mode)
    @io = File.open(path, mode)
  end
  def read
    @io.read
  end
  def write(data)
    if data.is_a?(Array)
      @io.write(data.pack("C*"))
    else
      @io.write(__pytra_str(data))
    end
  end
  def close
    @io.close
  end
end

def open(path, mode = "r")
  PyFile.new(__pytra_str(path), mode)
end

def ord(ch)
  s = __pytra_str(ch)
  s.empty? ? 0 : s.ord
end

def chr(n)
  __pytra_int(n).chr(Encoding::UTF_8)
end

class PytraSys
  attr_accessor :argv, :path
  def initialize
    @argv = ARGV
    @path = []
  end
  def set_argv(values)
    @argv = values
    ARGV.replace(values)
  end
  def set_path(values)
    @path = values
  end
  def write_stderr(text)
    Kernel.write_stderr(text)
  end
  def write_stdout(text)
    Kernel.write_stdout(text)
  end
end

class PytraPathModule
  def join(*parts)
    File.join(*parts.map { |p| __pytra_str(p) })
  end
  def splitext(path)
    __pytra_splitext(path)
  end
  def basename(path)
    File.basename(__pytra_str(path))
  end
  def dirname(path)
    File.dirname(__pytra_str(path))
  end
  def exists(path)
    File.exist?(__pytra_str(path))
  end
end

PYTRA_SYS = PytraSys.new
PYTRA_PATH = PytraPathModule.new

def sys
  PYTRA_SYS
end

def __pytra_path
  PYTRA_PATH
end

def __pytra_reversed(v)
  return __pytra_as_list(v).reverse
end

# Python dict/str/list method shims via monkey-patching
class Hash
  def items
    self.map { |k, v| [k, v] }
  end
  def get(key, default_val = nil)
    self.key?(key) ? self[key] : default_val
  end
  def keys
    self.map { |k, _| k }
  end
  def values
    self.map { |_, v| v }
  end
  def pop(key, *default_val)
    if self.key?(key)
      v = self[key]
      self.delete(key)
      return v
    end
    return default_val[0] if default_val.length > 0
    raise KeyError, "key not found: #{key}"
  end
  def setdefault(key, default_val = nil)
    unless self.key?(key)
      self[key] = default_val
    end
    self[key]
  end
  def update(other)
    self.merge!(other)
  end
end

class String
  def startswith(prefix)
    self.start_with?(prefix)
  end
  def endswith(suffix)
    self.end_with?(suffix)
  end
  def upper
    self.upcase
  end
  def lower
    self.downcase
  end
  def find(sub, start = 0)
    idx = self[start..].index(sub)
    idx.nil? ? -1 : idx + start
  end
  def rfind(sub)
    idx = self.rindex(sub)
    idx.nil? ? -1 : idx
  end
  def count(sub)
    self.scan(sub).length
  end
  def zfill(width)
    s = self
    w = __pytra_int(width)
    return s if s.length >= w
    pad = "0" * (w - s.length)
    if s.length > 0 && (s[0] == "-" || s[0] == "+")
      return s[0] + pad + s[1..]
    end
    pad + s
  end
end

class Array
  def copy
    self.dup
  end
end

# Python Enum base class
class Enum
  attr_reader :name, :value
  def initialize(name, value)
    @name = name
    @value = value
  end
  def to_s
    "#{self.class}.#{@name}"
  end
  def ==(other)
    return @value == other.value if other.is_a?(Enum)
    @value == other
  end
end

class IntEnum < Enum
  def to_i
    @value
  end
  def <=>(other)
    return @value <=> other.value if other.is_a?(IntEnum)
    @value <=> other
  end
  include Comparable
end

class IntFlag < IntEnum
  def |(other)
    v = other.is_a?(IntFlag) ? other.value : other
    IntFlag.new("#{@name}|#{other.is_a?(IntFlag) ? other.name : v}", @value | v)
  end
  def &(other)
    v = other.is_a?(IntFlag) ? other.value : other
    IntFlag.new("#{@name}&#{other.is_a?(IntFlag) ? other.name : v}", @value & v)
  end
end

# Floor division (Python semantics: floor toward negative infinity)
def __pytra_floordiv(a, b)
  af = __pytra_float(a)
  bf = __pytra_float(b)
  raise ZeroDivisionError, "division by zero" if bf == 0.0
  (af / bf).floor
end

# Math helpers
def __pytra_floor(v)
  __pytra_float(v).floor
end

def __pytra_ceil(v)
  __pytra_float(v).ceil
end

def __pytra_pow(base, exp)
  __pytra_float(base) ** __pytra_float(exp)
end

def __pytra_round(v, ndigits = 0)
  __pytra_float(v).round(ndigits)
end

def __pytra_trunc(v)
  __pytra_float(v).truncate
end

def __pytra_isfinite(v)
  __pytra_float(v).finite?
end

def __pytra_isinf(v)
  __pytra_float(v).infinite? != nil
end

def __pytra_isnan(v)
  __pytra_float(v).nan?
end

def __pytra_perf_counter
  Process.clock_gettime(Process::CLOCK_MONOTONIC)
end

def __pytra_zip(*args)
  return [] if args.empty?
  arrays = args.map { |a| __pytra_as_list(a) }
  min_len = arrays.map(&:length).min
  result = []
  i = 0
  while i < min_len
    tuple = arrays.map { |a| a[i] }
    result << tuple
    i += 1
  end
  result
end

def __pytra_sorted(v)
  __pytra_as_list(v).sort
end

def __pytra_makedirs(path, *args)
  require 'fileutils'
  FileUtils.mkdir_p(__pytra_str(path))
end

def __pytra_os_mkdir(path, exist_ok = false)
  dir = __pytra_str(path)
  return if exist_ok && File.exist?(dir)
  Dir.mkdir(dir)
end

def __pytra_splitext(path)
  txt = __pytra_str(path)
  ext = File.extname(txt)
  return [txt, ""] if ext == ""
  [txt[0...-ext.length], ext]
end

# sum built-in
def __pytra_sum(iterable, start = 0)
  __pytra_as_list(iterable).inject(start) { |s, x| s + x }
end

# type() built-in
def __pytra_type(obj)
  obj.class
end

# delete from dict/list
def __pytra_del(container, key)
  if container.is_a?(Hash)
    container.delete(key)
  elsif container.is_a?(Array)
    container.delete_at(__pytra_int(key))
  end
end
