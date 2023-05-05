import django_filters
from .models import Vendor


class VendorFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='icontains')
    second_name = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = Vendor
        fields = ['name', 'second_name']
