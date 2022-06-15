/*******************************************************************************

Copyright (c) 2010, Perforce Software, Inc.  All rights reserved.

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
 * Name		: PythonSpecData.cpp
 *
 * Author	: Sven Erik Knop <sknop@perforce.com>
 *
 * Description	: Python bindings for the Perforce API. SpecData subclass for
 * 		  P4Python. This class allows for manipulation of Spec data
 * 		  stored in a Python dict using the standard Perforce classes
 *
 ******************************************************************************/

#include <Python.h>
#include <bytesobject.h>
#include "undefdups.h"
#include "python2to3.h"
#include <clientapi.h>
#include <i18napi.h>
#include <spec.h>
#include "debug.h"
#include "P4PythonDebug.h"
#include "PythonSpecData.h"
#include <iostream>

using namespace std;

StrPtr *
PythonSpecData::GetLine( SpecElem *sd, int x, const char **cmt )
{
    PyObject * val = PyDict_GetItemString( dict, sd->tag.Text() );
    if( val == NULL ) return 0;

    if( !sd->IsList() )
    {
	if ( ! PyObject_IsInstance( val, (PyObject *) &StringType ) ) {
	    PyErr_WarnEx(PyExc_TypeError, "PythonSpecData::GetLine: value is not of type String",1);
	    return 0;
	}

	last = GetPythonString( val );

	return &last;
    }

    // It's a list, which means we should have an array value here
    // Let's see if the user provided a list

    if ( PyObject_IsInstance( val, (PyObject *) &PyList_Type ) ) {
        // GetLine keeps on asking for lines until we are exhausted.
        // This throws Python, so we need to bail early

        if ( x >= PyList_Size(val) ) {
          return 0;
        }

        val = PyList_GetItem( val, x );
        if( val == NULL ) {
          cout << "GetLine: SEVERE error!" << endl;
          return 0;
        }

        if ( ! PyObject_IsInstance( val, (PyObject *) &StringType ) ) {
            PyErr_WarnEx(PyExc_TypeError, "PythonSpecData::GetLine: value is not of type String",1);
            return 0;
        }

        last = GetPythonString( val );
        return &last;
    }
    else if ( PyObject_IsInstance( val, (PyObject *) &StringType )) {
        // We got a String but expected a list. Let's treat this as a list of 1 element

        if ( x > 0 ) {
            return 0; // we've already delivered the item, this time we bail
        }

        last = GetPythonString(val);

        return &last;
    }

    PyErr_WarnEx(PyExc_TypeError, "PythonSpecData::GetLine: value is not of type String or List",1);

    return 0; // safety
}

void	
PythonSpecData::SetLine( SpecElem *sd, int x, const StrPtr *v, Error *e )
{
    char * key = sd->tag.Text();
    PyObject * val = CreatePythonString( v->Text() );

    if( sd->IsList() )
    {
	PyObject * list = PyDict_GetItemString( dict, key );

	if( list == NULL )
	{
	    list = PyList_New(0);
	    PyDict_SetItemString( dict, key, list );
	    Py_DECREF(list);
	}

	PyList_Append( list, val );
	Py_DECREF( val );
    }
    else
    {
	PyDict_SetItemString( dict, key, val );
	    Py_DECREF( val );
    }
    return;
}

void
PythonSpecData::Comment( SpecElem *sd, int x, const char **wv, int nl, Error *e)
{
    char * key = sd->tag.Text(); // this will be "Protections" for the protection table
    const char * comment = *wv;

    if( sd->IsList() ) {
	PyObject * list = PyDict_GetItemString(dict, key);

	if( list == NULL ) {
	    list = PyList_New(0);
	    PyDict_SetItemString( dict, key, list );
	    Py_DECREF(list);
	}

	if( nl ) {
	    PyObject * content = CreatePythonString(comment);
	    PyList_Append(list, content);
	    Py_DECREF(content);
	}
	else { // append case
	    Py_ssize_t size = PyList_Size( list );

	    PyObject * content = PyList_GetItem(list, size - 1); // last element
	    const char * contentStr = GetPythonString(content);

	    StrBuf newContent = contentStr;
	    newContent << " ";
	    newContent << comment;

	    contentStr = newContent.Text();

	    content = CreatePythonString(contentStr);
	    PyList_SetItem(list, size - 1, content); // replace last element
	}

    }
    else
    {
	// ignore these entries for now
    }
}
