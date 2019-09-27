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

$Id: //depot/main/p4-python/PythonClientUser.cpp#37 $

*******************************************************************************/
 
#include <Python.h>
#include <bytesobject.h>
#include "undefdups.h"
#include "python2to3.h"
#include <clientapi.h>
#include <i18napi.h>
#include <clientprog.h>
#include <strtable.h>
#include <enviro.h>
#include <hostenv.h>
#include <spec.h>
#include <diff.h>
#include <mapapi.h>

#include <iostream>
#include <sstream>
#include <iomanip>

#include "P4PythonDebug.h"
#include "SpecMgr.h"
#include "P4Result.h"
#include "PythonClientUser.h"
#include "PythonClientAPI.h"
#include "P4PythonDebug.h"
#include "PythonThreadGuard.h"
#include "PythonMergeData.h"
#include "PythonActionMergeData.h"
#include "P4MapMaker.h"
#include "PythonMessage.h"
#include "PythonTypes.h"
#include "PythonClientProgress.h"

using namespace std;

PythonClientUser::PythonClientUser( PythonDebug * dbg, p4py::SpecMgr *s )
    : specMgr(s),
      debug(dbg),
      results(dbg, s)
{
    track = false;
    alive = 1;
    apiLevel = atoi( P4Tag::l_client );
    
    Py_INCREF(Py_None);
    input = Py_None;
    
    Py_INCREF(Py_None);
    resolver = Py_None;

    Py_INCREF(Py_None);
    handler = Py_None;

    Py_INCREF(Py_None);
    progress = Py_None;
}

PythonClientUser::~PythonClientUser()
{
    Py_DECREF(input);
    Py_DECREF(resolver);
    Py_DECREF(handler);
    Py_DECREF(progress);
}

void PythonClientUser::Reset()
{
    results.Reset();
    // input data is untouched

    alive = 1; // yes, we want data from the server
}

void PythonClientUser::Finished()
{
    EnsurePythonLock guard;
    
    if ( input != Py_None )
	debug->debug( P4PYDBG_CALLS, "[P4] Cleaning up saved input" );

    PyObject * tmp = input;
    Py_INCREF(Py_None);
    input = Py_None;
    Py_DECREF(tmp);
}

static const int REPORT = 0;
static const int HANDLED = 1;
static const int CANCEL = 2;

// returns true if output should be reported
// false if the output is handled and should be ignored

bool PythonClientUser::CallOutputMethod( const char * method, PyObject * data)
{
    long answer = REPORT;

    PyObject * result = PyObject_CallMethod( this->handler , (char*) method, (char*)"O", data );
    if( result == NULL ) { // exception thrown
	alive = 0;
    }
    else {
	long a = PyInt_AsLong( result );
	Py_DECREF( result );
	if( a == -1 ) {
	    alive = 0; // exception thrown or silly return value
	}
	else
	{
	    if ( a & CANCEL)
		alive = 0;
	    answer = a & HANDLED;
	}
    }

    return ( answer == 0 );
}

void PythonClientUser::ProcessOutput( const char * method, PyObject * data )
{
    if( this->handler != Py_None )
    {
	if( CallOutputMethod( method, data ) )
	    results.AddOutput( data );
	else
	{
	    Py_DECREF( data );
	}
    }
    else
	results.AddOutput( data );
}

void PythonClientUser::ProcessMessage( Error *e )
{
    if( this->handler != Py_None )
    {
	int s = e->GetSeverity();

	if ( s == E_EMPTY || s == E_INFO )
	{
	    // info messages should be send to outputInfo
	    // not outputError, or untagged output looks
	    // very strange indeed

	    StrBuf m;
	    e->Fmt( &m, EF_PLAIN );
	    PyObject * s = specMgr->CreatePyString( m.Text() );

	    if( s && CallOutputMethod( "outputInfo", s) )
		results.AddOutput( s );
	}
	else
	{
	    P4Message * msg = (P4Message *) PyObject_New(P4Message, &P4MessageType);
	    msg->msg = new PythonMessage(e, specMgr);

	    if( CallOutputMethod( "outputMessage", (PyObject *) msg ) )
		results.AddError( e );
	}
    }
    else
	results.AddError( e );
}

void PythonClientUser::Message( Error *e )
{
    EnsurePythonLock guard;

    debug->debug( P4PYDBG_CALLS , "[P4] Message()" );
    StrBuf t;
    e->Fmt( t, EF_PLAIN );

    stringstream s;
    s << "... [" << e->FmtSeverity() << "] " << t.Text() << ends;

    debug->debug( P4PYDBG_DATA , s.str().c_str());

    ProcessMessage( e );
}

// If we have a progress callback registered, we accept progress indication

int PythonClientUser::ProgressIndicator()
{
    debug->debug( P4PYDBG_COMMANDS, "[P4] ProgressIndicator()" );

    int result = (this->progress != Py_None);

    return result;
}

ClientProgress * PythonClientUser::CreateProgress( int type )
{
    debug->debug( P4PYDBG_COMMANDS, "[P4] CreateProgress()" );

    if( this->progress == Py_None) {
	return NULL;
    }

    return new PythonClientProgress(progress, type);
}

void PythonClientUser::HandleError( Error *e )
{
    EnsurePythonLock guard;
    
    debug->debug( P4PYDBG_CALLS, "[P4] HandleError()" );

    StrBuf t;
    e->Fmt( t, EF_PLAIN );

    StrBuf buf("... ");
    buf << "... [" << e->FmtSeverity() << "] " << t.Text();

    debug->debug( P4PYDBG_DATA , buf.Text() );

    ProcessMessage( e );
}

void PythonClientUser::OutputText( const char *data, int length )
{
    EnsurePythonLock guard;
    
    debug->debug( P4PYDBG_CALLS , "[P4] OutputText()" );
    stringstream s;
    s << "... [" << length << "]" << setw(length) << data << ends;

    debug->debug( P4PYDBG_DATA, s.str().c_str() );

    if( track && length > 4 && data[0] == '-' && data[1] == '-' && data[2] == '-' && data[3] == ' ') {
	int p = 4;
	for( int i = 4; i < length; ++i ) {
	    if( data[i] == '\n' ) {
		if( i > p ) {
		    PyObject * str = specMgr->CreatePyStringAndSize(data + p, i - p);
		    if( str )
			results.AddTrack( str );
		    p = i + 5;
		}
		else {
		    // a hack, we have encountered a line that looked like track but wasn't
		    // try to undo the damage by clearing the track output and returning the
		    // original string

		    results.ClearTrack();
		    PyObject * str = specMgr->CreatePyStringAndSize(data, length);
		    if( str ) {
			results.AddOutput( str );
		    }
		    return;
		}
	    }
	}
    }
    else {
	PyObject * s = specMgr->CreatePyStringAndSize(data, length);
	if( s ) {
	    ProcessOutput("outputText", s);
	}
    }
}

void PythonClientUser::OutputInfo( char level, const char *data )
{
    EnsurePythonLock guard;
    
    debug->debug( P4PYDBG_CALLS, "[P4] OutputInfo()" );
    stringstream s;
    s << "... [" << level << "] " << data << ends;
    debug->debug( P4PYDBG_DATA, s.str().c_str() );

    PyObject * str = specMgr->CreatePyString(data);
    if( str ) {
	ProcessOutput("outputInfo", str);
    }
}

void PythonClientUser::OutputBinary( const char *data, int length )
{
    EnsurePythonLock guard;
    
    debug->debug( P4PYDBG_CALLS, "[P4] OutputBinary()" );

    if( debug->getDebug() > P4PYDBG_DATA ) {
	ios::fmtflags oldFlags = cout.flags();
	stringstream s;

	s << showbase << hex << internal << setfill('0') << uppercase;
	for( int l = 0; l < length; l++ )
	{
	    if( l % 16 == 0 )
		s << (l ? "\n" : "") <<  "... ";
	    s << setw(4) << data[ l ] << " ";
	}

	s.flags(oldFlags);
	
	debug->debug( P4PYDBG_DATA, s.str().c_str());
    }

    //
    // Binary is stored in a Byte array
    //

    PyObject * b = PyBytes_FromStringAndSize(data, length);

    ProcessOutput("outputBinary", b);
}

void PythonClientUser::OutputStat( StrDict *values )
{
    EnsurePythonLock guard;
    
    StrPtr *		spec 	= values->GetVar( "specdef" );
    StrPtr *		data 	= values->GetVar( "data" );
    StrPtr *		sf	= values->GetVar( "specFormatted" );
    StrDict *		dict	= values;
    SpecDataTable	specData;
    Error		e;

    //
    // Determine whether or not the data we've got contains a spec in one form
    // or another. 2000.1 -> 2005.1 servers supplied the form in a data variable
    // and we use the spec variable to parse the form. 2005.2 and later servers
    // supply the spec ready-parsed but set the 'specFormatted' variable to tell 
    // the client what's going on. Either way, we need the specdef variable set
    // to enable spec parsing.
    //
    int			isspec	= spec && ( sf || data );

    //
    // Save the spec definition for later 
    //
    if( spec )
	specMgr->AddSpecDef( cmd.Text(), spec->Text() );

    //
    // Parse any form supplied in the 'data' variable and convert it into a 
    // dictionary.
    //
    if( spec && data )
    {
	// 2000.1 -> 2005.1 server's handle tagged form output by supplying the form
	// as text in the 'data' variable. We need to convert it to a dictionary
	// using the supplied spec.
	debug->debug( P4PYDBG_CALLS, "[P4] OutputStat() - parsing form" );

	// Parse the form. Use the ParseNoValid() interface to prevent
	// errors caused by the use of invalid defaults for select items in
	// jobspecs.

	Spec s( spec->Text(), "", &e );

	if( !e.Test() ) s.ParseNoValid( data->Text(), &specData, &e );
	if( e.Test() )
	{
	    HandleError( &e );
	    return;
	}
	dict = specData.Dict();
    }

    //
    // If what we've got is a parsed form, then we'll convert it to a P4::Spec
    // object. Otherwise it's a plain dict.
    //
    PyObject * r = 0;

    if( isspec )
    {
	debug->debug( P4PYDBG_CALLS, "[P4] OutputStat() - Converting to P4::Spec object" );
	r = specMgr->StrDictToSpec( dict, spec );
    }
    else
    {
	debug->debug( P4PYDBG_CALLS, "[P4] OutputStat() - Converting to dict" );
	r = specMgr->StrDictToDict( dict );
    }

    ProcessOutput("outputStat", r );
}


/*
 * Diff support for Python API. Since the Diff class only writes its output
 * to files, we run the requested diff putting the output into a temporary
 * file. Then we read the file in and add its contents line by line to the 
 * results.
 */

void PythonClientUser::Diff( FileSys *f1, FileSys *f2, int doPage, 
				char *diffFlags, Error *e )
{
    EnsurePythonLock guard;
    
    debug->debug( P4PYDBG_CALLS, "[P4] Diff() - comparing files" );

    //
    // Duck binary files. Much the same as ClientUser::Diff, we just
    // put the output into Python space rather than stdout.
    //
    if( !f1->IsTextual() || !f2->IsTextual() )
    {
	if ( f1->Compare( f2, e ) )
	    results.AddOutput( "(... files differ ...)" );
	return;
    }

    // Time to diff the two text files. Need to ensure that the
    // files are in binary mode, so we have to create new FileSys
    // objects to do this.

    FileSys *f1_bin = FileSys::Create( FST_BINARY );
    FileSys *f2_bin = FileSys::Create( FST_BINARY );
    FileSys *t = FileSys::CreateGlobalTemp( f1->GetType() );

    f1_bin->Set( f1->Name() );
    f2_bin->Set( f2->Name() );

    {
	//
	// In its own block to make sure that the diff object is deleted
	// before we delete the FileSys objects.
	//
	::Diff d;

	d.SetInput( f1_bin, f2_bin, diffFlags, e );
	if ( ! e->Test() ) d.SetOutput( t->Name(), e );
	if ( ! e->Test() ) d.DiffWithFlags( diffFlags );
	d.CloseOutput( e );

	// OK, now we have the diff output, read it in and add it to 
	// the output.
	if ( ! e->Test() ) t->Open( FOM_READ, e );
	if ( ! e->Test() ) 
	{
	    StrBuf 	b;
	    while( t->ReadLine( &b, e ) )
		results.AddOutput( b.Text() );
	}
    }

    delete t;
    delete f1_bin;
    delete f2_bin;

    if ( e->Test() ) HandleError( e );
}


/*
 * convert input from the user into a form digestible to Perforce. This
 * involves either (a) converting any supplied dict to a Perforce form, or
 * (b) running to_s on whatever we were given. 
 */

void PythonClientUser::InputData( StrBuf *strbuf, Error *e )
{
    EnsurePythonLock guard;
    
    debug->debug ( P4PYDBG_CALLS, "[P4] InputData(). Using supplied input" );

    PyObject * inval = input;

    if( PyTuple_Check(input) )
    {
	inval = PyTuple_GetItem(input, 0);
	input = PyTuple_GetSlice(input, 1, PyTuple_Size(input));
    }
    else if ( PyList_Check(input) )
    {
    	inval = PyList_GetItem(input, 0);
	input = PyList_GetSlice(input, 1, PyList_Size(input));
    }
    
    if( inval == Py_None || inval == NULL )
    {
	PyErr_WarnEx( PyExc_UserWarning, 
		"[P4] Expected user input, found none. "
		"Missing call to P4.input ?", 1 );
	return;
    }

    if ( PyDict_Check( inval ) )
    {
	StrPtr * specDef = varList->GetVar( "specdef" );

	specMgr->AddSpecDef( cmd.Text(), specDef->Text() );
	specMgr->SpecToString( cmd.Text(), inval, *strbuf, e );
	return;
    }
    
    // Convert whatever's left into a string
    PyObject * str = PyObject_Str(inval);
    strbuf->Set( GetPythonString(str) );
    Py_XDECREF(str);
}

/*
 * In a script we don't really want the user to see a prompt, so we
 * (ab)use P4.input= to allow the caller to supply the
 * answer before the question is asked.
 */
void PythonClientUser::Prompt( const StrPtr &msg, StrBuf &rsp, int noEcho, Error *e )
{
    EnsurePythonLock guard;
    stringstream s;
    s << "[P4] Prompt(): " << msg.Text();
    debug->debug ( P4PYDBG_CALLS, s.str().c_str() );

    InputData( &rsp, e );
}


/*
 * Do a resolve.
 */
int PythonClientUser::Resolve( ClientMerge *m, Error *e )
{
    debug->debug( P4PYDBG_CALLS, "[P4] Resolve()" );
    
    EnsurePythonLock guard;
    
    //
    // If no resolver is defined, default to using the merger's resolve
    // if p4.input is set. Otherwise, bail out of the resolve
    //
    if( this->resolver == Py_None ) {
        if ( this->input != Py_None ) {
            return m->Resolve( e );
        }
        else {
            PyErr_WarnEx( PyExc_UserWarning, 
                          "[P4::Resolve] Resolve called with no resolver and no input -> skipping resolve", 1);
            return CMS_QUIT;
        }
    }

    // 
    // First detect what the merger thinks the result ought to be
    //
    StrBuf t;
    MergeStatus autoMerge = m->AutoResolve( CMF_FORCE );

    // Now convert that to a string;
    switch( autoMerge )
    {
    case CMS_QUIT:	t = "q";	break;
    case CMS_SKIP:	t = "s";	break;
    case CMS_MERGED:	t = "am";	break;
    case CMS_EDIT:	t = "e";	break;
    case CMS_YOURS:	t = "ay";	break;
    case CMS_THEIRS:	t = "at";	break;
    }

    PyObject * mergeData = MkMergeInfo( m, t );

    PyObject * result = PyObject_CallMethod( this->resolver , (char*)"resolve", (char*)"(O)", mergeData );
    if( result == NULL ) { // exception thrown, bug out of here
	return CMS_QUIT;
    }
    else {
	Py_DECREF( result );
    }

    if (IsString(result)) {
        StrBuf reply = GetPythonString( result );

        if( reply == "ay" ) 		return CMS_YOURS;
        else if( reply == "at" )	return CMS_THEIRS;
        else if( reply == "am" )	return CMS_MERGED;
        else if( reply == "ae" )	return CMS_EDIT;
        else if( reply == "s" )		return CMS_SKIP;
        else if( reply == "q" ) 	return CMS_QUIT;
        else {
            StrBuf warning("[P4::Resolve] Illegal response : '");
            warning << reply;
            warning << "', skipping resolve";

            PyErr_WarnEx( PyExc_UserWarning, warning.Text(), 1);
            return CMS_QUIT;
        }
    }
    else {
        PyErr_WarnEx( PyExc_UserWarning, "[P4::Resolve] Illegal response : Expected String", 1);
        return CMS_QUIT;
    }
}

/*
 * Resolver method for action resolve
 */
int PythonClientUser::Resolve( ClientResolveA *m, int preview, Error *e )
{
    debug->debug ( P4PYDBG_CALLS, "[P4] Resolve(Action)" );

    EnsurePythonLock guard;

    //
    // If no resolver is defined, default to using the merger's resolve
    // if p4.input is set. Otherwise, bail out of the resolve
    //
    if( this->resolver == Py_None ) {
        if ( this->input != Py_None ) {
            return m->Resolve( 0, e ); /* no preview, actually do it */
        }
        else {
            PyErr_WarnEx( PyExc_UserWarning,
                          "[P4::Resolve] Resolve called with no resolver and no input -> skipping resolve", 1);
            return CMS_QUIT;
        }
    }

    //
    // First detect what the merger thinks the result ought to be
    //
    StrBuf t;
    MergeStatus autoMerge = m->AutoResolve( CMF_FORCE );

    // Now convert that to a string;
    switch( autoMerge )
    {
    case CMS_QUIT:	t = "q";	break;
    case CMS_SKIP:	t = "s";	break;
    case CMS_MERGED:	t = "am";	break;
    case CMS_YOURS:	t = "ay";	break;
    case CMS_THEIRS:	t = "at";	break;
    default:
	cerr << "Unknown autoMerge result " << autoMerge << " encountered" << endl;
	t = "q";
	break;
    }

    PyObject * mergeData = MkActionMergeInfo( m, t );

    PyObject * result = PyObject_CallMethod( this->resolver , (char*)"actionResolve", (char*)"(O)", mergeData );
    if( result == NULL ) { // exception thrown, bug out of here
	return CMS_QUIT;
    }
    else {
	Py_DECREF( result );
    }

    StrBuf reply = GetPythonString( result );

    if( reply == "ay" ) 		return CMS_YOURS;
    else if( reply == "at" )	return CMS_THEIRS;
    else if( reply == "am" )	return CMS_MERGED;
    else if( reply == "s" )		return CMS_SKIP;
    else if( reply == "q" ) 	return CMS_QUIT;
    else {
	StrBuf warning("[P4::Resolve] Illegal response : '");
	warning << reply;
	warning << "', skipping resolve";

	PyErr_WarnEx( PyExc_UserWarning, warning.Text(), 1);
	return CMS_QUIT;
    }
}

/*
 * Accept input from Python. We just save what we're given here because we may not 
 * have the specdef available to parse it with at this time.
 */

PyObject * PythonClientUser::SetInput( PyObject * i )
{
    debug->debug ( P4PYDBG_CALLS, "[P4] SetInput()" );

    PyObject * tmp = input;
    input = i;
    Py_INCREF(input);
    Py_DECREF(tmp);
    
    Py_RETURN_TRUE;
}

/*
 * Sets the resolver from Python
 */

PyObject * PythonClientUser::SetResolver( PyObject * r )
{
    debug->debug ( P4PYDBG_CALLS, "[P4] SetResolver()" );

    PyObject * tmp = resolver;
    resolver = r;
    Py_INCREF(resolver);
    Py_DECREF(tmp);
    
    Py_RETURN_TRUE;
}

/*
 * Sets the callback from Python
 */

PyObject * PythonClientUser::SetHandler( PyObject * c )
{
    debug->debug( P4PYDBG_CALLS, "[P4] SetIterator()" );

    int result = PyObject_IsInstance( c, P4OutputHandler );

    if( c == Py_None || 1 == result ) {
	PyObject * tmp = handler;
	handler = c;

	alive = 1; // ensure that we don't drop out after the next call

	Py_INCREF(handler);
	Py_DECREF(tmp);

	Py_RETURN_TRUE;
    }
    else if ( 0 == result ) {
	PyErr_SetString(PyExc_TypeError, "Iterator must be an instance of P4.Iterator.");
    }

    return NULL;
}

PyObject * PythonClientUser::SetProgress( PyObject * p )
{
    debug->debug( P4PYDBG_CALLS, "[P4] SetProgress()" );

    int result = PyObject_IsInstance( p, P4Progress );

    if( p == Py_None || 1 == result ) {
	PyObject * tmp = progress;
	progress = p;

	alive = 1; // ensure that we don't drop out after the next call

	Py_INCREF(progress);
	Py_DECREF(tmp);

	Py_RETURN_TRUE;
    }
    else if ( 0 == result ) {
	PyErr_SetString(PyExc_TypeError, "Progress must be an instance of P4.Progress.");
    }

    return NULL;

}

void PythonClientUser::SetApiLevel( int level )
{
    apiLevel = level;
    results.SetApiLevel( level );
}

PyObject * PythonClientUser::MkMergeInfo( ClientMerge *m, StrPtr &hint )
{
    debug->debug ( P4PYDBG_CALLS, "[P4] MkMergeInfo()" );

    EnsurePythonLock guard;
    
    P4MergeData *mergeObj = PyObject_New(P4MergeData, &P4MergeDataType);
    if (mergeObj != NULL) { 
        mergeObj->mergeData = new PythonMergeData( this, m, hint);
    }
    else {
        PyErr_WarnEx( PyExc_UserWarning, "[P4::Resolve] Failed to create object in MkMergeInfo", 1);
    }
    
    return (PyObject *) mergeObj; 
}

PyObject * PythonClientUser::MkActionMergeInfo( ClientResolveA *m, StrPtr &hint )
{
    debug->debug ( P4PYDBG_CALLS, "[P4] MkActionMergeInfo()" );

    EnsurePythonLock guard;

    // retrieve the last entry in the result array
    PyObject * output = results.GetOutputInternal();
    Py_ssize_t len = PyList_Size(output);
    PyObject * info = PyList_GetItem(output, len - 1);

    P4ActionMergeData *mergeObj = PyObject_New(P4ActionMergeData, &P4ActionMergeDataType);
    if (mergeObj != NULL) {
        mergeObj->mergeData = new PythonActionMergeData( this, m, hint, info);
    }
    else {
        PyErr_WarnEx( PyExc_UserWarning, "[P4::Resolve] Failed to create object in MkMergeInfo", 1);
    }

    return (PyObject *) mergeObj;
}
