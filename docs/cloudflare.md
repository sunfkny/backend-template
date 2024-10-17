Add the following lines to `/etc/nginx/nginx.conf`
```nginx
include /etc/nginx/cloudflare.conf;
```

Create `/etc/nginx/cloudflare.conf` with the following command
```shell
cat <<EOF >/etc/nginx/cloudflare.conf
real_ip_header CF-Connecting-IP;
# https://www.cloudflare.com/ips-v4
$(curl -s -L https://www.cloudflare.com/ips-v4 | awk '{print "set_real_ip_from "$0";"}')
# https://www.cloudflare.com/ips-v6
$(curl -s -L https://www.cloudflare.com/ips-v6 | awk '{print "set_real_ip_from "$0";"}')
EOF
```

Reload nginx
```shell
nginx -t && nginx -s reload
```
