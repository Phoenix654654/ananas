from django.urls import path
from .views import (
    ProductList,
    ProductCreateAPIView,
    ProductDetailAPIView,
    ProductUpdateAPIView,
    ProductDeleteAPIView,
    CartDetailAPIView,
    AddToCartAPIView,
    DashboardProduct,
    CreateCheckoutSession,
    CreateCheckoutSessionCart,
    CategoryCreateAPIView,
    ProductCommentView
)

urlpatterns = [
    path('list/', ProductList.as_view(), name='product-list'),
    path('create/', ProductCreateAPIView.as_view(), name='product-create'),
    path('<int:id>/', ProductDetailAPIView.as_view(), name='product-detail'),
    path('<int:id>/update/', ProductUpdateAPIView.as_view(), name='product-update'),
    path('<int:id>/delete/', ProductDeleteAPIView.as_view(), name='product-delete'),

    path('create-category/', CategoryCreateAPIView.as_view(), name='category-create'),

    path('cart/<int:user_id>/', CartDetailAPIView.as_view(), name='cart'),
    path('cart/<int:user_id>/add/', AddToCartAPIView.as_view(), name='add-cart'),

    path('avp/', DashboardProduct.as_view(), name='average-price'),

    path('buy-product/<int:id>/<int:customer_id>/', CreateCheckoutSession.as_view()),
    path('buy-product-cart/<int:id>/', CreateCheckoutSessionCart.as_view()),

    path('products/<int:product_id>/comments/', ProductCommentView.as_view()),

]
