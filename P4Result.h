/*
 * PythonClientAPI. Wrapper around P4API.
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
 * $Id: //depot/main/p4-python/P4Result.h#18 $
 *
 */

#ifndef P4RESULT_H
#define P4RESULT_H

namespace p4py
{

class P4Result
{
public:

    P4Result(PythonDebug * dbg, SpecMgr * s);
    ~P4Result();
    
    // Setting
    int         AddOutput( const char *msg );
    int         AddOutput( PyObject * out );
    int	        AddTrack( PyObject * t );
    int         AddError( Error *e );
    void	ClearTrack();
    void	SetApiLevel( int level ) { apiLevel = level; }

    // Getting
    PyObject *	GetOutput();
    PyObject *	GetErrors()     { Py_INCREF(errors); return errors;     }
    PyObject *	GetWarnings()   { Py_INCREF(warnings); return warnings; }
    PyObject *	GetMessages()   { Py_INCREF(messages); return messages; }
    PyObject *	GetTrack()	{ Py_INCREF(track); return track; }

    // Get errors/warnings as a formatted string
    void        FmtErrors( StrBuf &buf );
    void        FmtWarnings( StrBuf &buf );

    // Testing
    int         ErrorCount();
    int         WarningCount();
    bool	FatalError() { return fatal; }

    // Clear previous results
    void        Reset();

    // does not incr reference, this is the caller's responsibility
    PyObject *	GetOutputInternal() { return output; }

private:
    int         Length( PyObject * ary );
    void        Fmt( const char *label, PyObject * list, StrBuf &buf );
    int		AppendString(PyObject * list, const char * str);

    PyObject *	  output;
    PyObject *	  warnings;
    PyObject *	  errors;
    PyObject *	  messages;
    PyObject *	  track;
    SpecMgr *	  specMgr;
    PythonDebug * debug;
    int           apiLevel;
    bool	  fatal;
};
}

#endif
