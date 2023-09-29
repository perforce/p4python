## Building P4Python from Source

  1. Download the corresponding Perforce C++ API (e.g. if you trying to build P4Python 2023.1, download the r23.1 P4API) from
     https://ftp.perforce.com/perforce. The API archive is located in release and platform-specific subdirectories.

     Under Linux, the p4api is named _p4api-glib\<GLIBVER>-openssl\<SSLVER>.tgz_
     
     Note that setup.py will download the correct p4api automatically from
     https://ftp.perforce.com/perforce if you do not provide an\
     _--apidir_ parameter to the "setup.py build" command.

     Mac OS X users should get the API from the relevant platform directory e.g.
     "**bin.macosx1015x86_64**" or "**bin.macosx12arm64**".\
     The p4api is named _p4api-openssl\<SSLVER>.tgz_

     Under Windows the p4api needs to match your compiler, build type (static 
     or dynamic) and SSL version.  for instance:
	   "**p4api_vs2019_static_openssl3.zip**" or "**p4api_vs2019_dyn_openssl3.zip**"

     **Note:** 32-bit builds of P4Python require a 32-bit version of the
     C++ API and a 32-bit version of Python. 64-bit builds of
     P4Python require a 64-bit version of the C++ API and a
     64-bit version of Python.
	       
     Unzip the archive into an empty directory.

  4. Download the P4Python source code from this repository or https://ftp.perforce.com \
     (e.g. for release 2023.1, source code can be found at https://ftp.perforce.com/perforce/r23.1/bin.tools/) \
     extract the archive into a new empty directory.

  7. If needed, install the Openssl libraries.

  8. To build P4Python, execute setup.py in P4Python source directory, with the following arguments:

     ```
     python3 setup.py build --apidir <Perforce C++ API absolute path> --ssl <OpenSSL library path>
     ```

     **Note:** In order to cleanly reinstall P4Python, remove the directory named "build".

  10. To test your P4Python build, excecute p4test.py:
      ```
      python3 p4test.py
      ```
		 **Note:** This test requires the Perforce server executable p4d 17.1 or better to be installed and in the PATH.

  12. To install P4Python, execute the following command:
      
      ```
      python3 setup.py install
      ```
      
      
      If this doesn't work, you may need to build and install in the same command:

      ```
      python3 setup.py build --apidir <Perforce C++ API absolute path> --ssl <OpenSSL library path> install
      ```

      **Note:** On Unix/Mac platforms, the installation must be performed
      as the root user, so usually these commands are preceded by "sudo".
      Also ensure that the umask is set correctly (typically 0022) before
      running the install. With a umask of 027, for example, the resulting
      installed files are accessible only by users of group root.\
      On Windows platforms, open a Visual Studio Command window
      (with administrator permissions) and run the command there.

  SSL support
  -----------

Perforce Server 2012.1 and later supports SSL connections and the
C++ API has been compiled with this support. With 2020.1 SSL support
is mandatory, that is, P4Python must be linked with valid OpenSSL libraries.

To specify which SSL library to use, provide the --ssl \<OpenSSL library path>
switch to the build. Without this setup will attempt to run
"openssl version" to identify the location of the library path for
openssl and whether openssl has an appropriate version to link to.

If on linux, and the build process cannot find the correct openssl 
libraries, and the -ssl option was not used, then the openssl source will 
be downloaded, compiled and installed (this will require a superuser 
password for the installation)
