/*******************************************************************************

Copyright (c) 2024, Perforce Software, Inc.  All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1.  Redistributions of source code must retain the above copyright
    notice, this list of conditions and the following disclaimer.

2.  Redistributions in binary form must reproduce the above copyright
    notice, this list of conditions and the following disclaimer in the
    documentation and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
ARE DISCLAIMED. IN NO EVENT SHALL PERFORCE SOFTWARE, INC. BE LIABLE FOR ANY
DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

*******************************************************************************/

/*******************************************************************************
 * Name     : PythonKeepAlive.cpp
 *
 * Author   : Himanshu Jain <hjain@perforce.com>
 *
 * Description  : C++ subclass for KeepAlive used by Python KeepAlive.
 *                Allows Perforce API to implement a customized IsAlive function
 *
 * $Id: //depot/main/p4-python/PythonKeepAlive.cpp#1 $
 *
 ******************************************************************************/

#include <Python.h>
#include <keepalive.h>
#include "PythonThreadGuard.h"
#include "PythonKeepAlive.h"

PythonKeepAlive::PythonKeepAlive(PyObject* callable) : py_callable(callable) {
    // Increment the reference count for the callable
    Py_XINCREF(py_callable);
}

PythonKeepAlive::~PythonKeepAlive() {
    // Decrement the reference count for the callable
    Py_XDECREF(py_callable);
}

int PythonKeepAlive::IsAlive() {

    EnsurePythonLock guard;

    if (py_callable && PyCallable_Check(py_callable)) {
        PyObject* result = PyObject_CallObject(py_callable, NULL);
        if (result != NULL && PyLong_Check(result) && PyLong_AsLong(result) == 0) {
            Py_DECREF(result);
            return( 0 ); // To terminate the connection
        }
        
        return( 1 );
    }

    return( 1 ); // Default to true if callable is not set or failed
}