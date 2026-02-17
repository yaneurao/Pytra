using System.Collections.Generic;
using System.IO;
using System;

public static class Program
{
    public static void main()
    {
        Pytra.CsModule.py_runtime.print((Math.Abs(Math.Tan(0.0)) < 1e-12));
        Pytra.CsModule.py_runtime.print((Math.Abs((Math.Log(Math.Exp(1.0)) - 1.0)) < 1e-12));
        Pytra.CsModule.py_runtime.print(Pytra.CsModule.py_runtime.py_int(Math.Log10(1000.0)));
        Pytra.CsModule.py_runtime.print(Pytra.CsModule.py_runtime.py_int((Math.Abs((-3.5)) * 10.0)));
        Pytra.CsModule.py_runtime.print(Pytra.CsModule.py_runtime.py_int(Math.Ceiling(2.1)));
        Pytra.CsModule.py_runtime.print(Pytra.CsModule.py_runtime.py_int(Math.Pow(2.0, 5.0)));
    }

    public static void Main(string[] args)
    {
        main();
    }
}
