/*******************************************************************************

Copyright (c) 2014, Sven Erik Knop, Perforce Software, Inc.  All rights reserved.

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

$Id$
*******************************************************************************/

#include <Python.h>
#include <iostream>

#include <debug.h>

#include "P4PythonDebug.h"
#include "PythonThreadGuard.h"

using namespace std;

PythonDebug::PythonDebug()
    : debugLevel(0)
{
    Py_INCREF(Py_None);
    logger = Py_None;
}

void PythonDebug::setDebug(int d)
{
    debugLevel = d;

    if( debugLevel > 8 )
	p4debug.SetLevel( "rpc=5" );
    else
	p4debug.SetLevel( "rpc=0" );
}

int PythonDebug::getDebug() const
{
    return debugLevel;
}

void PythonDebug::setLogger(PyObject * l)
{
    PyObject * tmp = logger;
    logger = l;
    Py_INCREF(logger);
    Py_DECREF(tmp);
}

PyObject * PythonDebug::getLogger () const
{
    Py_INCREF(logger);

    return logger;
}

void PythonDebug::printDebug(const char * text)
{
    cerr << text << endl;
}

void PythonDebug::printDebug(int minLevel, const char * text)
{
    if (debugLevel >= minLevel)
	printDebug(text);
}


void PythonDebug::callLogger(const char * method, const char * text)
{
    EnsurePythonLock guard;

    PyObject * result = PyObject_CallMethod( logger , (char*) method, (char*)"(s)", text );
    if( result == NULL ) { // exception thrown
	cerr << "Failed to call " << method << " on logger with (" << text << ")" << endl;
    }
}

void PythonDebug::debug (int minLevel, const char * text)
{
    if( debugLevel >= minLevel) {
	if (logger == Py_None) {
	    printDebug(text);
	}
	else {
	    callLogger("debug", text);
	}
    }
}

void PythonDebug::info (const char * text)
{
    if( debugLevel >= P4PYDBG_COMMANDS) {
	if (logger == Py_None) {
	    printDebug(text);
	}
	else {
	    callLogger("info", text);
	}
    }
}

void PythonDebug::warning (const char * text)
{
    if( debugLevel >= P4PYDBG_COMMANDS) {
    	if (logger == Py_None) {
    	    printDebug(text);
	}
	else {
	    callLogger("warning", text);
	}
    }
}

void PythonDebug::error (const char * text)
{
    if( debugLevel >= P4PYDBG_COMMANDS) {
	if (logger == Py_None) {
	    printDebug(text);
	}
	else {
	    callLogger("error", text);
	}
    }
}

void PythonDebug::critical (const char * text)
{
    if( debugLevel >= P4PYDBG_COMMANDS) {
    	if (logger == Py_None) {
    	    printDebug(text);
    	}
	else {
	    callLogger("critical", text);
	}
    }
}
