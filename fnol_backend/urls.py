"""
fnol_backend URL configuration.

- "/"            -> serves the React (CDN) single-page frontend
- "/admin/"      -> Django admin (view claims in a built-in admin UI)
- "/api/..."     -> JSON API, defined in claims/urls.py
"""

from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("claims.urls")),
    path("", TemplateView.as_view(template_name="claims/index.html"), name="home"),
]
