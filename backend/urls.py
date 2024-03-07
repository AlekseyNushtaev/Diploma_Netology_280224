from django.urls import path, include

from backend.views import request_user_activation, PriceUpdate, ShopState, ProductView, ProductInfoView, ProductSoloView

urlpatterns = [
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
    path('request_activate/<str:uid>/<str:token>/', request_user_activation, name='user-activate'),
    path('shop/price_update/', PriceUpdate.as_view(), name='price-update'),
    path('shop/state/', ShopState.as_view(), name='shop-state'),
    path('products/', ProductView.as_view(), name='products'),
    path('products/<int:product_id>/', ProductInfoView.as_view(), name='product-info'),
    path('product/<int:product_id>/', ProductSoloView.as_view(), name='product-solo-info'),

]