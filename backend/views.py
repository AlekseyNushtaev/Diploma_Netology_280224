import json

from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.http import JsonResponse
from requests import get
from rest_framework.views import APIView
from yaml import load as load_yaml, Loader
from django.shortcuts import render

from backend.models import Shop, Category, ShopCategory, ProductInfo, Product, Parameter, ProductParameter


class PartnerUpdate(APIView):
    """
    A class for updating partner information.

    Methods:
    - post: Update the partner information.

    Attributes:
    - None
    """

    def get(self, request, *args, **kwargs):
        """
                Update the partner price list information.

                Args:
                - request (Request): The Django request object.

                Returns:
                - JsonResponse: The response indicating the status of the operation and any errors.
                """
        with open("data/shop1.json", encoding="utf-8") as f:
            data = json.load(f)
        shop = Shop.objects.filter(name=data["shop"])
        if not shop:
            shop = Shop.objects.create(name=data["shop"])
        else:
            shop = shop[0]
        old_cat_for_shop = ShopCategory.objects.filter(shop=shop)
        old_cat_for_shop.delete()
        for cat in data["categories"]:
            category = Category.objects.filter(name=cat["name"])
            if not category:
                category = Category.objects.create(name=cat["name"])
            else:
                category = category[0]
            ShopCategory.objects.create(shop=shop, category=category)
        ProductInfo.objects.filter(shop=shop).delete()
        for item in data['products']:
            product = Product.objects.filter(name=item['name'])
            if not product:
                category = Category.objects.filter(name=item["category"])[0]
                product = Product.objects.create(name=item["name"], category=category)
            else:
                product = product[0]
            product_info = ProductInfo.objects.create(product=product,
                                                      price=item["price"],
                                                      quantity=item['quantity'],
                                                      shop=shop)
            for name, value in item['parameters'].items():
                parameter = Parameter.objects.filter(name=name)
                if not parameter:
                    parameter = Parameter.objects.create(name=name)
                else:
                    parameter = parameter[0]
                ProductParameter.objects.create(product=product,
                                                parameter=parameter,
                                                value=value)
        return JsonResponse(data)
# Create your views here.
