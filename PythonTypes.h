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
 * $Id: //depot/main/p4-python/PythonTypes.h#12 $
 *
 * Build instructions:
 *  Use Distutils - see accompanying setup.py
 *
 *      python setup.py install
 *
 */

#ifndef PYTHON_TYPES_H
#define PYTHON_TYPES_H

class PythonClientAPI;
class PythonMergeData;
class PythonActionMergeData;

namespace p4py {
class P4MapMaker;
}
class PythonMessage;

/* C container for P4Adapter */
typedef struct {
    PyObject_HEAD
    PythonClientAPI *clientAPI;      /* The Perforce object we're wrapping */
} P4Adapter;

/* C container for MergeData */
typedef struct {
    PyObject_HEAD
    PythonMergeData *mergeData;      /* The mergeData object we're wrapping */
} P4MergeData;

/* C container for ActionMergeData */
typedef struct {
    PyObject_HEAD
    PythonActionMergeData *mergeData;      /* The mergeData object we're wrapping */
} P4ActionMergeData;

/* C container for Map */
typedef struct {
    PyObject_HEAD
    p4py::P4MapMaker *map;
} P4Map;

/* C container for Map */
typedef struct {
    PyObject_HEAD
    PythonMessage *msg;
} P4Message;

extern PyTypeObject P4MergeDataType;
extern PyTypeObject P4ActionMergeDataType;
extern PyTypeObject P4MapType;
extern PyObject * P4Error;
extern PyObject * P4OutputHandler;
extern PyObject * P4Progress;
extern PyTypeObject P4MessageType;

#endif
