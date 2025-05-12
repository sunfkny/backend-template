from django.http import HttpRequest


def get_client_ip(request: HttpRequest):
    """
    If the request is made through a proxy, the nginx realip module needs to be configured.
    """
    return request.META.get("REMOTE_ADDR")
