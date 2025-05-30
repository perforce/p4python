import os
import platform
import shutil
import urllib.request
import urllib.error
import re
import tarfile
import tempfile
import subprocess


class P4APIHttps:

    def get_ssl_ver(self, ssl_ver_string):
        pattern = re.compile(r"(\d+)\.(\d+).(\d+).*")
        match = pattern.match(str(ssl_ver_string))
        if match:
            return match.group(1), match.group(2), match.group(3)
        return "3", "0", "2"
    
    def get_glib_ver(self):
        pattern = re.compile(r"ldd\s+\(.*\)\s+(\d+)\.(\d+)")
        try:
            gentry = subprocess.check_output(["ldd", "--version"], text=True)
            match = pattern.search(gentry)
            if match:
                return match.group(1), match.group(2)
            else:
                raise Exception(f"Cannot parse ldd version from output: {gentry}")
        except subprocess.CalledProcessError as e:
            raise Exception(f"Failed to execute 'ldd --version': {e}")
        except FileNotFoundError:
            raise Exception("The 'ldd' command is not available on this system.")

    def get_url(self, g_minor, ssl_ver, api_ver):

        if int(g_minor) <= 3:
            glib_ver = "2.3"
        else:
            glib_ver = "2.12"

        s_major, s_minor, s_mini = self.get_ssl_ver(ssl_ver)

        if int(s_major) == 1:
            ssl_ver = "1.1.1"
        elif int(s_major) == 3:
            ssl_ver = "3"

        if platform.machine() in ["aarch64", "arm64"]:
            f = "p4api-openssl{1}.tgz".format(glib_ver, ssl_ver)
            url = "https://ftp.perforce.com/perforce/{0}/bin.linux26aarch64/{1}".format(api_ver, f)
        else:
            f = "p4api-glibc{0}-openssl{1}.tgz".format(glib_ver, ssl_ver)
            url = "https://ftp.perforce.com/perforce/{0}/bin.linux26x86_64/{1}".format(api_ver, f)
        return url

    def get_file(self, url):

        p4api = 'p4api.tgz'

        tempdir = tempfile.gettempdir()
        tar = None
        apidir = None

        try:
            # Don't download again if p4api exists
            if not os.path.exists(p4api):
                print("Downloading P4 API, this may take a while.")
                urllib.request.urlretrieve(url, p4api)

            tar = tarfile.open(p4api, 'r')
            apidir = os.path.join(tempdir, tar.getnames()[0])

            # If apidir exists, don't unpack again, otherwise read-only errors will occur
            if not (os.path.exists(apidir) and os.path.isdir(apidir)):
                tar.extractall(tempdir)

            # Clean up downloaded archive
            if os.path.exists(p4api):
                os.remove(p4api)

            return apidir, url
        except (urllib.error.HTTPError, tarfile.TarError):
            # If we are here errors occurred so lets clean up everything.
            print("Download of P4 API failed. Cleaning up.")
            if tar:
                tar.close()
            if os.path.exists(p4api):
                os.remove(p4api)
            if os.path.exists(apidir) and os.path.isdir(apidir):
                shutil.rmtree(apidir, ignore_errors=True)

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

    def get_ssl_src(self, ssl_ver):
        """
        Downloads and extracts the OpenSSL source code from the official OpenSSL website.
        :param ssl_ver: The version of OpenSSL to download (e.g., "3.0.2").
        :return: The directory where the source is extracted, the tarball path.
        """
        url = f"https://www.openssl.org/source/openssl-{ssl_ver}.tar.gz"
        print(f"Downloading OpenSSL source from {url}")

        tempdir = tempfile.gettempdir()
        tarball = os.path.join(tempdir, f"openssl-{ssl_ver}.tar.gz")
        ssl_src_dir = os.path.join(tempdir, f"openssl-{ssl_ver}")

        try:
            # Download the tarball if it doesn't already exist
            if not os.path.exists(tarball):
                with urllib.request.urlopen(url) as response, open(tarball, 'wb') as out_file:
                    out_file.write(response.read())

            # Extract the tarball if the directory doesn't already exist
            if not os.path.exists(ssl_src_dir):
                with tarfile.open(tarball, 'r:gz') as tar:
                    tar.extractall(tempdir)

            print(f"OpenSSL source extracted to {ssl_src_dir}")
            return ssl_src_dir, tarball
        except (urllib.error.HTTPError, urllib.error.URLError) as e:
            print(f"Failed to download OpenSSL source: {e}")
        except tarfile.TarError as e:
            print(f"Failed to extract OpenSSL source: {e}")

        # Cleanup in case of failure
        if os.path.exists(tarball):
            os.remove(tarball)
        if os.path.exists(ssl_src_dir):
            shutil.rmtree(ssl_src_dir, ignore_errors=True)

        return "", ""
