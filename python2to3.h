/*
 * PythonTypes.h
 *
 * Copyright (c) 2007-2008, Perforce Software, Inc.  All rights reserved.
 * 
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are met:
 * 
 * 1.  Redistributions of source code must retain the above copyright
 *     notice, this list of conditions and the following disclaimer.
 * 
 * 2.  Redistributions in binary form must reproduce the above copyright
 *     notice, this list of conditions and the following disclaimer in the
 *     documentation and/or other materials provided with the distribution.
 * 
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTR
 * IBUTORS "AS IS"
 * AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 * IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
 * ARE DISCLAIMED. IN NO EVENT SHALL PERFORCE SOFTWARE, INC. BE LIABLE FOR ANY
 * DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
 * (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
 * LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
 * ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
 * (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
 * SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 * 
 * $Id: //depot/main/p4-python/python2to3.h#6 $
 *
 * Build instructions:
 *  Use Distutils - see accompanying setup.py
 *
 *      python setup.py install
 *
 */
 
#ifndef PYTHON2TO3_H
#define PYTHON2TO3_H
 
#if PY_MAJOR_VERSION >= 3
#define PyInt_Check PyLong_Check
#define PyInt_AS_LONG PyLong_AS_LONG
#define PyInt_AsLong PyLong_AsLong
#define PyInt_FromLong PyLong_FromLong
#define StringType PyUnicode_Type

// The following functions are implemented in SpecMgr.cpp

PyObject * CreatePythonStringAndSize(const char * text, size_t len, const char *encoding = "");

PyObject * CreatePythonString(const char * text, const char *encoding = "");

inline bool IsString(PyObject *obj) {
    return PyUnicode_Check(obj);
}

const char * GetPythonString(PyObject *obj);

#else

#define StringType PyString_Type

inline PyObject * CreatePythonString(const char * text, const char *encoding = "") {
    if (text)
	return PyBytes_FromString(text);
    else
	Py_RETURN_NONE;
}

inline PyObject * CreatePythonStringAndSize(const char * text, size_t len, const char *encoding = "") {
    if (text)
	return PyBytes_FromStringAndSize(text, len);
    else
	Py_RETURN_NONE;
}

inline bool IsString(PyObject *obj) {
    return PyBytes_Check(obj);
}

inline const char * GetPythonString(PyObject *obj) {
    return PyBytes_AsString(obj);
}


#endif // PY_MAJOR_VERSION

#endif // PYTHON2TO3_H
 
