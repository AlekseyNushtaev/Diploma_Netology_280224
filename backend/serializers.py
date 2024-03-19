from rest_framework import serializers

from backend.models import (Shop, Product, ProductInfo,
                            ProductParameter, OrderItem, Order, Contact)


class ShopSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shop
        fields = '__all__'


class ProductSerializer(serializers.ModelSerializer):
    category = serializers.CharField(read_only=True, source='category.name')

    class Meta:
        model = Product
        fields = ('name', 'id', 'category',)


class ProductParameterSerializer(serializers.ModelSerializer):
    parameter = serializers.CharField(read_only=True, source='parameter.name')

    class Meta:
        model = ProductParameter
        fields = ('parameter', 'value')


class ProductInfoSerializer(serializers.ModelSerializer):
    shop = serializers.CharField(source='shop.name')
    shop_id = serializers.CharField(source='shop.id')

    class Meta:
        model = ProductInfo
        fields = ('id', 'shop', 'shop_id', 'price', 'quantity')


class ProductSoloSerializer(serializers.ModelSerializer):
    product_info = serializers.SerializerMethodField()
    product_parameters = ProductParameterSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = ('id', 'name', 'product_parameters', 'product_info')

    def get_product_info(self, obj):
        product_info_qs = obj.product_info.all()
        filtered_product_info_qs = product_info_qs.filter(shop__is_active=True)
        ser_product_info = ProductInfoSerializer(filtered_product_info_qs,
                                                 many=True)
        return ser_product_info.data


class OrderItemSerializer(serializers.ModelSerializer):

    class Meta:
        model = OrderItem
        fields = '__all__'


class OrderSerializer(serializers.ModelSerializer):
    order_items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ('id', 'order_items', 'state', 'created_at', 'contact',)


class ContactSerializer(serializers.ModelSerializer):

    class Meta:
        model = Contact
        fields = '__all__'
