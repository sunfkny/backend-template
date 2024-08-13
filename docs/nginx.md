```nginx
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
  '$time_iso8601 - $remote_addr $server_protocol $status '
  '$request_method $request_uri sent $body_bytes_sent in $request_time '
  '"$http_referer" "$http_user_agent" "$http_authorization"';

```

```nginx
set $base /data/wwwroot/www.example.com;

location ^~ /(jpeg|jpg|js|mp4|pdf|png|svg|css)/ {
  root $base/;
  add_header Cache-Control "public, max-age=31536000, immutable";
}
location ~ ^(/|/sw\.js|/index\.html|/manifest\.webmanifest|/manifest\.json)$ {
  add_header Cache-Control "no-store";
  root $base/;
}
location / {
  root $base/;
  try_files $uri $uri/ /index.html;
}

```
