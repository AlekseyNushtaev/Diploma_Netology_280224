from django.urls import path, re_path, include

from backend.views import PartnerUpdate

urlpatterns = [
    path('auth/', include('djoser.urls')),          # new
    re_path(r'^auth/', include('djoser.urls.authtoken')),  # new
    path('partner/update', PartnerUpdate.as_view(), name='partner-update'),
]