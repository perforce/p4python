from __future__ import print_function
import platform

import tarfile
import tempfile
import re
import os, os.path
from ftplib import FTP, error_perm
import itertools
from .Version import Version
import subprocess

PERFORCE_FTP = 'ftp.perforce.com'
OPENSSL_FTP = 'ftp.openssl.org'

# user is anonymous, no need to log on with a special user


class P4APIFtp:
    def __init__(self, site):
        if site == "perforce":
            self.ftp = FTP(PERFORCE_FTP)
        else:
            self.ftp = FTP(OPENSSL_FTP)

        self.pattern = re.compile(r'(?P<permissions>[ld-][r-][w-][x-][r-][w-][x-][r-][w-][x-])' + \
                                  r'\s+\d+\s+\w+\s+\w+\s+\d+\s+' + \
                                  r'(?P<date>\S+\s+\S+\s+\S+)\s+' + \
                                  r'(?P<name>.+)')
        self.platform = self.findPlatform

    @property
    def findPlatform(self):
        """
        We are looking for out platform following the Perforce naming standard,
        i.e. bin.xxxyyy
        :return: the platform we are on
        """

        architecture = platform.architecture()[0]  # 32bit or 64bit
        machine = platform.machine()
        system = platform.system()
        uname = platform.uname()

        platform_str = "bin."

        if system == "Linux":
            platform_str += "linux26"
            if machine in ['i386', 'i586', 'i686', 'x86']:
                platform_str += "x86"
            elif machine in ['x86_64', 'amd64']:
                platform_str += "x86_64"
            elif machine in ['armv6l']:
                platform_str += 'armhf'
            else:
                raise Exception("Unknown machine {}. Please configure P4API manually".format(machine))

        elif system == "Windows":
            platform_str = platform_str + "NT"
            if architecture == "32bit":
                platform_str += "X86"
            else:
                platform_str += "X64"

        elif system == "Darwin":
            platform_str = platform_str + "darwin90" + machine

        elif system == "FreeBSD":
            platform_str += "freebsd"
            release = uname.release

            value = int(''.join(itertools.takewhile(lambda s: s.isdigit(), release)))

            if value >= 10:
                platform_str += "100"
                if machine == 'amd64':
                    platform_str += "x86_64"
                elif machine == 'i386':
                    platform_str += "x86"
                else:
                    raise Exception("Unknown machine {}. Please configure P4API manually".format(machine))


        else:
            raise Exception(
                "System {} is not supported for automatic download. Please configure P4API manually".format(system))

        return platform_str

    def get_glib_ver(self):
        pattern = re.compile(r"ldd\s+\(.*\)\s+(\d+)\.(\d+)")
        gentry = subprocess.check_output("ldd --version | grep ldd", executable="/bin/bash", shell="True")
        if type(gentry) == bytes:
            gentry = gentry.decode()
        match = pattern.match(gentry)
        if match:
            return match.group(1),match.group(2)
        else:
            raise Exception("Cannot parse {}".format(gentry))


    def get_ssl_ver(self, ssl_ver_string):
        pattern = re.compile(r"(\d+)\.(\d+).(\d+).*")
        match = pattern.match(str(ssl_ver_string))
        if match:
            return match.group(1), match.group(2), match.group(3)
        return "1", "1", "1"


    def sorted_directories(self, dirs):
        # first, extract the directory names from the list output
        names = [self.pattern.match(x).group('name') for x in dirs]

        # sort them by date, avoiding the Y2K problem
        sorted_names = sorted(names, key=lambda x: '19' + x if x[1] == '9' else '20' + x, reverse=True)

        return sorted_names

    def descend(self, d, f):
        pwd = self.ftp.pwd()
        apidir = None
        tar = None

        try:
            self.ftp.cwd(d)
            self.ftp.cwd(self.platform.lower())
            p4api = 'p4api.tgz'

            files = []
            self.ftp.retrlines("LIST", lambda s: files.append(s))

            for file in files:
                if f in file:
                    p4api = f
                    break

            tempdir = tempfile.gettempdir()
            filename = os.path.join(tempdir, p4api)

            # if the api tarball exists, don't re-download it.
            if not os.path.exists(filename):
                with open(filename, 'wb') as f:
                    self.ftp.retrbinary('RETR ' + p4api, f.write)

            tar = tarfile.open(filename, 'r')
            apidir = os.path.join(tempdir, tar.getnames()[0])

            # if apidir exists, don't unpack again, otherwise read-only errors will occur
            if not (os.path.exists(apidir) and os.path.isdir(apidir)):
                tar.extractall(tempdir)
        except error_perm as e:
            return None
        finally:
            self.ftp.cwd(pwd)

            if tar:
                tar.close()

        return apidir, p4api

    def findAPI(self, names, api_ver, ssl_ver):
        """
        Searches through the provided list of directories depth first.
        :param names: list of directories
        :param api_ver: p4 API version
        :param ssl_ver: ssl version
        :return: The path to the API dir or None
        """

        # compute a list of preferred names
        g_major, g_minor = self.get_glib_ver()

        if int(g_minor) <= 3:
            glib_ver = "2.3"
        else:
            glib_ver = "2.12"

        s_major, s_minor, s_mini = self.get_ssl_ver(ssl_ver)

        if int(s_minor) == 0:
            ssl_ver = "1.0.2"
        else:
            ssl_ver = "1.1.1"

        f = "p4api-glibc{0}-openssl{1}.tgz".format(glib_ver, ssl_ver)

        # start with the first one
        #   drill down in the directory
        #   find the correct platform
        #   descend into the platform directory
        #   see if we can find p4api.tgz
        #   otherwise, use next dated directory and start over

        for d in names:
            try:
                dir_version = Version(d)
                if dir_version > api_ver:
                    continue
                api_dir, api_tar = self.descend(d, f)
                if api_dir:
                    return api_dir, api_tar
            except:
                pass

        return "", f


    def load_api(self, api_ver, ssl_ver):
        self.ftp.connect()
        self.ftp.login()
        self.ftp.cwd("perforce")

        dirs = []
        # self.ftp.set_debuglevel(2)
        self.ftp.retrlines("LIST", lambda str1: dirs.append(str1))

        s = self.sorted_directories(dirs)
        return self.findAPI(s, api_ver, ssl_ver)


    def build_ssl(self, src_dir):
        print("building openssl in {0}".format(src_dir))
        save_dir = os.getcwd()
        os.chdir(src_dir)
        rv = subprocess.call(['./config'])
        if rv == 0:
            rv = subprocess.call(['make'])
        if rv == 0:
            rv = subprocess.call(['make', 'install'])
        if rv == 0:
            os.chdir(save_dir)
            return("/usr/local/ssl/lib")
        os.chdir(save_dir)
        return ""

    def grab_ssl_src_from_ftp(self, name):
        pwd = self.ftp.pwd()
        tar = None

        try:
            tempdir = tempfile.gettempdir()
            filename = os.path.join(tempdir, name)

            # if the tarball already exists, don't download it again
            if not os.path.exists(filename):
                with open(filename, 'wb') as f:
                    self.ftp.retrbinary('RETR ' + name, f.write)

            ssl_src_dir = filename[0:-7]  # remove trailing .tar.gz from filename
            tar = tarfile.open(filename, 'r')

            # if ssldir exists, don't unpack again, otherwise read-only errors will occur
            if not (os.path.exists(ssl_src_dir) and os.path.isdir(ssl_src_dir)):
                tar.extractall(tempdir)

        except error_perm as e:
            return "",""
        finally:
            self.ftp.cwd(pwd)

            if tar:
                tar.close()

        return ssl_src_dir, filename

    # load the code from openSSL
    def get_ssl_src(self, ssl_ver):
        self.ftp.connect()
        self.ftp.login()
        self.ftp.cwd("source")
        print("looking for " + 'openssl-' + ssl_ver)
        dirs = []
        self.ftp.retrlines("LIST", lambda str: dirs.append(str.split()[8]))
        match = ""
        for i, entry in enumerate(dirs):
            if entry.startswith("openssl-" + ssl_ver) and entry.endswith('.tar.gz'):
                match = entry
                break

        if match:
            return self.grab_ssl_src_from_ftp(match)

        print("unable to find openssl-" + ssl_ver)
        return "", ""
