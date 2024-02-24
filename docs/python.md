```bash
#!/bin/bash
set -e
PYTHON_VERSION="3.10.13"
PYTHON_MINOR_VERSION="$(echo $PYTHON_VERSION | cut -d'.' -f 2)"
PYTHON_BUILD_VERSION="$(echo $PYTHON_VERSION | cut -d'.' -f 3)"
DOWNLOAD_PREFIX=https://registry.npmmirror.com/-/binary/python/$PYTHON_VERSION
# DOWNLOAD_PREFIX=https://www.python.org/ftp/python/$PYTHON_VERSION

yum -y install epel-release
yum -y install wget gcc zlib-devel libffi-devel readline-devel mysql-devel sqlite-devel

if [[ "$(rpm -E %{rhel})" == "7" ]]; then
    yum -y install openssl11-devel
    export CFLAGS=$(pkg-config --cflags openssl11)
    export LDFLAGS=$(pkg-config --libs openssl11)
elif [[ "$(rpm -E %{rhel})" == "8" ]]; then
    yum -y install openssl-devel
else
    echo "Unsupported CentOS version"
    exit 1
fi

cd /root
wget $DOWNLOAD_PREFIX/Python-$PYTHON_VERSION.tgz -O Python-$PYTHON_VERSION.tgz
tar -xzf Python-$PYTHON_VERSION.tgz
cd /root/Python-$PYTHON_VERSION
./configure
make -j$(nproc) && make altinstall
alternatives --install /usr/bin/python3 python3 /usr/local/bin/python3.$PYTHON_MINOR_VERSION 0
alternatives --config python3
python3 -V
```
