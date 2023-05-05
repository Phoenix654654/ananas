from django.contrib import admin
from .models import Product, Category, Cart, Comment

admin.site.register(Category)
admin.site.register(Product)
admin.site.register(Cart)
admin.site.register(Comment)
