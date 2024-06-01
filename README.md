# backend-template
```
git clone https://github.com/sunfkny/backend-template.git
cd backend-template
python3 -m venv venv
source venv/bin/activate
python -m pip install -U pip
pip install -U wheel setuptools
pip install -r requirements.txt
git clone https://github.com/sunfkny/typings.git
```
## startapp
```
cd backend/apps
django-admin startapp --template app_template <app_name>
cd ../..
```
