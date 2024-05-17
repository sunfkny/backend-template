```bash
rye init # for installable Python packages
rye init --virtual # for not installable Python packages
rye pin 3.10.14
rye sync
# /usr/bin/ld: cannot find -lpython3.10: No such file or directory
CC=gcc LIBRARY_PATH=~/.rye/py/cpython@3.10.14/include rye sync
```
