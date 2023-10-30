# backend-template
```
git clone https://ghproxy.com/https://github.com/sunfkny/backend-template.git
cd backend-template
python3 -m venv venv
source venv/bin/activate
python -m pip install -U pip
pip install -U wheel setuptools
pip install -r requirements.txt
git clone https://ghproxy.com/https://github.com/sunfkny/typings.git
```
## 新增 apps
```
cd backend/apps
python ../../manage.py startapp <app_name>
```
## 可选依赖
<details>
<summary>展开查看</summary>

### 定时任务 django-crontab
[kraiz/django-crontab](https://github.com/kraiz/django-crontab)
### 异步任务 django-rq
[rq/django-rq](https://github.com/rq/django-rq)
### 打印sql django-print-sql
[rabbit-aaron/django-print-sql](https://github.com/rabbit-aaron/django-print-sql)
### 生成邀请码 hashids
[davidaurelio/hashids-python](https://github.com/davidaurelio/hashids-python)
### 随机头像 multiavatar
[multiavatar/multiavatar-python](https://github.com/multiavatar/multiavatar-python)
### 文件类型识别 python-magic
[ahupp/python-magic](https://github.com/ahupp/python-magic)

</details>

## 安装 python
<details>
<summary>展开查看</summary>

```
#!/bin/bash
set -e
PYTHON_VERSION="3.10.12"
PYTHON_MINOR_VERSION="$(echo $PYTHON_VERSION | cut -d'.' -f 2)"
PYTHON_BUILD_VERSION="$(echo $PYTHON_VERSION | cut -d'.' -f 3)"
DOWNLOAD_PREFIX=https://registry.npmmirror.com/-/binary/python/$PYTHON_VERSION
# DOWNLOAD_PREFIX=https://www.python.org/ftp/python/$PYTHON_VERSION

yum -y install epel-release
yum -y install wget gcc zlib zlib-devel libffi libffi-devel readline-devel mysql-devel sqlite-devel

if [[ "$(rpm -E %{rhel})" == "7" ]]; then
    yum -y install openssl11 openssl11-devel
    export CFLAGS=$(pkg-config --cflags openssl11)
    export LDFLAGS=$(pkg-config --libs openssl11)
elif [[ "$(rpm -E %{rhel})" == "8" ]]; then
    yum -y install openssl openssl-devel
    export LD_LIBRARY_PATH=/usr/lib64
else
    echo "Unsupported CentOS version"
    exit 1
fi

cd /root
wget $DOWNLOAD_PREFIX/Python-$PYTHON_VERSION.tgz -O Python-$PYTHON_VERSION.tgz
tar -xzf Python-$PYTHON_VERSION.tgz
cd /root/Python-$PYTHON_VERSION
./configure --with-ssl --enable-loadable-sqlite-extensions
make -j$(nproc) && make altinstall
alternatives --install /usr/bin/python3 python3 /usr/local/bin/python3.$PYTHON_MINOR_VERSION 0
alternatives --config python3
python3 -V
```

</details>

## crontab 设置
<details>
<summary>展开查看</summary>

```
# /etc/anacrontab: configuration file for anacron

# See anacron(8) and anacrontab(5) for details.

SHELL=/bin/sh
PATH=/sbin:/bin:/usr/sbin:/usr/bin
MAILTO=root
# the maximal random delay added to the base delay of the jobs
# RANDOM_DELAY=45
# 把最大随机廷迟改为0分钟,不再随机廷迟
RANDOM_DELAY=0
# the jobs will be started during the following hours only
# START_HOURS_RANGE=3-22
#执行时间范围为0-22
START_HOURS_RANGE=0-22

#period in days   delay in minutes   job-identifier   command
# 1     5       cron.daily              nice run-parts /etc/cron.daily
# 把强制延迟也改为0分钟,不再强制廷迟
1       0       cron.daily              nice run-parts /etc/cron.daily
7       25      cron.weekly             nice run-parts /etc/cron.weekly
@monthly 45     cron.monthly            nice run-parts /etc/cron.monthly
```

</details>

## .bashrc 设置
<details>
<summary>展开查看</summary>

```
# shell 退出时添加新记录
shopt -s histappend
# 方向键翻阅历史
if [[ $- == *i* ]]
then
    bind '"\e[A": history-search-backward'
    bind '"\e[B": history-search-forward'
fi
```

</details>

## 升级 sqlite3
<details>
<summary>展开查看</summary>

```
yum install -y wget tar gzip gcc make expect

# 下载源码
wget --no-check-certificate https://www.sqlite.org/src/tarball/sqlite.tar.gz

# 编译
tar xzf sqlite.tar.gz
cd sqlite

export CFLAGS="-DSQLITE_ENABLE_FTS3 \
    -DSQLITE_ENABLE_FTS3_PARENTHESIS \
    -DSQLITE_ENABLE_FTS4 \
    -DSQLITE_ENABLE_FTS5 \
    -DSQLITE_ENABLE_JSON1 \
    -DSQLITE_ENABLE_LOAD_EXTENSION \
    -DSQLITE_ENABLE_RTREE \
    -DSQLITE_ENABLE_STAT4 \
    -DSQLITE_ENABLE_UPDATE_DELETE_LIMIT \
    -DSQLITE_SOUNDEX \
    -DSQLITE_TEMP_STORE=3 \
    -DSQLITE_USE_URI \
    -O2 \
    -fPIC"
export PREFIX="/usr/local"
#LIBS="-lm" ./configure --disable-tcl --enable-shared --enable-tempstore=always --prefix="$PREFIX"
LIBS="-lm" ./configure --enable-shared --enable-tempstore=always --prefix="$PREFIX"

make && make install

# 替换系统低版本 sqlite3
mv /usr/bin/sqlite3  /usr/bin/sqlite3_old
ln -s /usr/local/bin/sqlite3   /usr/bin/sqlite3
echo "/usr/local/lib" > /etc/ld.so.conf.d/sqlite3.conf
ldconfig
sqlite3 -version
```

</details>

## 升级 git
<details>
<summary>展开查看</summary>

```
yum install -y centos-release-scl
yum install -y rh-git227
echo '. /opt/rh/rh-git227/enable' >> ~/.bashrc
source ~/.bashrc
git --version  # git version 2.27.0
```

</details>

## swapfile
<details>
<summary>展开查看</summary>

https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux/7/html/storage_administration_guide/ch-swapspace

 **Table 15.1. Recommended System Swap Space** 

| Amount of RAM in the system | Recommended swap space     | Recommended swap space if allowing for hibernation |
| :-------------------------- | :------------------------- | :------------------------------------------------- |
| ⩽ 2 GB                      | 2 times the amount of RAM  | 3 times the amount of RAM                          |
| > 2 GB – 8 GB               | Equal to the amount of RAM | 2 times the amount of RAM                          |
| > 8 GB – 64 GB              | At least 4 GB              | 1.5 times the amount of RAM                        |
| > 64 GB                     | At least 4 GB              | Hibernation not recommended                        |

```
# Create an empty file:
dd if=/dev/zero of=/swapfile bs=1M count=4096
# Set up the swap file with the command:
mkswap  /swapfile
# Change the security of the swap file so it is not world readable.
chmod 0600 /swapfile
# To enable the swap file at boot time, edit /etc/fstab as root to include the following entry
# /swapfile          swap            swap    defaults        0 0
cat /etc/fstab | grep swapfile
# Regenerate mount units so that your system registers the new /etc/fstab configuration
systemctl daemon-reload
# To activate the swap file immediately
swapon  /swapfile
# To test if the new swap file was successfully created and activated, inspect active swap space
cat /proc/swaps
free -h
```
</details>

## nginx log_format
<details>
<summary>展开查看</summary>

```
log_format myjson
  escape=json
  '{"@timestamp":"$time_iso8601",'
  '"remote_addr":"$remote_addr",'
  '"scheme":"$scheme",'
  '"request_method": "$request_method",'
  '"request_uri": "$request_uri",'
  '"server_protocol": "$server_protocol",'
  '"request_time":$request_time,'
  '"status":"$status",'
  '"body_bytes_sent":$body_bytes_sent,'
  '"http_referer":"$http_referer",'
  '"http_user_agent":"$http_user_agent",'
  '"http_authorization":"$http_authorization"'
  '}';


log_format mycombined
  '$time_iso8601 - $remote_addr $server_protocol $status'
  '$request_method $request_uri sent $body_bytes_sent in $request_time'
  '"$http_referer" "$http_user_agent" "$http_authorization"';

```

</details>
