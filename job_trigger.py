from __future__ import print_function

import glob, sys, os
pathToBuild = glob.glob('../build/lib*')
if len(pathToBuild) > 0:
        versionString = "%d.%d" % (sys.version_info[0], sys.version_info[1])
        for i in pathToBuild:
                if versionString in i:
                        sys.path.insert(0,  os.path.realpath(i))

pathToBuild = glob.glob('/tmp/p4python*')
if len(pathToBuild) > 0:
        sys.path.insert(0, pathToBuild[0])

import P4


def run_trigger(specdef, formname, formfile):
    p4 = P4.P4()
    try:
        p4.define_spec('job', specdef)

        with open(formfile) as f:
            content = f.read()

        parsed = p4.parse_job(content)
        parsed._status = "suspended"

        content = p4.format_job(parsed)

        with open(formfile, "w") as f:
            f.write(content)

    except Exception as e:
        print("Received exception : {}".format(e))
        sys.exit(1)

    sys.exit(0)


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage : job_trigger.py specdef formname formfile")
        sys.exit(1)

    specdef = sys.argv[1]
    formname = sys.argv[2]
    formfile = sys.argv[3]
    run_trigger(specdef, formname, formfile)
