from django.urls import path, include

from backend.views import request_user_activation, PriceUpdate

urlpatterns = [
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
    path('request_activate/<str:uid>/<str:token>/', request_user_activation),
    path('price/update/', PriceUpdate.as_view(), name='partner-update'),
]