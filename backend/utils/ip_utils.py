from django.http import HttpRequest


def get_client_ip(request: HttpRequest):
    try:
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return str(x_forwarded_for).split(",")[0]
    except:
        pass
    return request.META.get("REMOTE_ADDR")
