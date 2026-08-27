#include <Python.h>

#include <stdlib.h>

int
main(int argc, char **argv)
{
    if (setenv("PYTHONPATH", "/ranex/runtime/data/python312.zip:/ranex/runtime/lib", 1) != 0) {
        return 125;
    }
    return Py_BytesMain(argc, argv);
}
