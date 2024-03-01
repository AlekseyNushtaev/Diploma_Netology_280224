from django.urls import path

from backend.views import PartnerUpdate

urlpatterns = [
    path('partner/update', PartnerUpdate.as_view(), name='partner-update'),
]