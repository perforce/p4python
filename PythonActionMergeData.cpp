/*
 * PythonActionMergeData.cpp
 *
 * Copyright (c) 2012, Perforce Software, Inc.  All rights reserved.
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
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
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
 * $Id: //depot/main/p4-python/PythonActionMergeData.cpp#3 $
 */

#include <Python.h>
#include <bytesobject.h>
#include "undefdups.h"
#include "python2to3.h"
#include <clientapi.h>
#include <i18napi.h>
#include <strtable.h>
#include <enviro.h>
#include <hostenv.h>
#include <spec.h>
#include <debug.h>

#include <iostream>

#include "PythonActionMergeData.h"

PythonActionMergeData::PythonActionMergeData(
	ClientUser *ui, ClientResolveA *m, StrPtr &hint, PyObject * info)
{
    this->debug = 0;
    this->ui = ui;
    this->merger = m;
    this->hint = hint;

    Py_INCREF(info);
    this->mergeInfo = info;
}

PythonActionMergeData::~PythonActionMergeData()
{
    if( mergeInfo ) {
	Py_DECREF(mergeInfo);
	mergeInfo = 0;
    }
}

PyObject * PythonActionMergeData::GetMergeInfo() const
{
    Py_INCREF(mergeInfo);
    return mergeInfo;
}

PyObject * PythonActionMergeData::GetMergeAction() const
{
    StrBuf buffer;

    merger->GetMergeAction().Fmt( &buffer, EF_PLAIN );

    return CreatePythonString( buffer.Text() );
}

PyObject * PythonActionMergeData::GetYoursAction() const
{
    StrBuf buffer;

    merger->GetYoursAction().Fmt( &buffer, EF_PLAIN );

    return CreatePythonString( buffer.Text() );
}

PyObject * PythonActionMergeData::GetTheirAction() const
{
    StrBuf buffer;

    merger->GetTheirAction().Fmt( &buffer, EF_PLAIN );

    return CreatePythonString( buffer.Text() );
}

PyObject * PythonActionMergeData::GetType() const
{
    StrBuf buffer;

    merger->GetType().Fmt( &buffer, EF_PLAIN );

    return CreatePythonString( buffer.Text() );
}

PyObject * PythonActionMergeData::GetMergeHint() const
{
    return CreatePythonString( hint.Text() );
}

StrBuf PythonActionMergeData::GetString() const
{
    StrBuf result = "P4ActionMergeData\n";
    StrBuf buffer;

    merger->GetMergeAction().Fmt(&buffer, EF_INDENT);
    result << "\tmergeAction: " << buffer << "\n";
    buffer.Clear();

    merger->GetTheirAction().Fmt(&buffer, EF_INDENT);
    result << "\ttheirAction: " << buffer << "\n";
    buffer.Clear();

    merger->GetYoursAction().Fmt(&buffer, EF_INDENT);
    result << "\tyoursAction: " << buffer << "\n";
    buffer.Clear();

    merger->GetType().Fmt(&buffer, EF_INDENT);
    result << "\ttype: " << buffer << "\n";
    buffer.Clear();

    result << "\thint: " << hint << "\n";
    return result;
}
