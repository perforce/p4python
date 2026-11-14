#ifndef PYTHON_CLIENT_USER_HELPER_H
#define PYTHON_CLIENT_USER_HELPER_H

#include <Python.h>

class PythonClientUser;

bool PythonClientUserSetPendingCurrentException(PythonClientUser *ui);
int PythonClientUserIsAlive(PythonClientUser *ui);

#endif
