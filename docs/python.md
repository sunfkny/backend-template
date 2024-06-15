```bash
#!/bin/bash
set -e

if [ -z "$1" ]; then
    echo "Error: No Python version provided."
    echo "Usage: $0 <python_version>"
    exit 1
fi

PYTHON_VERSION=$1
PYTHON_MINOR_VERSION="$(echo $PYTHON_VERSION | cut -d'.' -f 2)"
PYTHON_BUILD_VERSION="$(echo $PYTHON_VERSION | cut -d'.' -f 3)"

if [ -f /etc/debian_version ]; then
    apt-get -y update
    apt-get -y install make wget curl gcc zlib1g-dev libffi-dev libreadline-dev default-libmysqlclient-dev libsqlite3-dev libssl-dev openssl
elif [ -f /etc/redhat-release ]; then
    yum -y install epel-release
    yum -y install make wget curl gcc zlib-devel libffi-devel readline-devel mysql-devel sqlite-devel
    RHEL_VERSION=$(rpm -E %{rhel})
    case $RHEL_VERSION in
    7)
        yum -y install openssl11-devel
        export CFLAGS=$(pkg-config --cflags openssl11)
        export LDFLAGS=$(pkg-config --libs openssl11)
        ;;
    8 | 9)
        yum -y install openssl-devel
        ;;
    *)
        echo "Unsupported CentOS version"
        exit 1
        ;;
    esac
else
    echo "Unsupported operating system"
    exit 1
fi

LOCATION=$(curl -s https://cloudflare.com/cdn-cgi/trace | grep 'loc' | cut -d'=' -f2)
if [[ $LOCATION == "CN" ]]; then
    DOWNLOAD_PREFIX=https://registry.npmmirror.com/-/binary/python/$PYTHON_VERSION
else
    DOWNLOAD_PREFIX=https://www.python.org/ftp/python/$PYTHON_VERSION
fi

cd /root
wget $DOWNLOAD_PREFIX/Python-$PYTHON_VERSION.tgz -O Python-$PYTHON_VERSION.tgz
tar -xzf Python-$PYTHON_VERSION.tgz
cd /root/Python-$PYTHON_VERSION
./configure
make -j$(nproc) && make altinstall

echo "Python $PYTHON_VERSION has been installed successfully."
echo "To use Python $PYTHON_VERSION by \`python3\` command, you can run the following commands:"
echo "  update-alternatives --install /usr/bin/python3 python3 /usr/local/bin/python3.$PYTHON_MINOR_VERSION 0"
echo "  update-alternatives --config python3"
```
