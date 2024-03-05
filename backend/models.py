from django.contrib.auth.models import AbstractUser
from django.db import models
from backend.managers import UserManager


STATE_CHOICES = (
    (1, 'Новый'),
    (2, 'Подтвержден'),
    (3, 'Отправлен'),
)

TYPE_CHOICES = (
    (1, 'Покупатель'),
    (2, 'Магазин'),
)

class User(AbstractUser):
    """
    Настраиваемая модель пользователя
    """
    email = models.EmailField('email', unique=True)
    first_name = models.CharField('Имя', max_length=30, blank=True)
    last_name = models.CharField('Фамилия', max_length=30, blank=True)
    type = models.CharField('Тип пользователя', choices=TYPE_CHOICES, default='Покупатель')
    username = models.CharField('Username', max_length=150, blank=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        verbose_name = ('Пользователь')
        ordering = ('email',)

    def __str__(self):
        return f'{self.first_name} {self.last_name}'


class Shop(models.Model):
    name = models.CharField(max_length=30, verbose_name='Название магазина')
    file = models.CharField(null=True, blank=True, verbose_name='Файл с прайсом')
    user = models.OneToOneField(User, verbose_name='Пользователь',
                                blank=True, null=True,
                                on_delete=models.CASCADE)
    is_active = models.BooleanField(verbose_name='статус получения заказов', default=True)

    class Meta:
        verbose_name = 'Магазин'
        ordering = ('name',)

    def __str__(self):
        return self.name


class Category(models.Model):
    name = models.CharField(max_length=30, verbose_name='Название категории')

    class Meta:
        verbose_name = 'Категория'
        ordering = ('name',)

    def __str__(self):
        return self.name


class ShopCategory(models.Model):
    shop = models.ForeignKey(Shop, verbose_name='Магазин', related_name='shop_category', blank=True,
                                on_delete=models.CASCADE)
    category = models.ForeignKey(Category, verbose_name='Категория', related_name='category_shop', blank=True,
                                on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Связь категорий и магазинов'

class Product(models.Model):
    name = models.CharField(max_length=50, verbose_name='Название товара')
    category = models.ForeignKey(Category, verbose_name='Категория', related_name='products', blank=True,
                                 on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Товар'
        ordering = ('name',)

    def __str__(self):
        return self.name

class ProductInfo(models.Model):
    product = models.ForeignKey(Product, verbose_name='Продукт', related_name='product_info', blank=True,
                                on_delete=models.CASCADE)
    shop = models.ForeignKey(Shop, verbose_name='Магазин', related_name='product_info', blank=True,
                             on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(verbose_name='Количество')
    price = models.PositiveIntegerField(verbose_name='Цена')

    class Meta:
        verbose_name = 'Информация о продукте в конкретном магазине'


class Parameter(models.Model):
    name = models.CharField(max_length=30, verbose_name='Наименование параметра товара')

    class Meta:
        verbose_name = 'Имя параметра'
        ordering = ('name',)

    def __str__(self):
        return self.name


class ProductParameter(models.Model):
    product = models.ForeignKey(Product, verbose_name='Продукт', related_name='products', blank=True,
                                on_delete=models.CASCADE)
    parameter = models.ForeignKey(Parameter, verbose_name='Параметр', related_name='parameters', blank=True,
                                on_delete=models.CASCADE)
    value = models.CharField(verbose_name='Значение', max_length=50)

    class Meta:
        verbose_name = 'Параметр'


class Contact(models.Model):
    user = models.ForeignKey(User, verbose_name='Пользователь', related_name='contacts', blank=True,
                             on_delete=models.CASCADE)
    adress = models.CharField(verbose_name='Адрес', max_length=100, blank=True)
    phone = models.CharField(verbose_name='Телефон', max_length=30, blank=True)

    class Meta:
        verbose_name = 'Контакт'

    def __str__(self):
        return self.phone

class Order(models.Model):
    user = models.ForeignKey(User, verbose_name='Пользователь', related_name='orders', blank=True,
                             on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    state = models.CharField(verbose_name='Статус', choices=STATE_CHOICES, max_length=15)
    contact = models.ForeignKey(Contact, verbose_name='Контакт', blank=True, null=True,
                                on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Заказ'
        ordering = ('created_at',)

    def __str__(self):
        return str(self.created_at)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, verbose_name='Заказ', related_name='ordered_items', blank=True,
                              on_delete=models.CASCADE)
    product_info = models.ForeignKey(ProductInfo, verbose_name='Информация о продукте',
                                     related_name='ordered_items', blank=True, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(verbose_name='Количество')

    class Meta:
        verbose_name = 'Заказанная позиция'


# Create your models here.
