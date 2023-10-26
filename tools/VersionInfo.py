import os
import re

from tools.Version import Version


class VersionInfo:
  def __init__(self, p4api_dir):
    self.release_year = None
    self.release_version = None
    self.release_special = None
    self.patchlevel = None
    self.suppdate_year = None
    self.suppdate_month = None
    self.suppdate_day = None

    releasePattern = re.compile(r"RELEASE\s+=\s+(?P<year>\d+)\s+(?P<version>\d+)\s*(?P<special>.*?)\s*;")
    patchlevelPattern = re.compile(r"PATCHLEVEL\s+=\s+(?P<level>\d+)")
    suppdatePattern = re.compile(r"SUPPDATE\s+=\s+(?P<year>\d+)\s+(?P<month>\d+)\s+(?P<day>\d+)")

    self.patterns=[]
    self.patterns.append((releasePattern, self.handleRelease))
    self.patterns.append((patchlevelPattern, self.handlePatchlevel))
    self.patterns.append((suppdatePattern, self.handleSuppDate))

    ver_file = os.path.join(p4api_dir, "sample", "Version")
    if not os.path.exists(ver_file):
        ver_file = os.path.join(p4api_dir, "Version")
    input = open(ver_file)
    for line in input:
      for pattern, handler in self.patterns:
        m = pattern.match(line)
        if m:
          handler(**m.groupdict())
    input.close()

  def handleRelease(self, year=0, version=0, special=''):
    self.release_year = year
    self.release_version = version
    self.release_special = re.sub(r"\s+", ".", special)

  def handlePatchlevel(self, level=0):
    self.patchlevel = level

  def handleSuppDate(self, year=0, month=0, day=0):
    self.suppdate_year = year
    self.suppdate_month = month
    self.suppdate_day = day

  def getP4Version(self):
    return "%s.%s" % (self.release_year, self.release_version)

  def getVersion(self):
    return Version("r%s" % (self.getP4Version()[2:]))

  def getFullP4Version(self):
    version = "%s.%s" % (self.release_year, self.release_version)
    if self.release_special:
      version += ".%s" % self.release_special
    return version

  def getDistVersion(self):
    version = "%s.%s.%s" % (self.release_year, self.release_version, self.patchlevel)
#    if self.release_special:
#        if 'TEST' in self.release_special:
#            version += ".preview"
#    	version += ".%s" % self.release_special
    return version

  def getPatchVersion(self):
    version = "%s.%s" % (self.release_year, self.release_version)
    if self.release_special:
      version += ".%s" % self.release_special
    version += "/%s" % self.patchlevel
    return version