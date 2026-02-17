using System.Collections.Generic;
using System.IO;
using System;

public static class Program
{
    public static void main()
    {
        Pytra.CsModule.py_path root = new Pytra.CsModule.py_path(Convert.ToString("test/obj/pathlib_case32"));
        root.mkdir(parents: true, exist_ok: true);
        var child = (root / "values.txt");
        child.write_text("42");
        Pytra.CsModule.py_runtime.print(child.exists());
        Pytra.CsModule.py_runtime.print(child.name());
        Pytra.CsModule.py_runtime.print(child.stem());
        Pytra.CsModule.py_runtime.print(((double)(child.parent()) / (double)("values.txt")).exists());
        Pytra.CsModule.py_runtime.print(child.read_text());
    }

    public static void Main(string[] args)
    {
        main();
    }
}
