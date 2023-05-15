from __future__ import annotations

import os
import sys
import json
import arrow
import datetime
import pathlib

sys.path.append(str(pathlib.Path(__file__).parent))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
import django

django.setup()


from backend.settings import get_redis_connection
from typing import Iterable, List, Optional, Union, Tuple
from django.db.models import Q, F, Min, Max, QuerySet, Count, Sum, Value, Avg
