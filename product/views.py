import stripe
from django.conf import settings
from django.db.models import Avg, Sum, Count
from django.http import Http404
from rest_framework.views import APIView
from rest_framework import permissions, status, generics, filters
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from user.models import Customer
from .models import Product, Category, Cart, Comment
from .serializers import ProductSerializer, CartSerializer, CategorySerializer, CommentSerializer
from user.permissions import IsVendorPermission, IsOwnerOrReadOnly
from user.serializers import CustomerRegisterSerializer

stripe.api_key = settings.STRIPE_SECRET_KEY
webhook_secret = settings.STRIPE_WEBHOOK_SECRET

FRONTEND_CHECKOUT_SUCCESS_URL = settings.CHECKOUT_SUCCESS_URL
FRONTEND_CHECKOUT_FAILED_URL = settings.CHECKOUT_FAILED_URL


class ProductList(generics.ListAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'price']
    search_fields = ['name', 'category__id']
    ordering_fields = '__all__'
    templates = 'index.html'

    def get_context_data(self, **kwargs):
        context = super(ProductList, self).get_context_data(**kwargs)
        context.update({
            "STRIPE_PUBLIC_KEY": settings.STRIPE_PUBLIC_KEY
        })


class ProductCreateAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsVendorPermission]

    def post(self, request):
        serializer = ProductSerializer(data=request.data)
        if serializer.is_valid():
            product = Product.objects.create(
                vendor_id=request.data['vendor'],
                category_id=request.data['category'],
                name=request.data['name'],
                description=request.data['description'],
                price=request.data['price']
            )
            product.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProductDetailAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def get_object(self, id):
        try:
            return Product.objects.get(id=id)
        except Product.DoesNotExist:
            raise Http404

    def get(self, request, id):
        product = self.get_object(id)
        serializer = ProductSerializer(product)
        comments = Comment.objects.filter(product=product)
        serializer2 = CommentSerializer(comments, many=True)
        data = serializer.data
        data['comments'] = serializer2.data
        return Response(data, status=status.HTTP_200_OK)


class ProductUpdateAPIView(APIView):
    permission_classes = [IsVendorPermission, IsOwnerOrReadOnly]

    def get_object(self, id):
        try:
            return Product.objects.get(id=id)
        except Product.DoesNotExist:
            raise Http404

    def put(self, request, id):
        snippet = self.get_object(id)
        serializer = ProductSerializer(snippet, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProductDeleteAPIView(APIView):
    permission_classes = [IsVendorPermission, IsOwnerOrReadOnly]

    def get_object(self, id):
        try:
            return Product.objects.get(id=id)
        except Product.DoesNotExist:
            raise Http404

    def delete(self, request, id):
        snippet = self.get_object(id)
        snippet.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CartDetailAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def get_object(self, user_id):
        try:
            return Cart.objects.get(customer_id=user_id)
        except Product.DoesNotExist:
            raise Http404

    def get(self, request, user_id):
        cart = self.get_object(user_id)
        serializer = CartSerializer(cart)
        prod_serializer = ProductSerializer(cart.product.all(), many=True)
        user_serializer = CustomerRegisterSerializer(cart.customer)
        data = serializer.data
        data['customer'] = user_serializer.data
        data['product'] = prod_serializer.data
        return Response(data, status=status.HTTP_200_OK)


class AddToCartAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def get_object(self, user_id):
        try:
            return Cart.objects.get(customer_id=user_id)
        except Product.DoesNotExist:
            raise Http404

    def put(self, request, user_id):
        cart = self.get_object(user_id)
        serializer = CartSerializer(cart, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CategoryCreateAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = CategorySerializer(data=request.data)
        if serializer.is_valid():
            category = Category.objects.create(
                name=request.data['name'],
            )
            category.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DashboardProduct(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        product_count = Product.objects.count()
        category_count = Category.objects.count()
        average_price = Product.objects.aggregate(avg_price=Avg('price'))
        total_price = Product.objects.aggregate(sum_price=Sum('price'))
        category_price = Category.objects.annotate(product_count=Count('product'), avg_price=Avg('product__price'))
        categories = [{'id': category.id, 'name': category.name, 'product_count': category.product_count, 'сategory_price': category.avg_price} for category in category_price]
        data = {
            'average_price': average_price['avg_price'],
            'product_count': product_count,
            'category_count': category_count,
            'total_price': total_price['sum_price'],
            'categories': categories,
        }
        return Response(data)


class CreateCheckoutSession(APIView):

    def get(self, request, id, customer_id):
        product = Product.objects.get(id=id)

        try:
            customer = Customer.objects.get(id=customer_id)
        except Customer.DoesNotExist:
            return Response({'error': 'Customer not found.'}, status=status.HTTP_404_NOT_FOUND)

        if customer.referral_code_other is not None and customer.referral_code_other != 0:
            discount = 500
        elif customer.referral_customer != 0:
            discount = 500
        else:
            discount = 0

        checkout_session = stripe.checkout.Session.create(
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': product.name,
                    },
                    'unit_amount': product.price - discount
                },
                'quantity': 1
            }],
            mode='payment',
            success_url='https://example.com/checkout/success/',
            cancel_url='https://example.com/checkout/failed/',
        )

        if discount > 0:
            if customer.referral_customer != 0:
                customer.referral_customer -= 1
                customer.save()
            else:
                customer.referral_code_other = 0
                customer.save()

        return Response(checkout_session.url, status=status.HTTP_303_SEE_OTHER)


class CreateCheckoutSessionCart(APIView):
    permission_classes = [permissions.AllowAny]

    def get_object(self, id):
        try:
            return Cart.objects.get(customer_id=id)
        except Product.DoesNotExist:
            raise Http404

    def post(self, request, id):
        cart = self.get_object(id)
        line_items = []
        for product in cart.product.all():
            line_items.append({
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': product.name,
                    },
                    'unit_amount': product.price
                },
                'quantity': 1
            })
        checkout_session = stripe.checkout.Session.create(
            line_items=line_items,
            mode='payment',
            success_url='https://example.com/checkout/success/',
            cancel_url='https://example.com/checkout/failed/',
        )
        return Response(checkout_session.url, status=status.HTTP_303_SEE_OTHER)


class ProductCommentView(APIView):
    def post(self, request, product_id):
        product = Product.objects.get(id=product_id)
        serializer = CommentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(product=product)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)