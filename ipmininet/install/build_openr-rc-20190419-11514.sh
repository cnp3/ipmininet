#!/bin/bash

set -exo pipefail
### Install packages for Debian-based OS ###

apt-get update && apt-get install -yq autoconf-archive bison build-essential cmake curl flex git gperf joe libboost-all-dev libcap-dev libdouble-conversion-dev libevent-dev libgflags-dev libgoogle-glog-dev libkrb5-dev libpcre3-dev libpthread-stubs0-dev libnuma-dev libsasl2-dev libsnappy-dev libsqlite3-dev libssl-dev libtool netcat-openbsd pkg-config sudo unzip wget python3-venv python-setuptools python3-setuptools python3-pip ccache
apt-get install -yq gcc-'5' g++-'5'
update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-'5' 40 --slave /usr/bin/g++ g++ /usr/bin/g++-'5'
update-alternatives --config gcc

FOLLY_REV="3ceffd7d145be3c85a2aae39f99eb86ea730bdcc"
SODIUM_REV="6bece9c8c45259998f83ce243b1933e76c03f545"
FIZZ_REV="53e9df90e7876ba207deacbf60703bfbee31c442"
GTEST_REV="release-1.8.1"
RSOCKET_REV="8584e390e26c1eccae8da4283b42e93f7d4926f0"
WANGLE_REV="f2f8e1996739df1fc8ab1e003a1bc6472bd5b9bd"
ZSTD_REV="83b51e9f886be7c2a4d477b6e7bc6db831791d8d"
MSTCH_REV="ff459067bd02e80dc399006bb610238223d41c50"
FBTHRIFT_REV="2e3a85eb29e0cc3bad910093656bc2196f9e96ae"
SIGAR_REV="ad47dc3b494e9293d1f087aebb099bdba832de5e"
ZMQ_REV="v4.2.5"
FBZMQ_REV="8fba3b727c8194031351cefee71bd36ba3486645"
RE2_REV="653f9e2a6a17bcdf8dba2b3f8671aa8880efca29"
LIBNL_REV="libnl3_2_25"
OPENR_REV="rc-20190419-11514"

PY_VERSION="$(python3 --version 2>&1)"
PY_MINOR=$(sed -e 's/\(Python \)\([[:digit:]]\)\.\([[:digit:]]\)\(.*\)/\3/g' <<< "$PY_VERSION")
PY_LIB_PATH="/usr/local/lib/python3.$PY_MINOR/site-packages"
echo "PY_LIB_PATH: $PY_LIB_PATH"

NPROC=$(nproc 2> /dev/null || echo 1)
export MAKEFLAGS="$MAKEFLAGS -j $NPROC"

export CCACHE_DIR='/ccache' CC="ccache ${CC:-gcc}" CXX="ccache ${CXX:-g++}"
### Diagnostics ###

# Builder DebianSystemFBCodeBuilder(google/googletest:cmake_defines={u'BUILD_GTEST': u'ON', u'BUILD_SHARED_LIBS': u'OFF'}, gcc_version=u'5', facebook/zstd:git_hash=ShellQuoted(u'$(git describe --abbrev=0 --tags origin/master)'), hyperic/sigar:autoconf_options={u'CFLAGS': u'-fgnu89-inline'}, openr/build:cmake_defines={u'ADD_ROOT_TESTS': u'OFF'}, prefix=u'/usr/local', projects_dir=u'/usr/local/src', google/googletest:git_hash=u'release-1.8.1', wangle/wangle/build:cmake_defines={u'BUILD_TESTS': u'OFF'}, thom311/libnl:git_hash=u'libnl3_2_25', jedisct1/libsodium:git_hash=u'stable', ccache_dir=u'/ccache', make_parallelism=4, no1msd/mstch:git_hash=ShellQuoted(u'$(git describe --abbrev=0 --tags)'), zeromq/libzmq:git_hash=u'v4.2.5')
hostname
cat /etc/issue || echo no /etc/issue
g++ --version || echo g++ not installed
cmake --version || echo cmake not installed

### Check out facebook/folly, workdir _build ###

mkdir -p '/usr/local/src' && cd '/usr/local/src'
if [[ ! -d '/usr/local/src'/'folly' ]]; then 
	git clone https://github.com/'facebook/folly'
fi
mkdir -p '/usr/local/src'/'folly'/'_build' && cd '/usr/local/src'/'folly'/'_build'
git checkout $FOLLY_REV

### Build and install facebook/folly ###

CXXFLAGS="$CXXFLAGS -fPIC" CFLAGS="$CFLAGS -fPIC" cmake -D'BUILD_SHARED_LIBS'='ON' '..'
make VERBOSE=1
sudo make install VERBOSE=1 
sudo ldconfig

### Check out jedisct1/libsodium, workdir . ###

mkdir -p '/usr/local/src' && cd '/usr/local/src'
if [[ ! -d '/usr/local/src'/'libsodium' ]]; then 
	git clone https://github.com/'jedisct1/libsodium'
fi
mkdir -p '/usr/local/src'/'libsodium'/'.' && cd '/usr/local/src'/'libsodium'/'.'
git checkout $SODIUM_REV

### Build and install jedisct1/libsodium ###

./autogen.sh
LDFLAGS="$LDFLAGS" CFLAGS="$CFLAGS" CPPFLAGS="$CPPFLAGS" ./configure 
make VERBOSE=1
sudo make install VERBOSE=1 
sudo ldconfig

### Check out facebookincubator/fizz, workdir fizz/build ###

mkdir -p '/usr/local/src' && cd '/usr/local/src'
if [[ ! -d '/usr/local/src'/'fizz' ]]; then 
	git clone https://github.com/'facebookincubator/fizz'
fi
mkdir -p '/usr/local/src'/'fizz'/'fizz/build' && cd '/usr/local/src'/'fizz'/'fizz/build'
git checkout $FIZZ_REV

### Build and install fizz/fizz/build ###

CXXFLAGS="$CXXFLAGS -fPIC" CFLAGS="$CFLAGS -fPIC" cmake -D'BUILD_SHARED_LIBS'='ON' '..'
make VERBOSE=1
sudo make install VERBOSE=1 
sudo ldconfig

### Check out google/googletest, workdir build ###

mkdir -p '/usr/local/src' && cd '/usr/local/src'
if [[ ! -d '/usr/local/src'/'googletest' ]]; then 
	git clone https://github.com/'google/googletest'
fi
mkdir -p '/usr/local/src'/'googletest'/'build' && cd '/usr/local/src'/'googletest'/'build'
git checkout $GTEST_REV

### Build and install google/googletest ###

CXXFLAGS="$CXXFLAGS -fPIC" CFLAGS="$CFLAGS -fPIC" cmake -D'BUILD_GTEST'='ON' -D'BUILD_SHARED_LIBS'='OFF' '..'
make VERBOSE=1
sudo make install VERBOSE=1 
sudo ldconfig

### Check out rsocket/rsocket-cpp, workdir rsocket ###

mkdir -p '/usr/local/src' && cd '/usr/local/src'
if [[ ! -d '/usr/local/src'/'rsocket-cpp' ]]; then 
	git clone https://github.com/'rsocket/rsocket-cpp'
fi
mkdir -p '/usr/local/src'/'rsocket-cpp'/'rsocket' && cd '/usr/local/src'/'rsocket-cpp'/'rsocket'
git checkout $RSOCKET_REV

### Build and install rsocket-cpp/rsocket ###

CXXFLAGS="$CXXFLAGS -fPIC" CFLAGS="$CFLAGS -fPIC" cmake -D'BUILD_SHARED_LIBS'='ON' '..'
make gmock
make VERBOSE=1
sudo make install VERBOSE=1 
sudo ldconfig

### Check out facebook/wangle, workdir wangle/build ###

mkdir -p '/usr/local/src' && cd '/usr/local/src'
if [[ ! -d '/usr/local/src'/'wangle' ]]; then 
	git clone https://github.com/'facebook/wangle'
fi
mkdir -p '/usr/local/src'/'wangle'/'wangle/build' && cd '/usr/local/src'/'wangle'/'wangle/build'
git checkout $WANGLE_REV

### Build and install wangle/wangle/build ###

CXXFLAGS="$CXXFLAGS -fPIC" CFLAGS="$CFLAGS -fPIC" cmake -D'BUILD_SHARED_LIBS'='ON' -D'BUILD_TESTS'='OFF' '..'
make VERBOSE=1
sudo make install VERBOSE=1 
sudo ldconfig

### Check out facebook/zstd, workdir . ###

mkdir -p '/usr/local/src' && cd '/usr/local/src'
if [[ ! -d '/usr/local/src'/'zstd' ]]; then 
	git clone https://github.com/'facebook/zstd'
fi
mkdir -p '/usr/local/src'/'zstd'/'.' && cd '/usr/local/src'/'zstd'/'.'
git checkout $ZSTD_REV

### Build and install zstd ###

make VERBOSE=1 'PREFIX'='/usr/local'
sudo make install VERBOSE=1 'PREFIX'='/usr/local'
sudo ldconfig

### Check out no1msd/mstch, workdir build ###

mkdir -p '/usr/local/src' && cd '/usr/local/src'
if [[ ! -d '/usr/local/src'/'mstch' ]]; then 
	git clone https://github.com/'no1msd/mstch'
fi
mkdir -p '/usr/local/src'/'mstch'/'build' && cd '/usr/local/src'/'mstch'/'build'
git checkout $MSTCH_REV

### Build and install no1msd/mstch ###

CXXFLAGS="$CXXFLAGS -fPIC" CFLAGS="$CFLAGS -fPIC" cmake -D'BUILD_SHARED_LIBS'='ON' '..'
make VERBOSE=1
sudo make install VERBOSE=1 
sudo ldconfig

### Check out facebook/fbthrift, workdir thrift ###

mkdir -p '/usr/local/src' && cd '/usr/local/src'
if [[ ! -d '/usr/local/src'/'fbthrift' ]]; then 
	git clone https://github.com/'facebook/fbthrift'
fi
mkdir -p '/usr/local/src'/'fbthrift'/'thrift' && cd '/usr/local/src'/'fbthrift'/'thrift'
git checkout $FBTHRIFT_REV

### Build and install fbthrift/thrift ###

CXXFLAGS="$CXXFLAGS -fPIC" CFLAGS="$CFLAGS -fPIC" cmake -D'BUILD_SHARED_LIBS'='ON' '..'
make VERBOSE=1
sudo make install VERBOSE=1 
sudo ldconfig

### Install thrift python modules ###

mkdir -p '/usr/local/src'/'fbthrift/thrift/lib/py' && cd '/usr/local/src'/'fbthrift/thrift/lib/py'
PYTHONPATH="$PYTHONPATH:$PY_LIB_PATH" sudo python3 setup.py install

### Check out hyperic/sigar, workdir . ###

mkdir -p '/usr/local/src' && cd '/usr/local/src'
if [[ ! -d '/usr/local/src'/'sigar' ]]; then 
	git clone https://github.com/'hyperic/sigar'
fi
mkdir -p '/usr/local/src'/'sigar'/'.' && cd '/usr/local/src'/'sigar'/'.'
git checkout $SIGAR_REV

### Build and install sigar ###

./autogen.sh
LDFLAGS="$LDFLAGS" CFLAGS="$CFLAGS" CPPFLAGS="$CPPFLAGS" ./configure 'CFLAGS'='-fgnu89-inline'
make VERBOSE=1
sudo make install VERBOSE=1 
sudo ldconfig

### Check out zeromq/libzmq, workdir . ###

mkdir -p '/usr/local/src' && cd '/usr/local/src'
if [[ ! -d '/usr/local/src'/'libzmq' ]]; then 
	git clone https://github.com/'zeromq/libzmq'
fi
mkdir -p '/usr/local/src'/'libzmq'/'.' && cd '/usr/local/src'/'libzmq'/'.'
git checkout $ZMQ_REV

### Build and install zeromq/libzmq ###

./autogen.sh
LDFLAGS="$LDFLAGS" CFLAGS="$CFLAGS" CPPFLAGS="$CPPFLAGS" ./configure 
make VERBOSE=1
sudo make install VERBOSE=1 
sudo ldconfig

### Check out facebook/fbzmq, workdir fbzmq/build ###

mkdir -p '/usr/local/src' && cd '/usr/local/src'
if [[ ! -d '/usr/local/src'/'fbzmq' ]]; then 
	git clone https://github.com/'facebook/fbzmq'
fi
mkdir -p '/usr/local/src'/'fbzmq'/'fbzmq/build' && cd '/usr/local/src'/'fbzmq'/'fbzmq/build'
git checkout $FBZMQ_REV

### Build and install fbzmq/fbzmq/build ###

CXXFLAGS="$CXXFLAGS -fPIC" CFLAGS="$CFLAGS -fPIC" cmake -D'BUILD_SHARED_LIBS'='ON' '..'
PYTHONPATH="$PYTHONPATH:$PY_LIB_PATH" make
sudo make install
sudo ldconfig

### Install fbzmq python modules ###

mkdir -p '/usr/local/src'/'fbzmq/fbzmq/py' && cd '/usr/local/src'/'fbzmq/fbzmq/py'
PYTHONPATH="$PYTHONPATH:$PY_LIB_PATH" sudo python3 setup.py install

### Check out google/re2, workdir build ###

mkdir -p '/usr/local/src' && cd '/usr/local/src'
if [[ ! -d '/usr/local/src'/'re2' ]]; then 
	git clone https://github.com/'google/re2'
fi
mkdir -p '/usr/local/src'/'re2'/'build' && cd '/usr/local/src'/'re2'/'build'
git checkout $RE2_REV

### Build and install google/re2 ###

CXXFLAGS="$CXXFLAGS -fPIC" CFLAGS="$CFLAGS -fPIC" cmake -D'BUILD_SHARED_LIBS'='ON' '..'
make VERBOSE=1
sudo make install VERBOSE=1 
sudo ldconfig

### Check out thom311/libnl, workdir . ###

mkdir -p '/usr/local/src' && cd '/usr/local/src'
if [[ ! -d '/usr/local/src'/'libnl' ]]; then 
	git clone https://github.com/'thom311/libnl'
fi
mkdir -p '/usr/local/src'/'libnl'/'.' && cd '/usr/local/src'/'libnl'/'.'
git checkout $LIBNL_REV

### Build and install thom311/libnl ###

curl -O https://raw.githubusercontent.com/facebook/openr/$OPENR_REV/build/fix-route-obj-attr-list.patch
git apply 'fix-route-obj-attr-list.patch'
./autogen.sh
LDFLAGS="$LDFLAGS" CFLAGS="$CFLAGS" CPPFLAGS="$CPPFLAGS" ./configure 
make VERBOSE=1
sudo make install VERBOSE=1 
sudo ldconfig

### Check out facebook/openr, workdir build ###

mkdir -p '/usr/local/src' && cd '/usr/local/src'
if [[ ! -d '/usr/local/src'/'openr' ]]; then 
	git clone https://github.com/'facebook/openr'
fi
mkdir -p '/usr/local/src'/'openr'/'build' && cd '/usr/local/src'/'openr'/'build'
git checkout $OPENR_REV

### Build and install openr/build ###

CXXFLAGS="$CXXFLAGS -fPIC" CFLAGS="$CFLAGS -fPIC" cmake -D'BUILD_SHARED_LIBS'='ON' -D'ADD_ROOT_TESTS'='OFF' '..'
make Decision-cpp2-obj Dual-cpp2-obj HealthChecker-cpp2-obj KvStore-cpp2-obj LinkMonitor-cpp2-obj
PYTHONPATH="$PYTHONPATH:$PY_LIB_PATH" make
sudo make install
sudo ldconfig

### Install OpenR python modules ###

mkdir -p '/usr/local/src'/'openr/openr/py' && cd '/usr/local/src'/'openr/openr/py'
PYTHONPATH="$PYTHONPATH:$PY_LIB_PATH" sudo pip3 install cffi future pathlib 'networkx==2.2'
PYTHONPATH="$PYTHONPATH:$PY_LIB_PATH" sudo python3 setup.py build
PYTHONPATH="$PYTHONPATH:$PY_LIB_PATH" sudo python3 setup.py install

### Run openr tests ###

mkdir -p '/usr/local/src'/'openr/build' && cd '/usr/local/src'/'openr/build'
CTEST_OUTPUT_ON_FAILURE=TRUE make test

