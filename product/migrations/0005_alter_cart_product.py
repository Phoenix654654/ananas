# Generated by Django 4.2 on 2023-04-26 13:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0004_alter_cart_product'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cart',
            name='product',
            field=models.ManyToManyField(blank=True, null=True, to='product.product'),
        ),
    ]
