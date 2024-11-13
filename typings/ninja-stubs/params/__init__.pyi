from re import Pattern
from typing import Annotated, Any, TypeVar

from ninja.params.functions import Body as Body
from ninja.params.functions import Cookie as Cookie
from ninja.params.functions import File as File
from ninja.params.functions import Form as Form
from ninja.params.functions import Header as Header
from ninja.params.functions import Path as Path
from ninja.params.functions import Query as Query

BodyEx = Annotated
CookieEx = Annotated
FileEx = Annotated
FormEx = Annotated
HeaderEx = Annotated
PathEx = Annotated
QueryEx = Annotated

def P(
    *,
    alias: str | None = None,
    title: str | None = None,
    description: str | None = None,
    gt: float | None = None,
    ge: float | None = None,
    lt: float | None = None,
    le: float | None = None,
    min_length: int | None = None,
    max_length: int | None = None,
    pattern: str | Pattern[str] | None = None,
    example: Any = None,
    examples: dict[str, Any] | None = None,
    deprecated: bool | None = None,
    include_in_schema: bool = True,
    **extra: Any,
) -> dict[str, Any]: ...
