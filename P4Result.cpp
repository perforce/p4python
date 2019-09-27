/*******************************************************************************

Copyright (c) 2007-2008, Perforce Software, Inc.  All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1.  Redistributions of source code must retain the above copyright
    notice, this list of conditions and the following disclaimer.

2.  Redistributions in binary form must reproduce the above copyright
    notice, this list of conditions and the following disclaimer in the
    documentation and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTR
IBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
ARE DISCLAIMED. IN NO EVENT SHALL PERFORCE SOFTWARE, INC. BE LIABLE FOR ANY
DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

$Id: //depot/main/p4-python/P4Result.cpp#19 $
*******************************************************************************/

#include <Python.h>
#include <bytesobject.h>
#include "undefdups.h"
#include "python2to3.h"
#include <clientapi.h>

#include "P4PythonDebug.h"
#include "SpecMgr.h"
#include "P4Result.h"
#include "PythonMessage.h"
#include "P4PythonDebug.h"
#include "PythonTypes.h"

#include <iostream>

using namespace std;

namespace p4py {


P4Result::P4Result(PythonDebug * dbg, SpecMgr * s)
    : output(NULL),
      warnings(NULL),
      errors(NULL),
      messages(NULL),
      track(NULL),
      specMgr(s),
      debug(dbg),
      fatal(false)
{
    apiLevel = atoi( P4Tag::l_client );

    Reset();
}

P4Result::~P4Result()
{
    // reduce references to Python objects to avoid memory leaks
    
    if (output) 
        Py_DECREF(output);
    
    if (warnings) 
        Py_DECREF(warnings);
    
    if (errors)
        Py_DECREF(errors);

    if (messages)
        Py_DECREF(messages);

    if (track)
	Py_DECREF(track);
}

PyObject * P4Result::GetOutput()
{   
    PyObject * temp = output;
    output = NULL;  // last reference is removed by caller
    return temp;
}

void
P4Result::Reset()
{
    if (output)
        Py_DECREF(output);
    output = PyList_New(0);
    
    if (warnings) 
        Py_DECREF(warnings);
    warnings = PyList_New(0);
    
    if (errors)
        Py_DECREF(errors);
    errors = PyList_New(0);
    
    if (messages)
        Py_DECREF(messages);
    messages = PyList_New(0);

    if (track)
	Py_DECREF(track);
    track = PyList_New(0);

    if (output == NULL
	    || warnings == NULL
	    || errors == NULL
	    || messages == NULL
	    || track == NULL) {
    	cerr << "[P4Result::P4Result] Error creating lists" << endl;
    }

    fatal = false;
}

int P4Result::AppendString(PyObject * list, const char * str)
{
    PyObject *s = specMgr->CreatePyString(str);
    if (!s) {
	return -1;
    }
    if (PyList_Append(list, s) == -1) {
    	return -1;
    }
    Py_DECREF(s);

    return 0;
}

int P4Result::AddOutput( const char *msg )
{
    return AppendString(output, msg);
}

int P4Result::AddTrack( PyObject * t )
{
    if (PyList_Append(track, t) == -1) {
    	return -1;
    }
    Py_DECREF(t);

    return 0;
}

void P4Result::ClearTrack()
{
    if (track)
	Py_DECREF(track);
    track = PyList_New(0);
}

int P4Result::AddOutput( PyObject * out )
{
    if (PyList_Append(output, out) == -1) {
    	return -1;
    }
    Py_DECREF(out);

    return 0;
}

int
P4Result::AddError( Error *e )
{
    int s;
    s = e->GetSeverity();

    // 
    // Empty and informational messages are pushed out as output as nothing
    // worthy of error handling has occurred. Warnings go into the warnings
    // list and the rest are lumped together as errors.
    //

    StrBuf m;
    e->Fmt( &m, EF_PLAIN );

    // TODO: collect all return codes, report error if not 0

    if ( s == E_EMPTY || s == E_INFO ) {
	AddOutput( m.Text() );
	debug->info( m.Text() );
    }
    else if ( s == E_WARN ) {
	AppendString(warnings, m.Text() );
	debug->warning( m.Text() );
    }
    else {
	AppendString(errors, m.Text() );

	if( s == E_FATAL ) {
	    fatal = true;
	    debug->critical( m.Text() );
	}
	else {
	    debug->error( m.Text() );
	}
    }

    P4Message * msg = (P4Message *) PyObject_New(P4Message, &P4MessageType);
    msg->msg = new PythonMessage(e, specMgr);

    if (PyList_Append(messages, (PyObject *) msg) == -1) {
	return -1;
    }

    Py_DECREF(msg);

    return 0;
}

int
P4Result::ErrorCount()
{
    return PyList_Size( errors );
}

int
P4Result::WarningCount()
{
    return PyList_Size( warnings );
}

void
P4Result::FmtErrors( StrBuf &buf )
{
    Fmt( "[Error]: ", errors, buf );
}

void
P4Result::FmtWarnings( StrBuf &buf )
{
    Fmt( "[Warning]: ", warnings, buf );
}


int
P4Result::Length( PyObject * list )
{
    return PyList_Size( list );
}

void
P4Result::Fmt( const char *label, PyObject * list, StrBuf &buf )
{
    buf.Clear();
    // If the array is empty, then we just return
    if( PyList_Size(list) == 0 ) return;

    // This is the string we'll use to prefix each entry in the array
    StrBuf csep;
    
    csep << "\n\t" << label;
    
    // Instead of letting Python joining the separate strings
    // we do this ourselves. Only problem is: the objects in the list
    // might not be a string, but a P4Message object.
    // So we call repr() on the object. Since repr(aString) == aString
    // this can be safely done

    Py_ssize_t len = PyList_GET_SIZE(list);
    for (Py_ssize_t i = 0; i < len; i++) {
	buf << csep;
	PyObject * obj = PyList_GET_ITEM(list, i);
	reprfunc repr = obj->ob_type->tp_repr;
	PyObject * str = (*repr)(obj);
	buf << GetPythonString(str);
    }
}

}