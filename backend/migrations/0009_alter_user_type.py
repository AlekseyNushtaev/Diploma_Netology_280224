# Generated by Django 5.0.2 on 2024-03-05 20:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0008_alter_user_first_name_alter_user_last_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='type',
            field=models.CharField(choices=[('Покупатель', 'Клиент'), ('Магазин', 'Менеджер')], default='Покупатель', verbose_name='Тип пользователя'),
        ),
    ]
