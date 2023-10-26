import os
import shutil
import urllib.request
import urllib.error
import re
import tarfile
import tempfile


class P4APIHttps:

    def get_ssl_ver(self, ssl_ver_string):
        pattern = re.compile(r"(\d+)\.(\d+).(\d+).*")
        match = pattern.match(str(ssl_ver_string))
        if match:
            return match.group(1), match.group(2), match.group(3)
        return "1", "1", "1"

    def get_url(self, g_minor, ssl_ver, api_ver):

        if int(g_minor) <= 3:
            glib_ver = "2.3"
        else:
            glib_ver = "2.12"

        s_major, s_minor, s_mini = self.get_ssl_ver(ssl_ver)

        # When server releases ssl 3.x.x version of p4api, this will need to accommodate it
        if (int(s_major) == 1) and (int(s_minor) == 0):
            ssl_ver = "1.0.2"
        else:
            ssl_ver = "1.1.1"

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
