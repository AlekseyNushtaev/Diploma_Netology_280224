import json

import requests
from django.core.mail import send_mail
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from backend.models import (Shop, Category, ShopCategory, ProductInfo, Product,
                            Parameter, ProductParameter, Order, OrderItem)

from backend.serializers import (ShopSerializer, ProductSerializer,
                                 ProductSoloSerializer, OrderItemSerializer,
                                 OrderSerializer, ContactSerializer)


def chek_auth(request, type):
    """
    Функция для проверки авторизации и типа юзера (shop/buyer)

    Пытался сделать через декоратор View класса (method_decorator),
    но в переменную request декоратора попадал AnonymusUser,
    гугл решить проблему не помог.
    """
    if not request.user.is_authenticated:
        return JsonResponse({'Status': False, 'Error': 'Log in required'},
                            status=403)
    if request.user.type != type:
        return JsonResponse({'Status': False, 'Error': f'Just for {type}'},
                            status=403)


@api_view(['GET'])
def request_user_activation(request, uid, token):
    """
    Функция для активации аккаунта через GET-запрос
    (для нажатия ссылки в письме с подтверждением активации)
    """
    post_url = 'http://127.0.0.1:8000/api/v1/auth/users/activation/'
    post_data = {'uid': uid, 'token': token}
    requests.post(post_url, data=post_data)
    return JsonResponse({'Status': 'User activated'})


class PriceUpdate(APIView):
    """
    Класс для обновления прайса магазина
    """
    def post(self, request):
        """
        Метод обновляет прайс магазина
        """
        chek_auth(request, 'shop')

        file = request.data.get('file')
        if file:
            with open(f'data/{file}', encoding='utf-8') as f:
                data = json.load(f)
            old_shop = Shop.objects.filter(user=request.user)
            if old_shop and old_shop[0].name != data['shop']:
                return JsonResponse(
                    {'Status': False,
                     'Errors': 'У вас уже есть магазин с другим названием'})
            shop, _ = Shop.objects.get_or_create(name=data['shop'],
                                                 user=request.user)
            shop.file = file
            shop.save()
            old_cat_for_shop = ShopCategory.objects.filter(shop=shop)
            old_cat_for_shop.delete()
            for cat in data['categories']:
                category, _ = Category.objects.get_or_create(name=cat['name'])
                shop_category, _ = (ShopCategory.objects.get_or_create
                                    (shop=shop, category=category))
            for item in data['products']:
                product, _ = (Product.objects.get_or_create
                              (name=item['name'],
                               category__name=item['category']))
                ProductInfo.objects.create(product=product,
                                           price=item['price'],
                                           quantity=item['quantity'],
                                           shop=shop)
                for name, value in item['parameters'].items():
                    parameter, _ = Parameter.objects.get_or_create(name=name)
                    ProductParameter.objects.create(product=product,
                                                    parameter=parameter,
                                                    value=value)
            return JsonResponse({'Status': True})
        return JsonResponse({'Status': False,
                             'Errors': 'Не указан файл для загрузки'})


class ShopState(APIView):
    """
    Класс для действий со статусом магазина
    """

    def get(self, request, *args, **kwargs):
        """
        Метод для получения текущего статуса магазина
        """
        chek_auth(request, 'shop')

        try:
            shop = Shop.objects.get(user=request.user)
            serializer = ShopSerializer(shop)
            return Response(serializer.data)
        except ObjectDoesNotExist:
            return JsonResponse({'Status': False,
                                 'Error': 'Прайс не загружен'})

    def post(self, request):
        """
        Метод для изменения текущего статуса магазина
        """
        chek_auth(request, 'shop')

        try:
            shop = Shop.objects.get(user=request.user)
            shop.is_active = not shop.is_active
            shop.save()
            return JsonResponse({'Status': True,
                                 'shop_active': shop.is_active})
        except ObjectDoesNotExist:
            return JsonResponse({'Status': False,
                                 'Error': 'Прайс не загружен'})


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
        chek_auth(request, 'buyer')

        query = Order.objects.filter(user=request.user)
        serializer = OrderSerializer(query, many=True)
        return Response(serializer.data)

    def post(self, request):
        """
        Метод для создания заказа клиентом
        """
        chek_auth(request, 'buyer')

        products = request.data.get('products')
        if products:
            try:
                products_list = json.loads(products)
            except ValueError:
                return JsonResponse({'Status': False,
                                     'Errors': 'products - неверный формат'})
            order = Order.objects.create(user=request.user,
                                         state='not accepted')
            for product in products_list:
                product['order'] = order.id
                serializer = OrderItemSerializer(data=product)
                if serializer.is_valid():
                    shop = Shop.objects.get(
                        product_info__id=product['product_info'])
                    if shop.is_active:
                        try:
                            serializer.save()
                        except IntegrityError as error:
                            order.delete()
                            return JsonResponse({'Status': False,
                                                 'Errors': str(error)})
                    else:
                        order.delete()
                        return JsonResponse({'Status': False,
                                             'Errors': 'Магазин не активен'})
                else:
                    order.delete()
                    return JsonResponse({'Status': False,
                                         'Errors': serializer.errors})
            return JsonResponse({'Status': True,
                                 'Создан заказ с id:': order.id})
        else:
            return JsonResponse({'Status': False,
                                 'Errors': 'В запросе нет товаров'})

    def delete(self, request):
        """
        Метод для удаления заказа по id
        """
        chek_auth(request, 'buyer')

        order_id = request.data.get('order_id')
        if order_id:
            try:
                order_id = int(order_id)
            except TypeError:
                return JsonResponse(
                    {'Status': False,
                     'Errors': 'order_id - неверный формат данных'})
            try:
                Order.objects.get(id=order_id, user=request.user).delete()
            except ObjectDoesNotExist:
                return JsonResponse(
                    {'Status': False,
                     'Errors': 'У вас нет заказа с указанным id'})
            return JsonResponse({'Status': True,
                                 'Удален заказ под номером': order_id})
        else:
            return JsonResponse({'Status': False,
                                 'Errors': 'В запросе не указан order_id'})

    def patch(self, request):
        """
        Метод для добавления товаров в заказ
        """
        chek_auth(request, 'buyer')

        order_id = request.data.get('order_id')
        if order_id:
            try:
                order_id = int(order_id)
            except TypeError:
                return JsonResponse(
                    {'Status': False,
                     'Errors': 'order_id - неверный формат данных'})
            try:
                order = Order.objects.get(id=order_id, user=request.user)
            except ObjectDoesNotExist:
                return JsonResponse(
                    {'Status': False,
                     'Errors': 'У вас нет заказа с указанным id'})
            products = request.data.get('products')
            if products:
                try:
                    products_list = json.loads(products)
                except ValueError:
                    return JsonResponse(
                        {'Status': False,
                         'Errors': 'products - неверный формат данных'})
                for product in products_list:
                    product['order'] = order.id
                    serializer = OrderItemSerializer(data=product)
                    if serializer.is_valid():
                        shop = Shop.objects.get(
                            product_info__id=product['product_info'])
                        if shop.is_active:
                            try:
                                serializer.save()
                            except IntegrityError as error:
                                return JsonResponse(
                                    {'Status': False, 'Errors': str(error)})
                        else:
                            return JsonResponse(
                                {'Status': False,
                                 'Errors': 'Магазин отменил прием заказов'})
                    else:
                        return JsonResponse({'Status': False,
                                             'Errors': serializer.errors})
                return JsonResponse(
                    {'Status': True,
                     'Товары добавлены в заказ с id:': order.id})
            else:
                return JsonResponse(
                    {'Status': False,
                     'Errors': 'В запросе отсутствует список товаров'})
        else:
            return JsonResponse(
                {'Status': False,
                 'Errors': 'В запросе не указан order_id'})


class ContactView(APIView):
    """
    Класс для работы с контактами клиента
    """
    def post(self, request):
        """
        Метод для добавления контактов к заказу
        """
        chek_auth(request, 'buyer')

        order_id = request.data.get('order_id')
        if order_id:
            try:
                order_id = int(order_id)
            except TypeError:
                return JsonResponse(
                    {'Status': False,
                     'Errors': 'order_id - неверный формат данных'})
            try:
                order = Order.objects.get(id=order_id, user=request.user)
                if order.state == 'accepted':
                    return JsonResponse(
                        {'Status': False,
                         'Errors': 'У заказа с order_id контакты определены'})
            except ObjectDoesNotExist:
                return JsonResponse(
                    {'Status': False,
                     'Errors': 'У вас нет заказа с указанным id'})
            contact = request.data.get('contact')
            if contact:
                try:
                    contact_dict = json.loads(contact)
                except ValueError:
                    return JsonResponse(
                        {'Status': False,
                         'Errors': 'contact - неверный формат данных'})
                contact_dict['user'] = request.user.id
                serializer = ContactSerializer(data=contact_dict)
                if serializer.is_valid():
                    try:
                        obj = serializer.save()
                    except IntegrityError as error:
                        return JsonResponse(
                            {'Status': False, 'Errors': str(error)})
                    order.state = 'accepted'
                    order.contact = obj
                    order.save()
                    return JsonResponse(
                        {'Status': True,
                         'Контакт добавлен': 'Заказ подтвержден'})
                else:
                    return JsonResponse(
                        {'Status': False,
                         'Errors': serializer.errors})
            else:
                return JsonResponse(
                    {'Status': False,
                     'Errors': 'В запросе не указан contact'})
        else:
            return JsonResponse(
                {'Status': False, 'Errors': 'В запросе не указан order_id'})

    def delete(self, request):
        """
        Метод для удаления контакта из заказа
        """
        chek_auth(request, 'buyer')

        order_id = request.data.get('order_id')
        if order_id:
            try:
                order_id = int(order_id)
            except TypeError:
                return JsonResponse(
                    {'Status': False,
                     'Errors': 'order_id - неверный формат данных'})
            try:
                order = Order.objects.get(id=order_id, user=request.user)
                orderitem_query = OrderItem.objects.filter(
                    order=order, state='sent')
                if orderitem_query:
                    return JsonResponse(
                        {'Status': False,
                         'Errors': 'Позиция заказа уже отправлена магазином, '
                                   'изменить контакты нге возможно'})
                if order.state == 'not accepted':
                    return JsonResponse(
                        {'Status': False,
                         'Errors': 'У заказа с order_id контактов нет'})
            except ObjectDoesNotExist:
                return JsonResponse(
                    {'Status': False,
                     'Errors': 'У вас нет заказа с указанным id'})
            order.state = 'not accepted'
            order.contact = None
            order.save()
            return JsonResponse({'Status': True})
        else:
            return JsonResponse(
                {'Status': False,
                 'Errors': 'В запросе не указан order_id'})


class OrderShopView(APIView):
    """
    Класс для упраления заказами магазина
    """
    def get(self, request):
        """
        Метод для получения всех подтвержденных заказов от клиентов
        """
        chek_auth(request, 'shop')

        query = OrderItem.objects.filter(product_info__shop__user=request.user,
                                         order__state='accepted')
        serializer = OrderItemSerializer(query, many=True)
        return Response(serializer.data)

    def post(self, request):
        """
        Метод для изменения статуса заказа (отправлен/не отправлен)
        """
        chek_auth(request, 'shop')

        orderitem_id = request.data.get('orderitem_id')
        if orderitem_id:
            try:
                orderitem_id = int(orderitem_id)
            except TypeError:
                return JsonResponse(
                    {'Status': False,
                     'Errors': 'orderitem_id - неверный формат данных'})
            try:
                orderitem = OrderItem.objects.get(id=orderitem_id,
                                                  order__state='accepted')
                if orderitem.state == "sent":
                    orderitem.state = "not sent"
                else:
                    orderitem.state = "sent"
                orderitem.save()
                return JsonResponse(
                    {'Status': True,
                     'Статус заказа изменен на': orderitem.state})
            except ObjectDoesNotExist:
                JsonResponse(
                    {'Status': False,
                     'Errors': 'У вас нет заказа с указанным id'})
        else:
            return JsonResponse({'Status': False,
                                 'Errors': 'В запросе не указан orderitem_id'})

# Create your views here.
