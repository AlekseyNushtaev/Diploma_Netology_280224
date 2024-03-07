from rest_framework import serializers

from backend.models import Shop, Product, Category, ProductInfo, ProductParameter


class ShopSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shop
        fields = ('id', 'name', 'file', 'is_active',)


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
        fields = ('shop', 'shop_id', 'price', 'quantity')


class ProductSoloSerializer(serializers.ModelSerializer):
    product_info = serializers.SerializerMethodField()
    product_parameters = ProductParameterSerializer(many=True, read_only=True)
    class Meta:
        model = Product
        fields = ('id', 'name', 'product_parameters', 'product_info')

    def get_product_info(self, obj):
        # Get the product_info queryset
        product_info_qs = obj.product_info.all()

        # Filter the product_info queryset
        filtered_product_info_qs = product_info_qs.filter(shop__is_active=True)

        # Serialize the filtered product_info queryset
        serialized_product_info = ProductInfoSerializer(filtered_product_info_qs, many=True).data

        return serialized_product_info
