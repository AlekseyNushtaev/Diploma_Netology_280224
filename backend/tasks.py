from django.core.mail import send_mail
import time

from orders.settings import EMAIL_HOST_USER
from celery import shared_task


@shared_task
def mail(subj, msg, mail_to, id_order, id_orderitem, product, quantity,
         adress=None, phone=None):
    new_msg = f'{msg}\n'\
              f'ID заказа клиента: {id_order}\n'\
              f'ID заказа магазина: {id_orderitem}\n'\
              f'Продукт: {product}\n'\
              f'Кол-во: {quantity}\n'

    if adress:
        new_msg += f'Адрес: {adress}\n'\
                   f'Телефон: {phone}'
    time.sleep(60)
    send_mail(subj, new_msg, EMAIL_HOST_USER, [mail_to])
