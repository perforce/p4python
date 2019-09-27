/*******************************************************************************

Copyright (c) 2009, Perforce Software, Inc.  All rights reserved.

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
 * Name		: PythonSpecData.h
 *
 * Author	: Sven Erik Knop <sknop@perforce.com>
 *
 * Description	: Python bindings for the Perforce API. SpecData subclass for
 * 		  P4Python. This class allows for manipulation of Spec data
 * 		  stored in a Python dict using the standard Perforce classes
 *
 ******************************************************************************/

class PythonSpecData : public SpecData
{
public:
    PythonSpecData( PyObject * d ) { dict = d; }

    virtual StrPtr * GetLine( SpecElem *sd, int x, const char **cmt );
    virtual void     SetLine( SpecElem *sd, int x, const StrPtr *val, Error *e );
    virtual void     Comment( SpecElem *sd, int x, const char **wv, int nl, Error *e );

private:
    PyObject * 		dict;
    StrBuf		last;
};

