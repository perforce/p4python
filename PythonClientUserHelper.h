#ifndef PYTHON_CLIENT_USER_HELPER_H
#define PYTHON_CLIENT_USER_HELPER_H

#include <Python.h>

class PythonClientUser;

void PythonClientUserSetPendingException(PythonClientUser *ui,
        PyObject *type, PyObject *value, PyObject *tb);

#endif
