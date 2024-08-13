set -e

cd `dirname $0`

if [ -f .venv/bin/python ]; then
    PYTHON=.venv/bin/python
elif [ -f venv/bin/python ]; then
    PYTHON=venv/bin/python
else
    echo "Virtual environment not found."
    exit 1
fi

echo "Using Python: $PYTHON"

$PYTHON manage.py shell_plus \
    --print-sql \
    --ipython \
    --dont-load auth \
    --dont-load admin \
    --dont-load contenttypes \
    --dont-load sessions
