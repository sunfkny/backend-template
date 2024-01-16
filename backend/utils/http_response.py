from typing import Any
from urllib.parse import quote
from django.http import HttpResponse

from django import VERSION

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
