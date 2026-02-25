using System;
using System.Collections;
using System.Collections.Generic;
using System.Globalization;
using System.Reflection;

namespace Pytra.CsModule
{
    // Python の print 相当を提供する最小ランタイム。
    public static class py_runtime
    {
        public const long PYTRA_TID_NONE = 0;
        public const long PYTRA_TID_BOOL = 1;
        public const long PYTRA_TID_INT = 2;
        public const long PYTRA_TID_FLOAT = 3;
        public const long PYTRA_TID_STR = 4;
        public const long PYTRA_TID_LIST = 5;
        public const long PYTRA_TID_DICT = 6;
        public const long PYTRA_TID_SET = 7;
        public const long PYTRA_TID_OBJECT = 8;
        private const long PYTRA_USER_TYPE_ID_BASE = 1000;

        private static long _pyNextTypeId = PYTRA_USER_TYPE_ID_BASE;
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
            RegisterTypeNode(PYTRA_TID_NONE, -1);
            RegisterTypeNode(PYTRA_TID_OBJECT, -1);
            RegisterTypeNode(PYTRA_TID_INT, PYTRA_TID_OBJECT);
            RegisterTypeNode(PYTRA_TID_BOOL, PYTRA_TID_INT);
            RegisterTypeNode(PYTRA_TID_FLOAT, PYTRA_TID_OBJECT);
            RegisterTypeNode(PYTRA_TID_STR, PYTRA_TID_OBJECT);
            RegisterTypeNode(PYTRA_TID_LIST, PYTRA_TID_OBJECT);
            RegisterTypeNode(PYTRA_TID_DICT, PYTRA_TID_OBJECT);
            RegisterTypeNode(PYTRA_TID_SET, PYTRA_TID_OBJECT);
            RecomputeTypeRanges();
        }

        private static long NormalizeBaseTypeId(long baseTypeId)
        {
            long baseTid = baseTypeId;
            if (baseTid < 0)
            {
                baseTid = PYTRA_TID_OBJECT;
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

        public static long py_register_class_type(long baseTypeId = PYTRA_TID_OBJECT)
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

        public static long py_runtime_type_id(object value)
        {
            EnsureBuiltinTypeTable();
            if (value == null)
            {
                return PYTRA_TID_NONE;
            }
            if (value is bool)
            {
                return PYTRA_TID_BOOL;
            }
            if (value is sbyte || value is byte || value is short || value is ushort || value is int || value is uint || value is long || value is ulong)
            {
                return PYTRA_TID_INT;
            }
            if (value is float || value is double || value is decimal)
            {
                return PYTRA_TID_FLOAT;
            }
            if (value is string)
            {
                return PYTRA_TID_STR;
            }
            if (value is IDictionary)
            {
                return PYTRA_TID_DICT;
            }
            if (IsSetLike(value))
            {
                return PYTRA_TID_SET;
            }
            if (value is IList)
            {
                return PYTRA_TID_LIST;
            }

            Type t = value.GetType();
            FieldInfo field = t.GetField("PYTRA_TYPE_ID", BindingFlags.Public | BindingFlags.Static);
            if (field != null)
            {
                object raw = field.GetValue(null);
                if (raw is long taggedLong && _pyTypeBase.ContainsKey(taggedLong))
                {
                    return taggedLong;
                }
                if (raw is int taggedInt && _pyTypeBase.ContainsKey(taggedInt))
                {
                    return taggedInt;
                }
            }
            return PYTRA_TID_OBJECT;
        }

        public static bool py_is_subtype(long actualTypeId, long expectedTypeId)
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

        public static bool py_issubclass(long actualTypeId, long expectedTypeId)
        {
            return py_is_subtype(actualTypeId, expectedTypeId);
        }

        public static bool py_isinstance(object value, long expectedTypeId)
        {
            return py_is_subtype(py_runtime_type_id(value), expectedTypeId);
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

        public static List<byte> py_bytes(List<byte> source)
        {
            return new List<byte>(source);
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

        public static long py_len<T>(List<T> source)
        {
            return source.Count;
        }

        public static long py_len(string source)
        {
            return source.Length;
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
            if (value is string s)
            {
                string t = s.Trim();
                if (!long.TryParse(t, NumberStyles.Integer, CultureInfo.InvariantCulture, out long parsed))
                {
                    throw new ArgumentException("invalid literal for int()");
                }
                return parsed;
            }
            return Convert.ToInt64(value);
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
            Console.WriteLine(string.Join(" ", args));
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
                    if (Equals(item, needle))
                    {
                        return true;
                    }
                }
            }

            return false;
        }
    }
}
