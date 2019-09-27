/*******************************************************************************

Copyright (c) 2007-2008, Perforce Software, Inc.  All rights reserved.

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

$Id: //depot/main/p4-python/PythonMergeData.cpp#7 $

*******************************************************************************/

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

#include "PythonMergeData.h"

#include <iostream>

using namespace std;

PythonMergeData::PythonMergeData( ClientUser *ui, ClientMerge *m, StrPtr &hint )
{
    this->debug = 0;
    this->ui = ui;
    this->merger = m;
    this->hint = hint;

    // Extract (forcibly) the paths from the RPC buffer.
    StrPtr *t;
    if( ( t = ui->varList->GetVar( "baseName" ) ) ) base = t->Text();
    if( ( t = ui->varList->GetVar( "yourName" ) ) ) yours = t->Text();
    if( ( t = ui->varList->GetVar( "theirName" ) ) ) theirs = t->Text();

}

PyObject * PythonMergeData::GetYourName() const
{
    return CreatePythonString( yours.Text() );
}

PyObject * PythonMergeData::GetTheirName() const
{
    return CreatePythonString( theirs.Text() );
}

PyObject * PythonMergeData::GetBaseName() const
{
    return CreatePythonString( base.Text() );
}

PyObject * PythonMergeData::GetYourPath() const
{
    return CreatePythonString( merger->GetYourFile()->Name() );
}

PyObject * PythonMergeData::GetTheirPath() const
{
    if( merger->GetTheirFile() )
	return CreatePythonString( merger->GetTheirFile()->Name() );
    else
	Py_RETURN_NONE;
}

PyObject * PythonMergeData::GetBasePath() const
{
    if( merger->GetBaseFile() )
	return CreatePythonString( merger->GetBaseFile()->Name() );
    else
	Py_RETURN_NONE;
}

PyObject * PythonMergeData::GetResultPath() const
{
    if( merger->GetResultFile() )
	return CreatePythonString( merger->GetResultFile()->Name() );
    else
	Py_RETURN_NONE;
}

PyObject * PythonMergeData::GetMergeHint() const
{
    return CreatePythonString( hint.Text() );
}

PyObject * PythonMergeData::RunMergeTool()
{
    Error e;
    ui->Merge( merger->GetBaseFile(), merger->GetTheirFile(),
               merger->GetYourFile(), merger->GetResultFile(), &e );

    if( e.Test() )
        Py_RETURN_FALSE;
    
    Py_RETURN_TRUE;
}

StrBuf PythonMergeData::GetString() const
{
    StrBuf result = "P4MergeData\n";

    if( yours.Length() )  result << "\tyourName: " << yours << "\n";
    if( theirs.Length() ) result << "\ttheirName: " << theirs << "\n";
    if( base.Length() )   result << "\tbaseName: " << base << "\n";

    // be defensive, only add the additional information if it exists
    if( merger->GetYourFile() )
	result << "\tyourFile: " << merger->GetYourFile()->Name() << "\n";
    if( merger->GetTheirFile() )
	result << "\ttheirFile: " << merger->GetTheirFile()->Name() << "\n";
    if( merger->GetBaseFile() )
	result << "\tbaseFile: " << merger->GetBaseFile()->Name() << "\n";
    if( merger->GetResultFile() )
	result << "\tresultFile: " << merger->GetResultFile()->Name() << "\n";

    return result;
}
