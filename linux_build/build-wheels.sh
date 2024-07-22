#!/bin/bash
set -eEx

export PATH=$PATH:/work/p4-bin/bin.linux26x86_64/

# Extract the p4api and set the P4API path var
mkdir -p /work/p4-api
tar xvfz /work/p4-bin/bin.linux26x86_64/p4api-glibc2.12-openssl3.tgz -C /work/p4-api
P4API=`echo /work/p4-api/p4api-20*`

cd /work/p4-python
if [ -d repair ]; then
	rm -rf repair
fi

mkdir -p repair

# Compile wheels
for VERSION in $1; do
	PYBIN="/opt/python/$(ls /opt/python/ | grep cp$VERSION | grep -v 27mu)/bin"

	## Set env path for apidir and ssl directories 
	export apidir=$P4API
	export ssl=/openssl/lib

 	## Upgrade pip
	"${PYBIN}/python" -m pip install --upgrade pip

	#Install wheel module
	"${PYBIN}/python" -m pip install wheel

	## Build the installer
	"${PYBIN}/python" -m pip wheel . -w dist -v

	# Install the wheel
	"${PYBIN}/python" -m pip install /work/p4-python/dist/$(ls /work/p4-python/dist/ | grep $VERSION | grep \.whl)

	## Test the build
	"${PYBIN}/python" p4test.py

	## Repair wheel with new ABI tag manylinux_2_28_x86_64
	#auditwheel repair dist/p4python-*-linux_x86_64.whl --plat manylinux_2_28_x86_64 -w repair

	#Changing wheel platform ABI tag to manylinux_2_28_x86_64
	"${PYBIN}/python" -m wheel tags --platform-tag=manylinux_2_28_x86_64 dist/p4python-*-linux_x86_64.whl

  #Move wheel to repair directory
	mv dist/p4python-*-manylinux_2_28_x86_64.whl repair

	rm -rf build p4python.egg-info dist
done
