"""P4Python - Python interface to Perforce API

Perforce is the fast SCM system at www.perforce.com.
This package provides a simple interface from Python wrapping the
Perforce C++ API to gain performance and ease of coding.
Similar to interfaces available for Ruby and Perl.

"""
from __future__ import print_function

classifiers = """\
Development Status :: 5 - Production/Stable
Intended Audience :: Developers
License :: Freely Distributable
Programming Language :: Python
Topic :: Software Development :: Libraries :: Python Modules
Topic :: Software Development :: Version Control
Topic :: Software Development
Topic :: Utilities
Operating System :: Microsoft :: Windows
Operating System :: Unix
Operating System :: MacOS :: MacOS X
"""

# Customisations needed to use to build:
# 1. Set directory for p4api in setup.cfg

# See notes in P4API documentation for building with API on different
# platforms:
#   http://www.perforce.com/perforce/doc.current/manuals/p4api/02_clientprog.html

MIN_SSL_VERSION = 100
# MIN_SSL_RELEASE='e' # currently not restricting builds for any OpenSSL > 1.0.0

try:
    from setuptools import setup, Extension
except ImportError:
    from distutils.core import setup, Extension

from distutils.command.build import build as build_module
from distutils.command.build_ext import build_ext as build_ext_module
from distutils.command.sdist import sdist as sdist_module

import os, os.path, sys, re, shutil, stat, subprocess

from tools.P4APIFtp import P4APIFtp
from tools.PlatformInfo import PlatformInfo
from tools.VersionInfo import VersionInfo
from tools.P4APIHttps import P4APIHttps

if sys.version_info < (3, 0):
    from ConfigParser import ConfigParser
else:
    from configparser import ConfigParser

global_dist_directory = "p4python-"

doclines = __doc__.split("\n")

NAME = "p4python"
VERSION = "2023.1"
PY_MODULES = ["P4"]
P4_API_DIR = "p4api"
DESCRIPTION = doclines[0]
AUTHOR = "Perforce Software Inc"
MAINTAINER = "Perforce Software Inc"
AUTHOR_EMAIL = "support@perforce.com"
MAINTAINER_EMAIL = "support@perforce.com"
LICENSE = "LICENSE.txt"
URL = "http://www.perforce.com"
KEYWORDS = "Perforce perforce P4Python"

P4_CONFIG_FILE = "setup.cfg"
P4_CONFIG_SECTION = "p4python_config"
P4_CONFIG_P4APIDIR = "p4_apidir"
P4_CONFIG_SSLDIR = "p4_ssl"

P4_DOC_RELNOTES = "../p4-doc/user/p4pythonnotes.txt"
P4_RELNOTES = "RELNOTES.txt"

# you gotta love python for monkey patching
def monkey_nt_quote_args(args):
    rlist = []
    for arg in args:
        # if there is a space in the arg, wrap it in double quotes
        if " " in arg:
            arg = '"\"{}\""'.format(arg)
        rlist.append(arg)
    return rlist

######################################################
#  Command Classes
class p4build(build_module):
    """Subclass of build subcommand for passing paths to build_ext compiler and linker"""

    user_options = build_module.user_options + [
        ('ssl=', None, 'specify ssl library directory'),
        ('apidir=', None, 'specify root of p4api directory'),
    ]

    def initialize_options(self, *args, **kwargs):
        self.apidir = os.getenv("apidir", None)
        self.ssl = os.getenv("ssl", None)
        build_module.initialize_options(self, *args, **kwargs)

    def finalize_options(self):
        global p4_api_dir, p4_ssl_dir

        if self.apidir:
            p4_api_dir = self.apidir

        if self.ssl:
            p4_ssl_dir = self.ssl

        build_module.finalize_options(self)


class p4build_ext(build_ext_module):
    """Subclass of build subcommand for passing paths to compiler and linker"""

    user_options = build_ext_module.user_options + [
        ('ssl=', None, 'specify ssl library directory'),
        ('apidir=', None, 'specify root of p4api directory'),
    ]

    def initialize_options(self, *args, **kwargs):
        self.apidir = os.getenv("apidir", None)
        self.ssl = os.getenv("ssl", None)
        build_ext_module.initialize_options(self, *args, **kwargs)

    def get_config(self, option):
        config = ConfigParser()
        config.read(P4_CONFIG_FILE)
        dir = ""
        if config.has_section(P4_CONFIG_SECTION):
            if config.has_option(P4_CONFIG_SECTION, option):
                dir = config.get(P4_CONFIG_SECTION, option)
        return dir

    def finalize_options(self):
        global p4_api_dir, p4_ssl_dir

        # options passed to "build" are copied into globals for use in "build_ext"
        if p4_api_dir:
            self.apidir = p4_api_dir

        if p4_ssl_dir:
            self.ssl = p4_ssl_dir

        # if we didn't get values from the command line, check the config file
        if not self.apidir:
            self.apidir = self.get_config(P4_CONFIG_P4APIDIR)

        if not self.ssl:
            self.ssl = self.get_config(P4_CONFIG_SSLDIR)

        build_ext_module.finalize_options(self)

    def is_super(self):
        rv = subprocess.check_output("id -u", shell=True)
        if int(rv) != 0:
            return False
        return True

    def download_p4api(self, api_ver, ssl_ver):
        global loaded_lib_from_ftp

        print("Looking for P4 API {0} for SSL {1} on https://ftp.perforce.com".format(api_ver, ssl_ver))

        g_major, g_minor = P4APIFtp.get_glib_ver(self)
        p4https = P4APIHttps()
        url = p4https.get_url(g_minor, ssl_ver, api_ver)
        api_dir, api_tarball= p4https.get_file(url)
        print("Extracted {0} into {1}".format(api_tarball, api_dir))

        loaded_lib_from_ftp = True
        return api_dir

    # run strings on p4api librpc.a to get the version of OpenSSL needed
    def get_ssl_version_from_p4api(self):
        libpath = os.path.join(self.apidir, "lib", "librpc.a")

        p1 = subprocess.Popen(["strings", libpath], stdout=subprocess.PIPE)
        p2 = subprocess.Popen(["grep", "^OpenSSL"], stdin=p1.stdout, stdout=subprocess.PIPE)
        p1.stdout.close()
        out, err = p2.communicate()
        sslstr = out.split()

        return sslstr[1].decode(encoding='UTF-8')

    @staticmethod
    def build_ssl_lib(ssl_ver):

        # not for windows
        # get the openssl version needed
        #   Now that p4api needs to know the ssl version, this call gets recursive.
        #    ssl_ver = self.get_ssl_version_from_p4api(self)
        if not ssl_ver:
            ssl_ver = "1.1.1"    # default to latest ssl version

        # try to download the SSL source from the ftp site
        print("Downloading SSL {0} source from ftp.openssl.org".format(ssl_ver))
        (ssl_src_dir, tarball) = P4APIFtp("ssl").get_ssl_src(ssl_ver)

        print("Building SSL source in {0}".format(ssl_src_dir))
        ssl_from_ftp = True
        ssl_lib_dir = P4APIFtp("ssl").build_ssl(ssl_src_dir)

        return ssl_lib_dir, ssl_src_dir, tarball, ssl_from_ftp

    @staticmethod
    def check_installed_ssl():
        # not for windows
        try:
            (version_string, err) = subprocess.Popen(["openssl", "version"], stdout=subprocess.PIPE,
                                                     stderr=subprocess.PIPE).communicate()
        except IOError:
            print("****************************************************", file=sys.stderr)
            print("No openssl in path and no ssl library path specified", file=sys.stderr)
            print("****************************************************", file=sys.stderr)
            return "", ""

        if err:
            print("****************************************************", file=sys.stderr)
            print("Cannot determine the version of openssl", file=sys.stderr)
            print("****************************************************", file=sys.stderr)
            return "", ""

        if type(version_string) == bytes:
            version_string = version_string.decode('utf8')

        print("Found installed SSL version " + version_string)

        pattern = re.compile(r"OpenSSL (\d)\.(\d)\.(\d)(\S+\s?\S*)?\s+\d+ \S+ \d+")
        match = pattern.match(version_string)
        if match:
            version = int(match.group(1)) * 100 + int(match.group(2)) * 10 + int(match.group(3)) * 1
            if match.group(4) is None:
                ver_only = str(match.group(1)) + "." + str(match.group(2)) + "." + str(match.group(3))
            else:
                ver_only = str(match.group(1)) + "." + str(match.group(2)) + "." + str(match.group(3)) + str(match.group(4))
            if version >= MIN_SSL_VERSION:
                release = match.group(4)
                for p in os.environ["PATH"].split(os.pathsep):
                    pathToFile = os.path.join(p, "openssl")
                    if os.path.exists(pathToFile) and os.access(pathToFile, os.X_OK):
                        entry = subprocess.check_output("ldd {0} | grep libssl".format(pathToFile),
                                                        executable="/bin/bash", shell="True")
                        if entry is not False:
                            libpath = os.path.dirname(entry.split()[2])

                        if os.path.exists(libpath) and os.path.isdir(libpath):
                            print("Found installed SSL libraries " + libpath.decode('utf-8'))
                            return libpath, ver_only
                        else:
                            print("****************************************************", file=sys.stderr)
                            print("Calculated path {0} for SSL does not exist".format(libpath), file=sys.stderr)
                            print("****************************************************", file=sys.stderr)
                            return "", ""
            else:
                print("***************************************", file=sys.stderr)
                print("Minimum SSL release required is 1.0.0", file=sys.stderr)
                print("***************************************", file=sys.stderr)
        else:
            print("****************************************************", file=sys.stderr)
            print("Cannot match OpenSSL Version string '{0}'".format(version_string), file=sys.stderr)
            print("****************************************************", file=sys.stderr)

        return "", ""

    # run from setup.py after the options are processed
    def run(self, *args, **kwargs):
        global p4_api_dir, p4_ssl_dir, p4_ssl_ver, ssl_src, ssl_tarball, loaded_ssl_from_ftp, loaded_api_from_ftp
        global global_dist_directory
        global releaseVersion
        global p4_extension

        ssl_ver = ""
        if not p4_ssl_dir:
            if (not self.ssl) and (sys.platform == "linux" or sys.platform == "linux2"):
                # check for a version of SSL already installed via 'openssl version'
                self.ssl, ssl_ver = self.check_installed_ssl()  # return libpath or None

                # we only support 1.0.2 or 1.1.1 using 2019.1 p4api
                if not (("1.0.2" in ssl_ver) or ("1.1.1" in ssl_ver) or ("3.0" in ssl_ver)):
                    self.ssl = ""

                if not self.ssl:
                    # try downloading and building ssl
                    if self.is_super():
                        (self.ssl, ssl_src, ssl_tarball, loaded_ssl_from_ftp) = self.build_ssl_lib(ssl_ver)
                        p4_ssl_dir = self.ssl
                        p4_ssl_ver = ssl_ver
                    else:
                        print("must be root to build and install SSL")

        if not self.ssl:
            print("***********************************************", file=sys.stderr)
            print("** Cannot build P4Python without SSL support **", file=sys.stderr)
            print("***********************************************", file=sys.stderr)
            raise Exception("Parameter --ssl is needed")
        p4_ssl_dir = self.ssl

        if not p4_api_dir:
            if (not self.apidir) and (sys.platform == "linux" or sys.platform == "linux2"):
                # Attempt to download P4 API which matches our versions
                self.apidir = self.download_p4api(VersionInfo(".").getVersion(), ssl_ver)
                p4_api_dir = self.apidir

        if not self.apidir:
            print("***********************************************", file=sys.stderr)
            print("** Cannot build P4Python without P4API       **", file=sys.stderr)
            print("***********************************************", file=sys.stderr)
            raise Exception("Parameter --apidir is needed")
        p4_api_dir = self.apidir

        try:
            apiVersion = VersionInfo(p4_api_dir)
            releaseVersion = VersionInfo(".")
        except IOError:
            print("Cannot find Version file in API dir {0}.".format(p4_api_dir))
            exit(1)

        ryear = int(apiVersion.release_year)
        rversion = int(apiVersion.release_version)
        global_dist_directory += releaseVersion.getDistVersion()

        if ryear < 2021:
            print("API Release %s.%s not supported by p4python, Minimum API requirement is 2022.1" % (ryear, rversion))
            print("Please download a more recent API release from the Perforce ftp site.")
            exit(1)
        else:
            print("Using API Release %s.%s" % (ryear, rversion))

        # monkey patch nt_quote_args (Only works in the debugger!)
        #spawn._nt_quote_args = monkey_nt_quote_args

        # add the paths for p4 headers and library
        inc_path = [str(os.path.join(p4_api_dir, "include", "p4"))]
        lib_path = [str(os.path.join(p4_api_dir, "lib")), str(p4_ssl_dir)]

        # check if the interpreter is mayapy.exe
        namedir = os.path.dirname(os.path.dirname(sys.executable))
        if "maya" in namedir.lower():
            inc_path.append(str(os.path.join(namedir, "include")))
            inc_path.append(str(os.path.join(namedir, "include", "python2.7")))
            lib_path.append(str(os.path.join(namedir, "lib")))

        info = PlatformInfo(apiVersion, releaseVersion, str(p4_ssl_dir), p4_ssl_ver)

        # Extend the extension specification with the new configuration
        p4_extension.include_dirs += inc_path
        p4_extension.library_dirs += lib_path
        p4_extension.libraries += info.libraries
        p4_extension.extra_compile_args += info.extra_compile_args
        p4_extension.define_macros += info.define_macros
        p4_extension.extra_link_args += info.extra_link_args
        build_ext_module.run(self, *args, **kwargs)


class p4build_sdist(sdist_module):

    user_options = sdist_module.user_options + [
        ('ssl=', None, 'ignored by sdist'),
        ('apidir=', None, 'ignored by sdist'),
    ]

    @staticmethod
    def force_remove_file(function, path, excinfo):
        os.chmod(path, stat.S_IWRITE)
        os.unlink(path)

    def copyReleaseNotes(self):
        """Copies the relnotes from the doc directory to the local directory if they exist
        Returns True if the release notes were copied, otherwise False
        """
        if os.path.exists(P4_DOC_RELNOTES):
            try:
                shutil.copy(P4_DOC_RELNOTES, P4_RELNOTES)
                return True
            except Exception as e:
                print(e)
                return False
        else:
            return False

    def deleteReleaseNotes(self):
        """Removes RELNOTES.txt from the current directory again"""
        os.chmod(P4_RELNOTES, stat.S_IWRITE)
        os.remove(P4_RELNOTES)

    def initialize_options(self):
        global global_dist_directory
        # Don't use hard links when building source distribution.
        # It's great, apart from under VirtualBox where it falls
        # apart due to a bug
        try:
            del os.link
        except:
            pass

        if os.path.exists(P4_RELNOTES):
            self.deleteReleaseNotes()
        self.copyReleaseNotes()

        version = VersionInfo(".")

        distdir = global_dist_directory + version.getDistVersion()
        if os.path.exists(distdir):
            shutil.rmtree(distdir, False, self.force_remove_file)

        sdist_module.initialize_options(self)


def do_setup():
    global global_dist_directory
    global p4_extension

    p4_extension = Extension("P4API", ["P4API.cpp", "PythonClientAPI.cpp",
                                           "PythonClientUser.cpp", "SpecMgr.cpp",
                                           "P4Result.cpp",
                                           "PythonMergeData.cpp", "P4MapMaker.cpp",
                                           "PythonSpecData.cpp", "PythonMessage.cpp",
                                           "PythonActionMergeData.cpp", "PythonClientProgress.cpp",
                                           "P4PythonDebug.cpp", "PythonKeepAlive.cpp"],
                                 include_dirs=[],
                                 library_dirs=[],
                                 libraries=[],
                                 extra_compile_args=[],
                                 define_macros=[],
                                 extra_link_args=[]
                                 )

    setup(name=NAME,
          version=VersionInfo(".").getDistVersion(),
          description=DESCRIPTION,
          author=AUTHOR,
          author_email=AUTHOR_EMAIL,
          maintainer=MAINTAINER,
          maintainer_email=MAINTAINER_EMAIL,
          license=LICENSE,
          url=URL,
          keywords=KEYWORDS,
          classifiers=[x for x in classifiers.split("\n") if x],
          long_description="\n".join(doclines[2:]),
          py_modules=PY_MODULES,
          ext_modules=[p4_extension],
          cmdclass={
              'build': p4build,
              'build_ext': p4build_ext,
              'sdist': p4build_sdist,
          }
          )


# def rreplace(s, old, new, occurrence=1):
#    li = s.rsplit(old, occurrence)
#    return new.join(li)

def cleanup_api(api_dir, tarball):
    base = os.path.dirname(api_dir)
    # ===========================================================================
    # Delete p4api.tgz and p4_api_dir  or ssl.tar.gz and ssl_src_dir
    # ===========================================================================

    print("Deleting temporary files from '{}'".format(base))

    tarfile = os.path.join(base, tarball)
    os.unlink(tarfile)
    shutil.rmtree(api_dir)


# declare some evil globals
p4_api_dir = ""
p4_ssl_dir = ""
p4_ssl_ver = ""
ssl_tarball = ""
ssl_src = ""
loaded_api_from_ftp = False
loaded_ssl_from_ftp = False

if __name__ == "__main__":

    do_setup()

    if loaded_api_from_ftp:
        cleanup_api(p4_api_dir, "p4api.tgz")

    if loaded_ssl_from_ftp:
        cleanup_api(ssl_src, ssl_tarball)
