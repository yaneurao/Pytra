using System;
using System.Collections.Generic;
using System.Linq;
using Any = System.Object;
using int64 = System.Int64;
using float64 = System.Double;
using str = System.String;
using Pytra.CsModule;

public class deque
{
    public static readonly long PYTRA_TYPE_ID = Pytra.CsModule.py_runtime.py_register_class_type(Pytra.CsModule.py_runtime.PYTRA_TID_OBJECT);
    public System.Collections.Generic.List<long> _items;
    
    public deque()
    {
        this._items = new System.Collections.Generic.List<long>();
    }
    
    public void append(long value)
    {
        this._items.Add(value);
    }
    
    public void appendleft(long value)
    {
        this._items.insert(0, value);
    }
    
    public long pop()
    {
        if (((this._items).Count) == (0)) {
            throw new System.Exception("pop from empty deque");
        }
        return this._items.pop();
    }
    
    public long popleft()
    {
        if (((this._items).Count) == (0)) {
            throw new System.Exception("pop from empty deque");
        }
        long item = Pytra.CsModule.py_runtime.py_get(this._items, 0);
        this._items = Pytra.CsModule.py_runtime.py_slice(this._items, System.Convert.ToInt64(1), null);
        return item;
    }
    
    public long __len__()
    {
        return (this._items).Count;
    }
    
    public void clear()
    {
        this._items = new System.Collections.Generic.List<long>();
    }
}

public static class Program
{
    public static void Main(string[] args)
    {
    }
}
