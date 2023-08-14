import random

from django.core.cache import cache
from django.db.models import Count, Avg
from django.http import Http404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import permissions, status, filters, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
import jwt
from ananas.settings import SECRET_KEY
from rest_framework_simplejwt import exceptions

from .models import Vendor, Customer, Referral
from .permissions import AnonPermissionOnly
from .serializers import MyTokenObtainPairSerializer, VendorRegisterSerializer, CustomerRegisterSerializer, \
    VendorProfileSerializer, ReferralSerializer, ReferralCodeSerializer
from product.models import Product, Cart
from product.serializers import ProductSerializer


def decode_auth_token(token):
    try:
        user = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
    except jwt.ExpiredSignatureError:
        msg = 'Signature has expired. Login again'
        raise exceptions.AuthenticationFailed(msg)
    except jwt.DecodeError:
        msg = 'Error decoding signature. Type valid token'
        raise exceptions.AuthenticationFailed(msg)
    except jwt.InvalidTokenError:
        raise exceptions.AuthenticationFailed()
    return user



class LoginView(TokenObtainPairView):
    permission_classes = (AnonPermissionOnly,)
    serializer_class = MyTokenObtainPairSerializer


class VendorRegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = VendorRegisterSerializer(data=request.data)
        if serializer.is_valid():
            vendor = Vendor.objects.create(
                email=request.data['email'],
                name=request.data['name'],
                second_name=request.data['second_name'],
                phone_number=request.data['phone_number'],
                description=request.data['description'],
                is_Vendor=True
            )
            vendor.set_password(request.data['password'])
            vendor.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CustomerRegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = CustomerRegisterSerializer(data=request.data)
        if serializer.is_valid():

            referral_code = random.randint(100000, 999999)
            while Customer.objects.filter(referral_code=referral_code).exists():
                referral_code = random.randint(100000, 999999)

            customer = Customer.objects.create(
                email=request.data['email'],
                name=request.data['name'],
                second_name=request.data['second_name'],
                phone_number=request.data['phone_number'],
                card_number=request.data['card_number'],
                address=request.data['address'],
                post_code=request.data['post_code'],
                is_Vendor=False,
                referral_code=referral_code
            )
            customer.set_password(request.data['password'])
            customer.save()
            cart = Cart.objects.create(
                customer=customer
            )
            cart.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VendorList(generics.ListAPIView):
    queryset = Vendor.objects.all()
    serializer_class = VendorRegisterSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['name', 'second_name']
    search_fields = ['name', 'second_name']
    ordering_fields = '__all__'


class CustomerList(generics.ListAPIView):
    queryset = Customer.objects.all()
    serializer_class = CustomerRegisterSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['name', 'second_name']
    search_fields = ['name', 'second_name']
    ordering_fields = '__all__'


class VendorProfileAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def get_object(self, token):
        user = cache.get(token)
        if user:
            print('data from cache')
            return user
        else:
            try:
                user_data = decode_auth_token(token)
                user = Vendor.objects.get(id=user_data['user_id'])
                cache.set(token, user)
                print('data from db')
                return user
            except Vendor.DoesNotExist:
                raise Http404

    def get(self, request, token):
        snippet = self.get_object(token)
        products = Product.objects.filter(vendor=snippet)
        serializer = VendorProfileSerializer(snippet)
        serializer2 = ProductSerializer(products, many=True)
        data = serializer.data
        data['products'] = serializer2.data
        return Response(data, status=status.HTTP_200_OK)

    def put(self, request, token):
        snippet = self.get_object(token)
        serializer = VendorRegisterSerializer(snippet, data=request.data)
        if serializer.is_valid():
            serializer.save()
            cache.set(token, serializer.instance)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, token):
        snippet = self.get_object(token)
        cache.delete(token)
        snippet.delete()
        return Response(status.HTTP_204_NO_CONTENT)


class VendorDetailAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def get_object(self, id):
        try:
            return Vendor.objects.get(id=id)
        except Vendor.DoesNotExist:
            raise Http404

    def get(self, request, id):
        snippet = self.get_object(id)
        products = Product.objects.filter(vendor_id=id)
        serializer = VendorRegisterSerializer(snippet)
        serializer2 = ProductSerializer(products, many=True)
        data = serializer.data
        data['products'] = serializer2.data
        return Response(data, status=status.HTTP_200_OK)


class DashboardUser(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        customer_count = Customer.objects.count()
        vendor_count = Vendor.objects.count()
        avg_count_vendor_product = Vendor.objects.annotate(num_products=Count('product')).aggregate(avg_count=Avg('num_products'))
        vendors = Vendor.objects.annotate(sum_products=Count('product'))
        vendor_product_count = [{'id': v.id, 'name': v.name, 'product_count': v.sum_products} for v in vendors]
        customers = Customer.objects.annotate(avg_cart_products=Count('cart'), count_product_cart=Count('cart__product'))
        customers_count_count = [{'id': v.id, 'name': v.name, 'product_count': v.avg_cart_products} for v in customers]

        data = {
            'customer_count': customer_count,
            'vendor_count': vendor_count,
            'avg_count_vendor_product': avg_count_vendor_product['avg_count'],
            'vendors': vendor_product_count,
            'customers': customers_count_count
        }
        return Response(data)


class ShowCustomerReferralAPIView(APIView):
    def get(self, request, id):
        try:
            customer = Customer.objects.get(id=id)
        except Customer.DoesNotExist:
            return Response({'error': 'Customer not found.'}, status=status.HTTP_404_NOT_FOUND)

        referred_customers = Customer.objects.filter(referral_code_other=customer.referral_code)

        serializer = CustomerRegisterSerializer(referred_customers, many=True)

        return Response({'referral_code': customer.referral_code, 'referred_customers': serializer.data})


class AddReferralCodeOtherAPIView(APIView):
    def post(self, request, id):
        try:
            customer = Customer.objects.get(id=id)
        except Customer.DoesNotExist:
            return Response({'error': 'Customer not found.'}, status=status.HTTP_404_NOT_FOUND)

        referral_code_other = request.data.get('referral_code_other')
        if not referral_code_other:
            return Response({'error': 'Referral code other is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            referred_customer = Customer.objects.get(referral_code=referral_code_other)
        except Customer.DoesNotExist:
            return Response({'error': 'Referred customer not found.'}, status=status.HTTP_404_NOT_FOUND)

        if customer.referral_code_other == 0 or customer.referral_code_other:
            return Response({'error': 'Referral code other already set.'}, status=status.HTTP_400_BAD_REQUEST)

        customer.referral_code_other = referral_code_other
        customer.save()
        referred_customer.referral_customer += 1
        referred_customer.save()

        data = request.data

        return Response(data, status=status.HTTP_200_OK)


class ReferralDetailAPIView(APIView):

    def get_object(self, id):
        try:
            return Customer.objects.get(id=id)
        except Customer.DoesNotExist:
            raise Http404

    def get(self, request, id):
        referral = self.get_object(id)
        serializer = ReferralSerializer(referral)
        buyers = referral.customer.all()
        serializer2 = CustomerRegisterSerializer(buyers, many=True)
        data = serializer.data
        data['buyers'] = serializer2.data
        return Response(data, status=status.HTTP_200_OK)


class AddToReferralAPIView(APIView):
    def get_object(self, user_id):
        try:
            referral = Referral.objects.get(customer=user_id)
            return referral
        except Referral.DoesNotExist:
            raise Http404

    def put(self, request, user_id):
        referral = self.get_object(user_id)
        serializer = ReferralSerializer(referral, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


