from __future__ import print_function

import re

class Version:
    def __init__(self, version_string):
        self.version_string = version_string
        self.process(version_string)

    def process(self, version_string):
        r = re.compile(r"r(\d+).(\d+)")
        m = r.match(version_string)
        if m:
            self.year = m.group(1)
            self.issue = m.group(2)
        else:
            raise Exception("Illegal version %s" % version_string)

    def __lt__(self, other):
        if isinstance(other, Version):
            return (self.year, self.issue) < (other.year, other.issue)
        return NotImplemented

    def __le__(self, other):
        if isinstance(other, Version):
            return (self.year, self.issue) <= (other.year, other.issue)
        return NotImplemented

    def __eq__(self, other):
        if isinstance(other, Version):
            return (self.year, self.issue) == (other.year, other.issue)

        return NotImplemented

    def __ne__(self, other):
        if isinstance(other, Version):
            return (self.year, self.issue) != (other.year, other.issue)
        return NotImplemented

    def __gt__(self, other):
        if isinstance(other, Version):
            return (self.year, self.issue) > (other.year, other.issue)
        return NotImplemented

    def __ge__(self, other):
        if isinstance(other, Version):
            return (self.year, self.issue) >= (other.year, other.issue)
        return NotImplemented

    def __repr__(self):
        return "r%s.%s" % (self.year, self.issue)

if __name__ == '__main__':

    v1 = Version("r17.1")
    v2 = Version("r17.2")
    v3 = Version("r17.2")

    assert v1 < v2
    assert v2 > v1
    assert v1 == v1
    assert v2 == v3

    print("All tests have passed")
