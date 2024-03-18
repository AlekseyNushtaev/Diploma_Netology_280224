import json

import requests
from django.core.mail import send_mail
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.db import IntegrityError
from django.db.models import Q
from django.http import JsonResponse
from requests import get
from rest_framework.decorators import api_view
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import render

from backend.models import Shop, Category, ShopCategory, ProductInfo, Product, Parameter, ProductParameter, Order, \
    Contact
from django.conf import settings

from backend.serializers import ShopSerializer, ProductSerializer, ProductInfoSerializer, ProductSoloSerializer, \
    OrderItemSerializer, OrderSerializer, ContactSerializer


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

    def post(self, request):
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
        return JsonResponse({'Status': False, 'Errors': 'Не указано имя файла для загрузки'})

class ShopState(APIView):
    """
    Класс для действий со статусом магазина
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

    def post(self, request):
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


class ProductView(ListAPIView):
    """
    Класс для получения списка товаров из активных магазинов
    """

    shops = Shop.objects.filter(is_active=True)
    products = ProductInfo.objects.filter(shop__in=shops)
    queryset = Product.objects.filter(product_info__in=products).distinct()
    serializer_class = ProductSerializer


class ProductSoloView(APIView):
    """
    Класс для поиска товара по id
    """
    def get(self, request, product_id):
        query = Product.objects.filter(id=product_id).first()
        serializer = ProductSoloSerializer(query)
        return Response(serializer.data)


class OrderView(APIView):
    """
    Класс для работы с заказами клиента и магазина
    """
    def get(self, request):
        """
        Метод для просмотра всех заказов клиента
        """
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)

        if request.user.type != 'buyer':
            return JsonResponse({'Status': False, 'Error': 'Только для клиентов'}, status=403)
        query = Order.objects.filter(user=request.user)
        serializer = OrderSerializer(query, many=True)
        return Response(serializer.data)


    def post(self, request):
        """
        Метод для создания заказа клиентом
        """
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)

        if request.user.type != 'buyer':
            return JsonResponse({'Status': False, 'Error': 'Только для клиентов'}, status=403)

        products = request.data.get('products')
        if products:
            try:
                products_list = json.loads(products)
            except ValueError:
                return JsonResponse({'Status': False, 'Errors': 'products - неверный формат данных'})
            order =Order.objects.create(user=request.user, state='not accepted')
            for product in products_list:
                product['order'] = order.id
                serializer = OrderItemSerializer(data=product)
                if serializer.is_valid():
                    shop = Shop.objects.get(product_info__id=product['product_info'])
                    if shop.is_active:
                        try:
                            serializer.save()
                        except IntegrityError as error:
                            order.delete()
                            return JsonResponse({'Status': False, 'Errors': str(error)})
                    else:
                        order.delete()
                        return JsonResponse({'Status': False, 'Errors': 'Магазин отменил прием заказов'})
                else:
                    order.delete()
                    return JsonResponse({'Status': False, 'Errors': serializer.errors})
            return JsonResponse({'Status': True, 'Создан заказ с id:': order.id})
        else:
            return JsonResponse({'Status': False, 'Errors': 'В запросе отсутствует список товаров'})

    def delete(self, request):
        """
        Метод для удаления заказа по id
        """
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)

        if request.user.type != 'buyer':
            return JsonResponse({'Status': False, 'Error': 'Только для клиентов'}, status=403)
        order_id = request.data.get('order_id')
        if order_id:
            try:
                order_id = int(order_id)
            except TypeError:
                return JsonResponse({'Status': False, 'Errors': 'order_id - неверный формат данных'})
            try:
                Order.objects.get(id=order_id, user=request.user).delete()
            except ObjectDoesNotExist:
                return JsonResponse({'Status': False, 'Errors': 'У вас нет заказа с указанным id'})
            return JsonResponse({'Status': True, 'Удален заказ под номером': order_id})
        else:
            return JsonResponse({'Status': False, 'Errors': 'В запросе не указан order_id'})

    def patch(self, request):
        """
        Метод для добавления товаров в заказ
        """
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)

        if request.user.type != 'buyer':
            return JsonResponse({'Status': False, 'Error': 'Только для клиентов'}, status=403)
        order_id = request.data.get('order_id')
        if order_id:
            try:
                order_id = int(order_id)
            except TypeError:
                return JsonResponse({'Status': False, 'Errors': 'order_id - неверный формат данных'})
            try:
                order = Order.objects.get(id=order_id, user=request.user)
            except ObjectDoesNotExist:
                return JsonResponse({'Status': False, 'Errors': 'У вас нет заказа с указанным id'})
            products = request.data.get('products')
            if products:
                try:
                    products_list = json.loads(products)
                except ValueError:
                    return JsonResponse({'Status': False, 'Errors': 'products - неверный формат данных'})
                for product in products_list:
                    product['order'] = order.id
                    serializer = OrderItemSerializer(data=product)
                    if serializer.is_valid():
                        shop = Shop.objects.get(product_info__id=product['product_info'])
                        if shop.is_active:
                            try:
                                serializer.save()
                            except IntegrityError as error:
                                return JsonResponse({'Status': False, 'Errors': str(error)})
                        else:
                            return JsonResponse({'Status': False, 'Errors': 'Магазин отменил прием заказов'})
                    else:
                        return JsonResponse({'Status': False, 'Errors': serializer.errors})
                return JsonResponse({'Status': True, 'Товары добавлены в заказ с id:': order.id})
            else:
                return JsonResponse({'Status': False, 'Errors': 'В запросе отсутствует список товаров'})
        else:
            return JsonResponse({'Status': False, 'Errors': 'В запросе не указан order_id'})


class ContactView(APIView):
    """
    Класс для работы с контактами клиента
    """
    def post(self, request):
        """
        Метод для добавления контактов к заказу
        """
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)

        if request.user.type != 'buyer':
            return JsonResponse({'Status': False, 'Error': 'Только для клиентов'}, status=403)

        order_id = request.data.get('order_id')
        if order_id:
            try:
                order_id = int(order_id)
            except TypeError:
                return JsonResponse({'Status': False, 'Errors': 'order_id - неверный формат данных'})
            try:
                order = Order.objects.get(id=order_id, user=request.user)
                if order.state == 'accepted':
                    return JsonResponse({'Status': False, 'Errors': 'У заказа с order_id контакты определены'})
            except ObjectDoesNotExist:
                return JsonResponse({'Status': False, 'Errors': 'У вас нет заказа с указанным id'})
            contact = request.data.get('contact')
            if contact:
                try:
                    contact_dict = json.loads(contact)
                except ValueError:
                    return JsonResponse({'Status': False, 'Errors': 'contact - неверный формат данных'})
                contact_dict['user'] = request.user.id
                serializer = ContactSerializer(data=contact_dict)
                if serializer.is_valid():
                    try:
                        obj = serializer.save()
                    except IntegrityError as error:
                        return JsonResponse({'Status': False, 'Errors': str(error)})
                    order.state = 'accepted'
                    order.contact = obj
                    order.save()
                    return JsonResponse({'Status': True, 'Контакт добавлен': 'Заказ подтвержден'})
                else:
                    return JsonResponse({'Status': False, 'Errors': serializer.errors})
            else:
                return JsonResponse({'Status': False, 'Errors': 'В запросе не указан contact'})
        else:
            return JsonResponse({'Status': False, 'Errors': 'В запросе не указан order_id'})

    def delete(self, request):
        """
        Метод для удаления контакта из заказа
        """
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)

        if request.user.type != 'buyer':
            return JsonResponse({'Status': False, 'Error': 'Только для клиентов'}, status=403)

        order_id = request.data.get('order_id')
        if order_id:
            try:
                order_id = int(order_id)
            except TypeError:
                return JsonResponse({'Status': False, 'Errors': 'order_id - неверный формат данных'})
            try:
                order = Order.objects.get(id=order_id, user=request.user)
                if order.state == 'not accepted':
                    return JsonResponse({'Status': False, 'Errors': 'У заказа с order_id контактов нет'})
            except ObjectDoesNotExist:
                return JsonResponse({'Status': False, 'Errors': 'У вас нет заказа с указанным id'})
            Contact.objects.get(order=order).delete()
            order.state = 'not accepted'
            order.contact = None
            order.save()
            return JsonResponse({'Status': True})
        else:
            return JsonResponse({'Status': False, 'Errors': 'В запросе не указан order_id'})
# Create your views here.
