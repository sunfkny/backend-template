import itertools
import shlex

from backend.settings import BASE_DIR, DOMAIN_NAME

if not DOMAIN_NAME:
    raise Exception("backend.settings.DOMAIN_NAME is not set")


print(
    f"""
# ================== logrotate ==================
# /etc/logrotate.d/{DOMAIN_NAME}.conf

{BASE_DIR / 'logs/*.log'} {{
    daily
    rotate 14
    createolddir
    olddir old
    copytruncate
    missingok
    dateext
    compress
    notifempty
    sharedscripts
    postrotate
      touch {BASE_DIR / 'logs/run.log.logreopen'}
    endscript
}}
"""
)


is_www = DOMAIN_NAME.startswith("www.")

server_name_list = [DOMAIN_NAME]
if is_www:
    server_name_list.append(DOMAIN_NAME.removeprefix("www."))
server_name = " ".join(server_name_list)
non_www_domain_name = DOMAIN_NAME.removeprefix("www.")

redirect = ""
if is_www:
    redirect += f"""
    if ($http_host = {non_www_domain_name}) {{
        return 301 https://{DOMAIN_NAME}$request_uri;
    }}
"""


print(
    f"""# ================== nginx config ==================
# /etc/nginx/conf.d/{DOMAIN_NAME}.conf

server {{
    listen 80;
    server_name {server_name};
    access_log /var/log/nginx/{DOMAIN_NAME}_nginx.log combined;

    # listen 443 ssl http2;
    # ssl_certificate /etc/nginx/ssl/{DOMAIN_NAME}.pem;
    # ssl_certificate_key /etc/nginx/ssl/{DOMAIN_NAME}.key;
    # if ($scheme = http) {{
    #     return 301 https://$host$request_uri;
    # }}

    set $base {BASE_DIR};
    client_max_body_size 10m;

    {redirect}
    location /api/ {{
        include uwsgi_params;
        uwsgi_pass unix:$base/uwsgi.sock;
    }}
    location ~ ^/admin($|/) {{
        include uwsgi_params;
        uwsgi_pass unix:$base/uwsgi.sock;
    }}
    location /tinymce/ {{
        include uwsgi_params;
        uwsgi_pass unix:$base/uwsgi.sock;
    }}
    location /media/ {{
        alias $base/media/;
    }}
    location / {{
        root $base/dist/;
        # try_files $uri $uri/ /index.html;
    }}
    # location /index.html {{
    #     add_header Cache-Control "no-cache";
    #     root $base/dist/;
    # }}
}}
"""
)


acme_issue = shlex.join(
    [
        "acme.sh",
        "--issue",
        *itertools.chain(*[["-d", d] for d in server_name_list]),
        "--nginx",
        f"/etc/nginx/conf.d/{DOMAIN_NAME}.conf",
        "--debug",
        "2",
    ]
)

acme_install = shlex.join(
    [
        "acme.sh",
        "--install-cert",
        *itertools.chain(*[["-d", d] for d in server_name_list]),
        "--key-file",
        f"/etc/nginx/ssl/{DOMAIN_NAME}.key",
        "--fullchain-file",
        f"/etc/nginx/ssl/{DOMAIN_NAME}.pem",
        "--reloadcmd",
        "service nginx force-reload",
    ]
)

print(
    f"""
# ================== acme.sh ==================
{acme_issue}
{acme_install}
"""
)
