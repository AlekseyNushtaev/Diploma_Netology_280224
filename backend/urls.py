from django.urls import path, include

from backend.views import request_user_activation, PriceUpdate, ShopState, ProductView, ProductSoloView, OrderView, \
    ContactView, OrderShopView

urlpatterns = [
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
    path('request_activate/<str:uid>/<str:token>/', request_user_activation, name='user-activate'),
    path('shop/price_update/', PriceUpdate.as_view(), name='price-update'),
    path('shop/state/', ShopState.as_view(), name='shop-state'),
    path('products/', ProductView.as_view(), name='products'),
    path('product/<int:product_id>/', ProductSoloView.as_view(), name='product-solo-info'),
    path('order/', OrderView.as_view(), name='order'),
    path('contact/', ContactView.as_view(), name='contact'),
    path('shop/order/', OrderShopView.as_view(), name='order_shop'),

]