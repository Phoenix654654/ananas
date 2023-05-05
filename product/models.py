from django.db import models
from user.models import Vendor, Customer
import datetime


class Category(models.Model):
    name = models.CharField(max_length=255, null=False, blank=False)

    def __str__(self):
        return self.name


class Product(models.Model):
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, null=False, blank=False)
    description = models.TextField()
    price = models.IntegerField(null=False, blank=False)

    def __str__(self):
        return self.name


class Cart(models.Model):
    customer = models.OneToOneField(Customer, on_delete=models.CASCADE)
    product = models.ManyToManyField(Product)

    def __str__(self):
        return self.customer.email


class Comment(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    author = models.CharField(max_length=100)
    text = models.TextField()
    created_date = models.DateField(default=datetime.date.today)

    def __str__(self):
        return f'{self.author} comment'

