source ./venv/bin/activate

python manage.py shell_plus \
    --print-sql \
    --ipython \
    --dont-load auth \
    --dont-load admin \
    --dont-load contenttypes \
    --dont-load sessions

