/*
 * Python wrapper for the Perforce ClientApi object.
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
 * $Id: //depot/main/p4-python/P4API.cpp#63 $
 *
 * Build instructions:
 *  Use Distutils - see accompanying setup.py
 *
 *      python setup.py install
 *
 */
 
#include <Python.h>
#include <bytesobject.h>
#include <structmember.h>
#include "undefdups.h"
#include "python2to3.h"
#include <serverhelperapi.h>
#include <spec.h>
#include <ident.h>
#include <mapapi.h>
#include <clientprog.h>
#include "P4PythonDebug.h"
#include "SpecMgr.h"
#include "P4Result.h"
#include "PythonClientUser.h"
#include "PythonClientAPI.h"
#include "PythonMergeData.h"
#include "PythonActionMergeData.h"
#include "P4MapMaker.h"
#include "PythonMessage.h"
#include "PythonTypes.h"
#include "debug.h"

// #include <alloca.h> 

#include <iostream>
#include <cstring>
#include <sstream>
#include <vector>
#include <memory>

using namespace std;

static Ident ident = { 
	IdentMagic "P4PYTHON" "/" ID_OS  "/"  ID_REL "/" ID_PATCH  " (" ID_API " API)", ID_Y "/" ID_M "/" ID_D
};


// ===================
// ==== P4Adapter ====
// ===================

PyObject * P4Error;
PyObject * P4OutputHandler;
PyObject * P4Progress;

/*
 * P4Adapter destructor
 */
static void
P4Adapter_dealloc(P4Adapter *self)
{
    delete self->clientAPI;
    Py_TYPE(self)->tp_free((PyObject*)self);
}

/*
 * P4Adapter constructor.
 */
static PyObject *
P4Adapter_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
    P4Adapter *self = (P4Adapter *) type->tp_alloc(type, 0);
    if (self != NULL) {	
	self->clientAPI = new PythonClientAPI();
    }
    
    return (PyObject *) self;
}

/*
 * P4Adapter initializer.
 */
static int
P4Adapter_init(P4Adapter *self, PyObject *args, PyObject *kwds)
{

    if (kwds != NULL && PyDict_Check(kwds)) {
    	Py_ssize_t pos = 0;
    	PyObject *key, *value;
	
    	while (PyDict_Next(kwds, &pos, &key, &value)) {
     	    const char * name = GetPythonString(key);
	    
	    if (PyInt_Check(value)) {
	    	PythonClientAPI::intsetter isetter = self->clientAPI->GetIntSetter(name);
	    	if (isetter) {
	    	    int result = (self->clientAPI->*isetter)(PyInt_AS_LONG(value));
		    if (result) 
			return result;
	    	}
	    	else {
	    	    ostringstream os;
	    	    os << "No integer keyword with name " << name;
	    	    
	    	    PyErr_SetString(PyExc_AttributeError, os.str().c_str()); 
	            return -1;	
	    	}
	    }
	    else 
	    if (IsString(value)) {
	    	PythonClientAPI::strsetter ssetter = self->clientAPI->GetStrSetter(name);
	    	if (ssetter) {
	    	    int result = (self->clientAPI->*ssetter)(GetPythonString(value));
		    if (result)
			return result;
	    	}
	    	else {
	    	    ostringstream os;
	    	    os << "No string keyword with name " << name;
	    	    
	    	    PyErr_SetString(PyExc_AttributeError, os.str().c_str()); 
	            return -1;	
	    	}
	    }   	    	
    	} 
    }
    
    return 0;
}

static PyObject *
P4Adapter_repr(P4Adapter *self)
{
	return CreatePythonString("P4Adapter");
}

// **************************************
// P4Adapter directly implemented methods
// **************************************

static PyObject * P4Adapter_connect(P4Adapter * self)
{
    return self->clientAPI->Connect();
}

static PyObject * P4Adapter_connected(P4Adapter * self)
{
    return self->clientAPI->Connected();
}

static PyObject * P4Adapter_disconnect(P4Adapter * self)
{
    return self->clientAPI->Disconnect();
}

//
// Get a value from the environment following the Perforce conventions,
// including honouring P4CONFIG files etc.
//
static PyObject * P4Adapter_env(P4Adapter * self, PyObject * var)
{
    if ( !var ) Py_RETURN_NONE;

    const char *val = self->clientAPI->GetEnv( GetPythonString( var ) );
    if( !val ) Py_RETURN_NONE;

    return CreatePythonString( val );
}

static PyObject * P4Adapter_set_env(P4Adapter * self, PyObject *args)
{
    const char * var;
    const char * val = 0; // if not provided, will reset the registry value

    if ( PyArg_ParseTuple(args, "s|s", &var, &val) ) {
	return self->clientAPI->SetEnv( var, val );
    }

    return NULL;
}


static PyObject * P4Adapter_run(P4Adapter * self, PyObject * args)
{
    PyObject * cmd = PyTuple_GetItem(args, 0);
    if (cmd == NULL) {
    	return NULL;
    }
    
    // assume the args are flattened already
    
    vector<const char *> argv;
    for (Py_ssize_t i = 1; i < PyTuple_Size(args); ++i) {
	PyObject * item = PyTuple_GET_ITEM(args, i);
#if PY_MAJOR_VERSION >= 3
	// check encoding here?
	if( ! PyUnicode_Check(item) && ! PyBytes_Check(item) ) { // preserve plain Unicode and Byte strings
	    item = PyObject_Str(item);
	}
#else
	if( ! PyBytes_Check(item) ) {
	    item = PyObject_Str(item);
	}
#endif
    	argv.push_back(GetPythonString(item));
    }
    
    // this is a bit of a hack: it assumes the storage layout of the vector is continuous
    // the other hack is that the API expects (char * const *), but this cannot be stored
    // a std::vector<>, because it cannot exchange pointers
    
    return self->clientAPI->Run(GetPythonString(cmd), (int)argv.size(), 
        (argv.size() > 0) ? (char * const *) &argv[0] : NULL );
}

static PyObject * P4API_identify(PyObject * self)
{
    StrBuf	s;
    ident.GetMessage( &s );
    return CreatePythonString( s.Text() );
}

// DVCS init and clone commands
// Requires 2015.2 API

static bool found_error(Error& e)
{
    if( e.Test() ) {
	StrBuf msg;
	e.Fmt(&msg);

	PyErr_SetString(PyExc_RuntimeError, msg.Text());
	return true;
    }

    return false;
}

static ServerHelperApi * create_server(const char * user, const char * client, const char * directory, ClientUser * ui)
{
    Error e;

    ServerHelperApi * server = new ServerHelperApi(&e);
    if( found_error(e) ) return NULL;

    server->SetDvcsDir(directory, &e);
    if( found_error(e) ) return NULL;

    if( user )
	server->SetUser( user );

    if( client )
	server->SetClient( client );

    if( server->Exists(ui, &e)) {
	StrBuf msg("Personal Server already exists at path '");
	if( directory )
	    msg << directory << "'";
	else
	    msg << ".'";

	PyErr_SetString(PyExc_RuntimeError, msg.Text());
	return NULL;
    }
    if( found_error(e) ) return NULL;

    return server;
}

static bool copy_config(ServerHelperApi * personalServer, const char * port, ClientUser * ui)
{
    Error e;

    ServerHelperApi remoteServer(&e);
    if( found_error(e) ) return false;

    remoteServer.SetPort(port, &e);
    if( found_error(e) ) return false;

    personalServer->CopyConfiguration(&remoteServer, ui, &e);
    if( found_error(e) ) return false;

    return true;
}


static PyObject * P4API_dvcs_init(P4Adapter * self, PyObject * args, PyObject * keywds)
{
    char * user = NULL;
    char * client = NULL;
    char * directory = (char *) ".";
    char * port = NULL;
    PyObject * casesensitive = NULL;
    PyObject * unicode = NULL;

    PythonDebug debug;
    p4py::SpecMgr specMgr(&debug);
    PythonClientUser ui(&debug, &specMgr);
    Error e;

    static const char *kwlist[] = { "user", "client", "directory",
                              "port", "casesensitive", "unicode", NULL};

    if (!PyArg_ParseTupleAndKeywords(args, keywds, "|zzzzO!O!", (char **) kwlist,
                                         &user, &client, &directory,
					 &port,
					 &PyBool_Type, &casesensitive,
					 &PyBool_Type, &unicode))
            return NULL;


    auto_ptr<ServerHelperApi> personalServer( create_server(user, client, directory, &ui) );

    if( personalServer.get() == NULL)
	return NULL;

    if( port ) {
	if( !copy_config(personalServer.get(), port, &ui))
	    return NULL;
    }
    else if( casesensitive && unicode) {
	StrBuf caseFlag = PyObject_IsTrue(casesensitive) ? "0" : "1";
	personalServer->SetCaseFlag(&caseFlag, &e);

	int isUnicode = PyObject_IsTrue(unicode);
	personalServer->SetUnicode(isUnicode);
    }
    else { // default is to use "perforce:1666 if it can be reached
	if( !copy_config(personalServer.get(), "perforce:1666", &ui))
	    return NULL;
    }

//    personalServer->SetQuiet(); // always set, we do not ever want to see string output here

    personalServer->InitLocalServer(&ui, &e);
    if( found_error(e) ) return NULL;

    p4py::P4Result& results = ui.GetResults();
    return results.GetOutput();
}

static PyObject * P4API_dvcs_clone(P4Adapter * self, PyObject * args, PyObject * keywds)
{
    char * user = NULL;
    char * client = NULL;
    char * directory = NULL;
    int depth = 0;
    PyObject * verbose;
    char * port = NULL;
    char * remote = NULL;
    char * file = NULL;
    PyObject * archive = NULL;
    PyObject * progress = NULL;

    PythonDebug debug;
    p4py::SpecMgr specMgr(&debug);
    PythonClientUser ui(&debug, &specMgr);
    Error e;

    static const char *kwlist[] = { "user", "client", "directory",
                              "depth", "verbose", "port", "remote", "file",
			      "noarchive",
			      "progress", NULL};

    if (!PyArg_ParseTupleAndKeywords(args, keywds, "|zzziO!zzzO!O", (char **) kwlist,
                                         &user, &client, &directory,
					 &depth,
					 &PyBool_Type, &verbose,
					 &port, &remote, &file,
					 &PyBool_Type, &archive,
					 &progress))
	return NULL;

    auto_ptr<ServerHelperApi> personalServer( create_server(user, client, directory, &ui) );

    if( personalServer.get() == NULL)
	return NULL;

    if( port == NULL) {
	PyErr_SetString(PyExc_RuntimeError, "Need to specify P4PORT to clone");
	    return NULL;
    }

    if( progress != NULL ) {
	PyObject * result = ui.SetProgress(progress);
	if (result == NULL) {
	    cout << "Setting progress failed" << endl;
	    return NULL;
	}
    }

    ServerHelperApi remoteServer(&e);
    if( found_error(e) ) return NULL;

    remoteServer.SetPort(port, &e);
    if( found_error(e) ) return NULL;

    if( remote && file ) {
	PyErr_SetString(PyExc_RuntimeError, "Only specify one of (remote | file)");
	return NULL;
    }

    if( remote ) {
	personalServer->PrepareToCloneRemote(&remoteServer, remote, &ui, &e);
	if( found_error(e) ) return NULL;
    }
    else if ( file ) {
	personalServer->PrepareToCloneFilepath(&remoteServer, file, &ui, &e);
	if( found_error(e) ) return NULL;
    }
    else {
	PyErr_SetString(PyExc_RuntimeError, "Need to specify one of (remote | file)");
	return NULL;
    }

    personalServer->InitLocalServer( &ui, &e );
    if( found_error(e) ) return NULL;

    int noArchives = 0;
    if (archive != NULL && PyObject_IsTrue(archive))
	noArchives = 1;

    personalServer->CloneFromRemote( depth, noArchives, (char *) 0, &ui, &e );
    if( found_error(e) ) return NULL;

    p4py::P4Result& results = ui.GetResults();
    return results.GetOutput();
}


static PyObject * P4Adapter_formatSpec(P4Adapter * self, PyObject * args)
{
    const char * type;
    PyObject * dict;
    
    if ( PyArg_ParseTuple(args, "sO", &type, &dict) ) {
    	if ( PyDict_Check(dict) ) {
    	    return self->clientAPI->FormatSpec(type, dict);
    	}
    	else {
    	    PyErr_SetString(PyExc_TypeError, "Second argument needs to be a dictionary");
    	    return NULL;
    	}
    }
    
    return NULL;
}

static PyObject * P4Adapter_parseSpec(P4Adapter * self, PyObject * args)
{
    const char * type;
    const char * form;
    
    if ( PyArg_ParseTuple(args, "ss", &type, &form) ) {
    	return self->clientAPI->ParseSpec(type, form);
    }
    
    return NULL;
}

static PyObject * P4Adapter_defineSpec(P4Adapter * self, PyObject *args)
{
    const char * type;
    const char * spec;

    if ( PyArg_ParseTuple(args, "ss", &type, &spec) ) {
	return self->clientAPI->DefineSpec(type, spec);
    }

    return NULL;
}

static PyObject * P4Adapter_protocol(P4Adapter * self, PyObject *args)
{
    const char * var;
    const char * val = 0;

    if ( PyArg_ParseTuple(args, "s|s", &var, &val) ) {
	if ( val ) {
	    return self->clientAPI->SetProtocol( var, val );
	}
	else {
	    return self->clientAPI->GetProtocol( var );
	}
    }

    return NULL;
}

static PyObject * P4Adapter_isIgnored(P4Adapter * self, PyObject *args)
{
    const char * var;

    if ( PyArg_ParseTuple(args, "s", &var)) {
	return self->clientAPI->IsIgnored(var);
    }

    return NULL;
}

static PyObject * P4Adapter_disableTmpCleanup(P4Adapter * self, PyObject *args)
{

    return self->clientAPI->DisableTmpCleanup();
}

static PyObject * P4Adapter_setTunable(P4Adapter * self, PyObject *args)
{
    const char *tunable;
    const char *value;

    if( PyArg_ParseTuple(args, "ss", &tunable, &value)) {
        // check if tunable exists
        int index = p4tunable.GetIndex(tunable);
        if( index >= 0) {
            // Get the old value
            int oldValue = p4tunable.Get(index);

            // set the new tunable
            StrBuf setter(tunable);
            setter << "=" << value;

            p4tunable.Set(setter.Text());

            // return the old tunable

            return PyLong_FromLong(oldValue);
        }
        else {
            StrBuf errorMsg("Unknown tunable '");
            errorMsg << tunable << "'";
            PyErr_SetString(PyExc_TypeError, errorMsg.Text());
            return NULL;
        }
    }
    return NULL;
}

static PyObject * P4Adapter_getTunable(P4Adapter * self, PyObject *args)
{
    const char *tunable;

    if( PyArg_ParseTuple(args, "s", &tunable)) {
        // check if tunable exists
        int index = p4tunable.GetIndex(tunable);
        if( index >= 0) {
            // Get the old value
            int oldValue = p4tunable.Get(index);
            return PyLong_FromLong(oldValue);
        }
        else {
            StrBuf errorMsg("Unknown tunable '");
            errorMsg << tunable << "'";
            PyErr_SetString(PyExc_TypeError, errorMsg.Text());
            return NULL;
        }
    }
    return NULL;
}

#if PY_MAJOR_VERSION >= 3

static PyObject * P4Adapter_convert(P4Adapter * self, PyObject *args)
{
    const char * charset;
    PyObject * content;

    if( PyArg_ParseTuple(args, "sO", &charset, &content)) {
	return self->clientAPI->Convert(charset, content);
    }

    return NULL;
}

#endif

static PyMethodDef P4Adapter_methods[] = {
    {"connect", (PyCFunction)P4Adapter_connect, METH_NOARGS,
     "Connects to the Perforce Server"},
    {"connected", (PyCFunction)P4Adapter_connected, METH_NOARGS,
     "Checks whether we are (still) connected"},
    {"disconnect", (PyCFunction)P4Adapter_disconnect, METH_NOARGS,
     "Closes the connection to the Perforce Server"},
    {"env", (PyCFunction)P4Adapter_env, METH_O, 
     "Get values from the Perforce environment"},
    {"set_env", (PyCFunction)P4Adapter_set_env, METH_VARARGS,
     "Set values in the registry (if available on the platform) for the Perforce environment"},
    {"run", (PyCFunction)P4Adapter_run, METH_VARARGS,
     "Runs a command"},
    {"format_spec", (PyCFunction)P4Adapter_formatSpec, METH_VARARGS,
     "Converts a dictionary-based form into a string"},
    {"parse_spec", (PyCFunction)P4Adapter_parseSpec, METH_VARARGS,
     "Converts a string form into a dictionary"},
     {"define_spec", (PyCFunction)P4Adapter_defineSpec, METH_VARARGS,
     "Sets the internal spec for parsing and formating"},
    {"protocol", (PyCFunction)P4Adapter_protocol, METH_VARARGS,
     "Sets a server protocol variable to the given value or gets the protocol level"}, 
    {"disable_tmp_cleanup", (PyCFunction)P4Adapter_disableTmpCleanup, METH_VARARGS,
      "Makes P4Python thread safe by disabling cleanup of temporary resources"},
    {"is_ignored", (PyCFunction)P4Adapter_isIgnored, METH_VARARGS,
      "Returns True if the specified file path will be ignored by the current ignore file"},
    {"set_tunable", (PyCFunction)P4Adapter_setTunable, METH_VARARGS,
      "Sets a tunable to the specified value"},
    {"get_tunable", (PyCFunction)P4Adapter_getTunable, METH_VARARGS,
      "Returns the value for this tunable or 0"},

#if PY_MAJOR_VERSION >= 3
     {"__convert", (PyCFunction)P4Adapter_convert, METH_VARARGS,
     "Converts a Unicode string into a Perforce-converted String" },
#endif
    {NULL}  /* Sentinel */
};

static PyMemberDef P4Adapter_members[] = {
//    {"first", T_OBJECT_EX, offsetof(Noddy, first), 0,
//     "first name"},
    {NULL}  /* Sentinel */
};

static PyObject * P4Adapter_getattro(P4Adapter *self, PyObject * nameObject) 
{
    const char * name = GetPythonString(nameObject);
    
    PythonClientAPI::intgetter igetter = self->clientAPI->GetIntGetter(name);
    if (igetter) {
    	return PyInt_FromLong((self->clientAPI->*igetter)());
    }
    
    PythonClientAPI::strgetter sgetter = self->clientAPI->GetStrGetter(name);
    if (sgetter) {
    	return CreatePythonString((self->clientAPI->*sgetter)());
    }
    
    PythonClientAPI::objgetter ogetter = self->clientAPI->GetObjGetter(name);
    if (ogetter) {
    	return (self->clientAPI->*ogetter)();
    }
    
    return PyObject_GenericGetAttr((PyObject *) self, nameObject);
}

static int P4Adapter_setattro(P4Adapter *self, PyObject * nameObject, PyObject * value)
{
    const char * name = GetPythonString(nameObject);

    // Special case first: 
    // If there is a specific ObjectSetter for this name available use this one
    
    PythonClientAPI::objsetter osetter = self->clientAPI->GetObjSetter(name);
    if (osetter) {
        return (self->clientAPI->*osetter)(value);
    }
    else
    if (PyInt_Check(value)) {
    	PythonClientAPI::intsetter isetter = self->clientAPI->GetIntSetter(name);
    	if (isetter) {
    	    return (self->clientAPI->*isetter)(PyInt_AS_LONG(value));
    	}
    	else {
    	    ostringstream os;
    	    os << "No integer attribute with name " << name;
    	    
    	    PyErr_SetString(PyExc_AttributeError, os.str().c_str()); 
            return -1;	
    	}
    }
    else 
    if (IsString(value)) {
    	PythonClientAPI::strsetter ssetter = self->clientAPI->GetStrSetter(name);
    	if (ssetter) {
    	    return (self->clientAPI->*ssetter)(GetPythonString(value));
    	}
    	else {
    	    ostringstream os;
    	    os << "No string attribute with name " << name;
    	    
    	    PyErr_SetString(PyExc_AttributeError, os.str().c_str()); 
            return -1;	
    	}
    }
    
    // can only set int and string or certain object values -> bail out with exception
    ostringstream os;
    os << "Cannot set attribute : " << name << " with value " << GetPythonString(PyObject_Str(value));
    
    PyErr_SetString(PyExc_AttributeError, os.str().c_str()); 
    return -1;	
}

/* PyObject object for the P4Adapter */
static PyTypeObject P4AdapterType = {
    PyVarObject_HEAD_INIT(&PyType_Type, 0)
    "P4API.P4Adapter",				/* name */
    sizeof(P4Adapter),				/* basicsize */
    0,           				/* itemsize */
    (destructor) P4Adapter_dealloc,		/* dealloc */
    0,           				/* print */
    0,						/* getattr */
    0,						/* setattr */
    0,           				/* compare */
    (reprfunc) P4Adapter_repr,   		/* repr */
    0,           				/* number methods */
    0,           				/* sequence methods */
    0,           				/* mapping methods */
    0,                         			/* tp_hash */
    0,                         			/* tp_call*/
    0,                         			/* tp_str*/
    (getattrofunc) P4Adapter_getattro, 		/* tp_getattro*/
    (setattrofunc) P4Adapter_setattro,		/* tp_setattro*/
    0,                         			/* tp_as_buffer*/
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,	/* tp_flags*/
    "P4Adapter - base class for P4",		/* tp_doc */
    0,		               			/* tp_traverse */
    0,		               			/* tp_clear */
    0,		               			/* tp_richcompare */
    0,		               			/* tp_weaklistoffset */
    0,		               			/* tp_iter */
    0,		               			/* tp_iternext */
    P4Adapter_methods,             		/* tp_methods */
    P4Adapter_members,             		/* tp_members */
    0,                         			/* tp_getset */
    0,                         			/* tp_base */
    0,                         			/* tp_dict */
    0,                         			/* tp_descr_get */
    0,                         			/* tp_descr_set */
    0,                         			/* tp_dictoffset */
    (initproc)P4Adapter_init,      		/* tp_init */
    0,                         			/* tp_alloc */
    P4Adapter_new,                 		/* tp_new */
};

// =====================
// ==== P4MergeData ====
// =====================

/*
 * P4MergeData destructor
 */
static void P4MergeData_dealloc(P4MergeData *self)
{
    delete self->mergeData;
    Py_TYPE(self)->tp_free((PyObject*)self);
}

static PyObject * P4MergeData_repr(P4MergeData *self)
{
    // TODO: add more output information to give full representation
    return CreatePythonString(self->mergeData->GetString().Text());
}

// ****************************************
// P4MergeData directly implemented methods
// ****************************************

static PyObject * P4MergeData_run_merge(P4MergeData * self)
{
    return self->mergeData->RunMergeTool();
}

static PyMethodDef P4MergeData_methods[] = {
    {"run_merge", (PyCFunction)P4MergeData_run_merge, METH_NOARGS,
     "Runs the merge tool with this data"},
    {NULL}  /* Sentinel */
};

static PyObject * P4MergeData_getattro(P4MergeData * self, PyObject * nameObject)
{
    const char * name = GetPythonString(nameObject);
    
    if( !strcmp( name, "your_name" ) ) {
        return self->mergeData->GetYourName();
    } 
    else if( !strcmp( name, "their_name" ) ) {
        return self->mergeData->GetTheirName();
    }
    else if( !strcmp( name, "base_name" ) ) {
        return self->mergeData->GetBaseName();
    }
    else if( !strcmp( name, "your_path" ) ) {
        return self->mergeData->GetYourPath();
    }
    else if( !strcmp( name, "their_path" ) ) {
        return self->mergeData->GetTheirPath();
    }
    else if( !strcmp( name, "base_path" ) ) {
        return self->mergeData->GetBasePath();
    }
    else if( !strcmp( name, "result_path" ) ) {
        return self->mergeData->GetResultPath();
    }
    else if( !strcmp( name, "merge_hint" ) ) {
        return self->mergeData->GetMergeHint();
    }
    
    // no matching name found, falling back to default
    return PyObject_GenericGetAttr((PyObject *) self, nameObject);
}

/* PyObject object for the P4MergeData */
PyTypeObject P4MergeDataType = {
    PyVarObject_HEAD_INIT(&PyType_Type, 0)
    "P4API.P4MergeData",                        /* name */
    sizeof(P4MergeData),                        /* basicsize */
    0,                                          /* itemsize */
    (destructor) P4MergeData_dealloc,           /* dealloc */
    0,                                          /* print */
    0,                                          /* getattr */
    0,                                          /* setattr */
    0,                                          /* compare */
    (reprfunc) P4MergeData_repr,                /* repr */
    0,                                          /* number methods */
    0,                                          /* sequence methods */
    0,                                          /* mapping methods */
    0,                                          /* tp_hash */
    0,                                          /* tp_call*/
    0,                                          /* tp_str*/
    (getattrofunc) P4MergeData_getattro,        /* tp_getattro*/
    0,                                          /* tp_setattro*/
    0,                                          /* tp_as_buffer*/
    Py_TPFLAGS_DEFAULT,                         /* tp_flags*/
    "P4MergeData - contains merge information for resolve",            /* tp_doc */
    0,                                          /* tp_traverse */
    0,                                          /* tp_clear */
    0,                                          /* tp_richcompare */
    0,                                          /* tp_weaklistoffset */
    0,                                          /* tp_iter */
    0,                                          /* tp_iternext */
    P4MergeData_methods,                          /* tp_methods */
    0,                                          /* tp_members */
    0,                                          /* tp_getset */
    0,                                          /* tp_base */
    0,                                          /* tp_dict */
    0,                                          /* tp_descr_get */
    0,                                          /* tp_descr_set */
    0,                                          /* tp_dictoffset */
    0,                                          /* tp_init */
    0,                                          /* tp_alloc */
    0,                                          /* tp_new */
};

// ===========================
// ==== P4ActionMergeData ====
// ===========================

/*
 * P4ActionMergeData destructor
 */
static void P4ActionMergeData_dealloc(P4ActionMergeData *self)
{
    delete self->mergeData;
    Py_TYPE(self)->tp_free((PyObject*)self);
}

static PyObject * P4ActionMergeData_repr(P4ActionMergeData *self)
{
    // TODO: add more output information to give full representation
    return CreatePythonString(self->mergeData->GetString().Text());
}

// ****************************************
// P4MergeData directly implemented methods
// ****************************************

static PyObject * P4ActionMergeData_getattro(P4ActionMergeData * self, PyObject * nameObject)
{
    const char * name = GetPythonString(nameObject);

    if( !strcmp( name, "merge_action" ) ) {
        return self->mergeData->GetMergeAction();
    }
    else if( !strcmp( name, "yours_action" ) ) {
        return self->mergeData->GetYoursAction();
    }
    else if( !strcmp( name, "their_action" ) ) {
        return self->mergeData->GetTheirAction();
    }
    else if( !strcmp( name, "type" ) ) {
        return self->mergeData->GetType();
    }
    else if( !strcmp( name, "merge_hint" ) ) {
        return self->mergeData->GetMergeHint();
    }
    else if( !strcmp( name, "info" ) ) {
        return self->mergeData->GetMergeInfo();
    }

    // no matching name found, falling back to default
    return PyObject_GenericGetAttr((PyObject *) self, nameObject);
}

/* PyObject object for the P4MergeData */
PyTypeObject P4ActionMergeDataType = {
    PyVarObject_HEAD_INIT(&PyType_Type, 0)
    "P4API.P4ActionMergeData",                  /* name */
    sizeof(P4ActionMergeData),                  /* basicsize */
    0,                                          /* itemsize */
    (destructor) P4ActionMergeData_dealloc,     /* dealloc */
    0,                                          /* print */
    0,                                          /* getattr */
    0,                                          /* setattr */
    0,                                          /* compare */
    (reprfunc) P4ActionMergeData_repr,          /* repr */
    0,                                          /* number methods */
    0,                                          /* sequence methods */
    0,                                          /* mapping methods */
    0,                                          /* tp_hash */
    0,                                          /* tp_call*/
    0,                                          /* tp_str*/
    (getattrofunc) P4ActionMergeData_getattro,  /* tp_getattro*/
    0,                                          /* tp_setattro*/
    0,                                          /* tp_as_buffer*/
    Py_TPFLAGS_DEFAULT,                         /* tp_flags*/
    "P4ActionMergeData - contains action merge information for resolve",            /* tp_doc */
    0,                                          /* tp_traverse */
    0,                                          /* tp_clear */
    0,                                          /* tp_richcompare */
    0,                                          /* tp_weaklistoffset */
    0,                                          /* tp_iter */
    0,                                          /* tp_iternext */
    0,                                          /* tp_methods */
    0,                                          /* tp_members */
    0,                                          /* tp_getset */
    0,                                          /* tp_base */
    0,                                          /* tp_dict */
    0,                                          /* tp_descr_get */
    0,                                          /* tp_descr_set */
    0,                                          /* tp_dictoffset */
    0,                                          /* tp_init */
    0,                                          /* tp_alloc */
    0,                                          /* tp_new */
};

// ===============
// ==== P4Map ====
// ===============

extern PyTypeObject P4MapType; // forward


/*
 * P4Map destructor
 */
static void
        P4Map_dealloc(P4Map *self)
{
    delete self->map;
    Py_TYPE(self)->tp_free((PyObject*)self);
}

/*
 * P4Map constructor.
 */
static PyObject *
        P4Map_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
    P4Map *self = (P4Map *) type->tp_alloc(type, 0);
    if (self != NULL) { 
        self->map = new p4py::P4MapMaker();
    }
    
    return (PyObject *) self;
}

/*
 * P4Map initializer.
 */
static int
        P4Map_init(P4Map *self, PyObject *args, PyObject *kwds)
{
    // nothing to do for now
    return 0;
}

static PyObject *
        P4Map_repr(P4Map *self)
{
    return self->map->Inspect();
}

static PyObject *
        P4Map_insert(P4Map *self, PyObject * args)
{
    // expects one, or two arguments, lhs, and optional rhs. In the
    // absence of rhs, lhs is assumed to contain both halves.
    PyObject *lhs;
    PyObject *rhs = NULL;
    
    // ugly hack for now
#if PY_MAJOR_VERSION >= 3
    const char * format = "U|U";
#else
    const char * format = "S|S";
#endif
    int ok = PyArg_ParseTuple(args, format, &lhs, &rhs );
    if (ok) {
	if( !rhs )
	    self->map->Insert( lhs );
	else
	    self->map->Insert(lhs, rhs );
        Py_RETURN_NONE;
    }
    return NULL;
}

static PyObject *
        P4Map_clear(P4Map *self)
{
    // clears out the map
    
    self->map->Clear();
    
    Py_RETURN_NONE;
}

static PyObject *
        P4Map_translate(P4Map *self, PyObject * args)
{
    // expects two arguments, the string and the direction 
    // True (default) ==> Left to Right
    // False ==> Right to Left
    
    PyObject *str;
    int direction = 1;
    
#if PY_MAJOR_VERSION >= 3
    const char * format = "U|b";
#else
    const char * format = "S|b";
#endif

    int ok = PyArg_ParseTuple(args, format, &str, &direction);
    if (ok) {
        return self->map->Translate(str, direction);
    }
    return NULL;
}

static PyObject *
        P4Map_translateArray(P4Map *self, PyObject * args)
{
    // expects two arguments, the string and the direction
    // True (default) ==> Left to Right
    // False ==> Right to Left

    PyObject *str;
    int direction = 1;

#if PY_MAJOR_VERSION >= 3
    const char * format = "U|b";
#else
    const char * format = "S|b";
#endif

    int ok = PyArg_ParseTuple(args, format, &str, &direction);
    if (ok) {
        return self->map->TranslateArray(str, direction);
    }
    return NULL;
}

static PyObject *
        P4Map_reverse(P4Map *self)
{
    P4Map *	rmap = (P4Map *) P4MapType.tp_alloc(&P4MapType, 0);

    if (!rmap)
       return (PyObject *) rmap;

    rmap->map = new p4py::P4MapMaker( *self->map );
    rmap->map->Reverse();
    
    return (PyObject *) rmap;
}

static PyObject *
        P4Map_count(P4Map *self)
{
    return PyInt_FromLong( self->map->Count() );
}

static PyObject *
        P4Map_lhs(P4Map *self)
{
    return self->map->Lhs();
}

static PyObject *
        P4Map_rhs(P4Map *self)
{
    return self->map->Rhs();
}

static PyObject *
        P4Map_as_array(P4Map *self)
{
    return self->map->ToA();
}

static PyObject *
        P4Map_join(PyTypeObject *type, PyObject * args)
{
    // expects two P4Map objects
    
    P4Map *left;
    P4Map *right;
    P4Map *result;
    
    int ok = PyArg_ParseTuple(args, "O!O!", &P4MapType, (PyObject **) &left, &P4MapType, (PyObject **) &right);
    if (!ok) 
    	return NULL;
    
    PyObject * p4Module = PyImport_ImportModule("P4");
    PyObject * p4Dict = PyModule_GetDict(p4Module);
    PyObject * mapClass = PyDict_GetItemString(p4Dict, "Map");
    if (mapClass == NULL) {
        cout << "Could not find class P4.Map" << endl;
	return NULL;
    }

    result = (P4Map *) PyObject_CallObject(mapClass, NULL);
    delete result->map;
    result->map = p4py::P4MapMaker::Join(left->map, right->map);
    return (PyObject *) result;
}

static PyMethodDef P4Map_methods[] = {
    {"insert", (PyCFunction) P4Map_insert, METH_VARARGS,
                "Insert left hand, right hand, and the maptype ('', '+', '-')"},
    {"clear",  (PyCFunction) P4Map_clear, METH_NOARGS,
                "Clears out the map."},
    {"translate", (PyCFunction) P4Map_translate, METH_VARARGS,
                   "Translates the passed arguments using the map and returns a string"},
    {"translate_array", (PyCFunction) P4Map_translateArray, METH_VARARGS,
		                   "Translates the passed arguments using the map and returns an array"},
    {"count", (PyCFunction) P4Map_count, METH_NOARGS,
                   "Returns number of entries in the maps"},
    {"reverse", (PyCFunction) P4Map_reverse, METH_NOARGS,
                   "Swap the left and right sides of the map"},
    {"lhs", (PyCFunction) P4Map_lhs, METH_NOARGS,
                   "Returns a list containing the LHS"},
    {"rhs", (PyCFunction) P4Map_rhs, METH_NOARGS,
                   "Returns a list containing the RHS"},
    {"as_array", (PyCFunction) P4Map_as_array, METH_NOARGS,
                   "Returns the map contents as a list"},
    {"join", (PyCFunction) P4Map_join, METH_VARARGS | METH_CLASS,
                   "Joins two maps together and returns a third"},
    {NULL}  /* Sentinel */
};

/* PyObject object for the P4MergeData */
PyTypeObject P4MapType = {
    PyVarObject_HEAD_INIT(&PyType_Type, 0)
            "P4API.P4Map",                               /* name */
            sizeof(P4Map),                              /* basicsize */
            0,                                          /* itemsize */
            (destructor) P4Map_dealloc,                 /* dealloc */
            0,                                          /* print */
            0,                                          /* getattr */
            0,                                          /* setattr */
            0,                                          /* compare */
            (reprfunc) P4Map_repr,                      /* repr */
            0,                                          /* number methods */
            0,                                          /* sequence methods */
            0,                                          /* mapping methods */
            0,                                          /* tp_hash */
            0,                                          /* tp_call*/
            0,                                          /* tp_str*/
            0,                                          /* tp_getattro*/
            0,                                          /* tp_setattro*/
            0,                                          /* tp_as_buffer*/
            Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,   /* tp_flags*/
            "P4Map - client mapping interface",         /* tp_doc */
            0,                                          /* tp_traverse */
            0,                                          /* tp_clear */
            0,                                          /* tp_richcompare */
            0,                                          /* tp_weaklistoffset */
            0,                                          /* tp_iter */
            0,                                          /* tp_iternext */
            P4Map_methods,                              /* tp_methods */
            0,                                          /* tp_members */
            0,                                          /* tp_getset */
            0,                                          /* tp_base */
            0,                                          /* tp_dict */
            0,                                          /* tp_descr_get */
            0,                                          /* tp_descr_set */
            0,                                          /* tp_dictoffset */
            (initproc) P4Map_init,                      /* tp_init */
            0,                                          /* tp_alloc */
            P4Map_new,                                  /* tp_new */
};

// ===================
// ==== P4Message ====
// ===================

static
PyObject *P4Message_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
    P4Message *self = (P4Message *) type->tp_alloc(type, 0);
    if (self != NULL) {
        self->msg = NULL;
    }

    return (PyObject *) self;
}

static void
P4Message_dealloc(P4Message *self)
{
    delete self->msg;
    Py_TYPE(self)->tp_free((PyObject*)self);
}

static PyObject *
P4Message_str(P4Message *self)
{
    return self->msg->getText();
}

static PyObject *
P4Message_repr(P4Message *self)
{
    return self->msg->getRepr();
}

static int
P4Message_init(P4Message *self, PyObject *args, PyObject *kwds)
{
    return 0;
}

static PyMethodDef P4Message_methods[] = {
	{NULL}  /* Sentinel */
};

static PyObject *
P4Message_getattro(P4Message * self, PyObject * nameObject)
{
    const char * name = GetPythonString(nameObject);

    if( strcmp(name, "severity") == 0) {
	return self->msg->getSeverity();
    }
    else if( strcmp(name, "generic") == 0) {
	return self->msg->getGeneric();
    }
    else if( strcmp(name, "msgid") == 0) {
	return self->msg->getMsgid();
    }
    else if( strcmp(name, "dict") == 0) {
	return self->msg->getDict();
    }
    else
	return PyObject_GenericGetAttr((PyObject *) self, nameObject);
}

PyTypeObject P4MessageType =
{
    PyVarObject_HEAD_INIT(&PyType_Type, 0)
	    "P4API.P4Message",                          /* name */
	    sizeof(P4Message),                          /* basicsize */
	    0,                                          /* itemsize */
	    (destructor) P4Message_dealloc,             /* dealloc */
	    0,                                          /* print */
	    0,                                          /* getattr */
	    0,                                          /* setattr */
	    0,                                          /* compare */
	    (reprfunc) P4Message_repr,                  /* repr */
	    0,                                          /* number methods */
	    0,                                          /* sequence methods */
	    0,                                          /* mapping methods */
	    0,                                          /* tp_hash */
	    0,                                          /* tp_call*/
	    (reprfunc) P4Message_str,                   /* tp_str*/
	    (getattrofunc) P4Message_getattro,          /* tp_getattro*/
	    0,                                          /* tp_setattro*/
	    0,                                          /* tp_as_buffer*/
	    Py_TPFLAGS_DEFAULT,                         /* tp_flags*/
	    "P4Message - errors and warnings",          /* tp_doc */
	    0,                                          /* tp_traverse */
	    0,                                          /* tp_clear */
	    0,                                          /* tp_richcompare */
	    0,                                          /* tp_weaklistoffset */
	    0,                                          /* tp_iter */
	    0,                                          /* tp_iternext */
	    P4Message_methods,                          /* tp_methods */
	    0,                                          /* tp_members */
	    0,                                          /* tp_getset */
	    0,                                          /* tp_base */
	    0,                                          /* tp_dict */
	    0,                                          /* tp_descr_get */
	    0,                                          /* tp_descr_set */
	    0,                                          /* tp_dictoffset */
	    (initproc) P4Message_init,                  /* tp_init */
	    0,                                          /* tp_alloc */
	    P4Message_new,                              /* tp_new */
};


// ===============
// ==== P4API ====
// ===============

struct P4API_state {
        PyObject * error;
};

#if PY_MAJOR_VERSION >= 3
#define GETSTATE(m) ((struct P4API_state*)PyModule_GetState(m))
#else
#define GETSTATE(m) (&_state)
static struct P4API_state _state;
#endif

static struct PyMethodDef P4API_methods[] = {
    {"identify", (PyCFunction)P4API_identify, METH_NOARGS, "Identify module version"},
    {"dvcs_init", (PyCFunction)P4API_dvcs_init, METH_VARARGS | METH_KEYWORDS, "Initialize local server"},
    {"dvcs_clone", (PyCFunction)P4API_dvcs_clone, METH_VARARGS | METH_KEYWORDS, "Clone local server"},
    {NULL} /* Sentinel */
};

// ===================
// ==== initP4API ====
// ===================

#if PY_MAJOR_VERSION >= 3

static int P4API_traverse(PyObject *m, visitproc visit, void *arg) {
    Py_VISIT(GETSTATE(m)->error);
    return 0;
}

static int P4API_clear(PyObject *m) {
    Py_CLEAR(GETSTATE(m)->error);
    return 0;
}

static struct PyModuleDef P4API_moduledef = {
        PyModuleDef_HEAD_INIT,
        "P4API",
        "P4 Python Adapter Module",
        sizeof(struct P4API_state),
        P4API_methods,
        NULL,
        P4API_traverse,
        P4API_clear,
        NULL
};

#define INITERROR return NULL

PyMODINIT_FUNC
PyInit_P4API(void)

#else 

#define INITERROR return

PyMODINIT_FUNC
initP4API(void)
#endif

{
    if (PyType_Ready(&P4AdapterType) < 0) 
	INITERROR;
    if (PyType_Ready(&P4MapType) < 0)
        INITERROR;
    if (PyType_Ready(&P4MergeDataType) < 0)
        INITERROR;
    if (PyType_Ready(&P4ActionMergeDataType) < 0)
        INITERROR;
    if (PyType_Ready(&P4MessageType) < 0)
        INITERROR;

#if PY_MAJOR_VERSION >= 3
    PyObject * module = PyModule_Create(&P4API_moduledef);
#else
    PyObject * module = Py_InitModule3("P4API", P4API_methods, "P4 Python Adapter Module");
#endif

    if (module == NULL) INITERROR;

    Py_INCREF(&P4AdapterType);
    PyModule_AddObject(module, "P4Adapter", (PyObject*) &P4AdapterType);
    
    Py_INCREF(&P4MergeDataType);
    PyModule_AddObject(module, "P4MergeData", (PyObject*) &P4MergeDataType);

    Py_INCREF(&P4ActionMergeDataType);
    PyModule_AddObject(module, "P4ActionMergeData", (PyObject*) &P4ActionMergeDataType);

    Py_INCREF(&P4MapType);
    PyModule_AddObject(module, "P4Map", (PyObject*) &P4MapType);
    
    Py_INCREF(&P4MessageType);
    PyModule_AddObject(module, "P4Message", (PyObject*) &P4MessageType);

    struct P4API_state *st = GETSTATE(module);

    st->error = PyErr_NewException((char *)"P4API.Error", NULL, NULL);
    if (st->error == NULL) {
        Py_DECREF(module);
        INITERROR;
    }

    // Get a reference to P4.P4Error
    // Not declared as an exception here because of module inconsistencies
    // Better for the user to have an exception of type P4.P4Error than
    // P4API.P4Error
    
    PyObject * p4Module = PyImport_ImportModule("P4");
    PyObject * p4Dict = PyModule_GetDict(p4Module);
    P4Error = PyDict_GetItemString(p4Dict, "P4Exception");
    if (P4Error) 
    	Py_INCREF(P4Error);
    else {
    	PyErr_SetString(st->error, "Could not find P4.P4Exception." );
    	Py_DECREF(module);
        INITERROR;
    }
    
    P4OutputHandler = PyDict_GetItemString(p4Dict, "OutputHandler");
    if (P4OutputHandler)
    	Py_INCREF(P4OutputHandler);
    else {
    	PyErr_SetString(st->error, "Could not find P4.OutputHandler." );
    	Py_DECREF(module);
        INITERROR;
    }

    P4Progress = PyDict_GetItemString(p4Dict, "Progress");
    if (P4Progress)
    	Py_INCREF(P4Progress);
    else {
    	PyErr_SetString(st->error, "Could not find P4.Progress." );
    	Py_DECREF(module);
        INITERROR;
    }

#if PY_MAJOR_VERSION >= 3
    return module;
#endif
}

