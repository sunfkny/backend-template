```python
import os
import pathlib
import sys
import django

parts = list(pathlib.Path(__file__).parent.parts)
while len(parts):
    project_root = pathlib.Path(*parts)
    if (project_root / "manage.py").is_file():
        sys.path.append(str(project_root))
        break
    parts.pop()

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
# os.environ.setdefault("DJANGO_ALLOW_ASYNC_UNSAFE", "true")
django.setup()
```
