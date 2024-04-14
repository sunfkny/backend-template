from __future__ import annotations

import datetime
import json
import os
import pathlib
import sys

import arrow

sys.path.append(str(pathlib.Path(__file__).parent))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
import django

django.setup()


from typing import Iterable, Tuple, Union

from django.db.models import Avg, Count, F, Max, Min, Q, QuerySet, Sum, Value

from backend.settings import get_redis_connection
