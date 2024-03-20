from django.core.mail import send_mail

from orders.settings import EMAIL_HOST_USER


def mail(subj, msg, mail_to, orderitem):
    new_msg = f'{msg}\n'\
              f'ID заказа клиента: {orderitem.order.pk}\n'\
              f'ID заказа магазина: {orderitem.pk}\n'\
              f'Продукт: {orderitem.product_info.product.name}\n'\
              f'Кол-во: {orderitem.quantity}\n'

    if orderitem.order.contact:
        new_msg += f'Адрес: {orderitem.order.contact.adress}\n'\
                   f'Телефон: {orderitem.order.contact.phone}'

    send_mail(subj, new_msg, EMAIL_HOST_USER, [mail_to])
