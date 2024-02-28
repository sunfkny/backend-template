import io
import re
from typing import Any
from urllib.parse import quote

from django import VERSION
from django.http import HttpResponse, StreamingHttpResponse

LINE_SEP_EXPR = re.compile(r"\r\n|\r|\n")


if VERSION >= (4, 2):
    from django.utils.http import content_disposition_header
else:

    def content_disposition_header(as_attachment, filename: str):
        """
        Construct a Content-Disposition HTTP header value from the given filename
        as specified by RFC 6266.
        """
        if filename:
            disposition = "attachment" if as_attachment else "inline"
            try:
                filename.encode("ascii")
                file_expr = 'filename="{}"'.format(filename.replace("\\", "\\\\").replace('"', r"\""))
            except UnicodeEncodeError:
                file_expr = "filename*=utf-8''{}".format(quote(filename))
            return f"{disposition}; {file_expr}"
        elif as_attachment:
            return "attachment"
        else:
            return None


class AttachmentResponse(HttpResponse):
    def __init__(self, content: Any = b"", filename: str = "attachment.bin", *args, **kwargs) -> None:
        super().__init__(content=content, *args, **kwargs)
        if content_disposition := content_disposition_header(as_attachment=True, filename=filename):
            self.headers["Content-Disposition"] = content_disposition


class ExcelResponse(AttachmentResponse):
    def __init__(self, content: Any = b"", filename: str = "attachment.xlsx", *args, **kwargs) -> None:
        super().__init__(content=content, filename=filename, *args, **kwargs)
        self.headers["Content-Type"] = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


class ServerSentEvent:
    def __init__(
        self,
        data: Any | None = None,
        *,
        event: str | None = None,
        id: str | int | None = None,
        retry: int | None = None,
        comment: str | None = None,
        sep: str | None = None,
    ) -> None:
        self.data = data
        self.event = event
        self.id = id
        self.retry = retry
        self.comment = comment
        self.DEFAULT_SEPARATOR = "\r\n"
        self.LINE_SEP_EXPR = LINE_SEP_EXPR
        self._sep = sep if sep is not None else self.DEFAULT_SEPARATOR

    def __str__(self) -> str:
        buffer = io.StringIO()
        if self.comment is not None:
            for chunk in self.LINE_SEP_EXPR.split(str(self.comment)):
                buffer.write(f": {chunk}")
                buffer.write(self._sep)

        if self.id is not None:
            buffer.write(self.LINE_SEP_EXPR.sub("", f"id: {self.id}"))
            buffer.write(self._sep)

        if self.event is not None:
            buffer.write(self.LINE_SEP_EXPR.sub("", f"event: {self.event}"))
            buffer.write(self._sep)

        if self.data is not None:
            for chunk in self.LINE_SEP_EXPR.split(str(self.data)):
                buffer.write(f"data: {chunk}")
                buffer.write(self._sep)

        if self.retry is not None:
            buffer.write(f"retry: {self.retry}")
            buffer.write(self._sep)

        buffer.write(self._sep)
        return buffer.getvalue()

    def __bytes__(self) -> bytes:
        return str(self).encode()


class EventSourceResponse(StreamingHttpResponse):
    """
    @example
    ```
    @router.get("/stream")
    async def stream(request: HttpRequest):
        async def sse_generator():
            for i in range(10):
                yield ServerSentEvent(
                    event="message",
                    data=json.dumps({"i": i}),
                )
        return EventSourceResponse(sse_generator())
    ```
    """

    def __init__(
        self,
        streaming_content=(),
        *args,
        **kwargs,
    ):
        super().__init__(
            streaming_content=streaming_content,
            content_type="text/event-stream",
            *args,
            **kwargs,
        )
        self["X-Accel-Buffering"] = "no"  # Disable buffering in nginx
        self["Cache-Control"] = "no-cache"  # Ensure clients don't cache the data
