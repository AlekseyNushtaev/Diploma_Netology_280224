import json

import requests
from django.core.mail import send_mail
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.http import JsonResponse
from requests import get
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from yaml import load as load_yaml, Loader
from django.shortcuts import render

from backend.models import Shop, Category, ShopCategory, ProductInfo, Product, Parameter, ProductParameter
from django.conf import settings

from backend.serializers import ShopSerializer


@api_view(["GET"])
def request_user_activation(request, uid, token):
    """
    Метод для активации аккаунта через GET-запрос (для нажатия ссылки в письме с подтверждением активации)
    """
    post_url = "http://127.0.0.1:8000/api/v1/auth/users/activation/"
    post_data = {"uid": uid, "token": token}
    result = requests.post(post_url, data=post_data)
    return JsonResponse({'Status': 'User activated'})


class PriceUpdate(APIView):
    """
    Класс для обновления прайса магазина
    """

    def post(self, request, *args, **kwargs):
        """
        Метод обновляет прайс магазина
        """
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)

        if request.user.type != 'shop':
            return JsonResponse({'Status': False, 'Error': 'Только для магазинов'}, status=403)

        file = request.data.get('file')
        if file:
            with open(f'data/{file}', encoding="utf-8") as f:
                data = json.load(f)
            shop = Shop.objects.filter(name=data["shop"])
            if not shop:
                shop = Shop.objects.create(name=data["shop"], user=request.user, file=file)
            else:
                shop = shop[0]
                shop.user = request.user
                shop.file = file
                shop.save()
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
            return JsonResponse({'Status': True})
        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})

class ShopState(APIView):
    """
    Класс для смены статуса магазина
    """

    def get(self, request, *args, **kwargs):
        """
        Метод для получения текущего статуса магазина
        """
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)

        if request.user.type != 'shop':
            return JsonResponse({'Status': False, 'Error': 'Только для магазинов'}, status=403)

        shop = Shop.objects.filter(user=request.user)
        if shop:
            serializer = ShopSerializer(shop[0])
            return Response(serializer.data)
        else:
            return JsonResponse({'Status': False, 'Error': 'Прайс не загружен'}, status=403)

    def post(self, request, *args, **kwargs):
        """
        Метод для изменения текущего статуса магазина
        """
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)

        if request.user.type != 'shop':
            return JsonResponse({'Status': False, 'Error': 'Только для магазинов'}, status=403)

        shop = Shop.objects.filter(user=request.user)
        if shop:
            shop = shop[0]
            shop.is_active = not shop.is_active
            shop.save()
            return JsonResponse({'Status': True, 'shop_active': shop.is_active})
        else:
            return JsonResponse({'Status': False, 'Error': 'Прайс не загружен'}, status=403)

# Create your views here.
