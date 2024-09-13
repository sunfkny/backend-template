"""backend URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path
from ninja import NinjaAPI, Swagger

from backend.settings import DEBUG, DIST_ROOT, MEDIA_ROOT, MEDIA_URL_RELATIVE_PATH

from .handler import set_exception_handlers
from .renderer import CustomJSONRenderer

docs = Swagger(
    settings={
        "persistAuthorization": True,
        "requestSnippetsEnabled": True,
    }
)
renderer = CustomJSONRenderer()
api = NinjaAPI(
    title="Open API",
    renderer=renderer,
    docs=docs,
    urls_namespace="api",
)
api_back = NinjaAPI(
    title="Open API",
    docs=docs,
    renderer=renderer,
    urls_namespace="api_back",
)

set_exception_handlers(api)
set_exception_handlers(api_back)

from backend.apps.back.api_back import router as back_back_router
from backend.apps.common.api import router as common_router
from backend.apps.user.api import router as user_router

api.add_router("/", user_router)
api.add_router("/", common_router)
api_back.add_router("/", back_back_router)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", api.urls),
    path("api/back/", api_back.urls),
]


if DEBUG:
    urlpatterns += static(MEDIA_URL_RELATIVE_PATH, document_root=MEDIA_ROOT, show_indexes=True)
    urlpatterns += static("/", document_root=DIST_ROOT, show_indexes=True)
