"""HospFlow URL Configuration"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
]

try:
    from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
except ModuleNotFoundError:
    SpectacularAPIView = None
    SpectacularSwaggerView = None

if SpectacularAPIView is not None:
    urlpatterns += [
        path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
        path(
            "api/docs/",
            SpectacularSwaggerView.as_view(url_name="schema"),
            name="swagger-ui",
        ),
        path("api/accounts/", include("apps.accounts.urls")),
        path("api/patients/", include("apps.patients.urls")),
        path("api/consultations/", include("apps.consultations.urls")),
        path("api/clinical-records/", include("apps.clinical_records.urls")),
        path("api/billing/", include("apps.billing.urls")),
        path("api/inventory/", include("apps.inventory.urls")),
        path("api/notifications/", include("apps.notifications.urls")),
        path("api/wards/", include("apps.wards.urls")),
        path("api/audit/", include("apps.audit.urls")),
        path("api/reporting/", include("apps.reporting.urls")),
    ]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    if "debug_toolbar" in settings.INSTALLED_APPS:
        urlpatterns += [path("__debug__/", include("debug_toolbar.urls"))]
