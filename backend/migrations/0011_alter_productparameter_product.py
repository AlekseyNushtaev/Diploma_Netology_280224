# Generated by Django 5.0.2 on 2024-03-07 10:29

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0010_alter_user_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='productparameter',
            name='product',
            field=models.ForeignKey(blank=True, on_delete=django.db.models.deletion.CASCADE, related_name='products_parameters', to='backend.product', verbose_name='Продукт'),
        ),
    ]
