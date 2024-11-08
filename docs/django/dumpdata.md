```shell
python manage.py dumpdata -e admin -e auth -e contenttypes -e filebrowser > data.json
python manage.py loaddata data.json
```
