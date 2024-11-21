import os
import platform
import re


class PlatformInfo:
    def __init__(self, api_version, release_version, ssl, ssl_ver):
        """
             Sets platform specific options for compiling and linking
             :param api_version: version of the p4api
             :param release_version: the release version
             :param ssl: the linker path to ssl libraries
             :param ssl_ver: ssl version
             """
        self.libraries = None
        self.extra_compile_args = None
        self.define_macros = None
        self.extra_link_args = None

        # This is a hack for 'sdist'. I need to set up all other information, but do not need the libraries

        if ssl is None:
            ssl = ""

        unameOut = platform.uname()

        if os.name == "nt":
            if platform.python_compiler().find("64 bit") > 0:
                pl = "NTX64"
                arch = "64"
            else:
                pl = "NTX86"
                arch = "32"

            self.ID_OS = self.inStr(pl)
            self.ID_REL = self.inStr(release_version.getFullP4Version())
            self.ID_PATCH = self.inStr(release_version.patchlevel)
            self.ID_API = self.inStr(api_version.getPatchVersion())
            self.ID_Y = self.inStr(release_version.suppdate_year)
            self.ID_M = self.inStr(release_version.suppdate_month)
            self.ID_D = self.inStr(release_version.suppdate_day)

            self.libraries = ["oldnames", "wsock32", "advapi32", "ws2_32", "User32", "Gdi32", "Ole32", "Shell32", "crypt32", # MSVC libs
                              "libclient", "librpc", "libp4script_c", "libp4script", "libp4script_curl", "libp4script_sqlite", "libsupp"] # P4API libs

            # with OpenSSL 1.1.0+ windows libraries have changed names to libssl.lib and libcrypto.lib
            if os.path.isfile(os.path.join(ssl, "libssl.lib")):
                self.libraries.append("libssl")
            else:
                self.libraries.append("libeay%s" % arch)

            if os.path.isfile(os.path.join(ssl, "libcrypto.lib")):
                self.libraries.append("libcrypto")
            else:
                self.libraries.append("ssleay%s" % arch)

            self.extra_compile_args = ["/DOS_NT", "/DMT", "/DCASE_INSENSITIVE", "/EHsc"]

            self.extra_link_args = ["/NODEFAULTLIB:libcmt"]
        elif os.name == "posix":
            self.libraries = ["client", "rpc", "p4script_c", "p4script", "p4script_curl", "p4script_sqlite", "supp"]
            self.extra_link_args = []
            if unameOut[0] == "Darwin":
                self.extra_link_args = [os.path.join(ssl, "libssl.a"), os.path.join(ssl, "libcrypto.a")]
            else:
                self.libraries.append("ssl")
                self.libraries.append("crypto")

            self.extra_compile_args = ["-Wno-deprecated-declarations"]

            # it is UNIX, but which one? Let's ask uname()
            # details later

            if unameOut[0] == "Linux":
                unix = "LINUX"
                release = unameOut[2][0:1] + unameOut[2][2:3]
                arch = self.architecture(unameOut[4])
                self.libraries.append("rt")  # for clock_gettime
            elif unameOut[0] == "Darwin":
                unix = "DARWIN"

                self.extra_compile_args.append("-fvisibility-inlines-hidden")
                self.extra_compile_args.append("-DCASE_INSENSITIVE")
                self.extra_compile_args.append("-stdlib=libc++")

                if unameOut[2][0:2] == "13":
                    release = "109"
                    self.extra_link_args += ["-framework", "Carbon"]
                elif unameOut[2][0:2] == "14":
                    release = "1010"
                    self.extra_link_args += ["-framework", "Carbon"]
                elif unameOut[2][0:2] == "15":
                    release = "1011"
                    self.extra_link_args += ["-framework", "Carbon"]
                elif unameOut[2][0:2] == "16":
                    release = "1012"
                    self.extra_link_args += ["-framework", "Carbon"]
                elif unameOut[2][0:2] == "17":
                    release = "1013"
                    self.extra_link_args += ["-framework", "Carbon"]
                elif unameOut[2][0:2] == "18":
                    release = "1014"
                    self.extra_link_args += ["-framework", "Carbon"]
                else:
                    release = "109"
                    self.extra_link_args += ["-framework", "Carbon"]

                if unameOut.machine == 'arm64':
                    os.environ["MACOSX_DEPLOYMENT_TARGET"] = "12.6"
                else:
                    os.environ["MACOSX_DEPLOYMENT_TARGET"] = "10.15"

                arch = self.architecture(unameOut[4])

                # The following is another hack
                # There is no way to remove the standard compile flags. The default on a MAC
                # is to build a universal binary. The Perforce API is only built for one
                # platform, so we need to remove these flags. By setting the environment
                # variable ARCHFLAGS the defaults can be overriden.

                if arch == "PPC":
                    os.environ["ARCHFLAGS"] = "-arch ppc"
                elif arch == "i386":
                    os.environ["ARCHFLAGS"] = "-arch i386"
                elif arch == "X86_64":
                    os.environ["ARCHFLAGS"] = "-arch x86_64"

            elif unameOut[0] == "SunOS":
                unix = "SOLARIS"
                release = re.match(r"5.(\d+)", unameOut[2]).group(1)
                arch = self.architecture(unameOut[4])
            elif unameOut[0] == 'FreeBSD':
                unix = "FREEBSD"
                release = unameOut[2][0]
                if release == '5':
                    release += unameOut[2][2]

                arch = self.architecture(unameOut[4])
            elif unameOut[0] == 'CYGWIN_NT-5.1':
                unix = "CYGWIN"
                release = ""
                arch = self.architecture(unameOut[4])

            self.ID_OS = self.inStr(unix + release + arch)
            self.ID_REL = self.inStr(release_version.getFullP4Version())
            self.ID_PATCH = self.inStr(release_version.patchlevel)
            self.ID_API = self.inStr(api_version.getPatchVersion())
            self.ID_Y = self.inStr(release_version.suppdate_year)
            self.ID_M = self.inStr(release_version.suppdate_month)
            self.ID_D = self.inStr(release_version.suppdate_day)

            self.extra_compile_args.append("-DOS_" + unix)
            self.extra_compile_args.append("-DOS_" + unix + release)
            self.extra_compile_args.append("-DOS_" + unix + arch)
            self.extra_compile_args.append("-DOS_" + unix + release + arch)

        self.define_macros = [('ID_OS', self.ID_OS),
                              ('ID_REL', self.ID_REL),
                              ('ID_PATCH', self.ID_PATCH),
                              ('ID_API', self.ID_API),
                              ('ID_Y', self.ID_Y),
                              ('ID_M', self.ID_M),
                              ('ID_D', self.ID_D)]

    def inStr(self, str):
        return '"' + str + '"'

    def architecture(self, str):
        if str == 'x86_64':
            return "X86_64"
        elif re.match('i.86', str):
            return "X86"
        elif str == 'i86pc':
            return "X86"
        elif str == 'Power Macintosh':
            return 'PPC'
        elif str == 'powerpc':
            return 'PPC'
        elif str == 'amd64':
            return 'X86_64'
        elif str == 'sparc':
            return 'SPARC'
        elif str == 'aarch64':
            return 'ARM'
        elif re.match('arm.*', str):
            return "ARM"

    def get_ssl_ver(self, ssl_ver_string):
        pattern = re.compile(r"(\d+)\.(\d+).(\d+).*")
        match = pattern.match(ssl_ver_string)
        if match:
            return match.group(1), match.group(2), match.group(3)
        return "1", "1", "1"
