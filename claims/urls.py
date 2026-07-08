from django.urls import path

from . import views

urlpatterns = [
    path("claims/process-text/", views.ProcessTextView.as_view(), name="process-text"),
    path("claims/process-file/", views.ProcessFileView.as_view(), name="process-file"),
    path("claims/", views.ClaimListView.as_view(), name="claim-list"),
    path("claims/<int:pk>/", views.ClaimDetailView.as_view(), name="claim-detail"),
    path("samples/", views.list_samples, name="sample-list"),
    path("samples/<str:filename>/", views.get_sample_text, name="sample-detail"),
]
