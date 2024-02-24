安装 [acme.sh](https://github.com/acmesh-official/acme.sh/)
```bash
curl https://get.acme.sh | sh -s email=my@example.com
# Or install in China
git clone https://gitee.com/neilpang/acme.sh.git
cd acme.sh
./acme.sh --install -m my@example.com
```

签发证书
```bash
acme.sh --issue -d www.example.com --nginx --debug 2
```
nginx include 相对路径时会找不到配置文件, 显示指定配置文件
```bash
acme.sh --issue -d www.example.com --nginx /usr/local/nginx/conf/vhost/www.example.com.conf --debug 2
```

安装证书
```bash
acme.sh --install-cert -d www.example.com \
--key-file /usr/local/nginx/cert/www.example.com.key \
--fullchain-file /usr/local/nginx/cert/www.example.com.pem \
--reloadcmd "service nginx force-reload"
```
