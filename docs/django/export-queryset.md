```bash
uv add xlsxwriter
```

```python
from __future__ import annotations

import io
import typing

import xlsxwriter
from django.db import models
from ninja import Schema

T = typing.TypeVar("T", bound=models.Model)
S = typing.TypeVar("S", bound=Schema)


def queryset_to_iter(queryset: models.QuerySet[T], batch_size: int):
    total = queryset.count()
    for start in range(0, total, batch_size):
        end = min(start + batch_size, total)
        for i in queryset[start:end]:
            yield i


def export_queryset_to_excel(
    queryset: models.QuerySet[T],
    schema: type[S],
    batch_size: int = 1000,
) -> io.BytesIO:
    rows_count = queryset.count()
    if rows_count > 1024 * 1024 - 1:
        raise ValueError(f"行数过多 （{rows_count})")
    column_count = len(schema.model_fields)
    cells_count = rows_count * column_count
    if cells_count > 10 * 1024 * 1024:
        raise ValueError(f"单元格数过多 ({cells_count})")
    buf = io.BytesIO()
    with xlsxwriter.Workbook(buf) as workbook:
        worksheet = workbook.add_worksheet()
        header = [
            field_info.title or field_name
            for field_name, field_info in schema.model_fields.items()
        ]
        worksheet.write_row(0, 0, header)

        for row, item in enumerate(
            queryset_to_iter(queryset, batch_size),
            start=1,
        ):
            worksheet.write_row(row, 0, schema.from_orm(item).model_dump().values())
    buf.seek(0)
    return buf
```
