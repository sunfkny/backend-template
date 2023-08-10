from django.http import HttpResponse
from django.utils.http import content_disposition_header


class AttachmentResponse(HttpResponse):
    def __init__(self, filename: str, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        if content_disposition := content_disposition_header(as_attachment=True, filename=filename):
            self.headers["Content-Disposition"] = content_disposition


class ExcelResponse(AttachmentResponse):
    def __init__(self, filename: str, *args, **kwargs) -> None:
        super().__init__(filename=filename, *args, **kwargs)
        self.headers["Content-Type"] = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
