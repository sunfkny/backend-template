import io
import re
from typing import Any, BinaryIO

from django.http import FileResponse, StreamingHttpResponse

LINE_SEP_EXPR = re.compile(r"\r\n|\r|\n")


class AttachmentResponse(FileResponse):
    def __init__(
        self,
        streaming_content: BinaryIO,
        *args,
        as_attachment: bool = True,
        filename: str = "",
        **kwargs,
    ) -> None:
        return super().__init__(
            streaming_content=streaming_content,
            *args,
            as_attachment=as_attachment,
            filename=filename,
            **kwargs,
        )


class ExcelResponse(AttachmentResponse):
    def __init__(
        self,
        streaming_content: BinaryIO,
        *args,
        filename: str = "",
        **kwargs,
    ) -> None:
        filename = getattr(streaming_content, "name", filename)
        if not filename.endswith(".xlsx"):
            filename += ".xlsx"
        super().__init__(streaming_content, filename=filename, *args, **kwargs)


class ServerSentEvent:
    def __init__(
        self,
        data: Any | None = None,
        *,
        event: str | None = None,
        id: str | int | None = None,  # noqa: A002
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
