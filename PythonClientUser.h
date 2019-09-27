/*
 * PythonClientUser. Subclass of P4::ClientUser
 *
 * Copyright (c) 2007-2015, Perforce Software, Inc.  All rights reserved.
 * Portions Copyright (c) 1999, Mike Meyer. All rights reserved.
 * Portions Copyright (c) 2004-2007, Robert Cowham. All rights reserved.
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
 * $Id: //depot/main/p4-python/PythonClientUser.h#19 $
 *
 * Build instructions:
 *  Use Distutils - see accompanying setup.py
 *
 *      python setup.py install
 *
 */

#ifndef PYTHON_CLIENT_USER_H
#define PYTHON_CLIENT_USER_H

class ClientProgress;

class PythonClientUser: public ClientUser, public KeepAlive
{
public:
    PythonClientUser(PythonDebug *dbg, p4py::SpecMgr *s);

    virtual ~PythonClientUser();

    // Client User methods overridden here
    virtual void HandleError(Error *e);
    virtual void Message(Error *err);
    virtual void OutputText(const char *data, int length);
    virtual void OutputInfo(char level, const char *data);
    virtual void OutputStat(StrDict *values);
    virtual void OutputBinary(const char *data, int length);
    virtual void InputData(StrBuf *strbuf, Error *e);
    virtual void Diff(FileSys *f1, FileSys *f2, int doPage, char *diffFlags,
            Error *e);
    virtual void Prompt(const StrPtr &msg, StrBuf &rsp, int noEcho, Error *e);

    virtual int Resolve(ClientMerge *m, Error *e);
    virtual int Resolve(ClientResolveA *m, int preview, Error *e);

    virtual ClientProgress *CreateProgress(int);
    virtual int ProgressIndicator();

    virtual void Finished();

    // Local methods
    PyObject * SetInput(PyObject * i);
    PyObject * GetInput()
    {
        Py_INCREF(input);
        return input;
    }

    PyObject * SetResolver(PyObject * i);
    PyObject * GetResolver()
    {
        Py_INCREF(resolver);
        return resolver;
    }

    PyObject * SetHandler(PyObject * i);
    PyObject * GetHandler()
    {
        Py_INCREF(handler);
        return handler;
    }

    PyObject * SetProgress(PyObject * p);
    PyObject * GetProgress()
    {
        Py_INCREF(progress);
        return progress;
    }

    void SetCommand(const char *c)
    {
        cmd = c;
    }
    void SetApiLevel(int level);
    void SetTrack(bool t)
    {
        track = t;
    }

    p4py::P4Result& GetResults()
    {
        return results;
    }
    int ErrorCount();
    void Reset();

    // override from KeepAlive
    virtual int IsAlive()
    {
        return alive;
    }

private:
    PyObject * MkMergeInfo(ClientMerge *m, StrPtr &hint);
    PyObject * MkActionMergeInfo(ClientResolveA *m, StrPtr &hint);
    void ProcessOutput(const char * method, PyObject * data);
    void ProcessMessage(Error * e);
    bool CallOutputMethod(const char * method, PyObject * data);

private:
    StrBuf              cmd;
    p4py::SpecMgr *     specMgr;
    PythonDebug *       debug;
    p4py::P4Result      results;
    PyObject *          input;
    PyObject *          resolver;
    PyObject *          handler;
    PyObject *          progress;
    int                 apiLevel;
    int                 alive;
    bool                track;
};

#endif
