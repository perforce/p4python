/*******************************************************************************

Copyright (c) 2012, Perforce Software, Inc.  All rights reserved.

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
 * Name		: PythonClientProgress.cpp
 *
 * Author	: Sven Erik Knop <sknop@perforce.com>
 *
 * Description	: C++ Subclass for ClientProgress used by Python ClientProgress.
 * 		  Allows Perforce API to indicate progress of calls to P4Python
 *
 * 		  $Id: //depot/main/p4-python/PythonClientProgress.cpp#5 $
 *
 ******************************************************************************/

#include <Python.h>
#include <bytesobject.h>
#include "undefdups.h"
#include "python2to3.h"
#include <clientapi.h>
#include <clientprog.h>
#include <strtable.h>

#include <iostream>
#include <iomanip>

#include "P4PythonDebug.h"
#include "SpecMgr.h"
#include "P4Result.h"
#include "PythonClientUser.h"
#include "P4PythonDebug.h"
#include "PythonThreadGuard.h"
#include "PythonClientProgress.h"
#include "PythonMessage.h"
#include "PythonTypes.h"

using namespace std;

PythonClientProgress::PythonClientProgress(PyObject * prog, int type)
    :	progress(prog)
{
    EnsurePythonLock guard;

    PyObject * res = PyObject_CallMethod( this->progress , (char*) "init", (char*)"i", type );
    if( res ) {
	Py_DECREF( res );
    }
    else {
	cout << "Exception thrown in init" << endl;
	PyErr_PrintEx(0);
    }
}

PythonClientProgress::~PythonClientProgress()
{
    this->progress = NULL;
}

void PythonClientProgress::Description( const StrPtr *desc, int units )
{
    EnsurePythonLock guard;

    PyObject * res = PyObject_CallMethod( this->progress , (char*) "setDescription", (char*)"si", desc->Text(), units );
    if( res ) {
	Py_DECREF( res );
    }
    else {
	cout << "Exception thrown in setDescription" << endl;
    }
}

void PythonClientProgress::Total( long total )
{
    EnsurePythonLock guard;

    PyObject * res = PyObject_CallMethod( this->progress , (char*) "setTotal", (char*)"i", total );
    if( res ) {
	Py_DECREF( res );
    }
    else {
	cout << "Exception thrown in setTotal" << endl;
    }

}

int PythonClientProgress::Update( long pos )
{
    EnsurePythonLock guard;

    PyObject * result = PyObject_CallMethod( this->progress , (char*) "update", (char*)"l", pos );
    if( result == NULL ) { // exception thrown
	cout << "Exception thrown in update" << endl;
	return 1; // TODO: Is this the correct value to return in case of an error?
    }
    else {
	Py_DECREF( result );
    }

    return 0;
}

void PythonClientProgress::Done( int fail )
{
    EnsurePythonLock guard;

    PyObject * res = PyObject_CallMethod( this->progress , (char*) "done", (char*)"i", fail );
    if( res ) {
	Py_DECREF( res );
    }
    else {
	    cout << "Exception thrown in Done" << endl;
    }
}

