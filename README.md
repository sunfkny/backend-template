# backend-template
```
git clone https://ghproxy.com/https://github.com/sunfkny/backend-template.git
cd backend-template
pip install -r requirements.txt
git clone https://ghproxy.com/https://github.com/sunfkny/typings.git
```
## 可选依赖
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

## 新增 apps
```
cd backend/apps
python ../../manage.py startapp <app_name>
```