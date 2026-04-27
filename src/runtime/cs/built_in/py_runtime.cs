using System;
using System.Collections;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Reflection;

namespace Pytra.CsModule
{
    public sealed class PyArrayComparer<T> : IEqualityComparer<T[]>
    {
        public bool Equals(T[] left, T[] right)
        {
            return StructuralComparisons.StructuralEqualityComparer.Equals(left, right);
        }

        public int GetHashCode(T[] value)
        {
            return StructuralComparisons.StructuralEqualityComparer.GetHashCode(value);
        }
    }

    public sealed class PyFile : IDisposable
    {
        private readonly Stream _stream;
        private bool _closed;

        public PyFile(string path, string mode)
        {
            string m = mode ?? "r";
            bool binary = m.Contains("b");
            bool write = m.Contains("w");
            bool append = m.Contains("a");
            bool read = m.Contains("r") && !write && !append;
            if (!binary)
            {
                // Pytra generated image/runtime code only relies on binary mode.
                binary = true;
            }
            if (write)
            {
                _stream = new FileStream(path, FileMode.Create, FileAccess.Write);
                return;
            }
            if (append)
            {
                _stream = new FileStream(path, FileMode.Append, FileAccess.Write);
                return;
            }
            if (read)
            {
                _stream = new FileStream(path, FileMode.Open, FileAccess.Read);
                return;
            }
            _stream = new FileStream(path, FileMode.OpenOrCreate, FileAccess.ReadWrite);
        }

        public long write(object data)
        {
            EnsureOpen();
            if (!(_stream is FileStream))
            {
                throw new InvalidOperationException("stream is not file stream");
            }
            if (data is List<byte> listBytes)
            {
                byte[] arr = listBytes.ToArray();
                _stream.Write(arr, 0, arr.Length);
                return arr.Length;
            }
            if (data is byte[] bytes)
            {
                _stream.Write(bytes, 0, bytes.Length);
                return bytes.Length;
            }
            if (data is string text)
            {
                byte[] utf8 = System.Text.Encoding.UTF8.GetBytes(text);
                _stream.Write(utf8, 0, utf8.Length);
                return utf8.Length;
            }
            if (data is IEnumerable enumerable)
            {
                var outv = new List<byte>();
                foreach (object item in enumerable)
                {
                    outv.Add((byte)Convert.ToInt64(item, CultureInfo.InvariantCulture));
                }
                byte[] arr = outv.ToArray();
                _stream.Write(arr, 0, arr.Length);
                return arr.Length;
            }
            throw new ArgumentException("unsupported write() payload");
        }

        public string read()
        {
            EnsureOpen();
            _stream.Seek(0, SeekOrigin.Begin);
            using (var reader = new System.IO.StreamReader(_stream, System.Text.Encoding.UTF8, false, 4096, true))
            {
                return reader.ReadToEnd();
            }
        }

        public PyFile __enter__()
        {
            EnsureOpen();
            return this;
        }

        public object __exit__(object excType, object excValue, object traceback)
        {
            close();
            return null;
        }

        public void close()
        {
            if (_closed)
            {
                return;
            }
            _stream.Dispose();
            _closed = true;
        }

        public void Dispose()
        {
            close();
        }

        private void EnsureOpen()
        {
            if (_closed)
            {
                throw new ObjectDisposedException(nameof(PyFile));
            }
        }
    }

    // Python の print 相当を提供する最小ランタイム。
    public static class py_runtime
    {
        private const long TYPE_NONE = 0;
        private const long TYPE_BOOL = 1;
        private const long TYPE_INT = 2;
        private const long TYPE_FLOAT = 3;
        private const long TYPE_STR = 4;
        private const long TYPE_LIST = 5;
        private const long TYPE_DICT = 6;
        private const long TYPE_SET = 7;
        private const long TYPE_OBJECT = 8;
        private const long TYPE_BASE_EXCEPTION = 9;
        private const long TYPE_EXCEPTION = 10;
        private const long TYPE_RUNTIME_ERROR = 11;
        private const long TYPE_VALUE_ERROR = 12;
        private const long TYPE_TYPE_ERROR = 13;
        private const long TYPE_INDEX_ERROR = 14;
        private const long TYPE_KEY_ERROR = 15;
        private const long TYPE_INT8 = 16;
        private const long TYPE_INT16 = 17;
        private const long TYPE_INT32 = 18;
        private const long TYPE_INT64 = 19;
        private const long TYPE_UINT8 = 20;
        private const long TYPE_UINT16 = 21;
        private const long TYPE_UINT32 = 22;
        private const long TYPE_UINT64 = 23;
        private const long TYPE_FLOAT32 = 24;
        private const long TYPE_FLOAT64 = 25;
        private const long USER_TYPE_ID_BASE = 1000;

        private static long _pyNextTypeId = USER_TYPE_ID_BASE;
        private static readonly List<long> _pyTypeIds = new List<long>();
        private static readonly Dictionary<long, long> _pyTypeBase = new Dictionary<long, long>();
        private static readonly Dictionary<long, List<long>> _pyTypeChildren = new Dictionary<long, List<long>>();
        private static readonly Dictionary<long, long> _pyTypeOrder = new Dictionary<long, long>();
        private static readonly Dictionary<long, long> _pyTypeMin = new Dictionary<long, long>();
        private static readonly Dictionary<long, long> _pyTypeMax = new Dictionary<long, long>();

        static py_runtime()
        {
            EnsureBuiltinTypeTable();
        }

        private static bool ContainsLong(List<long> items, long value)
        {
            int i = 0;
            while (i < items.Count)
            {
                if (items[i] == value)
                {
                    return true;
                }
                i += 1;
            }
            return false;
        }

        private static void RemoveLong(List<long> items, long value)
        {
            int i = 0;
            while (i < items.Count)
            {
                if (items[i] == value)
                {
                    items.RemoveAt(i);
                    return;
                }
                i += 1;
            }
        }

        private static List<long> SortedCopy(List<long> items)
        {
            List<long> outv = new List<long>(items);
            outv.Sort();
            return outv;
        }

        private static void RegisterTypeNode(long typeId, long baseTypeId)
        {
            if (!ContainsLong(_pyTypeIds, typeId))
            {
                _pyTypeIds.Add(typeId);
            }

            long prevBase;
            if (_pyTypeBase.TryGetValue(typeId, out prevBase) && prevBase >= 0)
            {
                List<long> prevChildren;
                if (_pyTypeChildren.TryGetValue(prevBase, out prevChildren))
                {
                    RemoveLong(prevChildren, typeId);
                }
            }

            _pyTypeBase[typeId] = baseTypeId;
            if (!_pyTypeChildren.ContainsKey(typeId))
            {
                _pyTypeChildren[typeId] = new List<long>();
            }
            if (baseTypeId < 0)
            {
                return;
            }
            if (!_pyTypeChildren.ContainsKey(baseTypeId))
            {
                _pyTypeChildren[baseTypeId] = new List<long>();
            }
            List<long> children = _pyTypeChildren[baseTypeId];
            if (!ContainsLong(children, typeId))
            {
                children.Add(typeId);
            }
        }

        private static List<long> SortedChildTypeIds(long typeId)
        {
            List<long> children;
            if (!_pyTypeChildren.TryGetValue(typeId, out children))
            {
                return new List<long>();
            }
            return SortedCopy(children);
        }

        private static List<long> CollectRootTypeIds()
        {
            List<long> roots = new List<long>();
            int i = 0;
            while (i < _pyTypeIds.Count)
            {
                long typeId = _pyTypeIds[i];
                long baseTypeId;
                if (!_pyTypeBase.TryGetValue(typeId, out baseTypeId) || baseTypeId < 0 || !_pyTypeBase.ContainsKey(baseTypeId))
                {
                    roots.Add(typeId);
                }
                i += 1;
            }
            roots.Sort();
            return roots;
        }

        private static long AssignTypeRangesDfs(long typeId, long nextOrder)
        {
            _pyTypeOrder[typeId] = nextOrder;
            _pyTypeMin[typeId] = nextOrder;
            long cur = nextOrder + 1;
            List<long> children = SortedChildTypeIds(typeId);
            int i = 0;
            while (i < children.Count)
            {
                cur = AssignTypeRangesDfs(children[i], cur);
                i += 1;
            }
            _pyTypeMax[typeId] = cur - 1;
            return cur;
        }

        private static void RecomputeTypeRanges()
        {
            _pyTypeOrder.Clear();
            _pyTypeMin.Clear();
            _pyTypeMax.Clear();

            long nextOrder = 0;
            List<long> roots = CollectRootTypeIds();
            int i = 0;
            while (i < roots.Count)
            {
                nextOrder = AssignTypeRangesDfs(roots[i], nextOrder);
                i += 1;
            }

            List<long> allIds = SortedCopy(_pyTypeIds);
            i = 0;
            while (i < allIds.Count)
            {
                long typeId = allIds[i];
                if (!_pyTypeOrder.ContainsKey(typeId))
                {
                    nextOrder = AssignTypeRangesDfs(typeId, nextOrder);
                }
                i += 1;
            }
        }

        private static void EnsureBuiltinTypeTable()
        {
            if (_pyTypeIds.Count > 0)
            {
                return;
            }
            RegisterTypeNode(TYPE_NONE, -1);
            RegisterTypeNode(TYPE_OBJECT, -1);
            RegisterTypeNode(TYPE_INT, TYPE_OBJECT);
            RegisterTypeNode(TYPE_BOOL, TYPE_INT);
            RegisterTypeNode(TYPE_INT8, TYPE_INT);
            RegisterTypeNode(TYPE_INT16, TYPE_INT);
            RegisterTypeNode(TYPE_INT32, TYPE_INT);
            RegisterTypeNode(TYPE_INT64, TYPE_INT);
            RegisterTypeNode(TYPE_UINT8, TYPE_INT);
            RegisterTypeNode(TYPE_UINT16, TYPE_INT);
            RegisterTypeNode(TYPE_UINT32, TYPE_INT);
            RegisterTypeNode(TYPE_UINT64, TYPE_INT);
            RegisterTypeNode(TYPE_FLOAT, TYPE_OBJECT);
            RegisterTypeNode(TYPE_FLOAT32, TYPE_FLOAT);
            RegisterTypeNode(TYPE_FLOAT64, TYPE_FLOAT);
            RegisterTypeNode(TYPE_STR, TYPE_OBJECT);
            RegisterTypeNode(TYPE_LIST, TYPE_OBJECT);
            RegisterTypeNode(TYPE_DICT, TYPE_OBJECT);
            RegisterTypeNode(TYPE_SET, TYPE_OBJECT);
            RegisterTypeNode(TYPE_BASE_EXCEPTION, TYPE_OBJECT);
            RegisterTypeNode(TYPE_EXCEPTION, TYPE_BASE_EXCEPTION);
            RegisterTypeNode(TYPE_RUNTIME_ERROR, TYPE_EXCEPTION);
            RegisterTypeNode(TYPE_VALUE_ERROR, TYPE_EXCEPTION);
            RegisterTypeNode(TYPE_TYPE_ERROR, TYPE_EXCEPTION);
            RegisterTypeNode(TYPE_INDEX_ERROR, TYPE_EXCEPTION);
            RegisterTypeNode(TYPE_KEY_ERROR, TYPE_EXCEPTION);
            RecomputeTypeRanges();
        }

        private static long NormalizeBaseTypeId(long baseTypeId)
        {
            long baseTid = baseTypeId;
            if (baseTid < 0)
            {
                baseTid = TYPE_OBJECT;
            }
            if (!_pyTypeBase.ContainsKey(baseTid))
            {
                throw new ArgumentException("unknown base type_id");
            }
            return baseTid;
        }

        public static long py_register_type(long typeId, long baseTypeId)
        {
            EnsureBuiltinTypeTable();
            RegisterTypeNode(typeId, NormalizeBaseTypeId(baseTypeId));
            RecomputeTypeRanges();
            return typeId;
        }

        public static long py_register_class_type(long baseTypeId = TYPE_OBJECT)
        {
            EnsureBuiltinTypeTable();
            while (_pyTypeBase.ContainsKey(_pyNextTypeId))
            {
                _pyNextTypeId += 1;
            }
            long outv = _pyNextTypeId;
            _pyNextTypeId += 1;
            return py_register_type(outv, baseTypeId);
        }

        private static bool IsSetLike(object value)
        {
            Type t = value.GetType();
            Type[] interfaces = t.GetInterfaces();
            int i = 0;
            while (i < interfaces.Length)
            {
                Type iface = interfaces[i];
                if (iface.IsGenericType && iface.GetGenericTypeDefinition() == typeof(ISet<>))
                {
                    return true;
                }
                i += 1;
            }
            return false;
        }

        public static bool py_is_set(object value)
        {
            return value != null && IsSetLike(value);
        }

        public static long py_runtime_value_type_id(object value)
        {
            EnsureBuiltinTypeTable();
            if (value == null)
            {
                return TYPE_NONE;
            }
            if (value is bool)
            {
                return TYPE_BOOL;
            }
            if (value is sbyte)
            {
                return TYPE_INT8;
            }
            if (value is short)
            {
                return TYPE_INT16;
            }
            if (value is int)
            {
                return TYPE_INT32;
            }
            if (value is long)
            {
                return TYPE_INT64;
            }
            if (value is byte)
            {
                return TYPE_UINT8;
            }
            if (value is ushort)
            {
                return TYPE_UINT16;
            }
            if (value is uint)
            {
                return TYPE_UINT32;
            }
            if (value is ulong)
            {
                return TYPE_UINT64;
            }
            if (value is float)
            {
                return TYPE_FLOAT32;
            }
            if (value is double || value is decimal)
            {
                return TYPE_FLOAT64;
            }
            if (value is string)
            {
                return TYPE_STR;
            }
            if (value is KeyNotFoundException)
            {
                return TYPE_KEY_ERROR;
            }
            if (value is ArgumentOutOfRangeException)
            {
                return TYPE_INDEX_ERROR;
            }
            if (value is ArgumentException)
            {
                return TYPE_VALUE_ERROR;
            }
            if (value is InvalidCastException)
            {
                return TYPE_TYPE_ERROR;
            }
            if (value is Exception)
            {
                return TYPE_EXCEPTION;
            }
            if (value is IDictionary)
            {
                return TYPE_DICT;
            }
            if (IsSetLike(value))
            {
                return TYPE_SET;
            }
            if (value is IList)
            {
                return TYPE_LIST;
            }
            return TYPE_OBJECT;
        }

        private static long py_runtime_type_id(object value)
        {
            return py_runtime_value_type_id(value);
        }

        public static bool py_runtime_type_id_is_subtype(long actualTypeId, long expectedTypeId)
        {
            EnsureBuiltinTypeTable();
            long actualOrder;
            if (!_pyTypeOrder.TryGetValue(actualTypeId, out actualOrder))
            {
                return false;
            }
            long expectedMin;
            long expectedMax;
            if (!_pyTypeMin.TryGetValue(expectedTypeId, out expectedMin))
            {
                return false;
            }
            if (!_pyTypeMax.TryGetValue(expectedTypeId, out expectedMax))
            {
                return false;
            }
            return expectedMin <= actualOrder && actualOrder <= expectedMax;
        }

        private static bool py_is_subtype(long actualTypeId, long expectedTypeId)
        {
            return py_runtime_type_id_is_subtype(actualTypeId, expectedTypeId);
        }

        public static bool py_runtime_type_id_issubclass(long actualTypeId, long expectedTypeId)
        {
            return py_runtime_type_id_is_subtype(actualTypeId, expectedTypeId);
        }

        private static bool py_issubclass(long actualTypeId, long expectedTypeId)
        {
            return py_runtime_type_id_issubclass(actualTypeId, expectedTypeId);
        }

        public static bool py_runtime_value_isinstance(object value, long expectedTypeId)
        {
            return py_runtime_type_id_is_subtype(py_runtime_value_type_id(value), expectedTypeId);
        }

        private static bool py_isinstance(object value, long expectedTypeId)
        {
            return py_runtime_value_isinstance(value, expectedTypeId);
        }

        private static int NormalizeSliceIndex(long index, int length)
        {
            long v = index;
            if (v < 0)
            {
                v += length;
            }
            if (v < 0)
            {
                return 0;
            }
            if (v > length)
            {
                return length;
            }
            return (int)v;
        }

        private static int NormalizeIndex(long index, int length)
        {
            long v = index;
            if (v < 0)
            {
                v += length;
            }
            if (v < 0 || v >= length)
            {
                throw new ArgumentOutOfRangeException(nameof(index));
            }
            return (int)v;
        }

        public static List<T> py_slice<T>(List<T> source, long? start, long? stop)
        {
            if (source == null)
            {
                throw new ArgumentNullException(nameof(source));
            }
            int length = source.Count;
            int s = start.HasValue ? NormalizeSliceIndex(start.Value, length) : 0;
            int e = stop.HasValue ? NormalizeSliceIndex(stop.Value, length) : length;
            if (e < s)
            {
                return new List<T>();
            }
            return source.GetRange(s, e - s);
        }

        public static string py_slice(string source, long? start, long? stop)
        {
            if (source == null)
            {
                throw new ArgumentNullException(nameof(source));
            }
            int length = source.Length;
            int s = start.HasValue ? NormalizeSliceIndex(start.Value, length) : 0;
            int e = stop.HasValue ? NormalizeSliceIndex(stop.Value, length) : length;
            if (e < s)
            {
                return string.Empty;
            }
            return source.Substring(s, e - s);
        }

        public static List<byte> py_bytearray(object countLike)
        {
            int n = Convert.ToInt32(countLike);
            if (n < 0)
            {
                throw new ArgumentOutOfRangeException(nameof(countLike));
            }
            var outv = new List<byte>(n);
            for (int i = 0; i < n; i++)
            {
                outv.Add(0);
            }
            return outv;
        }

        public static PyFile open(object pathLike, object modeLike)
        {
            string path = Convert.ToString(pathLike, CultureInfo.InvariantCulture) ?? "";
            string mode = Convert.ToString(modeLike, CultureInfo.InvariantCulture) ?? "r";
            return new PyFile(path, mode);
        }

        public static PyFile open(object pathLike, object modeLike, object encoding)
        {
            _ = encoding;
            return open(pathLike, modeLike);
        }

        public static PyFile open(object pathLike)
        {
            return open(pathLike, "r");
        }

        public static List<byte> py_bytes(List<byte> source)
        {
            return new List<byte>(source);
        }

        public static List<byte> py_bytes(object source)
        {
            if (source == null)
            {
                return new List<byte>();
            }
            if (source is List<byte> listBytes)
            {
                return new List<byte>(listBytes);
            }
            if (source is byte[] rawBytes)
            {
                return new List<byte>(rawBytes);
            }
            if (source is string text)
            {
                return new List<byte>(System.Text.Encoding.UTF8.GetBytes(text));
            }
            if (source is IEnumerable enumerable)
            {
                var outv = new List<byte>();
                foreach (object item in enumerable)
                {
                    outv.Add((byte)Convert.ToInt64(item, CultureInfo.InvariantCulture));
                }
                return outv;
            }
            return new List<byte> { (byte)Convert.ToInt64(source, CultureInfo.InvariantCulture) };
        }

        public static List<T> py_concat<T>(IEnumerable<T> left, IEnumerable<T> right)
        {
            var outv = new List<T>();
            if (left != null)
            {
                outv.AddRange(left);
            }
            if (right != null)
            {
                outv.AddRange(right);
            }
            return outv;
        }

        public static long sum(IEnumerable<long> source)
        {
            long acc = 0;
            foreach (long value in source)
            {
                acc += value;
            }
            return acc;
        }

        public static double sum(IEnumerable<double> source)
        {
            double acc = 0.0;
            foreach (double value in source)
            {
                acc += value;
            }
            return acc;
        }

        public static List<object[]> zip<T, U>(IEnumerable<T> left, IEnumerable<U> right)
        {
            var outv = new List<object[]>();
            using (IEnumerator<T> itLeft = left.GetEnumerator())
            using (IEnumerator<U> itRight = right.GetEnumerator())
            {
                while (itLeft.MoveNext() && itRight.MoveNext())
                {
                    outv.Add(new object[] { itLeft.Current, itRight.Current });
                }
            }
            return outv;
        }

        public static List<object[]> enumerate<T>(IEnumerable<T> source)
        {
            return enumerate(source, 0L);
        }

        public static List<object[]> enumerate<T>(IEnumerable<T> source, object startLike)
        {
            long index = Convert.ToInt64(startLike, CultureInfo.InvariantCulture);
            var outv = new List<object[]>();
            foreach (T value in source)
            {
                outv.Add(new object[] { index, value });
                index += 1;
            }
            return outv;
        }

        public static List<T> reversed<T>(List<T> source)
        {
            var outv = new List<T>(source);
            outv.Reverse();
            return outv;
        }

        public static long index<T>(List<T> source, T value)
        {
            for (int i = 0; i < source.Count; i++)
            {
                if (py_equals(source[i], value))
                {
                    return i;
                }
            }
            throw new ArgumentException("value is not in list");
        }

        public static long index(string source, string value)
        {
            int idx = source.IndexOf(value, StringComparison.Ordinal);
            if (idx < 0)
            {
                throw new ArgumentException("substring is not in string");
            }
            return idx;
        }

        public static long count(string source, string value)
        {
            string haystack = source ?? "";
            string needle = value ?? "";
            if (needle.Length == 0)
            {
                return haystack.Length + 1L;
            }
            long total = 0L;
            int pos = 0;
            while (true)
            {
                int next = haystack.IndexOf(needle, pos, StringComparison.Ordinal);
                if (next < 0)
                {
                    return total;
                }
                total += 1L;
                pos = next + needle.Length;
            }
        }

        public static List<long> range(long stop)
        {
            return range(0L, stop, 1L);
        }

        public static List<long> range(long start, long stop)
        {
            return range(start, stop, 1L);
        }

        public static List<long> range(long start, long stop, long step)
        {
            List<long> outv = new List<long>();
            if (step == 0)
            {
                throw new ArgumentException("range() arg 3 must not be zero");
            }
            if (step > 0)
            {
                for (long value = start; value < stop; value += step)
                {
                    outv.Add(value);
                }
                return outv;
            }
            for (long value = start; value > stop; value += step)
            {
                outv.Add(value);
            }
            return outv;
        }

        public static string strip(string value)
        {
            return value.Trim();
        }

        public static string rstrip(string value)
        {
            return value.TrimEnd();
        }

        public static bool startswith(string value, string prefix)
        {
            return value.StartsWith(prefix, StringComparison.Ordinal);
        }

        public static bool endswith(string value, string suffix)
        {
            return value.EndsWith(suffix, StringComparison.Ordinal);
        }

        public static string replace(string value, string oldValue, string newValue)
        {
            return value.Replace(oldValue, newValue);
        }

        public static T min<T>(T left, T right) where T : IComparable<T>
        {
            return left.CompareTo(right) <= 0 ? left : right;
        }

        public static T max<T>(T left, T right) where T : IComparable<T>
        {
            return left.CompareTo(right) >= 0 ? left : right;
        }

        public static List<T> py_sorted<T>(List<T> source)
        {
            var outv = new List<T>(source ?? new List<T>());
            outv.Sort();
            return outv;
        }

        public static List<T> py_sorted<T>(HashSet<T> source)
        {
            var outv = new List<T>(source ?? new HashSet<T>());
            outv.Sort();
            return outv;
        }

        public static List<T> py_reversed_object<T>(IEnumerable<T> source)
        {
            var outv = new List<T>(source ?? new List<T>());
            outv.Reverse();
            return outv;
        }

        public static void py_set_update<T>(HashSet<T> target, object values)
        {
            if (target == null || values == null)
            {
                return;
            }
            if (values is IEnumerable<T> typed)
            {
                foreach (T item in typed)
                {
                    target.Add(item);
                }
                return;
            }
            if (values is IEnumerable raw)
            {
                foreach (object item in raw)
                {
                    if (item is T typedItem)
                    {
                        target.Add(typedItem);
                    }
                }
            }
        }

        public static List<byte> py_int_to_bytes(object valueLike, object lengthLike, object byteorderLike)
        {
            long value = Convert.ToInt64(valueLike, CultureInfo.InvariantCulture);
            int length = Convert.ToInt32(lengthLike, CultureInfo.InvariantCulture);
            string byteorder = Convert.ToString(byteorderLike, CultureInfo.InvariantCulture) ?? "little";
            if (length < 0)
            {
                throw new ArgumentOutOfRangeException(nameof(lengthLike));
            }
            var outv = new List<byte>(length);
            long cur = value;
            for (int i = 0; i < length; i++)
            {
                outv.Add((byte)(cur & 0xFF));
                cur >>= 8;
            }
            if (byteorder == "big")
            {
                outv.Reverse();
            }
            return outv;
        }

        public static T py_get<T>(List<T> source, object indexLike)
        {
            int idx = NormalizeIndex(Convert.ToInt64(indexLike), source.Count);
            return source[idx];
        }

        public static string py_get(string source, object indexLike)
        {
            int idx = NormalizeIndex(Convert.ToInt64(indexLike), source.Length);
            return source[idx].ToString();
        }

        public static V py_get<K, V>(Dictionary<K, V> source, K key)
        {
            return source[key];
        }

        public static string get(string source, object indexLike)
        {
            return py_get(source, indexLike);
        }

        public static V get<K, V>(Dictionary<K, V> source, K key)
        {
            return py_get(source, key);
        }

        public static object py_get(object source, object indexLike)
        {
            if (source is string text)
            {
                return py_get(text, indexLike);
            }
            if (source is IList list)
            {
                int idx = NormalizeIndex(Convert.ToInt64(indexLike), list.Count);
                return list[idx];
            }
            if (source is IDictionary dict)
            {
                return dict[indexLike];
            }
            if (source is Array array)
            {
                int idx = NormalizeIndex(Convert.ToInt64(indexLike), array.Length);
                return array.GetValue(idx);
            }
            throw new ArgumentException("unsupported py_get() source");
        }

        public static object get(object source, object indexLike)
        {
            return py_get(source, indexLike);
        }

        public static T[] py_array_cast<T>(object value)
        {
            if (value is T[] direct)
            {
                return direct;
            }
            if (value is IEnumerable enumerable)
            {
                var outv = new List<T>();
                foreach (object item in enumerable)
                {
                    outv.Add(py_convert_value<T>(item));
                }
                return outv.ToArray();
            }
            throw new ArgumentException("unsupported array cast");
        }

        public static void py_set<T>(List<T> source, object indexLike, object value)
        {
            int idx = NormalizeIndex(Convert.ToInt64(indexLike), source.Count);
            source[idx] = py_convert_value<T>(value);
        }

        public static void py_set<K, V>(Dictionary<K, V> source, K key, V value)
        {
            source[key] = value;
        }

        public static void py_append<T>(List<T> source, object value)
        {
            source.Add(py_convert_value<T>(value));
        }

        public static void clear<T>(List<T> source)
        {
            source.Clear();
        }

        public static void clear<K, V>(Dictionary<K, V> source)
        {
            source.Clear();
        }

        public static void clear<T>(HashSet<T> source)
        {
            source.Clear();
        }

        public static void extend<T>(List<T> source, IEnumerable<T> values)
        {
            source.AddRange(values);
        }

        public static void sort<T>(List<T> source)
        {
            source.Sort();
        }

        public static void reverse<T>(List<T> source)
        {
            source.Reverse();
        }

        public static IEqualityComparer<T[]> array_comparer<T>()
        {
            return new PyArrayComparer<T>();
        }

        public static List<T> py_repeat<T>(List<T> source, object timesLike)
        {
            long times = Convert.ToInt64(timesLike);
            List<T> outList = new List<T>();
            if (times <= 0)
            {
                return outList;
            }
            for (long i = 0; i < times; i++)
            {
                outList.AddRange(source);
            }
            return outList;
        }

        private static T py_convert_value<T>(object value)
        {
            if (value is T same)
            {
                return same;
            }
            Type target = typeof(T);
            try
            {
                if (target == typeof(string))
                {
                    return (T)(object)Convert.ToString(value, CultureInfo.InvariantCulture);
                }
                object converted = Convert.ChangeType(value, target, CultureInfo.InvariantCulture);
                return (T)converted;
            }
            catch
            {
                return (T)value;
            }
        }

        public static T py_pop<T>(List<T> source)
        {
            if (source.Count == 0)
            {
                throw new ArgumentOutOfRangeException(nameof(source));
            }
            int last = source.Count - 1;
            T value = source[last];
            source.RemoveAt(last);
            return value;
        }

        public static T py_pop<T>(List<T> source, object indexLike)
        {
            int idx = NormalizeIndex(Convert.ToInt64(indexLike), source.Count);
            T value = source[idx];
            source.RemoveAt(idx);
            return value;
        }

        public static V pop<K, V>(Dictionary<K, V> source, K key)
        {
            V value = source[key];
            source.Remove(key);
            return value;
        }

        public static V setdefault<K, V>(Dictionary<K, V> source, K key, V defaultValue)
        {
            V value;
            if (source.TryGetValue(key, out value))
            {
                return value;
            }
            source[key] = defaultValue;
            return defaultValue;
        }

        public static long py_len<T>(List<T> source)
        {
            return source.Count;
        }

        public static long py_len<T>(ICollection<T> source)
        {
            return source.Count;
        }

        public static long py_len(object source)
        {
            if (source == null)
            {
                return 0;
            }
            if (source is string text)
            {
                return text.Length;
            }
            if (source is ICollection collection)
            {
                return collection.Count;
            }
            MethodInfo lenMethod = source.GetType().GetMethod("__len__", Type.EmptyTypes);
            if (lenMethod != null)
            {
                object value = lenMethod.Invoke(source, null);
                return Convert.ToInt64(value, CultureInfo.InvariantCulture);
            }
            throw new ArgumentException("object has no len()");
        }

        public static long py_len(string source)
        {
            return source.Length;
        }

        public static T py_or<T>(Func<T> left, Func<T> right)
        {
            T value = left();
            if (py_bool(value))
            {
                return value;
            }
            return right();
        }

        public static T py_and<T>(Func<T> left, Func<T> right)
        {
            T value = left();
            if (py_bool(value))
            {
                return right();
            }
            return value;
        }

        public static List<K> py_dict_keys<K, V>(Dictionary<K, V> source)
        {
            return new List<K>(source.Keys);
        }

        public static List<object[]> py_dict_items<K, V>(Dictionary<K, V> source)
        {
            var outv = new List<object[]>();
            foreach (KeyValuePair<K, V> item in source)
            {
                outv.Add(new object[] { item.Key, item.Value });
            }
            return outv;
        }

        public static List<object[]> py_dict_items(System.Collections.IDictionary source)
        {
            var outv = new List<object[]>();
            foreach (System.Collections.DictionaryEntry item in source)
            {
                outv.Add(new object[] { item.Key, item.Value });
            }
            return outv;
        }

        public static List<V> py_dict_values<K, V>(Dictionary<K, V> source)
        {
            return new List<V>(source.Values);
        }

        public static Dictionary<string, object> py_dict_string_object(object value)
        {
            if (value is Dictionary<string, object> direct)
            {
                return direct;
            }
            if (value is IDictionary<string, object> generic)
            {
                return new Dictionary<string, object>(generic);
            }
            if (value is IDictionary dict)
            {
                var outv = new Dictionary<string, object>();
                foreach (DictionaryEntry item in dict)
                {
                    string key = Convert.ToString(item.Key, CultureInfo.InvariantCulture) ?? "";
                    outv[key] = item.Value;
                }
                return outv;
            }
            return (Dictionary<string, object>)value;
        }

        public static bool py_set_add<T>(HashSet<T> source, object value)
        {
            return source.Add(py_convert_value<T>(value));
        }

        public static bool py_set_discard<T>(HashSet<T> source, object value)
        {
            return source.Remove(py_convert_value<T>(value));
        }

        public static void py_set_remove<T>(HashSet<T> source, object value)
        {
            if (!source.Remove(py_convert_value<T>(value)))
            {
                throw new KeyNotFoundException();
            }
        }

        public static bool py_bool(object value)
        {
            if (value == null)
            {
                return false;
            }
            if (value is bool b)
            {
                return b;
            }
            if (value is long l)
            {
                return l != 0;
            }
            if (value is int i)
            {
                return i != 0;
            }
            if (value is double d)
            {
                return d != 0.0;
            }
            if (value is string s)
            {
                return s.Length != 0;
            }
            if (value is ICollection c)
            {
                return c.Count != 0;
            }
            return true;
        }

        private static bool py_is_numeric(object value)
        {
            if (value == null)
            {
                return false;
            }
            TypeCode code = Type.GetTypeCode(value.GetType());
            switch (code)
            {
                case TypeCode.Byte:
                case TypeCode.SByte:
                case TypeCode.Int16:
                case TypeCode.UInt16:
                case TypeCode.Int32:
                case TypeCode.UInt32:
                case TypeCode.Int64:
                case TypeCode.UInt64:
                case TypeCode.Single:
                case TypeCode.Double:
                case TypeCode.Decimal:
                    return true;
                default:
                    return false;
            }
        }

        private static bool py_equals(object left, object right)
        {
            if (left == null || right == null)
            {
                return Equals(left, right);
            }
            if (left is Array leftArray && right is Array rightArray)
            {
                return StructuralComparisons.StructuralEqualityComparer.Equals(leftArray, rightArray);
            }
            if (py_is_numeric(left) && py_is_numeric(right))
            {
                return Convert.ToDouble(left, CultureInfo.InvariantCulture)
                    == Convert.ToDouble(right, CultureInfo.InvariantCulture);
            }
            return Equals(left, right);
        }

        public static bool py_eq(object left, object right)
        {
            return py_equals(left, right);
        }

        private static string py_format_float(double value)
        {
            string text = value.ToString("R", CultureInfo.InvariantCulture).Replace("E", "e");
            if (!text.Contains(".") && !text.Contains("E") && !text.Contains("e"))
            {
                return text + ".0";
            }
            return text;
        }

        private static string py_quote_string(string value)
        {
            string text = value ?? "";
            text = text.Replace("\\", "\\\\");
            text = text.Replace("'", "\\'");
            text = text.Replace("\n", "\\n");
            text = text.Replace("\r", "\\r");
            text = text.Replace("\t", "\\t");
            return "'" + text + "'";
        }

        private static string py_format_list(IEnumerable source)
        {
            var parts = new List<string>();
            foreach (object item in source)
            {
                parts.Add(py_repr(item));
            }
            return "[" + string.Join(", ", parts) + "]";
        }

        private static string py_format_tuple(Array source)
        {
            var parts = new List<string>();
            foreach (object item in source)
            {
                parts.Add(py_repr(item));
            }
            if (parts.Count == 1)
            {
                return "(" + parts[0] + ",)";
            }
            return "(" + string.Join(", ", parts) + ")";
        }

        private static string py_format_dict(IDictionary source)
        {
            var parts = new List<string>();
            foreach (DictionaryEntry entry in source)
            {
                parts.Add(py_repr(entry.Key) + ": " + py_repr(entry.Value));
            }
            return "{" + string.Join(", ", parts) + "}";
        }

        private static string py_repr(object value)
        {
            if (value == null)
            {
                return "None";
            }
            if (value is bool boolean)
            {
                return boolean ? "True" : "False";
            }
            if (value is float f)
            {
                return py_format_float(f);
            }
            if (value is double d)
            {
                return py_format_float(d);
            }
            if (value is decimal m)
            {
                return py_format_float((double)m);
            }
            if (value is Exception ex)
            {
                return ex.Message;
            }
            if (value is string text)
            {
                return py_quote_string(text);
            }
            MethodInfo reprMethod = value.GetType().GetMethod("__repr__", BindingFlags.Instance | BindingFlags.Public, null, Type.EmptyTypes, null);
            if (reprMethod != null && reprMethod.ReturnType == typeof(string))
            {
                object rendered = reprMethod.Invoke(value, Array.Empty<object>());
                if (rendered is string renderedText)
                {
                    return renderedText;
                }
            }
            MethodInfo strMethod = value.GetType().GetMethod("__str__", BindingFlags.Instance | BindingFlags.Public, null, Type.EmptyTypes, null);
            if (strMethod != null && strMethod.ReturnType == typeof(string))
            {
                object rendered = strMethod.Invoke(value, Array.Empty<object>());
                if (rendered is string renderedText)
                {
                    return renderedText;
                }
            }
            if (value is IDictionary dictionary)
            {
                return py_format_dict(dictionary);
            }
            if (value is Array array)
            {
                return py_format_tuple(array);
            }
            if (value is IEnumerable enumerable)
            {
                return py_format_list(enumerable);
            }
            return Convert.ToString(value, CultureInfo.InvariantCulture);
        }

        private static string py_display(object value)
        {
            if (value == null)
            {
                return "None";
            }
            if (value is string text)
            {
                return text;
            }
            if (value is IDictionary dictionary)
            {
                return py_format_dict(dictionary);
            }
            if (value is Array array)
            {
                return py_format_tuple(array);
            }
            if (value is IEnumerable enumerable)
            {
                return py_format_list(enumerable);
            }
            if (value is bool boolean)
            {
                return boolean ? "True" : "False";
            }
            if (value is float f)
            {
                return py_format_float(f);
            }
            if (value is double d)
            {
                return py_format_float(d);
            }
            if (value is decimal m)
            {
                return py_format_float((double)m);
            }
            if (value is Exception ex)
            {
                return ex.Message;
            }
            MethodInfo strMethod = value.GetType().GetMethod("__str__", BindingFlags.Instance | BindingFlags.Public, null, Type.EmptyTypes, null);
            if (strMethod != null && strMethod.ReturnType == typeof(string))
            {
                object rendered = strMethod.Invoke(value, Array.Empty<object>());
                if (rendered is string renderedText)
                {
                    return renderedText;
                }
            }
            return Convert.ToString(value, CultureInfo.InvariantCulture);
        }

        public static string py_to_string(object value)
        {
            return py_display(value);
        }

        public static string lstrip(string value, string chars)
        {
            string text = value ?? "";
            if (string.IsNullOrEmpty(chars))
            {
                return text.TrimStart();
            }
            return text.TrimStart(chars.ToCharArray());
        }

        public static string lstrip(string value)
        {
            return lstrip(value, null);
        }

        public static Exception SystemExit(object code)
        {
            string text = py_to_string(code);
            return new Exception(text);
        }

        public static string py_chr(object codeLike)
        {
            int code = Convert.ToInt32(codeLike, CultureInfo.InvariantCulture);
            return char.ConvertFromUtf32(code);
        }

        public static string repeat_string(string text, object timesLike)
        {
            int times = Math.Max(0, Convert.ToInt32(timesLike, CultureInfo.InvariantCulture));
            if (times == 0 || string.IsNullOrEmpty(text))
            {
                return "";
            }
            return string.Concat(System.Linq.Enumerable.Repeat(text, times));
        }

        public static long find(string text, string needle)
        {
            return find(text, needle, 0L);
        }

        public static long find(string text, string needle, object startLike)
        {
            string haystack = text ?? "";
            string target = needle ?? "";
            int start = Math.Max(0, Convert.ToInt32(startLike, CultureInfo.InvariantCulture));
            if (start > haystack.Length)
            {
                return -1L;
            }
            return haystack.IndexOf(target, start, StringComparison.Ordinal);
        }

        public static long rfind(string text, string needle)
        {
            string haystack = text ?? "";
            string target = needle ?? "";
            return haystack.LastIndexOf(target, StringComparison.Ordinal);
        }

        public static long rfind(string text, string needle, object startLike)
        {
            string haystack = text ?? "";
            string target = needle ?? "";
            int start = Math.Max(0, Convert.ToInt32(startLike, CultureInfo.InvariantCulture));
            if (start >= haystack.Length)
            {
                return haystack.LastIndexOf(target, StringComparison.Ordinal);
            }
            return haystack.LastIndexOf(target, start, StringComparison.Ordinal);
        }

        public static List<string> split(string text)
        {
            return split(text, null);
        }

        public static List<string> split(string text, string sep)
        {
            string source = text ?? "";
            if (string.IsNullOrEmpty(sep))
            {
                return new List<string>(source.Split((char[])null, StringSplitOptions.RemoveEmptyEntries));
            }
            return new List<string>(source.Split(new[] { sep }, StringSplitOptions.None));
        }

        public static string upper(string value)
        {
            return (value ?? "").ToUpperInvariant();
        }

        public static string lower(string value)
        {
            return (value ?? "").ToLowerInvariant();
        }

        public static bool isspace(string value)
        {
            if (string.IsNullOrEmpty(value))
            {
                return false;
            }
            foreach (char ch in value)
            {
                if (!char.IsWhiteSpace(ch))
                {
                    return false;
                }
            }
            return true;
        }

        public static bool isalnum(string value)
        {
            if (string.IsNullOrEmpty(value))
            {
                return false;
            }
            foreach (char ch in value)
            {
                if (!char.IsLetterOrDigit(ch))
                {
                    return false;
                }
            }
            return true;
        }

        public static string py_format(object value, string spec)
        {
            if (string.IsNullOrEmpty(spec))
            {
                return py_to_string(value);
            }
            if (spec.EndsWith("%", StringComparison.Ordinal))
            {
                string innerSpec = spec.Substring(0, spec.Length - 1);
                return py_format(Convert.ToDouble(value, CultureInfo.InvariantCulture) * 100.0, innerSpec + "f") + "%";
            }
            char kind = spec[spec.Length - 1];
            string widthSpec = spec.Substring(0, spec.Length - 1);
            if (kind == 'd' || kind == 'x' || kind == 'X')
            {
                string text = kind == 'd'
                    ? Convert.ToInt64(value, CultureInfo.InvariantCulture).ToString("D", CultureInfo.InvariantCulture)
                    : Convert.ToInt64(value, CultureInfo.InvariantCulture).ToString(kind.ToString(), CultureInfo.InvariantCulture);
                if (int.TryParse(widthSpec, NumberStyles.Integer, CultureInfo.InvariantCulture, out int width) && width > text.Length)
                {
                    return text.PadLeft(width);
                }
                return text;
            }
            if (kind == 'f')
            {
                int precision = 6;
                int width = 0;
                if (widthSpec.StartsWith(".", StringComparison.Ordinal))
                {
                    int.TryParse(widthSpec.Substring(1), NumberStyles.Integer, CultureInfo.InvariantCulture, out precision);
                }
                else if (!string.IsNullOrEmpty(widthSpec))
                {
                    int dot = widthSpec.IndexOf('.');
                    if (dot >= 0)
                    {
                        int.TryParse(widthSpec.Substring(0, dot), NumberStyles.Integer, CultureInfo.InvariantCulture, out width);
                        int.TryParse(widthSpec.Substring(dot + 1), NumberStyles.Integer, CultureInfo.InvariantCulture, out precision);
                    }
                    else
                    {
                        int.TryParse(widthSpec, NumberStyles.Integer, CultureInfo.InvariantCulture, out width);
                    }
                }
                string text = Convert.ToDouble(value, CultureInfo.InvariantCulture).ToString("F" + precision.ToString(CultureInfo.InvariantCulture), CultureInfo.InvariantCulture);
                if (width > text.Length)
                {
                    return text.PadLeft(width);
                }
                return text;
            }
            return py_to_string(value);
        }

        public static bool py_isdigit(string value)
        {
            if (string.IsNullOrEmpty(value))
            {
                return false;
            }
            foreach (char ch in value)
            {
                if (!char.IsDigit(ch))
                {
                    return false;
                }
            }
            return true;
        }

        public static bool py_isalpha(string value)
        {
            if (string.IsNullOrEmpty(value))
            {
                return false;
            }
            foreach (char ch in value)
            {
                if (!char.IsLetter(ch))
                {
                    return false;
                }
            }
            return true;
        }

        public static long py_ord(string value)
        {
            if (string.IsNullOrEmpty(value) || value.Length != 1)
            {
                throw new ArgumentException("ord() expected a character");
            }
            return value[0];
        }

        public static long py_int(object value)
        {
            if (value == null)
            {
                throw new ArgumentException("int() argument must not be null");
            }
            if (value is bool b)
            {
                return b ? 1L : 0L;
            }
            if (value is sbyte || value is byte || value is short || value is ushort || value is int || value is uint || value is long || value is ulong)
            {
                return Convert.ToInt64(value, CultureInfo.InvariantCulture);
            }
            if (value is float f)
            {
                return checked((long)Math.Truncate((double)f));
            }
            if (value is double d)
            {
                return checked((long)Math.Truncate(d));
            }
            if (value is decimal m)
            {
                return checked((long)decimal.Truncate(m));
            }
            if (value is string s)
            {
                string t = s.Trim();
                if (!long.TryParse(t, NumberStyles.Integer, CultureInfo.InvariantCulture, out long parsed))
                {
                    throw new ArgumentException("invalid literal for int()");
                }
                return parsed;
            }
            return Convert.ToInt64(value, CultureInfo.InvariantCulture);
        }

        public static long py_floordiv(object left, object right)
        {
            long a = Convert.ToInt64(left);
            long b = Convert.ToInt64(right);
            if (b == 0)
            {
                throw new DivideByZeroException();
            }
            long q = a / b;
            long r = a % b;
            if (r != 0 && ((r > 0) != (b > 0)))
            {
                q -= 1;
            }
            return q;
        }

        public static long py_mod(object left, object right)
        {
            long a = Convert.ToInt64(left);
            long b = Convert.ToInt64(right);
            if (b == 0)
            {
                throw new DivideByZeroException();
            }
            long r = a % b;
            if (r != 0 && ((r > 0) != (b > 0)))
            {
                r += b;
            }
            return r;
        }

        public static void print(params object[] args)
        {
            if (args == null || args.Length == 0)
            {
                Console.WriteLine();
                return;
            }
            string[] rendered = new string[args.Length];
            for (int i = 0; i < args.Length; i++)
            {
                rendered[i] = py_display(args[i]);
            }
            Console.WriteLine(string.Join(" ", rendered));
        }

        // Python の `x in y` に相当する最小判定ヘルパ。
        public static bool py_in(object needle, object haystack)
        {
            if (haystack == null)
            {
                return false;
            }

            string text = haystack as string;
            if (text != null)
            {
                return text.Contains(Convert.ToString(needle));
            }

            IDictionary dict = haystack as IDictionary;
            if (dict != null)
            {
                return dict.Contains(needle);
            }

            IEnumerable enumerable = haystack as IEnumerable;
            if (enumerable != null)
            {
                foreach (object item in enumerable)
                {
                    if (py_equals(item, needle))
                    {
                        return true;
                    }
                }
            }

            return false;
        }
    }
}
