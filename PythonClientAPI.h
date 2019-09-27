/*
 * PythonClientAPI. Wrapper around P4API.
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
 * $Id: //depot/main/p4-python/PythonClientAPI.h#43 $
 *
 * Build instructions:
 *  Use Distutils - see accompanying setup.py
 *
 *      python setup.py install
 *
 */

#ifndef PYTHON_CLIENT_API_H
#define PYTHON_CLIENT_API_H

class Enviro;
class PythonClientAPI
{
public:
    PythonClientAPI();
    ~PythonClientAPI();
 	
public:
    typedef int (PythonClientAPI::*intsetter)(int);
    typedef int (PythonClientAPI::*strsetter)(const char *);
    typedef int (PythonClientAPI::*intgetter)();
    typedef const char * (PythonClientAPI::*strgetter)();
    typedef int (PythonClientAPI::*objsetter)(PyObject *);
    typedef PyObject * (PythonClientAPI::*objgetter)();

private:
    struct intattribute_t {
    	const char * attribute;
    	intsetter setter;
    	intgetter getter;
    };
    
    struct strattribute_t {
    	const char * attribute;
    	strsetter setter;
    	strgetter getter;
    };

    struct objattribute_t {
    	const char * attribute;
    	objsetter setter;
    	objgetter getter;
    };

    static intattribute_t intattributes[];
    static strattribute_t strattributes[];
    static objattribute_t objattributes[];
    
public:
 	    // Tagged mode - can be enabled/disabled on a per-command basis
    int SetTagged( int enable );
    int	GetTagged();

    // Set track mode - track usage of this command on the server

    int SetTrack( int enable );
    int GetTrack();

    // Set streams mode 

    int SetStreams( int enable );
    int GetStreams();

    // Set graph mode

    int SetGraph( int enable );
    int GetGraph();

    // Set API level for backwards compatibility
    int SetApiLevel( int level );
    int SetMaxResults( int v )		{ maxResults = v; return 0; }
    int SetMaxScanRows( int v )		{ maxScanRows = v; return 0; }
    int SetMaxLockTime( int v )		{ maxLockTime = v; return 0; }

    int SetCaseFolding( int v )		{ StrPtr::SetCaseFolding((StrPtr::CaseUse) v); return 0;}

    //
    // Debugging support. Debug levels are:
    //
    //     1:	Debugs commands being executed
    //     2:	Debug UI method calls
    //     3:	Show garbage collection ??? 
    //
    int SetDebug( int d );

    // Returns 0 on success, otherwise -1 and might raise exception
    int SetCharset( const char *c );

    int SetClient( const char *c )	{ client.SetClient( c ); return 0; }
    int SetCwd( const char *c );
    PyObject * SetEnv( const char *var, const char *val );
    int SetHost( const char *h )	{ client.SetHost( h ); return 0; }
    int SetIgnoreFile( const char *h )	{ client.SetIgnoreFile( h ); return 0; }
    int SetLanguage( const char *l )	{ client.SetLanguage( l ); return 0; }
    int SetPassword( const char *p )	{ client.SetPassword( p ); return 0; }
    int SetPort( const char *p );
    int SetProg( const char *p )	{ prog = p; return 0; }
    int SetTicketFile( const char *p );
    int SetEncoding( const char *e );
    int SetUser( const char *u )	{ client.SetUser( u ); return 0; }
    int SetVersion( const char *v )	{ version = v; return 0; }
    int SetEnviroFile( const char *v );

    const char * GetCharset()		{ return client.GetCharset().Text(); }
    const char * GetClient()		{ return client.GetClient().Text();}
    const char * GetConfig()		{ return client.GetConfig().Text();}
    const char * GetEnviroFile();
    const char * GetEncoding()		{ return specMgr.GetEncoding(); }
    const char * GetCwd()		{ return client.GetCwd().Text(); }
    const char * GetEnv( const char *var );
    const char * GetHost()		{ return client.GetHost().Text(); }
    const char * GetIgnoreFile()	{ return client.GetIgnoreFile().Text(); }
    const char * GetLanguage()		{ return client.GetLanguage().Text(); }
    const char * GetPassword()		{ return client.GetPassword().Text(); }
    const char * GetPort()		{ return client.GetPort().Text(); }
    const char * GetProg()		{ return prog.Text(); }
    const char * GetTicketFile()	{ return ticketFile.Text(); }
    const char * GetUser()		{ return client.GetUser().Text(); }
    const char * GetVersion()		{ return version.Text(); }
    const char * GetPatchlevel()	{ return ID_PATCH; }
    const char * GetOs()		{ return ID_OS; }
    int GetMaxResults()			{ return maxResults; }
    int GetMaxScanRows()		{ return maxScanRows; }
    int GetMaxLockTime()		{ return maxLockTime; }
    int GetDebug()			{ return debug.getDebug(); }
    int GetApiLevel()			{ return apiLevel; }
    int GetCaseFolding()		{ return (int) StrPtr::CaseUsage(); }
    
    // Session management
    PyObject * Connect();		// P4Exception on error
    PyObject * Connected();	// Return true if connected and not dropped.
    PyObject * Disconnect();

    PyObject * GetServerLevel();  // P4Exception if asked when disconnected
    PyObject * GetServerCaseInsensitive(); // P4Exception if asked when disconnected
    PyObject * GetServerUnicode(); // P4Exception if asked when disconnected

    PyObject * DisableTmpCleanup();

    PyObject * IsIgnored(const char *path);

    // Executing commands. 
    PyObject * Run( const char *cmd, int argc, char * const *argv );
    int SetInput( PyObject * input );
    PyObject * GetInput();
    
    int SetResolver( PyObject * resolver );
    PyObject * GetResolver();

    // OutputHandler interface
    int SetHandler( PyObject * handler );
    PyObject * GetHandler();

    // Progress interface
    int SetProgress( PyObject * progress );
    PyObject * GetProgress();

    // Result handling
    PyObject * GetErrors()		{ return ui.GetResults().GetErrors(); }
    PyObject * GetWarnings()		{ return ui.GetResults().GetWarnings();}
    PyObject * GetMessages()		{ return ui.GetResults().GetMessages();}
    PyObject * GetTrackOutput()		{ return ui.GetResults().GetTrack();}

    // Config files
    PyObject * GetConfigFiles();

    // Logger interface
    int SetLogger( PyObject * logger);
    PyObject * GetLogger();

#if PY_MAJOR_VERSION >= 3
    // Conversion from Unicode into a Perforce Charset

    PyObject * Convert(const char *charset, PyObject * content);
#endif

    // __members__ handling
    
    PyObject * GetMembers();
    
    // Spec parsing
    PyObject * ParseSpec( const char * type, const char *form );
    PyObject * FormatSpec( const char *type, PyObject * dict );
    PyObject * DefineSpec( const char *type, const char *spec);

    PyObject * SpecFields( const char * type );

    // Protocol
    PyObject * SetProtocol( const char * var, const char *val );
    PyObject * GetProtocol( const char * var );

    // Exception levels:
    //
    // 		0 - No exceptions raised
    // 		1 - Exceptions raised for errors
    // 		2 - Exceptions raised for errors and warnings
    //
    int  SetExceptionLevel( int i )	{ exceptionLevel = i; return 0;	}
    int  GetExceptionLevel()		{ return exceptionLevel; }

    void Except( const char *func, const char *msg );
    void Except( const char *func, Error *e );
    void Except( const char *func, const char *msg, const char *cmd );

public:
    // setter/getter methods and attributes
    
    static intsetter GetIntSetter(const char * forAttr);
    static intgetter GetIntGetter(const char * forAttr);
    static strsetter GetStrSetter(const char * forAttr);
    static strgetter GetStrGetter(const char * forAttr);
    static objsetter GetObjSetter(const char * forAttr);
    static objgetter GetObjGetter(const char * forAttr);

    // Ownership of returned list is passed to caller!
    // Free it, keep it or suffer memory leak!
    static const char ** GetAttributes();
    
private:
    void RunCmd(const char *cmd, ClientUser *ui, int argc, char * const *argv);
    PyObject * ConnectOrReconnect();

    static intattribute_t * GetInt(const char * forAttr);
    static strattribute_t * GetStr(const char * forAttr);
    static objattribute_t * GetObj(const char * forAttr);
    
    StrBuf SetProgString(StrBuf& progStr);

private:
    enum {
	S_TAGGED 	= 0x0001,
	S_CONNECTED	= 0x0002,
	S_CMDRUN	= 0x0004,
	S_UNICODE	= 0x0008,
	S_CASEFOLDING	= 0x0010,
	S_TRACK		= 0x0020,
	S_STREAMS	= 0x0040,
	S_GRAPH	    = 0x0080,

	S_INITIAL_STATE	= 0x00C1, // Streams, Graph, and Tagged enabled by default
	S_RESET_MASK	= 0x001E,
    };

    void	InitFlags()		{ flags = S_INITIAL_STATE;	}
    void	ResetFlags()		{ flags &= ~S_RESET_MASK;	}

    void	SetTag()		{ flags |= S_TAGGED;		}
    void	ClearTag()		{ flags &= ~S_TAGGED;		}
    int		IsTag()			{ return flags & S_TAGGED;	}

    void	SetConnected()		{ flags |= S_CONNECTED;		}
    void	ClearConnected() 	{ flags &= ~S_CONNECTED;	}
    int		IsConnected()		{ return flags & S_CONNECTED;	}

    void	SetCmdRun()		{ flags |= S_CMDRUN;		}
    void	ClearCmdRun() 		{ flags &= ~S_CMDRUN;		}
    int		IsCmdRun()		{ return flags & S_CMDRUN;	}

    void	SetUnicode()		{ flags |= S_UNICODE;		}
    void	ClearUnicode() 		{ flags &= ~S_UNICODE;		}
    int		IsUnicode()		{ return flags & S_UNICODE;	}

    void	SetCaseFold()		{ flags |= S_CASEFOLDING;	}
    void	ClearCaseFold()		{ flags &= ~S_CASEFOLDING;	}
    int		IsCaseFold()		{ return flags & S_CASEFOLDING;	}

    void	SetTrackMode()		{ flags |= S_TRACK;		}
    void	ClearTrackMode()	{ flags &= ~S_TRACK;		}
    int		IsTrackMode()		{ return flags & S_TRACK;	}

    void	SetStreamsMode()	{ flags |= S_STREAMS;		}
    void	ClearStreamsMode()	{ flags &= ~S_STREAMS;		}
    int		IsStreamsMode()		{ return flags & S_STREAMS;	}

    void	SetGraphMode()	    { flags |= S_GRAPH;		}
    void	ClearGraphMode()	{ flags &= ~S_GRAPH;		}
    int		IsGraphMode()		{ return flags & S_GRAPH;	}

private:
    ClientApi		client;		// Perforce API Class
    PythonClientUser	ui;
    Enviro *		enviro;
    PythonDebug		debug;
    p4py::SpecMgr		specMgr;
    StrBufDict		specDict;
    StrBuf		prog;
    StrBuf		version;
    StrBuf		ticketFile;
    int			depth;
    int 		apiLevel;
    int			exceptionLevel;
    int			server2;
    int			flags;
    int			maxResults;
    int			maxScanRows;
    int			maxLockTime;
};

#endif
