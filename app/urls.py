from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/user/", include("user.urls")),
    path("api/dashboard/", include("dashboard.urls")),
    path("api/spread/", include("spread.urls")),
]
