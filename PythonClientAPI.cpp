/*******************************************************************************

Copyright (c) 2007-2008, Perforce Software, Inc.  All rights reserved.
Portions Copyright (c) 1999, Mike Meyer. All rights reserved.
Portions Copyright (c) 2004-2007, Robert Cowham. All rights reserved.

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

$Id: //depot/main/p4-python/PythonClientAPI.cpp#81 $
*******************************************************************************/
 
#include <Python.h>
#include <bytesobject.h>
#include "undefdups.h"
#include "python2to3.h"
#include <clientapi.h>
#include <ignore.h>
#include <i18napi.h>
#include <charcvt.h>
#include <strtable.h>
#include <strarray.h>
#include <enviro.h>
#include <hostenv.h>
#include <spec.h>
#include <debug.h>
#include <mapapi.h>

#include "P4PythonDebug.h"
#include "SpecMgr.h"
#include "P4Result.h"
#include "PythonClientUser.h"
#include "PythonClientAPI.h"
#include "P4PythonDebug.h"
#include "PythonThreadGuard.h"
#include "PythonMergeData.h"
#include "P4MapMaker.h"
#include "PythonMessage.h"
#include "PythonTypes.h"

#include <iostream>

#define	M_TAGGED		0x01
#define	M_PARSE_FORMS		0x02
#define	IS_TAGGED(x)		(x & M_TAGGED )
#define	IS_PARSE_FORMS(x)	(x & M_PARSE_FORMS )

using namespace std;

PythonClientAPI::PythonClientAPI()
    : ui(&debug, &specMgr),
      specMgr(&debug)
{
    server2 = 0;
    depth = 0;
    exceptionLevel = 2;
    maxResults = 0;
    maxScanRows = 0;
    maxLockTime = 0;
    maxOpenFiles = 0;
    maxMemory = 0;
    prog = "unnamed p4-python script";
    apiLevel = atoi( P4Tag::l_client );
    enviro = new Enviro;

    InitFlags();

    // Enable form parsing
    client.SetProtocol( "specstring", "" );

    //
    // Load the current working directory, and any P4CONFIG file in place
    //
    HostEnv 	henv;
    StrBuf	cwd;

    henv.GetCwd( cwd, enviro );
    if( cwd.Length() )
	enviro->Config( cwd );

    //
    // Load the current ticket file. Start with the default, and then
    // override it if P4TICKETS is set.
    //
    const char *t;

    henv.GetTicketFile( ticketFile );
    
    if( (t = enviro->Get( "P4TICKETS" )) ) {
	ticketFile = t;
    }
    
    // 
    // Do the same for P4CHARSET
    //
    
    const char *lc;
    if( ( lc = enviro->Get( "P4CHARSET" )) ) {
        SetCharset(lc);
    }
}

PythonClientAPI::~PythonClientAPI()
{
    // can't use logger here, probably already destructed at this time
    debug.printDebug(P4PYDBG_GC, "Destructor PythonClientAPI::~PythonClientAPI called");

    if( IsConnected() ) {
	Error e;
	client.Final( &e );
	// Ignore errors
    }
    delete enviro;
}

StrBuf PythonClientAPI::SetProgString(StrBuf& progStr)
{
    StrBuf result = progStr;

    result << " [PY";
    result << PY_VERSION;
    result << "/P4PY";
    result << ID_REL;
    result << "/API";
    result << ID_API;
    result << "]";

    return result;
}

PyObject *  PythonClientAPI::DisableTmpCleanup()
{
    ui.DisableTmpCleanup();

    Py_RETURN_NONE;
}

PythonClientAPI::intattribute_t PythonClientAPI::intattributes[] = {
	{ "tagged",		&PythonClientAPI::SetTagged,		&PythonClientAPI::GetTagged },
	{ "api_level",		&PythonClientAPI::SetApiLevel,		&PythonClientAPI::GetApiLevel },
	{ "maxresults",		&PythonClientAPI::SetMaxResults,	&PythonClientAPI::GetMaxResults },
	{ "maxscanrows",	&PythonClientAPI::SetMaxScanRows,	&PythonClientAPI::GetMaxScanRows },
	{ "maxlocktime",	&PythonClientAPI::SetMaxLockTime,	&PythonClientAPI::GetMaxLockTime },
	{ "maxopenfiles",	&PythonClientAPI::SetMaxOpenFiles,	&PythonClientAPI::GetMaxOpenFiles },
	{ "maxmemory",	&PythonClientAPI::SetMaxMemory,	&PythonClientAPI::GetMaxMemory },
	{ "exception_level",	&PythonClientAPI::SetExceptionLevel,	&PythonClientAPI::GetExceptionLevel },
	{ "debug",		&PythonClientAPI::SetDebug,		&PythonClientAPI::GetDebug },
	{ "track",		&PythonClientAPI::SetTrack,		&PythonClientAPI::GetTrack },
	{ "streams",		&PythonClientAPI::SetStreams,		&PythonClientAPI::GetStreams },
	{ "graph",		&PythonClientAPI::SetGraph,		&PythonClientAPI::GetGraph },
	{ "case_folding",	&PythonClientAPI::SetCaseFolding,	&PythonClientAPI::GetCaseFolding},
	{ NULL, NULL, NULL }, // guard
};

PythonClientAPI::strattribute_t PythonClientAPI::strattributes[] = {
	{ "charset",		&PythonClientAPI::SetCharset,		&PythonClientAPI::GetCharset },
	{ "client",		&PythonClientAPI::SetClient,		&PythonClientAPI::GetClient },
	{ "p4config_file",	NULL,					&PythonClientAPI::GetConfig },
	{ "p4enviro_file",	&PythonClientAPI::SetEnviroFile,	&PythonClientAPI::GetEnviroFile },
	{ "cwd",		&PythonClientAPI::SetCwd,		&PythonClientAPI::GetCwd },
	{ "host",		&PythonClientAPI::SetHost,		&PythonClientAPI::GetHost },
	{ "ignore_file",	&PythonClientAPI::SetIgnoreFile,	&PythonClientAPI::GetIgnoreFile },
	{ "language",		&PythonClientAPI::SetLanguage,		&PythonClientAPI::GetLanguage },
	{ "port",		&PythonClientAPI::SetPort,		&PythonClientAPI::GetPort },
	{ "prog",		&PythonClientAPI::SetProg,		&PythonClientAPI::GetProg },
	{ "ticket_file",	&PythonClientAPI::SetTicketFile,	&PythonClientAPI::GetTicketFile },
	{ "password",		&PythonClientAPI::SetPassword,		&PythonClientAPI::GetPassword },
	{ "user",		&PythonClientAPI::SetUser,		&PythonClientAPI::GetUser },
	{ "version",		&PythonClientAPI::SetVersion,		&PythonClientAPI::GetVersion },	
	{ "PATCHLEVEL",		NULL,					&PythonClientAPI::GetPatchlevel },
	{ "OS",			NULL,					&PythonClientAPI::GetOs },
#if PY_MAJOR_VERSION >= 3
	{ "encoding",		&PythonClientAPI::SetEncoding,		&PythonClientAPI::GetEncoding },
#endif
	{ NULL, NULL, NULL }, // guard
};

PythonClientAPI::objattribute_t PythonClientAPI::objattributes[] = {
	{ "input",		&PythonClientAPI::SetInput,		&PythonClientAPI::GetInput },
        { "resolver",           &PythonClientAPI::SetResolver,          &PythonClientAPI::GetResolver },
        { "handler",            &PythonClientAPI::SetHandler,           &PythonClientAPI::GetHandler },
        { "progress",           &PythonClientAPI::SetProgress,          &PythonClientAPI::GetProgress },
        { "errors",		NULL,					&PythonClientAPI::GetErrors },
	{ "warnings",		NULL,					&PythonClientAPI::GetWarnings },
        { "messages",		NULL,					&PythonClientAPI::GetMessages },
	{ "p4config_files",	NULL,					&PythonClientAPI::GetConfigFiles },
	{ "track_output",	NULL,					&PythonClientAPI::GetTrackOutput },
	{ "__members__",	NULL,					&PythonClientAPI::GetMembers },
	{ "server_level",	NULL,					&PythonClientAPI::GetServerLevel },
	{ "server_case_insensitive",	NULL,				&PythonClientAPI::GetServerCaseInsensitive },
	{ "server_unicode",	NULL,					&PythonClientAPI::GetServerUnicode },
	{ "logger",		&PythonClientAPI::SetLogger,		&PythonClientAPI::GetLogger },
	{ NULL, NULL, NULL }, // guard
};

PythonClientAPI::intattribute_t * PythonClientAPI::GetInt(const char * forAttr)
{
    PythonClientAPI::intattribute_t * ptr = PythonClientAPI::intattributes;
    
    while (ptr->attribute != NULL) {
    	if( !strcmp(forAttr, ptr->attribute) ) {
    	    return ptr;
    	}
    	ptr++;
    }
    
    return NULL;
}

PythonClientAPI::strattribute_t * PythonClientAPI::GetStr(const char * forAttr)
{
    PythonClientAPI::strattribute_t * ptr = PythonClientAPI::strattributes;
    
    while (ptr->attribute != NULL) {
    	if( !strcmp(forAttr, ptr->attribute) ) {
    	    return ptr;
    	}
    	ptr++;
    }
    
    return NULL;	
}

PythonClientAPI::objattribute_t * PythonClientAPI::GetObj(const char * forAttr)
{
    PythonClientAPI::objattribute_t * ptr = PythonClientAPI::objattributes;
    
    while (ptr->attribute != NULL) {
    	if( !strcmp(forAttr, ptr->attribute) ) {
    	    return ptr;
    	}
    	ptr++;
    }
    
    return NULL;	
}

PythonClientAPI::intsetter PythonClientAPI::GetIntSetter(const char * forAttr)
{
    PythonClientAPI::intattribute_t * ptr = PythonClientAPI::GetInt(forAttr);
    if (ptr) {
    	return ptr->setter;
    }
    return NULL;
}

PythonClientAPI::intgetter PythonClientAPI::GetIntGetter(const char * forAttr)
{
    PythonClientAPI::intattribute_t * ptr = PythonClientAPI::GetInt(forAttr);
    if (ptr) {
    	return ptr->getter;
    }
    return NULL;
}

PythonClientAPI::strsetter PythonClientAPI::GetStrSetter(const char * forAttr)
{
    PythonClientAPI::strattribute_t * ptr = PythonClientAPI::GetStr(forAttr);
    if (ptr) {
    	return ptr->setter;
    }
    return NULL;
}

PythonClientAPI::strgetter PythonClientAPI::GetStrGetter(const char * forAttr)
{
    PythonClientAPI::strattribute_t * ptr = PythonClientAPI::GetStr(forAttr);
    if (ptr) {
    	return ptr->getter;
    }
    return NULL;
}

PythonClientAPI::objsetter PythonClientAPI::GetObjSetter(const char * forAttr)
{
    PythonClientAPI::objattribute_t * ptr = PythonClientAPI::GetObj(forAttr);
    if (ptr) {
    	return ptr->setter;
    }
    return NULL;
}

PythonClientAPI::objgetter PythonClientAPI::GetObjGetter(const char * forAttr)
{
    PythonClientAPI::objattribute_t * ptr = PythonClientAPI::GetObj(forAttr);
    if (ptr) {
    	return ptr->getter;
    }
    return NULL;
}

const char * PythonClientAPI::GetEnviroFile()
{
    const StrPtr * s = enviro->GetEnviroFile();
    if (s) {
	return s->Text();
    }
    else {
	return NULL;
    }
}

int PythonClientAPI::SetEnviroFile( const char *v )
{
    enviro->SetEnviroFile( v );
    enviro->Reload();

    return 0;
}

// Returns an array of string pointers with the attributes defined
// in P4API, such as "client" or "port"
// Ownership of returned list is passed to caller!
// Free it, keep it or suffer memory leak!
 
const char ** PythonClientAPI::GetAttributes()
{
    size_t intAttrCount = 0;
    size_t strAttrCount = 0;
    size_t objAttrCount = 0;
    
    for (PythonClientAPI::intattribute_t * pi = PythonClientAPI::intattributes;
         pi->attribute != NULL; pi++) 
    {
    	intAttrCount++;
    }
    
    for (PythonClientAPI::strattribute_t * ps = PythonClientAPI::strattributes;
         ps->attribute != NULL; ps++) 
    {
    	strAttrCount++;
    }

    for (PythonClientAPI::objattribute_t * po = PythonClientAPI::objattributes;
         po->attribute != NULL; po++) 
    {
    	objAttrCount++;
    }

    size_t total = intAttrCount + strAttrCount + + objAttrCount + 1;
    
    const char ** result = (const char **) malloc(total * sizeof(const char *));
    const char **ptr = result;

    
    for (PythonClientAPI::intattribute_t * pi = PythonClientAPI::intattributes;
         pi->attribute != NULL; pi++) 
    {
    	*ptr = pi->attribute; ptr++;
    }
    for (PythonClientAPI::strattribute_t * ps = PythonClientAPI::strattributes;
         ps->attribute != NULL; ps++) 
    {
    	*ptr = ps->attribute; ptr++;
    }
    for (PythonClientAPI::objattribute_t * po = PythonClientAPI::objattributes;
         po->attribute != NULL; po++) 
    {
    	*ptr = po->attribute; ptr++;
    }
    *ptr = NULL;    
    
    return result;
}


int PythonClientAPI::SetTagged( int enable )
{
    if( enable )
	SetTag();
    else
	ClearTag();
	
    return 0;
}

int PythonClientAPI::GetTagged()
{
    return IsTag();
}

int PythonClientAPI::SetTrack( int enable )
{
    if ( IsConnected() ) {
	PyErr_SetString(P4Error, "Can't change tracking once you've connected.");
	return -1;
    }
    else {
	if( enable ) {
	    SetTrackMode();
	    ui.SetTrack(true);
	}
	else {
	    ClearTrackMode();
	    ui.SetTrack(false);
	}
    }
    return 0;
}

int PythonClientAPI::GetTrack()
{
    return IsTrackMode() != 0;
}

int PythonClientAPI::SetStreams( int enable )
{
    if( enable )
	SetStreamsMode();
    else
	ClearStreamsMode();

    return 0;
}

int PythonClientAPI::GetStreams()
{
    return IsStreamsMode() != 0;
}

int PythonClientAPI::SetGraph( int enable )
{
    if (enable)
        SetGraphMode();
    else
        ClearGraphMode();

    return 0;
}

int PythonClientAPI::GetGraph()
{
    return IsGraphMode() != 0;
}

int PythonClientAPI::SetCwd( const char *c )
{
    client.SetCwd( c );
    enviro->Config( StrRef( c ) );
    return 0;
}

int PythonClientAPI::SetCharset( const char *c )
{
    StrBuf buf("[P4] Setting charset: ");
    buf << c;

    debug.debug(P4PYDBG_COMMANDS, buf.Text() );

    CharSetApi::CharSet cs = CharSetApi::NOCONV;
    
    if ( strlen(c) > 0 ) {
	cs = CharSetApi::Lookup( c );
	if( cs < 0 )
	{
	    if( exceptionLevel )
	    {
		StrBuf	m;
		m = "Unknown or unsupported charset: ";
		m.Append( c );
		Except( "P4.charset", m.Text() );
		return -1;
	    }
	    return -1;
	}
    }

#if PY_MAJOR_VERSION < 3
    if( CharSetApi::Granularity( cs ) != 1 ) {
	Except( "P4.charset", "P4Python does not support a wide charset!");
	return -1;
    }
#endif

    client.SetCharset(c);

#if PY_MAJOR_VERSION >= 3
    if( strlen(c) > 0 && strcmp("none", c) != 0 ) {
	CharSetApi::CharSet utf8 = CharSetApi::UTF_8;
	client.SetTrans( utf8, cs, utf8, utf8 );
    }
    else {
	cs = CharSetApi::NOCONV;
	client.SetTrans(cs, cs, cs, cs);
    }
#else
    client.SetTrans( cs, cs, cs, cs );
#endif
    
    return 0;
}

int PythonClientAPI::SetEncoding( const char *e )
{
    // TODO: verify the different types of encoding and throw an error if it's not supported
    specMgr.SetEncoding( e );

    return 0;
}

int PythonClientAPI::SetTicketFile( const char *p )
{
    client.SetTicketFile( p );
    ticketFile = p;
    
    return 0;
}

int PythonClientAPI::SetDebug( int d )
{
    debug.setDebug(d);
	
    return 0; 
}

int PythonClientAPI::SetApiLevel( int level )
{
    StrBuf	b;
    b << level;
    apiLevel = level;
    client.SetProtocol( "api", b.Text() );
    ui.SetApiLevel( level );
    
    return 0;
}

int PythonClientAPI::SetPort( const char *p ) 
{
    if ( IsConnected() ) {
	PyErr_SetString(P4Error, "Can't change port once you've connected."); 
	return -1;
    }
    else {
	client.SetPort( p );
	return 0; 
    }
}

const char * PythonClientAPI::GetEnv( const char *var )
{
    return enviro->Get( var );
}

PyObject * PythonClientAPI::SetEnv( const char *var, const char *val )
{
    Error e;

    enviro->Set(var, val, &e);

    if ( e.Test() && exceptionLevel ) {
	Except( "P4.set_env()", &e );
	return NULL;
    }

    if ( e.Test() )
	Py_RETURN_FALSE;

    Py_RETURN_TRUE;
}

#if PY_MAJOR_VERSION >= 3

PyObject * PythonClientAPI::Convert(const char * charset, PyObject * content)
{
    debug.debug( P4PYDBG_COMMANDS, "[P4] Convert" );

    CharSetApi::CharSet utf8 = CharSetApi::UTF_8;
    CharSetApi::CharSet cs = CharSetApi::Lookup( charset );
    if( cs < 0 ) {
	if( exceptionLevel )
	{
	    StrBuf	m;
	    m = "Unknown or unsupported charset: ";
	    m.Append( charset );
	    Except( "P4.__convert", m.Text() );
	    return NULL;
	}
	return NULL;
    }

    if( cs == CharSetApi::UTF_8 ) {
	// no conversion from UTF8 to UTF8 needed
	PyObject * bytes = PyUnicode_AsUTF8String(content);

	return bytes;
    }
    else {
	CharSetCvt * cvt = CharSetCvt::FindCvt(utf8, cs);

	// let's be paranoid

	if( cvt == NULL ) {
	    if( exceptionLevel )
	    {
		StrBuf	m;
		m = "Cannot convert to charset: ";
		m.Append( charset );
		Except( "P4.__convert", m.Text() );
		return NULL;
	    }
	    return NULL;
	}

	PyObject * bytes = PyUnicode_AsUTF8String(content);
	const char * contentAsUTF8 = PyBytes_AS_STRING(bytes);

	int retlen = 0;
	const char * converted = cvt->FastCvt(contentAsUTF8, (int)strlen(contentAsUTF8), &retlen);
	Py_DECREF( bytes ); // we do not need this object anymore

	if (converted == NULL) {
		if ( exceptionLevel )
		{
		StrBuf m;
		if (cvt->LastErr() == CharSetCvt::NOMAPPING)
			m = "Translation of file content failed";
		else if (cvt->LastErr() == CharSetCvt::PARTIALCHAR)
			m = "Partial character in translation";
		else {
			m = "Cannot convert to charset: ";
			m.Append( charset );
		}
		delete cvt;
		Except( "P4.__convert", m.Text() );
		return NULL;
		}
	}

	PyObject * result = PyBytes_FromStringAndSize(converted, retlen);
	delete cvt;

	return result;
    }
}

#endif

PyObject * PythonClientAPI::GetMembers() {
    debug.debug( P4PYDBG_COMMANDS, "[P4] GetMembers");
    
    PyObject * memberList = PyList_New(0); // empty list
    
    static const char ** members = PythonClientAPI::GetAttributes();
    for (int i = 0; members[i] != NULL; ++i) {
    	const char * member = members[i];
        PyObject * str = CreatePythonString(member);
    	PyList_Append(memberList, str);
        Py_DECREF( str );
    }
    
    return memberList;
}

PyObject * PythonClientAPI::GetConfigFiles() {
    debug.debug( P4PYDBG_COMMANDS, "[P4] GetConfigFiles");

    PyObject * configFiles = PyList_New(0); // empty list

    const StrArray * configs = client.GetConfigs();
    for (int i = 0; i < configs->Count(); i++) {
	const StrBuf * entry = configs->Get(i);
	PyObject * str = CreatePythonString(entry->Text());
	PyList_Append(configFiles, str);
	Py_DecRef( str );
    }

    return configFiles;
}

PyObject * PythonClientAPI::Connect()
{
    debug.debug( P4PYDBG_COMMANDS, "[P4] Connecting to Perforce" );

    if ( IsConnected() )
    {
	(void) PyErr_WarnEx( PyExc_UserWarning, 
		"P4.connect() - Perforce client already connected!", 1 );
	Py_RETURN_NONE;
    }

    return ConnectOrReconnect();
}

PyObject * PythonClientAPI::ConnectOrReconnect()
{
    if( IsTrackMode() )
	client.SetProtocol( "track", "" );

    Error e;

    ResetFlags();

    {
        ReleasePythonLock guard;    // Release GIL during connect
        client.Init( &e );
    }
    
    if ( e.Test() && exceptionLevel ) {
	Except( "P4.connect()", &e );
	return NULL;
    }

    if ( e.Test() )
	Py_RETURN_FALSE;

    // If an iterator is defined, reset the break functionality
    // for the KeepAlive function

    if( ui.GetHandler() != Py_None )
    {
	client.SetBreak( &ui );
    }

    SetConnected();
    Py_RETURN_NONE;
}

PyObject * PythonClientAPI::Connected()
{
    if ( IsConnected() && !client.Dropped()) {
	Py_RETURN_TRUE;
    }
    else if ( IsConnected() ) 
	Disconnect();

    Py_RETURN_FALSE;
}

PyObject * PythonClientAPI::Disconnect()
{
    debug.debug ( P4PYDBG_COMMANDS, "[P4] Disconnect" );

    if ( ! IsConnected() )
    {
	(void) PyErr_WarnEx( PyExc_UserWarning, 
		"P4.disconnect() - Not connected!", 1 );
	Py_RETURN_NONE;
    }
    
    Error	e;

    {
        ReleasePythonLock guard;    // Release GIL during disconnect
        client.Final( &e );
    }
    
    ResetFlags();
    
    // Clear the specdef cache.
    specMgr.Reset();

    // Clear out any results from the last command
    ui.Reset();

    Py_RETURN_NONE;
}

PyObject * PythonClientAPI::Run( const char *cmd, int argc, char * const *argv )
{
    // Save the entire command string for our error messages. Makes it
    // easy to see where a script has gone wrong.
    StrBuf	cmdString;
    cmdString << "\"p4 " << cmd;
    for( int i = 0; i < argc; i++ )
        cmdString << " " << argv[ i ];
    cmdString << "\"";

    StrBuf buf("[P4] Executing ");
    buf << cmdString;

    debug.info ( buf.Text() );

    if ( depth )
    {
    	(void) PyErr_WarnEx( PyExc_UserWarning, 
		"P4.run() - Can't execute nested Perforce commands.", 1 );
	Py_RETURN_FALSE;
    }

    // Clear out any results from the previous command
    ui.Reset();

    // Tell the UI which command we're running.
    ui.SetCommand( cmd );

    if ( ! IsConnected() && exceptionLevel ) {
	Except( "P4.run()", "not connected." );
	return NULL;
    }
    
    if ( ! IsConnected()  )
	Py_RETURN_FALSE;

    depth++;
    RunCmd( cmd, &ui, argc, argv );
    depth--;

    PyObject *handler = ui.GetHandler();
    Py_DECREF(handler);
    if( handler != Py_None ) {
	if( client.Dropped() && ! ui.IsAlive() ) {
	    Disconnect();
	    ConnectOrReconnect();
	}

	if( PyErr_Occurred() )
	    return NULL;
    }

    p4py::P4Result &results = ui.GetResults();

    if ( results.ErrorCount() && exceptionLevel ) {
	Except( "P4#run", "Errors during command execution", cmdString.Text() );

	if( results.FatalError() )
	    Disconnect();

	return NULL;
    }

    if ( results.WarningCount() && exceptionLevel > 1 ) {
	Except( "P4#run", "Warnings during command execution",cmdString.Text());
	return NULL;
    }

    return results.GetOutput();
}


int PythonClientAPI::SetInput( PyObject * input )
{
    debug.debug ( P4PYDBG_COMMANDS, "[P4] Received input for next command" );

    if ( ! ui.SetInput( input ) )
    {
	if ( exceptionLevel ) {
	    Except( "P4#input", "Error parsing supplied data." );
	    return -1;
	}
    	else {
	    return -1;
    	}
    }
    return 0;
}

PyObject * PythonClientAPI::GetInput()
{
    return ui.GetInput();
}

int PythonClientAPI::SetResolver( PyObject * resolver )
{
    debug.debug ( P4PYDBG_COMMANDS, "[P4] Received resolver used for resolve" );

    if ( ! ui.SetResolver( resolver ) )
    {
        if ( exceptionLevel ) {
            Except( "P4#resolver", "Error setting resolver." );
            return -1;
        }
        else {
            return -1;
        }
    }
    return 0;
}

PyObject * PythonClientAPI::GetResolver()
{
    return ui.GetResolver();
}

int PythonClientAPI::SetHandler( PyObject * iterator )
{
    debug.debug ( P4PYDBG_COMMANDS, "[P4] Received iterator object" );

    if ( ! ui.SetHandler( iterator ) )
    {
	return -1;
    }

    if( iterator == Py_None)
	client.SetBreak(NULL);
    else
	client.SetBreak(&ui);

    return 0;
}

PyObject * PythonClientAPI::GetHandler()
{
    return ui.GetHandler();
}

int PythonClientAPI::SetProgress( PyObject * progress )
{
    debug.debug ( P4PYDBG_COMMANDS, "[P4] Received progress object" );

    if ( ! ui.SetProgress( progress ) )
    {
	return -1;
    }

    return 0;
}

PyObject * PythonClientAPI::GetProgress()
{
    return ui.GetProgress();
}

int PythonClientAPI::SetLogger( PyObject * logger )
{
    debug.setLogger(logger);

    return 0;
}

PyObject * PythonClientAPI::GetLogger()
{
    return debug.getLogger();
}

//
// Parses a string supplied by the user into a dict. To do this we need
// the specstring from the server. We try to cache those as we see them, 
// but the user may not have executed any commands to allow us to cache
// them so we may have to fetch the spec first.
//

PyObject * PythonClientAPI::ParseSpec( const char * type, const char *form )
{
    if ( !specMgr.HaveSpecDef( type ) )
    {
	if( exceptionLevel )
	{
	    StrBuf m;
	    m = "No spec definition for ";
	    m.Append( type );
	    m.Append( " objects." );
	    Except( "P4.parse_spec()", m.Text() );
	    return NULL;
	}
	else
	{
	    Py_RETURN_FALSE;
	}
    }

    // Got a specdef so now we can attempt to parse it.
    Error e;
    PyObject * v = specMgr.StringToSpec( type, form, &e );
    
    if ( e.Test() ) 
    {
	if( exceptionLevel ) {
	    Except( "P4.parse_spec()", &e );
	    return NULL;
	}
	else {
	    Py_RETURN_FALSE;
	}
    }

    return v;
}

//
// Converts a dict supplied by the user into a string using the specstring
// from the server. We may have to fetch the specstring first.
//

PyObject * PythonClientAPI::FormatSpec( const char *type, PyObject * dict )
{
    if ( !specMgr.HaveSpecDef( type ) )
    {
	if( exceptionLevel )
	{
	    StrBuf m;
	    m = "No spec definition for ";
	    m.Append( type );
	    m.Append( " objects." );
	    Except( "P4.format_spec()", m.Text() );
	    return NULL;
	}
	else
	{
	    Py_RETURN_FALSE;
	}
    }

    // Got a specdef so now we can attempt to convert. 
    StrBuf	buf;
    Error	e;

    specMgr.SpecToString( type, dict, buf, &e );
    if( !e.Test() ) {
	return CreatePythonString( buf.Text() );
    }
    
    if( exceptionLevel )
    {
	StrBuf m;
	m = "Error converting hash to a string.";
	if( e.Test() ) e.Fmt( m, EF_PLAIN );
	Except( "P4.format_spec()", m.Text() );
	return NULL;
    }
    Py_RETURN_NONE;
}

//
// Sets the spec field in the cache, used for triggers with the new 16.1 ability to pass the spec definition
//

PyObject * PythonClientAPI::DefineSpec( const char *type, const char * spec)
{
    specMgr.AddSpecDef(type, spec);

    Py_RETURN_TRUE;
}

//
// Returns a dict whose keys contain the names of the fields in a spec of the
// specified type. Not yet exposed to Python clients, but may be in future.
//
PyObject * PythonClientAPI::SpecFields( const char * type )
{
    if ( !specMgr.HaveSpecDef( type ) )
    {
	if( exceptionLevel )
	{
	    StrBuf m;
	    m = "No spec definition for ";
	    m.Append( type );
	    m.Append( " objects." );
	    Except( "P4.spec_fields()", m.Text() );
	    return NULL;
	}
	else
	{
	    Py_RETURN_FALSE;
	}
    }

    return specMgr.SpecFields( type );
}

//
// Sets a server protocol value
//
PyObject * PythonClientAPI::SetProtocol( const char * var, const char * val )
{
    client.SetProtocol( var, val );

    Py_RETURN_NONE;
}

//
// Gets a protocol value
//
PyObject * PythonClientAPI::GetProtocol( const char * var ) 
{
    StrPtr *pv = client.GetProtocol( var );
    if ( pv ) {
	return CreatePythonString( pv->Text() );
    }
    Py_RETURN_NONE;
}

//
// Checks whether a path is ignored or not
//
PyObject * PythonClientAPI::IsIgnored( const char * path)
{
    StrRef p = path;
    if ( client.GetIgnore()->Reject( p, client.GetIgnoreFile() ) ) {
	Py_RETURN_TRUE;
    }
    Py_RETURN_FALSE;
}

//
// Returns the server level as provided by the server
//

PyObject * PythonClientAPI::GetServerLevel()
{
    if( !IsConnected() ) {
	PyErr_SetString(P4Error, "Not connected to a Perforce server");
	return NULL;
    }
    
    if( !IsCmdRun() ) 
	Run( "info", 0, 0 );

    return PyInt_FromLong(server2);
}

// 
// Returns true if the server is case-insensitive
// Might throw exception if the information is not available yet
//
PyObject * PythonClientAPI::GetServerCaseInsensitive() 
{
    if( !IsConnected() ) {
	PyErr_SetString(P4Error, "Not connected to a Perforce server");
	return NULL;
    }
    
    if( !IsCmdRun() ) 
	Run( "info", 0, 0 );

    if ( IsCaseFold() ) {
	Py_RETURN_TRUE;
    }
    Py_RETURN_FALSE;
}

// 
// Returns true if the server is case-insensitive
// Might throw exception if the information is not available yet
//
PyObject * PythonClientAPI::GetServerUnicode() 
{
    if( !IsConnected() ) {
	PyErr_SetString(P4Error, "Not connected to a Perforce server");
	return NULL;
    }
    
    if( !IsCmdRun() ) 
	Run( "info", 0, 0 );

    if ( IsUnicode() ) {
	Py_RETURN_TRUE;
    }
    Py_RETURN_FALSE;
}

void PythonClientAPI::Except( const char *func, const char *msg )
{
    StrBuf	m;
    StrBuf	errors;
    StrBuf	warnings;
    bool	terminate = false;
    
    m << "[" << func << "] " << msg;

    // Now append any errors and warnings to the text
    ui.GetResults().FmtErrors( errors );
    ui.GetResults().FmtWarnings( warnings );
    
    if( errors.Length() )
    {
	m << "\n" << errors;
	terminate= true;
    }

    if( exceptionLevel > 1 && warnings.Length() )
    {
	m << "\n" << warnings;
	terminate = true;
    }

    if( terminate )
	m << "\n\n";

    if( apiLevel < 68 )
	PyErr_SetString(P4Error, m.Text() );
    else {
	// return a list with three elements:
	// the string value, the list of errors and list of warnings
	// P4Exception will sort out what's what
	PyObject * list = PyList_New(3);
	PyList_SET_ITEM(list, 0, CreatePythonString(m.Text()));
	PyList_SET_ITEM(list, 1, ui.GetResults().GetErrors());
	PyList_SET_ITEM(list, 2, ui.GetResults().GetWarnings());

	PyErr_SetObject(P4Error, list);
    Py_DECREF(list);
    }
}

void PythonClientAPI::Except( const char *func, Error *e )
{
    StrBuf	m;

    e->Fmt( &m );
    Except( func, m.Text() );
}


void PythonClientAPI::Except( const char *func, const char *msg, const char *cmd )
{
    StrBuf m;

    m << msg;
    m << "( " << cmd << " )";
    Except( func, m.Text() );
}

//
// RunCmd is a private function to work around an obscure protocol
// bug in 2000.[12] servers. Running a "p4 -Ztag client -o" messes up the
// protocol so if they're running this command then we disconnect and
// reconnect to refresh it. For efficiency, we only do this if the 
// server2 protocol is either 9 or 10 as other versions aren't affected.
//

void PythonClientAPI::RunCmd(const char *cmd, ClientUser *ui, int argc, char * const *argv)
{
    StrBuf theProgStr = SetProgString(prog);

    client.SetProg( &theProgStr );

    if( version.Length() )
	client.SetVersion( &version );

    if( IsTag() )
        client.SetVar( "tag" );

    if( IsStreamsMode() && apiLevel >= 70 )
        client.SetVar( "enableStreams" );

    if ( IsGraphMode() && apiLevel > 81 )
        client.SetVar( "enableGraph" );

    // If maxresults or maxscanrows is set, enforce them now
    if( maxResults  )	client.SetVar( "maxResults",  maxResults  );
    if( maxScanRows )	client.SetVar( "maxScanRows", maxScanRows );
    if( maxLockTime )	client.SetVar( "maxLockTime", maxLockTime );
    if( maxOpenFiles )	client.SetVar( "maxOpenFiles", maxOpenFiles );
    if( maxMemory)	client.SetVar( "maxMemory", maxMemory );

    // if progress is set, set the progress var
    if( ((PythonClientUser*)ui)->GetProgress() != Py_None )
	client.SetVar( P4Tag::v_progress, 1);

    {
        ReleasePythonLock guard;
        
        client.SetArgv( argc, argv );
        client.Run( cmd, ui );
    }
    
    // Have to request server2 protocol *after* a command has been run. I
    // don't know why, but that's the way it is.

    if ( ! IsCmdRun() )
    {
	StrPtr *pv = client.GetProtocol( "server2" );
	if ( pv )
	    server2 = pv->Atoi();

	pv = client.GetProtocol( P4Tag::v_nocase );
	if ( pv ) 
	    SetCaseFold();
	    
	pv = client.GetProtocol( P4Tag::v_unicode );
	if ( pv && pv->Atoi() )
	    SetUnicode();
    }
    SetCmdRun();

}

void PythonClientAPI::SetBreak(PythonKeepAlive* cb)
{
    if( IsConnected() ) {
        debug.debug(P4PYDBG_COMMANDS, "[P4] Establish the callback" );
        client.SetBreak(cb);
    }

}
