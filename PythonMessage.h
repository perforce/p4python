/*
 * PythonMessage. Wrapper around errors and warnings.
 *
 * Copyright (c) 2010, Perforce Software, Inc.  All rights reserved.
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
 * $Id: //depot/main/p4-python/PythonMessage.h#5 $
 *
 */

/*******************************************************************************
 * Name		: PythonMessage.h
 *
 * Author	: Sven Erik Knop <sknop@perforce.com>
 *
 * Description	: Class for bridging Perforce's Error class to Python
 *
 ******************************************************************************/

#ifndef PYTHONMESSAGE_H_
#define PYTHONMESSAGE_H_

class PythonMessage
{
private:
    Error err;
    p4py::SpecMgr * specMgr;

public:
    PythonMessage(const Error * other, p4py::SpecMgr * s);

public:
    PyObject * getText();
    PyObject * getRepr();
    PyObject * getSeverity();
    PyObject * getGeneric();
    PyObject * getMsgid();
    PyObject * getDict();

};

#endif /* PYTHONMESSAGE_H_ */
